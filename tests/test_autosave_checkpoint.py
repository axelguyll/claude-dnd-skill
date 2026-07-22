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


class SessionClaimEvidenceTests(unittest.TestCase):
    """Which user commands prove this session is the one playing the campaign.

    `/dm:dnd load` was the only accepted evidence, so a session that CREATED a
    campaign and played it straight away never claimed the unbound marker:
    every Stop hook returned above `_run_lint` and `snapshot`, costing that
    campaign both turn lint and automatic durability. Observed on
    "the-long-ward" (created and played 2026-07-22); manual `/dm:dnd save`
    still worked, which hid it.
    """

    CAMPAIGN = "the-long-ward"

    @classmethod
    def setUpClass(cls):
        cls.ac = _import("autosave_checkpoint", "autosave_checkpoint.py")

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def _transcript(self, *entries):
        """Write a transcript; str entries are genuine user messages."""
        path = pathlib.Path(self.tmp.name) / "session.jsonl"
        lines = [
            json.dumps({"type": "user",
                        "message": {"role": "user", "content": e}})
            if isinstance(e, str) else json.dumps(e)
            for e in entries
        ]
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return str(path)

    @staticmethod
    def _cmd(args):
        """A real harness-encoded slash invocation, verbatim in transcript form."""
        return ("<command-message>dm:dnd</command-message>\n"
                "<command-name>/dm:dnd</command-name>\n"
                f"<command-args>{args}</command-args>")

    def _claims(self, *entries):
        return self.ac.transcript_loaded_campaign(
            self._transcript(*entries), self.CAMPAIGN)

    # --- harness-encoded invocations (how real commands actually appear) ---

    def test_harness_encoded_prep_claims(self):
        self.assertTrue(self._claims(self._cmd("prep")))

    def test_harness_encoded_load_claims(self):
        """The old regex never matched this: `/dm:dnd` is followed by
        `</command-name>`, so `/dm:dnd\\s+load` could not span the tags."""
        self.assertTrue(self._claims(self._cmd("load the-long-ward")))

    def test_harness_encoded_natural_language_create_claims(self):
        """Args are free text, not a parsed subcommand — real sessions carry
        'new campaign', 'start a new prep campaign', 'new campaign prep setup'."""
        self.assertTrue(self._claims(self._cmd("start a new prep campaign")))

    def test_harness_encoded_load_of_other_campaign_does_not_claim(self):
        self.assertFalse(self._claims(self._cmd("load the-hollow-crown")))

    def test_harness_encoded_save_does_not_claim(self):
        self.assertFalse(self._claims(self._cmd("save campaign progress")))

    def test_bare_dm_dnd_without_args_does_not_claim(self):
        """`/dm:dnd` alone carries no verb — the intent is unknowable."""
        self.assertFalse(self._claims(self._cmd("")))

    # --- prose mentions are not invocations ---

    def test_mid_sentence_prose_mention_does_not_claim(self):
        self.assertFalse(self._claims(
            "they never type load, they use /dm:dnd prep, /dm:dnd new, "
            "or /dm:dnd import instead"))

    def test_backtick_prose_mention_does_not_claim(self):
        self.assertFalse(self._claims(
            "the `/dm:dnd new` path skips leveling, see `/dm:dnd prep`"))

    # --- create-family evidence (the bug) ---

    def test_prep_claims(self):
        self.assertTrue(self._claims("/dm:dnd prep the-long-ward"))

    def test_prep_with_option_args_claims(self):
        """prep's real signature takes key:value options, never the slug."""
        self.assertTrue(self._claims('/dm:dnd prep premise:"a walled city"'))

    def test_bare_prep_claims(self):
        self.assertTrue(self._claims("/dm:dnd prep"))

    def test_new_with_quoted_name_claims(self):
        """`new` names the campaign, but the typed form need not be the slug."""
        self.assertTrue(self._claims('/dm:dnd new "The Long Ward" grimdark'))

    def test_import_claims_despite_filepath_argument(self):
        """import's first argument is a file, not the campaign name."""
        self.assertTrue(self._claims("/dm:dnd import ~/modules/ward.pdf"))

    # --- load evidence (unchanged) ---

    def test_bare_load_claims(self):
        self.assertTrue(self._claims("/dm:dnd load"))

    def test_load_of_named_campaign_claims(self):
        self.assertTrue(self._claims("/dm:dnd load the-long-ward"))

    def test_load_of_other_campaign_does_not_claim(self):
        self.assertFalse(self._claims("/dm:dnd load some-other-camp"))

    # --- everything else stays out ---

    def test_unrelated_session_does_not_claim(self):
        self.assertFalse(self._claims(
            "fix the autosave hook", "run the tests again"))

    def test_prep_quoted_in_assistant_text_does_not_claim(self):
        self.assertFalse(self._claims(
            {"type": "assistant",
             "message": {"role": "assistant",
                         "content": [{"type": "text",
                                      "text": "Run /dm:dnd prep to begin."}]}}))

    def test_prep_inside_tool_result_does_not_claim(self):
        self.assertFalse(self._claims(
            {"type": "user",
             "message": {"role": "user",
                         "content": [{"type": "tool_result",
                                      "content": "/dm:dnd prep the-long-ward"}]}}))

    def test_unrelated_subcommand_does_not_claim(self):
        self.assertFalse(self._claims("/dm:dnd list", "/dm:dnd roll 1d20"))


if __name__ == "__main__":
    unittest.main()
