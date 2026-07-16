"""test_grid.py — grid.py combat-grid math: tile labels, distance, spec
validation, movement pathing, range, AoE. Pure-function tests, no filesystem
except tmp spec files. Spec:
docs/superpowers/specs/2026-07-16-combat-grid-map-cue-design.md
"""
import pathlib
import sys
import unittest

SCRIPTS = pathlib.Path(__file__).resolve().parent.parent / "skills" / "dnd" / "scripts"
sys.path.insert(0, str(SCRIPTS))
import grid  # noqa: E402


class TileTests(unittest.TestCase):
    def test_parse_tile(self):
        self.assertEqual(grid.parse_tile("A1"), (0, 0))
        self.assertEqual(grid.parse_tile("C4"), (2, 3))
        self.assertEqual(grid.parse_tile("z99"), (25, 98))

    def test_tile_name_roundtrip(self):
        self.assertEqual(grid.tile_name(2, 3), "C4")
        self.assertEqual(grid.tile_name(*grid.parse_tile("R24")), "R24")

    def test_bad_labels_raise(self):
        for bad in ("", "4C", "AA1", "C0", "C", "C100"):
            with self.assertRaises(ValueError, msg=bad):
                grid.parse_tile(bad)


class DistTests(unittest.TestCase):
    def test_orthogonal(self):
        self.assertEqual(grid.dist_ft("A1", "A4"), 15)

    def test_diagonal_costs_5(self):
        self.assertEqual(grid.dist_ft("A1", "D4"), 15)   # pure diagonal, 3 tiles

    def test_mixed_is_chebyshev(self):
        self.assertEqual(grid.dist_ft("C4", "F5"), 15)   # dx=3, dy=1

    def test_same_tile_is_zero(self):
        self.assertEqual(grid.dist_ft("B2", "B2"), 0)


if __name__ == "__main__":
    unittest.main()
