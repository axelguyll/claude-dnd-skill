"""session_audit.py — between-session audit checkers (Pass B Cluster A).

Five post-hoc checks, zero per-turn cost, reviewed by a human between
sessions. Each check is tested in both directions: violation caught,
clean session passes.

Run from repo root:
    python -m unittest tests.test_session_audit -v
"""
import json
import os
import pathlib
import sys
import tempfile
import time
import unittest

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "skills" / "dnd" / "scripts"))

import session_audit as sa  # noqa: E402


def _user(text):
    return {"type": "user",
            "message": {"role": "user", "content": text},
            "timestamp": "2026-07-20T18:00:00.000Z"}


def _assistant(text):
    return {"type": "assistant",
            "message": {"role": "assistant",
                        "content": [{"type": "text", "text": text}]},
            "timestamp": "2026-07-20T18:00:05.000Z"}


def _bash(command):
    return {"type": "assistant",
            "message": {"role": "assistant",
                        "content": [{"type": "tool_use", "name": "Bash",
                                     "input": {"command": command}}]},
            "timestamp": "2026-07-20T18:00:06.000Z"}


def _read(file_path):
    return {"type": "assistant",
            "message": {"role": "assistant",
                        "content": [{"type": "tool_use", "name": "Read",
                                     "input": {"file_path": file_path}}]},
            "timestamp": "2026-07-20T18:00:06.000Z"}


def _tool_result():
    return {"type": "user",
            "message": {"role": "user",
                        "content": [{"type": "tool_result", "content": "ok"}]}}


class TranscriptFixture(unittest.TestCase):
    def _write(self, *objs):
        f = tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False,
                                        encoding="utf-8")
        for o in objs:
            f.write(json.dumps(o) + "\n")
        f.close()
        self.addCleanup(os.unlink, f.name)
        return f.name


class DiceProvenanceTests(TranscriptFixture):
    def test_roll_line_without_tool_call_flagged(self):
        turns = sa.parse_turns(self._write(
            _user("i attack"),
            _assistant("The goblin swings. Goblin: d20+4 = 17 — a hit."),
        ))
        out = sa.check_dice_provenance(turns)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["check"], "dice_provenance")

    def test_roll_line_with_dice_call_same_turn_passes(self):
        turns = sa.parse_turns(self._write(
            _user("i attack"),
            _bash("python3 scripts/dice.py d20+4"),
            _tool_result(),
            _assistant("Goblin: d20+4 = 17 — a hit."),
        ))
        self.assertEqual(sa.check_dice_provenance(turns), [])

    def test_combat_py_counts_as_provenance(self):
        turns = sa.parse_turns(self._write(
            _user("i attack"),
            _bash("python3 scripts/combat.py attack --json '[]'"),
            _tool_result(),
            _assistant("**Roll:** d20+4 → 17 against the mail."),
        ))
        self.assertEqual(sa.check_dice_provenance(turns), [])

    def test_tool_call_in_earlier_turn_does_not_cover_later_roll(self):
        turns = sa.parse_turns(self._write(
            _user("i attack"),
            _bash("python3 scripts/dice.py d20+4"),
            _tool_result(),
            _assistant("A hit."),
            _user("i attack again"),
            _assistant("Goblin: d20+4 = 12 — a miss."),
        ))
        out = sa.check_dice_provenance(turns)
        self.assertEqual(len(out), 1)
        self.assertIn("d20+4 = 12", out[0]["excerpt"])

    def test_narration_without_rolls_passes(self):
        turns = sa.parse_turns(self._write(
            _user("i look around"),
            _assistant("Rain in the alley. Nothing moves."),
        ))
        self.assertEqual(sa.check_dice_provenance(turns), [])


class NoXpTests(TranscriptFixture):
    def test_xp_award_tool_call_flagged(self):
        turns = sa.parse_turns(self._write(
            _user("we won"),
            _bash("python3 scripts/xp.py award --campaign c --amount 200"),
        ))
        out = sa.check_no_xp(turns)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["check"], "no_xp")

    def test_xp_award_block_in_text_flagged(self):
        turns = sa.parse_turns(self._write(
            _user("we won"),
            _assistant("The fight ends. Each of you is awarded 150 XP."),
        ))
        self.assertEqual(len(sa.check_no_xp(turns)), 1)

    def test_xp_deprecation_talk_passes(self):
        turns = sa.parse_turns(self._write(
            _user("do we get xp?"),
            _assistant("This campaign levels by milestone — no XP tracking."),
        ))
        self.assertEqual(sa.check_no_xp(turns), [])


