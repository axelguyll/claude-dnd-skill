"""test_prep_milestone.py — XP-free pending-level marker for milestone leveling.

Run from repo root:
    python3 -m unittest tests.test_prep_milestone -v
"""
import pathlib
import subprocess
import sys
import tempfile
import unittest

REPO = pathlib.Path(__file__).resolve().parent.parent
SKILL = REPO / "skills" / "dnd" if (REPO / "skills" / "dnd").is_dir() else REPO
sys.path.insert(0, str(SKILL / "scripts"))

from prep import milestone

_MILESTONE = (
    pathlib.Path(__file__).resolve().parent.parent
    / "skills" / "dnd" / "scripts" / "prep" / "milestone.py"
)

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

    def test_raises_if_no_anchor_line(self):
        with self.assertRaises(ValueError):
            milestone.set_pending_level("# Sheet with no xp or level line\n", 3)

    def test_clear_pending_removes_marker_preserving_xp(self):
        marked = milestone.set_pending_level(SHEET, 3)
        cleared = milestone.clear_pending(marked)
        self.assertNotIn("LEVEL UP PENDING", cleared)
        self.assertIn("**XP:** 0 / 900", cleared)  # numbers untouched

    def test_clear_pending_noop_when_no_marker(self):
        # clearing a sheet with no marker leaves it unchanged (no raise)
        self.assertEqual(milestone.clear_pending(SHEET), SHEET)


# Milestone-fork sheets carry no XP numbers (template ships the field blank) —
# the marker falls back to the **Level:** line. 2026-07-16 re-probe finding.
XPLESS_SHEET = """# Mara
- **Race:** Human | **Class:** Fighter | **Level:** 3 | **Background:** Sailor
- **Alignment:** NG | **XP:** — / —
## Combat
- **HP:** 28 / 28
"""


class LevelLineFallbackTests(unittest.TestCase):
    def test_marks_on_level_line_when_no_numeric_xp(self):
        out = milestone.set_pending_level(XPLESS_SHEET, 4)
        self.assertIn("**Level:** 3 ⚠ LEVEL UP PENDING (Level 4)", out)

    def test_idempotent_on_level_line(self):
        once = milestone.set_pending_level(XPLESS_SHEET, 4)
        twice = milestone.set_pending_level(once, 5)
        self.assertIn("(Level 5)", twice)
        self.assertNotIn("(Level 4)", twice)

    def test_clear_removes_level_line_marker(self):
        marked = milestone.set_pending_level(XPLESS_SHEET, 4)
        cleared = milestone.clear_pending(marked)
        self.assertNotIn("LEVEL UP PENDING", cleared)
        self.assertIn("**Level:** 3", cleared)

    def test_numeric_xp_line_still_wins_over_level_line(self):
        out = milestone.set_pending_level(SHEET, 3)
        self.assertIn("**XP:** 0 / 900 ⚠ LEVEL UP PENDING (Level 3)", out)
        self.assertNotIn("**Level:** 2 ⚠", out)


class MilestoneCliErrorTests(unittest.TestCase):
    def test_no_anchor_line_exits_clean_no_traceback(self):
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write("# Sheet with no XP or Level line\n")
            sheet = f.name
        proc = subprocess.run(
            [sys.executable, str(_MILESTONE), "--sheet", sheet, "--level", "4"],
            capture_output=True, text=True,
        )
        self.assertEqual(proc.returncode, 1)
        self.assertNotIn("Traceback", proc.stderr)
        self.assertIn("error:", proc.stderr.lower())

    def test_level_line_only_sheet_succeeds(self):
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write("# Sheet with no XP line\n**Level:** 3\n")
            sheet = f.name
        proc = subprocess.run(
            [sys.executable, str(_MILESTONE), "--sheet", sheet, "--level", "4"],
            capture_output=True, text=True,
        )
        self.assertEqual(proc.returncode, 0)
        self.assertIn(
            "⚠ LEVEL UP PENDING (Level 4)",
            pathlib.Path(sheet).read_text(encoding="utf-8"),
        )


if __name__ == "__main__":
    unittest.main()
