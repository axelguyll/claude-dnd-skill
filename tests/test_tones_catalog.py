"""test_tones_catalog.py — the shared tone catalog is well-formed and complete."""
import pathlib
import unittest

import yaml

DATA = pathlib.Path(__file__).resolve().parent.parent / "skills" / "dnd" / "data"
EXPECTED_IDS = {"heroic", "mythic", "grimdark", "horror", "intrigue", "swashbuckling", "cosmic"}


class ToneCatalogTests(unittest.TestCase):
    def setUp(self):
        self.doc = yaml.safe_load((DATA / "tones.yaml").read_text(encoding="utf-8"))

    def test_has_tones_list(self):
        self.assertIn("tones", self.doc)
        self.assertIsInstance(self.doc["tones"], list)

    def test_exactly_seven_expected_ids(self):
        ids = {t["id"] for t in self.doc["tones"]}
        self.assertEqual(ids, EXPECTED_IDS)

    def test_every_entry_has_descriptor_and_mood_note(self):
        for t in self.doc["tones"]:
            self.assertTrue(t.get("descriptor", "").strip(), f"{t['id']} missing descriptor")
            self.assertTrue(t.get("mood_note", "").strip(), f"{t['id']} missing mood_note")


if __name__ == "__main__":
    unittest.main()
