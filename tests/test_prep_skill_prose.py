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
SCRIPTS = (DND / "SKILL-scripts.md").read_text(encoding="utf-8")


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

    def test_beat_complete_handles_multi_level_jump(self):
        # milestone jumps can span >1 level (e.g. 4 -> 6); the procedure must loop
        idx = CMDS.find("/dm:dnd beat complete")
        section = CMDS[idx: idx + 900]
        self.assertIn("once per level", section)

    def test_beat_complete_clears_pending_marker(self):
        idx = CMDS.find("/dm:dnd beat complete")
        section = CMDS[idx: idx + 900]
        self.assertIn("--clear", section)

    def test_combat_end_awards_no_xp(self):
        self.assertNotIn("⭐ XP Awarded", CMDS)
        self.assertNotIn("send XP summary", CMDS)

    def test_xp_award_script_deprecated(self):
        # xp.py award must be signposted as deprecated under milestone leveling
        idx = SCRIPTS.find("xp.py")
        self.assertNotEqual(idx, -1)
        self.assertIn("deprecated", SCRIPTS.lower())


if __name__ == "__main__":
    unittest.main()
