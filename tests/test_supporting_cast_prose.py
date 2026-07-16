"""test_supporting_cast_prose.py — prose contracts for the supporting-cast NPC
tier: seeding steps in SKILL-commands.md (new 11.5, prep 1.5), the promotion
rule in SKILL.md, and the template note. Spec:
docs/superpowers/specs/2026-07-16-npc-supporting-cast-design.md
"""
import pathlib
import re
import unittest

DND = pathlib.Path(__file__).resolve().parent.parent / "skills" / "dnd"
COMMANDS = (DND / "SKILL-commands.md").read_text(encoding="utf-8")
SKILL = (DND / "SKILL.md").read_text(encoding="utf-8")
NPCS_TEMPLATE = (DND / "templates" / "npcs.md").read_text(encoding="utf-8")


class NewCommandSeedingTests(unittest.TestCase):
    def test_new_has_step_11_5_supporting_cast(self):
        m = re.search(r"^11\.5 \*\*Supporting cast\.\*\*", COMMANDS, re.M)
        self.assertIsNotNone(m, "new needs step 11.5 'Supporting cast.'")

    def test_step_11_5_seeds_6_to_8_index_only(self):
        step = re.search(r"^11\.5 .*?(?=^\d+\.)", COMMANDS, re.M | re.S).group(0)
        self.assertIn("6–8", step)
        self.assertIn("npcs.md", step)
        self.assertIn("one distinct", step)
        self.assertIn("name-registry", step.lower())
        self.assertNotIn("npcs-full.md entry is required", step)

    def test_step_11_5_excludes_full_entries(self):
        step = re.search(r"^11\.5 .*?(?=^\d+\.)", COMMANDS, re.M | re.S).group(0)
        self.assertIn("No npcs-full.md entry", step)


class PrepSeedingTests(unittest.TestCase):
    def _step_1_5(self):
        return re.search(r"^1\.5 \*\*NPC layer\.\*\*.*?(?=^2\. )",
                         COMMANDS, re.M | re.S).group(0)

    def test_prep_1_5_has_supporting_cast_pass(self):
        self.assertIn("supporting cast", self._step_1_5())

    def test_prep_supporting_pass_is_new_names_only(self):
        self.assertIn("new names only", self._step_1_5())

    def test_prep_supporting_pass_counts_match_new(self):
        self.assertIn("6–8", self._step_1_5())


class PromotionRuleTests(unittest.TestCase):
    def test_skill_md_defines_promotion(self):
        self.assertIn("supporting cast", SKILL)
        self.assertRegex(SKILL, r"author(?:ing)? their full entry")

    def test_promotion_is_before_dialogue(self):
        idx = SKILL.find("supporting cast")
        window = SKILL[idx:idx + 600]
        self.assertIn("before writing the dialogue", window)


class TemplateNoteTests(unittest.TestCase):
    def test_npcs_template_names_the_tier(self):
        self.assertIn("supporting cast", NPCS_TEMPLATE.lower())
        self.assertIn("npcs-full.md", NPCS_TEMPLATE)


if __name__ == "__main__":
    unittest.main()
