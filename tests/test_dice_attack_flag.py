"""test_dice_attack_flag.py — dice.py must only assert CRITICAL HIT / FUMBLE on
attack rolls (--attack). A bare d20 is a check/save and gets a neutral nat note.
Spec: docs/superpowers/specs/2026-07-15-dm-authenticity-rules-design.md (rule 4a).
"""
import contextlib
import io
import pathlib
import sys
import unittest

SCRIPTS = pathlib.Path(__file__).resolve().parent.parent / "skills" / "dnd" / "scripts"
sys.path.insert(0, str(SCRIPTS))
import dice  # noqa: E402


def _run_capturing(notation, forced, **kwargs):
    orig = dice.roll_dice
    dice.roll_dice = lambda n, s: list(forced)
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            dice.run(notation, **kwargs)
    finally:
        dice.roll_dice = orig
    return buf.getvalue()


class DiceAttackFlagTests(unittest.TestCase):
    def test_bare_nat20_is_neutral_not_crit(self):
        out = _run_capturing("d20", [20])
        self.assertIn("(nat 20)", out)
        self.assertNotIn("CRITICAL HIT", out)

    def test_bare_nat1_is_neutral_not_fumble(self):
        out = _run_capturing("d20", [1])
        self.assertIn("(nat 1)", out)
        self.assertNotIn("FUMBLE", out)

    def test_attack_nat20_is_critical_hit(self):
        out = _run_capturing("d20", [20], attack=True)
        self.assertIn("CRITICAL HIT", out)

    def test_attack_nat1_is_fumble(self):
        out = _run_capturing("d20", [1], attack=True)
        self.assertIn("FUMBLE", out)


if __name__ == "__main__":
    unittest.main()
