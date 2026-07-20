"""
test_autosave_checkpoint.py — cadence + flag logic for the autosave Stop hook
(v2.2.0). Covers the pure `count_turn()` counter, Session-Flags parsing,
and the active-campaign marker. No Claude Code harness is exercised — only the
deterministic pieces the hook relies on.

Run from repo root:
    python3 -m unittest tests.test_autosave_checkpoint -v
"""
import importlib.util
import json
import os
import pathlib
import sys
import tempfile
import unittest

REPO = pathlib.Path(__file__).resolve().parent.parent
SKILL = REPO / "skills" / "dnd" if (REPO / "skills" / "dnd").is_dir() else REPO
SCRIPTS = SKILL / "scripts"


def _import(name, filename):
    sys.path.insert(0, str(SCRIPTS))
    spec = importlib.util.spec_from_file_location(name, str(SCRIPTS / filename))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TurnCounterTests(unittest.TestCase):
    """`count_turn` is telemetry for --status. It triggers nothing.

    It replaced `decide()`, which returned a block reason on every Nth turn.
    See tests/test_autosave_no_block.py for why that behavior was removed.
    """

    @classmethod
    def setUpClass(cls):
        cls.ac = _import("autosave_checkpoint", "autosave_checkpoint.py")

    def test_increments(self):
        self.assertEqual(self.ac.count_turn({}, 0, every_n=10), 1)

    def test_wraps_at_period(self):
        self.assertEqual(self.ac.count_turn({}, 9, every_n=10), 0)

    def test_holds_when_another_continuation_is_active(self):
        self.assertEqual(
            self.ac.count_turn({"stop_hook_active": True}, 9, every_n=10), 9)

    def test_every_zero_never_wraps(self):
        self.assertEqual(self.ac.count_turn({}, 5, every_n=0), 6)

    def test_full_cycle_wraps_once_per_period(self):
        turns, wraps = 0, 0
        for _ in range(30):
            turns = self.ac.count_turn({}, turns, every_n=10)
            if turns == 0:
                wraps += 1
        self.assertEqual(wraps, 3)


class FlagAndMarkerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ac = _import("autosave_checkpoint", "autosave_checkpoint.py")

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        os.environ["DND_CAMPAIGN_ROOT"] = self.tmp
        os.environ["DND_RUNTIME_DIR"] = os.path.join(self.tmp, ".runtime")
        self.camp_dir = pathlib.Path(self.tmp) / "campaigns" / "test-camp"
        self.camp_dir.mkdir(parents=True)

    def tearDown(self):
        os.environ.pop("DND_CAMPAIGN_ROOT", None)
        os.environ.pop("DND_RUNTIME_DIR", None)

    def _write_state(self, flags_body):
        (self.camp_dir / "state.md").write_text(
            "# Campaign: test-camp\n\n## Session Flags\n" + flags_body + "\n",
            encoding="utf-8",
        )

    def test_autosave_default_on_when_flag_absent(self):
        self._write_state("tutor_mode: false")
        self.assertTrue(self.ac.autosave_enabled("test-camp"))

    def test_autosave_default_on_when_section_absent(self):
        (self.camp_dir / "state.md").write_text("# Campaign: test-camp\n", encoding="utf-8")
        self.assertTrue(self.ac.autosave_enabled("test-camp"))

    def test_autosave_off_respected(self):
        self._write_state("autosave: off")
        self.assertFalse(self.ac.autosave_enabled("test-camp"))

    def test_autosave_on_explicit(self):
        self._write_state("autosave: on")
        self.assertTrue(self.ac.autosave_enabled("test-camp"))

    def test_missing_state_is_disabled(self):
        self.assertFalse(self.ac.autosave_enabled("no-such-camp"))

    def test_active_campaign_marker_roundtrip(self):
        runtime = pathlib.Path(os.environ["DND_RUNTIME_DIR"])
        runtime.mkdir(parents=True, exist_ok=True)
        (runtime / self.ac.ACTIVE_MARKER).write_text(
            json.dumps({"name": "test-camp"}), encoding="utf-8"
        )
        self.assertEqual(self.ac.active_campaign(), "test-camp")

    def test_active_campaign_none_when_no_marker(self):
        self.assertIsNone(self.ac.active_campaign())

    def test_snapshot_writes_recovery_file(self):
        self._write_state("autosave: on")
        self.ac.snapshot("test-camp")
        runtime = pathlib.Path(os.environ["DND_RUNTIME_DIR"])
        self.assertTrue((runtime / "test-camp.autocheckpoint.md").exists())


class LintHeartbeatTests(unittest.TestCase):
    """Caller-owned liveness evidence for the turn lint.

    run_and_log never raises by contract, so the caller's blanket only ever
    catches import death — exactly the observed 2026-07-20 failure class.
    The heartbeat converts silence into evidence: no record in
    .lint-health.jsonl means "the hook never ran", never "the lint died
    quietly".
    """

    CAMPAIGN = "hb-camp"

    @classmethod
    def setUpClass(cls):
        cls.ac = _import("autosave_checkpoint", "autosave_checkpoint.py")

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        os.environ["DND_CAMPAIGN_ROOT"] = self.tmp.name
        os.environ["DND_RUNTIME_DIR"] = os.path.join(self.tmp.name, ".runtime")
        self.addCleanup(lambda: os.environ.pop("DND_CAMPAIGN_ROOT", None))
        self.addCleanup(lambda: os.environ.pop("DND_RUNTIME_DIR", None))
        self.camp = pathlib.Path(self.tmp.name) / "campaigns" / self.CAMPAIGN
        self.camp.mkdir(parents=True)
        (self.camp / "state.md").write_text(
            "# state\n\n## Session Flags\nroll_mode: players\n",
            encoding="utf-8")
        self.transcript = self.camp / "session.jsonl"
        self.transcript.write_text(
            json.dumps({"type": "user",
                        "message": {"role": "user", "content": "hi"}}) + "\n" +
            json.dumps({"type": "assistant",
                        "message": {"role": "assistant",
                                    "content": [{"type": "text",
                                                 "text": "Make a DC 15 check."}]}})
            + "\n", encoding="utf-8")

    def _health(self):
        f = self.camp / ".lint-health.jsonl"
        if not f.exists():
            return []
        return [json.loads(line) for line in
                f.read_text(encoding="utf-8").splitlines()]

    def test_ok_heartbeat_with_findings_count(self):
        self.ac._run_lint({"transcript_path": str(self.transcript),
                           "session_id": "s1"}, self.CAMPAIGN)
        records = self._health()
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["event"], "lint_ok")
        self.assertEqual(records[0]["findings"], 1)  # the DC leak
        self.assertEqual(records[0]["session_id"], "s1")
        self.assertIn("ts", records[0])

    def test_import_death_heartbeat(self):
        broken = type(sys)("turn_lint")  # module with no run_and_log
        saved = sys.modules.get("turn_lint")
        sys.modules["turn_lint"] = broken
        try:
            self.ac._run_lint({"transcript_path": str(self.transcript),
                               "session_id": "s1"}, self.CAMPAIGN)
        finally:
            if saved is not None:
                sys.modules["turn_lint"] = saved
            else:
                del sys.modules["turn_lint"]
        records = self._health()
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["event"], "lint_raised")

    def test_heartbeat_failure_never_raises(self):
        """Best-effort: an unwritable campaign dir must not break the hook."""
        self.ac._run_lint({"transcript_path": str(self.transcript)},
                          "no-such-campaign")  # find_campaign -> nonexistent


if __name__ == "__main__":
    unittest.main()
