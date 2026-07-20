"""test_turn_lint.py — detector + transcript-parsing tests for the log-only turn lint.

Run from repo root:
    python3 -m unittest tests.test_turn_lint -v
"""
import json
import os
import pathlib
import sys
import tempfile
import unittest

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "skills" / "dnd" / "scripts"))

import turn_lint  # noqa: E402

FLAGS_PLAYERS = {"roll_mode": "players"}
FLAGS_AUTO = {"roll_mode": "auto"}


class RoteCloserTests(unittest.TestCase):
    def test_flags_stock_closer(self):
        text = "The reeve turns away. Holg — what do you do?"
        self.assertEqual(len(turn_lint.check_rote_closer(text)), 1)

    def test_flags_whats_your_move(self):
        self.assertEqual(
            len(turn_lint.check_rote_closer("The door creaks. What's your move?")), 1)

    def test_allows_real_options_closer(self):
        text = "The gate is shut. Fight, or find another way out — or something else?"
        self.assertEqual(turn_lint.check_rote_closer(text), [])

    def test_only_scans_turn_end(self):
        text = ("Early on he asked 'what do you do for coin?' and laughed. "
                + "The night market unfolds ahead of you. " * 20)
        self.assertEqual(turn_lint.check_rote_closer(text), [])


class DcLeakTests(unittest.TestCase):
    def test_flags_dc_number(self):
        out = turn_lint.check_dc_leak("Make a DC 15 Strength check to hold the gate.")
        self.assertEqual(len(out), 1)
        self.assertIn("DC 15", out[0]["detail"])

    def test_tutor_line_exempt(self):
        text = "> ◈ Tutor: You failed by 3 — the lock was DC 15 against your +2."
        self.assertEqual(turn_lint.check_dc_leak(text), [])

    def test_spell_save_dc_exempt(self):
        text = "The goblin rolls against your spell save DC 13 and shrieks."
        self.assertEqual(turn_lint.check_dc_leak(text), [])

    def test_clean_narration_passes(self):
        self.assertEqual(turn_lint.check_dc_leak("The lock gives. You're in."), [])


class RollNotFinalTests(unittest.TestCase):
    REQUEST = "Give me a Wisdom (Perception) check — d20 plus your Wisdom."
    PADDING = "The alley smells of rain and old rope, and somewhere a shutter bangs. " * 8

    def test_flags_request_followed_by_narration(self):
        out = turn_lint.check_roll_not_final(self.REQUEST + " " + self.PADDING, "players")
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["detector"], "roll_not_final")

    def test_request_at_turn_end_passes(self):
        text = self.PADDING + " " + self.REQUEST
        self.assertEqual(turn_lint.check_roll_not_final(text, "players"), [])

    def test_short_option_tail_allowed(self):
        text = self.REQUEST + " …or you can back away quietly instead."
        self.assertEqual(turn_lint.check_roll_not_final(text, "players"), [])

    def test_auto_mode_skipped(self):
        text = self.REQUEST + " " + self.PADDING
        self.assertEqual(turn_lint.check_roll_not_final(text, "auto"), [])

    def test_no_request_no_finding(self):
        self.assertEqual(turn_lint.check_roll_not_final(self.PADDING, "players"), [])


class PcAutoRollTests(unittest.TestCase):
    def test_flags_transcript_style_resolved_check(self):
        # Verbatim shape of the session-1 violation.
        line = "**Roll:** Wisdom (Animal Handling), d20+0 → **19**"
        out = turn_lint.check_pc_auto_roll(line, "players")
        self.assertEqual(len(out), 1)
        self.assertIn("skill check", out[0]["detail"])

    def test_flags_resolved_save(self):
        line = "**Roll:** Dexterity save, d20+2 -> 11"
        self.assertEqual(len(turn_lint.check_pc_auto_roll(line, "players")), 1)

    def test_npc_attack_format_passes(self):
        line = "Goblin attacks: d20+4 = 17 vs AC 16 — hit! 1d6+2 = 5 piercing damage"
        self.assertEqual(turn_lint.check_pc_auto_roll(line, "players"), [])

    def test_auto_mode_skipped(self):
        line = "**Roll:** Wisdom (Perception), d20+0 → **12**"
        self.assertEqual(turn_lint.check_pc_auto_roll(line, "auto"), [])


class UnknownCueTests(unittest.TestCase):
    AMBIENT = {"underwatch-town", "crypt-drips"}
    MAPS = {"cavern-large"}

    def test_known_sound_cue_passes(self):
        text = "🔊 **Cue:** *underwatch-town*"
        self.assertEqual(turn_lint.check_unknown_cue(text, self.AMBIENT, self.MAPS), [])

    def test_unknown_sound_cue_flagged(self):
        text = "🔊 **Cue:** *battle-drums*"
        out = turn_lint.check_unknown_cue(text, self.AMBIENT, self.MAPS)
        self.assertEqual(len(out), 1)
        self.assertIn("battle-drums", out[0]["detail"])

    def test_map_down_cue_always_allowed(self):
        text = "🗺 **Map:** *down — theater of the mind*"
        self.assertEqual(turn_lint.check_unknown_cue(text, self.AMBIENT, self.MAPS), [])

    def test_unknown_map_cue_flagged(self):
        text = "🗺 **Map:** *volcano-lair*"
        self.assertEqual(
            len(turn_lint.check_unknown_cue(text, self.AMBIENT, self.MAPS)), 1)


def _jsonl(*objs) -> str:
    return "\n".join(json.dumps(o) for o in objs) + "\n"


def _user(text):
    return {"type": "user", "message": {"role": "user", "content": text}}


