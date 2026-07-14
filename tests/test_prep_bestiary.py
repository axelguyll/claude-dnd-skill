"""test_prep_bestiary.py — CR band math + candidate filtering over the vendored SRD.

Run from repo root:
    python3 -m unittest tests.test_prep_bestiary -v
"""
import pathlib
import sys
import unittest

REPO = pathlib.Path(__file__).resolve().parent.parent
SKILL = REPO / "skills" / "dnd" if (REPO / "skills" / "dnd").is_dir() else REPO
sys.path.insert(0, str(SKILL / "scripts"))

from prep import bestiary


class BandMathTests(unittest.TestCase):
    def test_band_low_level_is_generous_at_floor(self):
        # L1: piecewise floor keeps CR-1/8 minions legal; ceiling = level+2.
        self.assertEqual(bestiary.band_for_level(1), (0.125, 3.0))

    def test_band_high_level_scales_up(self):
        # L8 finale: young dragons (CR 10) reachable, goblins (CR 1) dropped.
        self.assertEqual(bestiary.band_for_level(8), (2.0, 10.0))

    def test_floor_switches_to_quarter_rule_above_level_3(self):
        self.assertEqual(bestiary.floor_cr(3), 0.125)
        self.assertEqual(bestiary.floor_cr(4), 1.0)

    def test_cr_in_band_membership(self):
        self.assertTrue(bestiary.cr_in_band(0.25, 1))   # Goblin at L1
        self.assertFalse(bestiary.cr_in_band(0.0, 1))   # Commoner never a threat
        self.assertFalse(bestiary.cr_in_band(10.0, 1))  # dragon not at L1
        self.assertTrue(bestiary.cr_in_band(10.0, 8))   # young dragon at L8
        self.assertFalse(bestiary.cr_in_band(1.0, 8))   # bugbear outgrown by L8


if __name__ == "__main__":
    unittest.main()
