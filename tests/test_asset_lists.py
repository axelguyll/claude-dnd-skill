"""test_asset_lists.py — the three prep asset-list templates exist and carry the
sealed-campaign discipline; prep step 4 generates them and builds the asset hub.
"""
import pathlib
import unittest

REPO = pathlib.Path(__file__).resolve().parent.parent
DND = REPO / "skills" / "dnd"
TPL = DND / "templates"
CMDS = (DND / "SKILL-commands.md").read_text(encoding="utf-8")


class AssetListTemplateTests(unittest.TestCase):
    def test_map_list_restricted_to_encounters(self):
        text = (TPL / "map-list.md").read_text(encoding="utf-8")
        self.assertIn("Encounter scenes only", text)
        self.assertIn("File: maps/", text)

    def test_ambient_list_exists_and_is_atmosphere_only(self):
        text = (TPL / "ambient-list.md").read_text(encoding="utf-8")
        self.assertIn("atmosphere only", text)
        self.assertIn("File: sounds/", text)

    def test_sfx_list_exists_and_forbids_leaking_the_trigger(self):
        text = (TPL / "sfx-list.md").read_text(encoding="utf-8")
        self.assertIn("sound only", text)
        self.assertIn("spine-guaranteed", text)
        self.assertIn("File: sounds/", text)


class PrepFlowTests(unittest.TestCase):
    def test_prep_generates_all_three_lists(self):
        self.assertIn("ambient-list.md", CMDS)
        self.assertIn("sfx-list.md", CMDS)

    def test_prep_builds_the_asset_hub(self):
        self.assertIn("render_assets.py", CMDS)


if __name__ == "__main__":
    unittest.main()
