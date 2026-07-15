"""test_render_assets.py — render_assets.py parses the three asset lists and
renders the asset-hub HTML. Pure-function tests, no filesystem.
"""
import pathlib
import sys
import unittest

SCRIPTS = pathlib.Path(__file__).resolve().parent.parent / "skills" / "dnd" / "scripts"
sys.path.insert(0, str(SCRIPTS))
import render_assets  # noqa: E402


class ParseTests(unittest.TestCase):
    def test_parses_handle_desc_and_file_dropping_hint(self):
        text = ('# heading\n\n'
                '- **Collapse** — heavy stone-on-stone collapse rumble. '
                '*Find:* "cave collapse" on Tabletop Audio. File: sounds/sfx_collapse.mp3\n')
        self.assertEqual(render_assets.parse_asset_list(text), [
            {"handle": "Collapse",
             "desc": "heavy stone-on-stone collapse rumble",
             "file": "sounds/sfx_collapse.mp3"}])

    def test_ignores_non_entry_lines(self):
        self.assertEqual(render_assets.parse_asset_list("just prose\n- not an entry\n"), [])


class RenderTests(unittest.TestCase):
    def setUp(self):
        self.html = render_assets.render_assets_html(
            maps=[{"handle": "Cavern", "desc": "big cave", "file": "maps/cavern.png"}],
            ambient=[{"handle": "Cave", "desc": "drips", "file": "sounds/cave.mp3"}],
            sfx=[{"handle": "Collapse", "desc": "rumble", "file": "sounds/sfx_collapse.mp3"}])

    def test_map_image_wired(self):
        self.assertIn('src="maps/cavern.png"', self.html)

    def test_ambient_is_looped_audio(self):
        self.assertIn('src="sounds/cave.mp3"', self.html)
        self.assertIn("loop", self.html)

    def test_sfx_button_wired(self):
        self.assertIn('src="sounds/sfx_collapse.mp3"', self.html)

    def test_assets_never_auto_refresh(self):
        # A refresh would reload the page and kill any playing ambient loop.
        self.assertNotIn('http-equiv="refresh"', self.html)

    def test_map_desc_and_link_render(self):
        self.assertIn("big cave", self.html)
        self.assertIn('href="maps/cavern.png"', self.html)


TPL = pathlib.Path(__file__).resolve().parent.parent / "skills" / "dnd" / "templates"


class TemplateRoundTripTests(unittest.TestCase):
    def test_map_template_example_parses(self):
        items = render_assets.parse_asset_list((TPL / "map-list.md").read_text(encoding="utf-8"))
        self.assertEqual(len(items), 1)
        self.assertTrue(items[0]["file"].startswith("maps/"))

    def test_ambient_template_example_parses(self):
        items = render_assets.parse_asset_list((TPL / "ambient-list.md").read_text(encoding="utf-8"))
        self.assertEqual(len(items), 1)
        self.assertTrue(items[0]["file"].startswith("sounds/"))

    def test_sfx_template_example_parses(self):
        items = render_assets.parse_asset_list((TPL / "sfx-list.md").read_text(encoding="utf-8"))
        self.assertEqual(len(items), 1)
        self.assertTrue(items[0]["file"].startswith("sounds/"))


if __name__ == "__main__":
    unittest.main()
