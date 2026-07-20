"""Guard tests for the session-2 prose patches (2026-07-20).

Closes a gap found by hand during play that the turn lint scored 0.00/turn on:
advantage/disadvantage settled before the roll rather than after the result.

The PC knowledge boundary also shipped in session 2 and was guarded here. It was
restructured the same day (Thornwake notes showed it covered only one of the two
axes it appeared to cover), and its guards now live in tests/test_session3_prose.py
— which asserts a superset: both axes, all four failure examples, and the same
placement invariant.

    python3 -m unittest tests.test_session2_prose -v
"""
import pathlib
import unittest

DND = pathlib.Path(__file__).resolve().parent.parent / "skills" / "dnd"
SKILL = (DND / "SKILL.md").read_text(encoding="utf-8")


class AdvantageBeforeRollTests(unittest.TestCase):
    def test_rule_exists(self):
        self.assertIn("Settle advantage and disadvantage", SKILL)

    def test_forbids_adjusting_after_the_result(self):
        self.assertRegex(SKILL, r"never after the number comes back")

    def test_names_armor_as_a_sheet_lookup(self):
        idx = SKILL.find("Settle advantage and disadvantage")
        window = SKILL[idx:idx + 1400]
        self.assertIn("Stealth disadvantage", window)
        self.assertIn("chain mail", window.lower())

    def test_requires_same_breath_as_the_request(self):
        idx = SKILL.find("Settle advantage and disadvantage")
        window = SKILL[idx:idx + 1400]
        self.assertIn("same breath", window)

    def test_lives_in_the_roll_mode_block(self):
        block = SKILL.find("Roll handling is chosen at game start")
        rule = SKILL.find("Settle advantage and disadvantage")
        # `roll_mode: auto` also appears up in the conditions rule (~:221), so
        # search for the bullet from the new rule forward, not from the top.
        auto = SKILL.find("- **`roll_mode: auto`", rule)
        self.assertNotEqual(block, -1)
        self.assertNotEqual(auto, -1, "auto-mode bullet not found after the rule")
        self.assertLess(block, rule, "rule must sit inside the roll-mode block")
        self.assertLess(rule, auto, "rule must precede the auto-mode bullet")


if __name__ == "__main__":
    unittest.main()
