"""test_prep_skill_prose.py — structural invariants on the forked SKILL prose:
milestone leveling replaced XP awards, and the new commands exist.

Run from repo root:
    python3 -m unittest tests.test_prep_skill_prose -v
"""
import pathlib
import unittest

REPO = pathlib.Path(__file__).resolve().parent.parent
DND = REPO / "skills" / "dnd"
SKILL = (DND / "SKILL.md").read_text(encoding="utf-8")
CMDS = (DND / "SKILL-commands.md").read_text(encoding="utf-8")


class SkillProseTests(unittest.TestCase):
    def test_xp_awards_section_replaced_by_milestone(self):
        self.assertNotIn("## XP Awards", SKILL)
        self.assertIn("## Milestone Leveling", SKILL)

    def test_milestone_section_disclaims_xp(self):
        idx = SKILL.find("## Milestone Leveling")
        section = SKILL[idx: idx + 1500]
        self.assertIn("no XP", section)

    def test_prep_and_beat_commands_exist(self):
        self.assertIn("/dm:dnd prep", CMDS)
        self.assertIn("/dm:dnd beat complete", CMDS)

    def test_deed_cite_rule_present(self):
        self.assertIn("cite a deed", CMDS)

    def test_level_up_gate_reconciled_for_milestone(self):
        # milestone campaigns must bypass the /dm:dnd level up XP gate
        self.assertIn("Milestone campaigns bypass this gate", CMDS)


if __name__ == "__main__":
    unittest.main()
