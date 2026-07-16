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


SPEC = {
    "handle": "cavern",
    "cols": 8, "rows": 6,
    "terrain": [
        {"tiles": "C3-D5", "kind": "rubble", "difficult": True},
        {"tiles": "F1", "kind": "pillar", "impassable": True, "blocks_los": True},
    ],
    "notes": "test map",
}


class ExpandTilesTests(unittest.TestCase):
    def test_single_tile(self):
        self.assertEqual(grid.expand_tiles("F1"), [(5, 0)])

    def test_rectangle_inclusive(self):
        tiles = grid.expand_tiles("C3-D5")
        self.assertEqual(len(tiles), 6)          # 2 cols x 3 rows
        self.assertIn((2, 2), tiles)             # C3
        self.assertIn((3, 4), tiles)             # D5

    def test_corners_any_order(self):
        self.assertEqual(set(grid.expand_tiles("D5-C3")),
                         set(grid.expand_tiles("C3-D5")))


class ValidateTests(unittest.TestCase):
    def test_valid_spec_no_errors(self):
        self.assertEqual(grid.validate_spec(SPEC), [])

    def test_missing_dims(self):
        errs = grid.validate_spec({"handle": "x", "terrain": []})
        self.assertTrue(any("cols" in e for e in errs))
        self.assertTrue(any("rows" in e for e in errs))

    def test_cols_over_26_rejected(self):
        errs = grid.validate_spec({"handle": "x", "cols": 30, "rows": 5})
        self.assertTrue(any("cols" in e for e in errs))

    def test_terrain_out_of_bounds_rejected(self):
        bad = dict(SPEC, terrain=[{"tiles": "J9", "difficult": True}])  # 8x6 grid
        self.assertTrue(grid.validate_spec(bad))

    def test_bad_tile_expr_rejected(self):
        bad = dict(SPEC, terrain=[{"tiles": "C3-D5-E6"}])
        self.assertTrue(grid.validate_spec(bad))

    def test_missing_handle_rejected(self):
        errs = grid.validate_spec({"cols": 8, "rows": 6})
        self.assertTrue(any("handle" in e for e in errs))


class TerrainSetsTests(unittest.TestCase):
    def test_split_by_flag(self):
        difficult, impassable = grid.terrain_sets(SPEC)
        self.assertIn((2, 2), difficult)
        self.assertIn((5, 0), impassable)
        self.assertNotIn((5, 0), difficult)


if __name__ == "__main__":
    unittest.main()
