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


class CommandsMdTests(unittest.TestCase):
    def _prep_step_4(self):
        return re.search(r"^4\. \*\*Asset shopping lists\.\*\*.*?(?=^5\. )",
                         COMMANDS, re.M | re.S).group(0)

    def test_prep_authors_grid_specs(self):
        step = self._prep_step_4()
        self.assertIn("grid.json", step)
        self.assertIn("grid.py validate", step)

    def test_prep_spec_is_spoiler_free(self):
        self.assertIn("terrain only", self._prep_step_4())

    def _combat_start(self):
        return re.search(r"^## `/dm:dnd combat start`.*?(?=^---)",
                         COMMANDS, re.M | re.S).group(0)

    def test_combat_start_emits_cue(self):
        self.assertIn("🗺 **Map:**", self._combat_start())

    def test_combat_start_first_use_confirm(self):
        self.assertIn("confirmed", self._combat_start())

    def test_combat_start_places_positions(self):
        self.assertIn('"pos"', self._combat_start())

    def test_combat_end_clears_map(self):
        self.assertIn("--clear", self._combat_start())
        self.assertIn("down — theater of the mind", self._combat_start())


class MapTemplateTests(unittest.TestCase):
    def test_template_mentions_grid_sidecar(self):
        self.assertIn("grid.json", MAP_TEMPLATE)


if __name__ == "__main__":
    unittest.main()
