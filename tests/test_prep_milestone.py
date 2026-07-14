"""test_prep_milestone.py — XP-free pending-level marker for milestone leveling.

Run from repo root:
    python3 -m unittest tests.test_prep_milestone -v
"""
import pathlib
import sys
import unittest

REPO = pathlib.Path(__file__).resolve().parent.parent
SKILL = REPO / "skills" / "dnd" if (REPO / "skills" / "dnd").is_dir() else REPO
sys.path.insert(0, str(SKILL / "scripts"))

from prep import milestone

SHEET = """# Aldric
- **Race:** Human | **Class:** Fighter | **Level:** 2 | **Background:** Soldier
- **Alignment:** LG | **XP:** 0 / 900
## Combat
- **HP:** 20 / 20
"""


class MilestoneMarkerTests(unittest.TestCase):
    def test_marks_pending_level_preserving_xp_numbers(self):
        out = milestone.set_pending_level(SHEET, 3)
        self.assertIn("⚠ LEVEL UP PENDING (Level 3)", out)
        self.assertIn("**XP:** 0 / 900", out)  # numbers untouched

    def test_idempotent_replaces_existing_marker(self):
        once = milestone.set_pending_level(SHEET, 3)
        twice = milestone.set_pending_level(once, 4)
        self.assertIn("(Level 4)", twice)
        self.assertNotIn("(Level 3)", twice)   # old marker replaced, not stacked

    def test_raises_if_no_xp_line(self):
        with self.assertRaises(ValueError):
            milestone.set_pending_level("# Sheet with no xp line\n", 3)

    def test_clear_pending_removes_marker_preserving_xp(self):
        marked = milestone.set_pending_level(SHEET, 3)
        cleared = milestone.clear_pending(marked)
        self.assertNotIn("LEVEL UP PENDING", cleared)
        self.assertIn("**XP:** 0 / 900", cleared)  # numbers untouched

    def test_clear_pending_noop_when_no_marker(self):
        # clearing a sheet with no marker leaves it unchanged (no raise)
        self.assertEqual(milestone.clear_pending(SHEET), SHEET)


if __name__ == "__main__":
    unittest.main()
