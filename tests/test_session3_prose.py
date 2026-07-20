"""Guard tests for the session-3 prose patches (2026-07-20, Thornwake notes).

Six of seven hand-noted defects from Thornwake session 1 were one family: names
entering narration without grounding. The knowledge rule shipped that morning
covered only the character-knowledge axis, so it read the player-comprehension
failures as legal. These guards pin both axes, plus NPC knowledge sourcing,
referent resolution, and gendered address.

    python3 -m unittest tests.test_session3_prose -v
"""
import pathlib
import unittest

DND = pathlib.Path(__file__).resolve().parent.parent / "skills" / "dnd"
SKILL = (DND / "SKILL.md").read_text(encoding="utf-8")

RULE = "Every proper noun has to clear two tests"


def window(anchor: str, size: int = 3200) -> str:
    idx = SKILL.find(anchor)
    assert idx != -1, f"anchor not found: {anchor!r}"
    return SKILL[idx:idx + size]


class TwoTestsRuleTests(unittest.TestCase):
    def test_rule_exists(self):
        self.assertIn(RULE, SKILL)

    def test_names_both_axes_explicitly(self):
        block = window(RULE)
        self.assertIn("Does the *character* know it?", block)
        self.assertIn("Can the *player* follow it?", block)

    def test_keeps_the_character_knowledge_test(self):
        """The original axis must survive the rewrite, wording intact."""
        block = window(RULE)
        self.assertIn("witnessed on-screen or been told out loud", block)
        self.assertRegex(block, r"described, not named")

    def test_player_axis_requires_gloss_on_first_use(self):
        block = window(RULE)
        self.assertIn("first use", block)
        self.assertIn("same breath", block)
        self.assertIn("only once", block)

    def test_carries_the_original_two_failures(self):
        self.assertIn("the Warden's cloak is already rounding the corner", SKILL)
        self.assertIn("the drift the ledger's been hinting at", SKILL)

    def test_carries_the_thornwake_failures(self):
        self.assertIn("The ford at Reachwater is churned to soup", SKILL)
        self.assertIn("Ford-Stranger", SKILL)

    def test_sits_with_the_specificity_rule_it_bounds(self):
        """Placement stays load-bearing: 'commit to specifics' creates the pressure."""
        spec = SKILL.find("Commit to specifics, not abstractions")
        rule = SKILL.find(RULE)
        self.assertNotEqual(spec, -1)
        self.assertNotEqual(rule, -1)
        self.assertLess(spec, rule, "the two-tests rule must follow the specificity rule")


class NpcKnowledgeSourcingTests(unittest.TestCase):
    def test_rule_exists(self):
        self.assertIn("An NPC may only act on what they could have learned", SKILL)

    def test_requires_an_on_screen_path(self):
        block = window("An NPC may only act on what they could have learned", 1400)
        self.assertIn("path by which they learned it", block)

    def test_carries_the_real_failures(self):
        block = window("An NPC may only act on what they could have learned", 1400)
        self.assertIn("just left Reeve's Hall", block)
        self.assertIn("private hire", block)

    def test_still_allows_the_world_to_supply_knowledge(self):
        """The rule must not forbid NPCs from telling the PC things."""
        block = window("An NPC may only act on what they could have learned", 1400)
        self.assertIn("says the name out loud, it's the character's too", block)


class ReferentTests(unittest.TestCase):
    def test_rule_exists(self):
        self.assertIn("Referents must resolve", SKILL)

    def test_carries_the_real_failure(self):
        block = window("Referents must resolve", 500)
        self.assertIn("that boy inherited a job", block)


class GenderedAddressTests(unittest.TestCase):
    ANCHOR = "Never assign the PC a gender the sheet doesn't record"

    def test_rule_exists(self):
        self.assertIn(self.ANCHOR, SKILL)

    def test_defaults_to_they_them(self):
        self.assertIn("they/them", window(self.ANCHOR, 700))

    def test_bans_the_observed_forms(self):
        block = window(self.ANCHOR, 700)
        for form in ("ma'am", "sir", "my lady", "lad"):
            self.assertIn(form, block, f"{form!r} not named as banned")

    def test_framed_as_a_sheet_lookup_not_a_judgement(self):
        """Same framing as the advantage rule: a skipped check, not a missed call."""
        block = window(self.ANCHOR, 700)
        self.assertIn("sheet lookup, not a judgement call", block)

    def test_does_not_key_off_name_or_description(self):
        block = window(self.ANCHOR, 700)
        self.assertIn("not the character's description or their name", block)


if __name__ == "__main__":
    unittest.main()
