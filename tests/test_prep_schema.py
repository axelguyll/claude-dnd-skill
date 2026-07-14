"""test_prep_schema.py — bible validation: party-level chain + full validator.

Run from repo root:
    python3 -m unittest tests.test_prep_schema -v
"""
import pathlib
import sys
import unittest

REPO = pathlib.Path(__file__).resolve().parent.parent
SKILL = REPO / "skills" / "dnd" if (REPO / "skills" / "dnd").is_dir() else REPO
sys.path.insert(0, str(SKILL / "scripts"))

from prep import schema


class PartyLevelTests(unittest.TestCase):
    def test_level_holds_until_a_beat_levels_then_carries(self):
        beats = [
            {"level_up_to": None},   # beat 1: at level 1
            {"level_up_to": 2},      # beat 2: still 1 while playing, becomes 2 after
            {"level_up_to": None},   # beat 3: at level 2
            {"level_up_to": 4},      # beat 4: at level 2, becomes 4 after
        ]
        self.assertEqual(schema.party_levels(beats), [1, 1, 2, 2])


if __name__ == "__main__":
    unittest.main()
