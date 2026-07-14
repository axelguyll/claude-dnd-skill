"""test_prep_smoke.py — the prep package imports.

Run from repo root:
    python3 -m unittest tests.test_prep_smoke -v
"""
import pathlib
import sys
import unittest

REPO = pathlib.Path(__file__).resolve().parent.parent
SKILL = REPO / "skills" / "dnd" if (REPO / "skills" / "dnd").is_dir() else REPO
sys.path.insert(0, str(SKILL / "scripts"))


class PrepSmokeTests(unittest.TestCase):
    def test_package_imports(self):
        import prep  # noqa: F401
        self.assertTrue(hasattr(prep, "__doc__"))


if __name__ == "__main__":
    unittest.main()