class LintLogPrivacyTests(TranscriptFixture):
    def test_read_of_lint_log_flagged(self):
        turns = sa.parse_turns(self._write(
            _user("how am i doing?"),
            _read("C:/dnd/campaigns/thornwake/.lint-log.jsonl"),
        ))
        out = sa.check_lint_log_privacy(turns)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["check"], "lint_log_privacy")

    def test_bash_tail_of_lint_log_flagged(self):
        turns = sa.parse_turns(self._write(
            _user("hm"),
            _bash("python3 scripts/turn_lint.py --campaign thornwake --tail 5"),
        ))
        self.assertEqual(len(sa.check_lint_log_privacy(turns)), 1)

    def test_ordinary_reads_pass(self):
        turns = sa.parse_turns(self._write(
            _user("recap"),
            _read("C:/dnd/campaigns/thornwake/state.md"),
            _bash("python3 scripts/dice.py d20"),
        ))
        self.assertEqual(sa.check_lint_log_privacy(turns), [])


class MicrosaveLivenessTests(TranscriptFixture):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.camp = pathlib.Path(self.tmp.name)
        (self.camp / "state.md").write_text(
            "# state\n\n## Session Flags\nautosave: on\n", encoding="utf-8")
        (self.camp / "session-tail.md").write_text("- beat", encoding="utf-8")

    def _turns(self, n):
        """Turns whose timestamps start 10 minutes ago — mtimes in the tests
        are set relative to now so the comparison is clock-independent."""
        import datetime
        start = datetime.datetime.fromtimestamp(
            time.time() - 600, datetime.timezone.utc)
        entries = []
        for i in range(n):
            ts = (start + datetime.timedelta(seconds=30 * i)).isoformat()
            u, a = _user("go"), _assistant("Narration.")
            u["timestamp"] = ts
            a["timestamp"] = ts
            entries += [u, a]
        return sa.parse_turns(self._write(*entries))

    def test_stale_anchors_over_long_session_flagged(self):
        old = time.time() - 7200
        os.utime(self.camp / "state.md", (old, old))
        os.utime(self.camp / "session-tail.md", (old, old))
        # session started 10 minutes ago — anchors predate it by ~2h
        out = sa.check_microsave_liveness(self._turns(12), self.camp,
                                          min_turns=8)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["check"], "microsave_liveness")

    def test_fresh_anchors_pass(self):
        now = time.time()
        os.utime(self.camp / "state.md", (now, now))
        os.utime(self.camp / "session-tail.md", (now, now))
        self.assertEqual(
            sa.check_microsave_liveness(self._turns(12), self.camp,
                                        min_turns=8), [])

    def test_short_session_not_judged(self):
        old = time.time() - 7200
        os.utime(self.camp / "state.md", (old, old))
        self.assertEqual(
            sa.check_microsave_liveness(self._turns(3), self.camp,
                                        min_turns=8), [])

    def test_autosave_off_not_judged(self):
        (self.camp / "state.md").write_text(
            "# state\n\n## Session Flags\nautosave: off\n", encoding="utf-8")
        old = time.time() - 7200
        os.utime(self.camp / "state.md", (old, old))
        self.assertEqual(
            sa.check_microsave_liveness(self._turns(12), self.camp,
                                        min_turns=8), [])


class StateDivergenceTests(TranscriptFixture):
    STATE = '[{"name": "Piper", "hp": 18, "max_hp": 24}, {"name": "Goblin", "hp": 3, "max_hp": 7}]'

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.camp = pathlib.Path(self.tmp.name)

    def _state_md(self, active_combat_body):
        (self.camp / "state.md").write_text(
            "# state\n\n## Active Combat\n" + active_combat_body +
            "\n\n## Live State Flags\n", encoding="utf-8")

    def _render_turns(self):
        return sa.parse_turns(self._write(
            _user("fight"),
            _bash("python3 scripts/render_tracker.py --campaign c "
                  f"--state '{self.STATE}' --round 2"),
        ))

    def test_matching_block_passes(self):
        self._state_md(self.STATE)
        self.assertEqual(
            sa.check_state_divergence(self._render_turns(), self.camp), [])

    def test_matching_block_reordered_passes(self):
        """Per-turn renders rotate the active actor to the front; the durable
        copy diverges only if a combatant's facts differ."""
        self._state_md('[{"name": "Goblin", "hp": 3, "max_hp": 7}, '
                       '{"name": "Piper", "hp": 18, "max_hp": 24}]')
        self.assertEqual(
            sa.check_state_divergence(self._render_turns(), self.camp), [])

    def test_diverged_hp_flagged(self):
        self._state_md('[{"name": "Piper", "hp": 24, "max_hp": 24}, '
                       '{"name": "Goblin", "hp": 3, "max_hp": 7}]')
        out = sa.check_state_divergence(self._render_turns(), self.camp)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["check"], "state_divergence")
        self.assertIn("Piper", out[0]["detail"])

    def test_missing_combatant_flagged(self):
        self._state_md('[{"name": "Piper", "hp": 18, "max_hp": 24}]')
        out = sa.check_state_divergence(self._render_turns(), self.camp)
        self.assertEqual(len(out), 1)
        self.assertIn("Goblin", out[0]["detail"])

    def test_no_render_calls_passes(self):
        self._state_md("*(none)*")
        turns = sa.parse_turns(self._write(
            _user("talk"), _assistant("Words are had.")))
        self.assertEqual(sa.check_state_divergence(turns, self.camp), [])


if __name__ == "__main__":
    unittest.main()