def _assistant_text(text):
    return {"type": "assistant",
            "message": {"role": "assistant",
                        "content": [{"type": "text", "text": text}]}}


def _tool_use(command):
    return {"type": "assistant",
            "message": {"role": "assistant",
                        "content": [{"type": "tool_use", "name": "Bash",
                                     "input": {"command": command}}]}}


def _tool_result():
    return {"type": "user",
            "message": {"role": "user",
                        "content": [{"type": "tool_result", "content": "ok"}]}}


class LastTurnTests(unittest.TestCase):
    def test_collects_text_since_last_genuine_user_message(self):
        transcript = _jsonl(
            _user("hello"),
            _assistant_text("OLD TURN — must not appear"),
            _user("i want to catch the horse"),
            _assistant_text("He moves in low and steady."),
            _tool_use("python3 dice.py d20+0"),
            _tool_result(),
            _assistant_text("**Roll:** d20+0 → 19. The mare settles."),
        )
        with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False,
                                         encoding="utf-8") as f:
            f.write(transcript)
            path = f.name
        try:
            text = turn_lint.last_turn(path)
        finally:
            os.unlink(path)
        self.assertIn("moves in low", text)
        self.assertIn("The mare settles", text)
        self.assertNotIn("OLD TURN", text)

    def test_missing_file_returns_empty(self):
        self.assertEqual(turn_lint.last_turn("/nonexistent/t.jsonl"), "")


class RunAndLogTests(unittest.TestCase):
    def test_writes_findings_to_campaign_log(self):
        with tempfile.TemporaryDirectory() as root:
            camp = pathlib.Path(root) / "campaigns" / "lint-test-camp"
            camp.mkdir(parents=True)
            (camp / "state.md").write_text(
                "# state\n\n## Session Flags\nroll_mode: players\n",
                encoding="utf-8")
            transcript = camp / "session.jsonl"
            transcript.write_text(_jsonl(
                _user("hi"),
                _assistant_text("Make a DC 15 check. Holg — what do you do?"),
            ), encoding="utf-8")
            old = os.environ.get("DND_CAMPAIGN_ROOT")
            os.environ["DND_CAMPAIGN_ROOT"] = root
            try:
                n = turn_lint.run_and_log(
                    {"transcript_path": str(transcript), "session_id": "s1"},
                    "lint-test-camp")
            finally:
                if old is None:
                    del os.environ["DND_CAMPAIGN_ROOT"]
                else:
                    os.environ["DND_CAMPAIGN_ROOT"] = old
            self.assertEqual(n, 2)  # dc_leak + rote_closer
            log = (camp / turn_lint.LOG_NAME).read_text(encoding="utf-8")
            entries = [json.loads(line) for line in log.splitlines()]
            detectors = {e["detector"] for e in entries}
            self.assertEqual(detectors, {"dc_leak", "rote_closer"})

    def test_turn_lint_off_flag_disables(self):
        with tempfile.TemporaryDirectory() as root:
            camp = pathlib.Path(root) / "campaigns" / "lint-test-camp"
            camp.mkdir(parents=True)
            (camp / "state.md").write_text(
                "# state\n\n## Session Flags\nroll_mode: players\nturn_lint: off\n",
                encoding="utf-8")
            transcript = camp / "session.jsonl"
            transcript.write_text(_jsonl(
                _user("hi"), _assistant_text("Make a DC 15 check.")),
                encoding="utf-8")
            old = os.environ.get("DND_CAMPAIGN_ROOT")
            os.environ["DND_CAMPAIGN_ROOT"] = root
            try:
                n = turn_lint.run_and_log(
                    {"transcript_path": str(transcript)}, "lint-test-camp")
            finally:
                if old is None:
                    del os.environ["DND_CAMPAIGN_ROOT"]
                else:
                    os.environ["DND_CAMPAIGN_ROOT"] = old
            self.assertEqual(n, 0)
            self.assertFalse((camp / turn_lint.LOG_NAME).exists())


class AllTurnsTests(unittest.TestCase):
    """Backfill support — lint a whole session, not just its final turn.

    Needed because the Stop hook can be broken or absent while play happens
    (the `python3` interpreter regression, 2026-07-20): the transcript is the
    only surviving record of those turns.
    """

    def _write(self, *objs):
        f = tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False,
                                        encoding="utf-8")
        f.write(_jsonl(*objs))
        f.close()
        self.addCleanup(os.unlink, f.name)
        return f.name

    def test_splits_on_genuine_user_messages(self):
        path = self._write(
            _user("i climb out"), _assistant_text("The shutter gives."),
            _user("i run"), _assistant_text("The alley opens."),
            _user("i stop"), _assistant_text("Rain, and nothing else."),
        )
        self.assertEqual(len(turn_lint.all_turns(path)), 3)

    def test_tool_results_do_not_split_turns(self):
        path = self._write(
            _user("i roll"),
            _assistant_text("Rolling."),
            _tool_use("python3 dice.py d20+3"),
            _tool_result(),
            _assistant_text("19 — the mare settles."),
        )
        turns = turn_lint.all_turns(path)
        self.assertEqual(len(turns), 1)
        self.assertIn("Rolling.", turns[0])
        self.assertIn("the mare settles", turns[0])

    def test_last_turn_matches_final_all_turns_entry(self):
        path = self._write(
            _user("a"), _assistant_text("first"),
            _user("b"), _assistant_text("second"),
        )
        self.assertEqual(turn_lint.all_turns(path)[-1], turn_lint.last_turn(path))

    def test_missing_transcript_returns_empty(self):
        self.assertEqual(turn_lint.all_turns("/no/such/transcript.jsonl"), [])


if __name__ == "__main__":
    unittest.main()
