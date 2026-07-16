"""test_render_map.py — render_map.py builds the player-facing battle-map HTML
(projected page: map image, grid overlay, token positions). Pure-function
tests, no filesystem. Spec:
docs/superpowers/specs/2026-07-16-combat-grid-map-cue-design.md
"""
import pathlib
import sys
import unittest

SCRIPTS = pathlib.Path(__file__).resolve().parent.parent / "skills" / "dnd" / "scripts"
sys.path.insert(0, str(SCRIPTS))
import render_map  # noqa: E402

SPEC = {"handle": "cavern", "cols": 8, "rows": 6, "terrain": []}
COMBATANTS = [
    {"name": "Piper", "type": "pc", "hp": 18, "ac": 15, "pos": "C4"},
    {"name": "Goblin", "type": "npc", "hp": 7, "ac": 15, "pos": "F2"},
    {"name": "Lurker", "type": "npc", "hp": 30, "ac": 13, "pos": "A1",
     "hidden": True},
    {"name": "Wolf", "type": "npc", "hp": 11, "ac": 13},   # no pos
]


class RenderMapTests(unittest.TestCase):
    def setUp(self):
        self.out = render_map.render_map_html(SPEC, COMBATANTS, 2,
                                              "maps/cavern.png")

    def test_round_and_handle_shown(self):
        self.assertIn("Round 2", self.out)
        self.assertIn("cavern", self.out)

    def test_image_embedded_stretched_to_grid(self):
        self.assertIn('href="maps/cavern.png"', self.out)
        self.assertIn('preserveAspectRatio="none"', self.out)

    def test_grid_labels_present(self):
        self.assertIn(">A<", self.out)        # column letter
        self.assertIn(">H<", self.out)        # 8th column
        self.assertIn(">6<", self.out)        # last row number

    def test_placed_tokens_rendered(self):
        self.assertIn("Piper", self.out)
        self.assertIn("Goblin", self.out)

    def test_hidden_combatant_absent(self):
        self.assertNotIn("Lurker", self.out)

    def test_unplaced_listed_off_map(self):
        self.assertIn("off-map", self.out)
        self.assertIn("Wolf", self.out)

    def test_active_combatant_ringed(self):
        # First in list is active; its token carries the active class/marker.
        self.assertIn('class="token active"', self.out)

    def test_meta_refresh_present(self):
        self.assertIn('http-equiv="refresh"', self.out)

    def test_no_image_renders_grid_only(self):
        out = render_map.render_map_html(SPEC, COMBATANTS, 1, None)
        self.assertNotIn("<image", out)
        self.assertIn(">A<", out)             # grid still there

    def test_hidden_unplaced_stays_out_of_strip(self):
        combatants = COMBATANTS + [
            {"name": "Shade", "type": "npc", "hp": 9, "ac": 12, "hidden": True}]
        out = render_map.render_map_html(SPEC, combatants, 1, None)
        self.assertNotIn("Shade", out)


class IdleTests(unittest.TestCase):
    def test_idle_screen(self):
        out = render_map.render_idle_html()
        self.assertIn("theater of the mind", out.lower())
        self.assertIn('http-equiv="refresh"', out)


class FindImageTests(unittest.TestCase):
    def test_finds_png_then_jpg(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            camp = pathlib.Path(d)
            (camp / "maps").mkdir()
            self.assertIsNone(render_map.find_image(camp, "cavern"))
            (camp / "maps" / "cavern.jpg").write_bytes(b"x")
            self.assertEqual(render_map.find_image(camp, "cavern"),
                             "maps/cavern.jpg")
            (camp / "maps" / "cavern.png").write_bytes(b"x")
            self.assertEqual(render_map.find_image(camp, "cavern"),
                             "maps/cavern.png")


if __name__ == "__main__":
    unittest.main()
