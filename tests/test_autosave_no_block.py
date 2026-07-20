"""
test_autosave_no_block.py — the cadence checkpoint must never block the turn.

Measured on the Thornwake session (2026-07-20): each cadence block spawned a
full extra model turn averaging ~33s and returning a few dozen characters to
the player, re-flushing files the DM had already written in-turn. The hook
keeps its deterministic snapshot; it no longer hands work back to the model.

Run from repo root:
    python3 -m unittest tests.test_autosave_no_block -v
"""
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

REPO = pathlib.Path(__file__).resolve().parent.parent
SCRIPTS = REPO / "skills" / "dnd" / "scripts"
HOOK = SCRIPTS / "autosave_checkpoint.py"

CAMPAIGN = "cadence-probe"


class CadenceNeverBlocksTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = pathlib.Path(self.tmp.name)
        camp = root / "campaigns" / CAMPAIGN
        camp.mkdir(parents=True)
        (camp / "state.md").write_text(
            "# State\n\n## Session Flags\n- roll_mode: players\n",
            encoding="utf-8")
        self.env = dict(os.environ)
        self.env["DND_CAMPAIGN_ROOT"] = str(root)
        self.env["DND_RUNTIME_DIR"] = str(root / ".runtime")
        self.root = root

    def tearDown(self):
        self.tmp.cleanup()

    def _run(self, *extra):
        return subprocess.run(
            [sys.executable, str(HOOK), "--campaign", CAMPAIGN, *extra],
            capture_output=True, text=True, env=self.env, cwd=str(REPO))

    def test_cadence_turn_emits_no_block(self):
        """--every 1 makes every turn a cadence turn; none may block."""
        for _ in range(3):
            result = self._run("--every", "1")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), "",
                             "cadence turn wrote a Stop-hook decision to stdout")

    def test_no_decision_json_on_any_turn(self):
        for turn in range(1, 13):
            result = self._run("--every", "10")
            self.assertNotIn("decision", result.stdout,
                             f"turn {turn} emitted a hook decision")

    def test_snapshot_still_taken(self):
        """Deterministic durability must survive the change."""
        self._run("--every", "1")
        snaps = list((self.root / ".runtime").glob("*.autocheckpoint.md"))
        self.assertTrue(snaps, "no state snapshot written")
        self.assertIn("Session Flags", snaps[0].read_text(encoding="utf-8"))

    def test_status_still_reports(self):
        result = self._run("--status")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("active_campaign", result.stdout)


class NoCheckpointInstructionTests(unittest.TestCase):
    """The instruction string that spawned the extra turn must be gone."""

    def test_module_defines_no_checkpoint_reason(self):
        source = HOOK.read_text(encoding="utf-8")
        self.assertNotIn("CHECKPOINT_REASON", source)
        self.assertNotIn('"decision": "block"', source)
        self.assertNotIn("'decision': 'block'", source)
        self.assertNotIn(json.dumps({"decision": "block"})[:20], source)


if __name__ == "__main__":
    unittest.main()
