"""test_render_tracker.py — render_tracker.py builds combat-tracker HTML from
combatant STATE_JSON + tracker.json + SRD condition text. Pure-function tests,
no filesystem. Spec: docs/superpowers/specs/2026-07-15-dm-tool-html-dashboard-design.md
"""
import pathlib
import sys
import unittest

SCRIPTS = pathlib.Path(__file__).resolve().parent.parent / "skills" / "dnd" / "scripts"
sys.path.insert(0, str(SCRIPTS))
import render_tracker  # noqa: E402

SRD = {"conditions": [
    {"name": "Poisoned", "index": "poisoned",
     "description": "- A poisoned creature has disadvantage on attack rolls and ability checks."},
    {"name": "Frightened", "index": "frightened",
     "description": "- A frightened creature has disadvantage on ability checks and attack rolls while the source of its fear is within line of sight."},
]}


class ConditionEffectsTests(unittest.TestCase):
    def test_collapses_srd_bullets_to_one_line(self):
        eff = render_tracker.condition_effects(SRD)
        self.assertEqual(
            eff["poisoned"],
            "A poisoned creature has disadvantage on attack rolls and ability checks.")


class RenderTrackerTests(unittest.TestCase):
    def setUp(self):
        self.eff = render_tracker.condition_effects(SRD)
        self.combatants = [
            {"name": "Ogre", "hp": 20, "max_hp": 59, "ac": 11,
             "initiative": 8, "conditions": ["poisoned"]},
            {"name": "Piper", "hp": 18, "max_hp": 24, "ac": 15,
             "initiative": 14, "conditions": []},
        ]

    def test_header_and_hp_render(self):
        out = render_tracker.render_tracker_html(self.combatants, 2, {}, self.eff)
        self.assertIn("Round 2", out)
        self.assertIn("Ogre", out)
        self.assertIn("20/59", out)

    def test_condition_effect_text_is_inline(self):
        out = render_tracker.render_tracker_html(self.combatants, 2, {}, self.eff)
        self.assertIn("disadvantage on attack rolls and ability checks", out)

    def test_first_row_is_active(self):
        out = render_tracker.render_tracker_html(self.combatants, 2, {}, self.eff)
        self.assertIn('class="row active"', out)

    def test_meta_refresh_present(self):
        out = render_tracker.render_tracker_html(self.combatants, 2, {}, self.eff)
        self.assertIn('http-equiv="refresh"', out)
        self.assertIn('content="4"', out)

    def test_tracker_json_merges_conditions_conc_and_death_saves(self):
        ts = {"piper": {"conditions": ["frightened"], "concentration": "Bless",
                        "death_saves": {"successes": 1, "failures": 2, "stable": False}}}
        out = render_tracker.render_tracker_html(
            [{"name": "Piper", "hp": 0, "max_hp": 24, "ac": 15,
              "initiative": 14, "conditions": []}], 3, ts, self.eff)
        self.assertIn("frightened", out)
        self.assertIn("Bless", out)
        self.assertIn("✔1", out)
        self.assertIn("✘2", out)


class PositionColumnTests(unittest.TestCase):
    def setUp(self):
        self.eff = render_tracker.condition_effects(SRD)

    def test_pos_shown_when_present(self):
        combatants = [{"name": "Piper", "hp": 18, "max_hp": 24, "ac": 15,
                       "initiative": 14, "conditions": [], "pos": "C4"}]
        out = render_tracker.render_tracker_html(combatants, 1, {}, self.eff)
        self.assertIn("@ C4", out)

    def test_no_pos_no_marker(self):
        combatants = [{"name": "Piper", "hp": 18, "max_hp": 24, "ac": 15,
                       "initiative": 14, "conditions": []}]
        out = render_tracker.render_tracker_html(combatants, 1, {}, self.eff)
        self.assertNotIn("@ ", out)


if __name__ == "__main__":
    unittest.main()
