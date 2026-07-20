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

    def test_status_sees_hook_counter(self):
        """The count must round-trip through the real hook path.

        The regression: the hook wrote a session-keyed counter file while
        --status read a campaign-keyed one, so the counter's only consumer
        always saw 0 whenever the harness supplied a session id.
        """
        runtime = self.root / ".runtime"
        runtime.mkdir(exist_ok=True)
        (runtime / "active-campaign.json").write_text(
            json.dumps({"name": CAMPAIGN}), encoding="utf-8")
        transcript = self.root / "play.jsonl"
        transcript.write_text(
            json.dumps({"type": "user",
                        "message": {"role": "user",
                                    "content": f"/dm:dnd load {CAMPAIGN}"}}) + "\n",
            encoding="utf-8")
        payload = json.dumps({"session_id": "play-1",
                              "transcript_path": str(transcript),
                              "hook_event_name": "Stop",
                              "stop_hook_active": False})
        for _ in range(3):
            result = subprocess.run(
                [sys.executable, str(HOOK)], input=payload,
                capture_output=True, text=True, env=self.env, cwd=str(REPO))
            self.assertEqual(result.returncode, 0, result.stderr)
        status = self._run("--status")
        self.assertIn("turn_counter: 3", status.stdout)


class NoCheckpointInstructionTests(unittest.TestCase):
    """The instruction string that spawned the extra turn must be gone."""

    def test_module_defines_no_checkpoint_reason(self):
        source = HOOK.read_text(encoding="utf-8")
        self.assertNotIn("CHECKPOINT_REASON", source)
        self.assertNotIn('"decision": "block"', source)
        self.assertNotIn("'decision': 'block'", source)
        self.assertNotIn(json.dumps({"decision": "block"})[:20], source)


class DocsPromiseNoBackstopTests(unittest.TestCase):
    """The SKILL files must not promise the removed cadence-prompt backstop.

    bd4fc69 removed the block decision from the hook; the docs kept telling
    the DM a prompting safety net exists. The micro-save now rides on the
    scene-boundary habit alone, and the docs must say so.
    """

    DND = REPO / "skills" / "dnd"

    def test_no_ghost_backstop_strings(self):
        skill = (self.DND / "SKILL.md").read_text(encoding="utf-8")
        scripts = (self.DND / "SKILL-scripts.md").read_text(encoding="utf-8")
        commands = (self.DND / "SKILL-commands.md").read_text(encoding="utf-8")
        self.assertNotIn("will also prompt this flush", skill)
        self.assertNotIn("prompts the DM to flush", scripts)
        self.assertNotIn("block` decision", scripts)
        self.assertNotIn("prompts a micro-save", commands)

    def test_no_line_claims_the_hook_prompts(self):
        for name in ("SKILL.md", "SKILL-scripts.md", "SKILL-commands.md"):
            text = (self.DND / name).read_text(encoding="utf-8")
            for i, line in enumerate(text.splitlines(), 1):
                low = line.lower()
                if "hook" in low and "prompt" in low:
                    self.fail(f"{name}:{i} pairs 'hook' with 'prompt': {line[:120]}")


if __name__ == "__main__":
    unittest.main()
