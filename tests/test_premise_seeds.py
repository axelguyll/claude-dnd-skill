"""test_premise_seeds.py — the premise seed bank is well-formed and deep enough
to actually produce variety."""
import pathlib
import unittest

import yaml

DATA = pathlib.Path(__file__).resolve().parent.parent / "skills" / "dnd" / "data"
AXES = ("setting", "conflict", "antagonist", "twist")
TONE_IDS = {"heroic", "mythic", "grimdark", "horror", "intrigue", "swashbuckling", "cosmic"}


class PremiseSeedTests(unittest.TestCase):
    def setUp(self):
        self.doc = yaml.safe_load((DATA / "premise-seeds.yaml").read_text(encoding="utf-8"))

    def test_all_four_axes_present_and_deep(self):
        for axis in AXES:
            entries = self.doc["axes"][axis]
            self.assertGreaterEqual(len(entries), 6, f"{axis} needs >=6 entries for variety")
            self.assertTrue(all(isinstance(e, str) and e.strip() for e in entries))

    def test_exemplars_cover_every_tone(self):
        for tone in TONE_IDS:
            self.assertIn(tone, self.doc["exemplars"])
            self.assertGreaterEqual(len(self.doc["exemplars"][tone]), 2, f"{tone} needs >=2 exemplars")

    def test_axes_are_tone_agnostic_no_tone_keys(self):
        # axes must be flat lists, not tone-keyed dicts — orthogonality depends on it
        for axis in AXES:
            self.assertIsInstance(self.doc["axes"][axis], list)

    def test_every_catalog_tone_has_exemplars(self):
        # Cross-file guard: derive coverage from tones.yaml itself, so adding a tone
        # there without seeding exemplars here fails loudly instead of silently
        # degrading to an empty exemplar list at roll time.
        tones = yaml.safe_load((DATA / "tones.yaml").read_text(encoding="utf-8"))["tones"]
        for t in tones:
            self.assertIn(t["id"], self.doc["exemplars"], f"{t['id']} has no exemplars")
            self.assertGreaterEqual(len(self.doc["exemplars"][t["id"]]), 2)


if __name__ == "__main__":
    unittest.main()
