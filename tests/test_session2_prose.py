"""Guard tests for the two session-2 prose patches (2026-07-20).

Both close gaps found by hand during play that the turn lint scored 0.00/turn on:
the PC knowledge boundary (narration naming things the character can't know) and
advantage/disadvantage settled before the roll rather than after the result.

    python3 -m unittest tests.test_session2_prose -v
"""
import pathlib
import unittest

DND = pathlib.Path(__file__).resolve().parent.parent / "skills" / "dnd"
SKILL = (DND / "SKILL.md").read_text(encoding="utf-8")


class KnowledgeBoundaryTests(unittest.TestCase):
    def test_rule_exists(self):
        self.assertIn("Name only what the character could actually know", SKILL)

    def test_states_the_describe_dont_name_default(self):
        self.assertRegex(SKILL, r"describe(?:d)?,? not name(?:d)?")

    def test_carries_both_real_failure_examples(self):
        self.assertIn("the Warden's cloak is already rounding the corner", SKILL)
        self.assertIn("the drift the ledger's been hinting at", SKILL)

    def test_names_the_witnessed_or_told_test(self):
        self.assertRegex(SKILL, r"witnessed on-screen or been told")

    def test_allows_npcs_to_supply_knowledge_in_fiction(self):
        """The rule must not forbid the world from telling the PC things."""
        idx = SKILL.find("Name only what the character could actually know")
        window = SKILL[idx:idx + 2600]
        self.assertIn("say so out loud", window)

    def test_sits_with_the_specificity_rule_it_bounds(self):
        """Placement is load-bearing: 'commit to specifics' creates the pressure."""
        spec = SKILL.find("Commit to specifics, not abstractions")
        know = SKILL.find("Name only what the character could actually know")
        self.assertNotEqual(spec, -1)
        self.assertNotEqual(know, -1)
        self.assertLess(spec, know, "knowledge rule must follow the specificity rule")


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
