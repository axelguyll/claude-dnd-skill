"""test_grid_prose.py — prose contracts for the combat grid + map cue:
SKILL.md (cue bullet, per-turn steps, compaction), SKILL-commands.md (prep
step 4 spec authoring, combat start), SKILL-scripts.md (script syntax),
templates/map-list.md (sidecar note). Spec:
docs/superpowers/specs/2026-07-16-combat-grid-map-cue-design.md
"""
import pathlib
import re
import unittest

DND = pathlib.Path(__file__).resolve().parent.parent / "skills" / "dnd"
SKILL = (DND / "SKILL.md").read_text(encoding="utf-8")
COMMANDS = (DND / "SKILL-commands.md").read_text(encoding="utf-8")
SCRIPTS_DOC = (DND / "SKILL-scripts.md").read_text(encoding="utf-8")
MAP_TEMPLATE = (DND / "templates" / "map-list.md").read_text(encoding="utf-8")


class SkillMdTests(unittest.TestCase):
    def test_map_cue_block_defined(self):
        self.assertIn("🗺 **Map:** *<handle>*", SKILL)

    def test_down_cue_defined(self):
        self.assertIn("down — theater of the mind", SKILL)

    def test_cue_never_invented(self):
        idx = SKILL.find("🗺 **Map:**")
        window = SKILL[idx:idx + 900]
        self.assertIn("never invent", window)

    def test_per_turn_step_b_validates_movement(self):
        seq = SKILL[SKILL.find("Per-turn combat sequence"):]
        block = re.search(r"```(.*?)```", seq, re.S).group(1)
        self.assertIn("grid.py move", block)
        self.assertIn("grid.py range", block)

    def test_per_turn_d2_renders_map(self):
        block = re.search(r"Per-turn combat sequence.*?```(.*?)```",
                          SKILL, re.S).group(1)
        self.assertIn("render_map.py", block)

    def test_compaction_ladder_mentions_positions(self):
        self.assertRegex(SKILL, r"Mid-combat:.*positions")


if __name__ == "__main__":
    unittest.main()
