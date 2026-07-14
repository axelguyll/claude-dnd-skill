"""test_prep_cli.py — invoke each prep CLI by file path, exactly as the
`/dm:dnd prep` procedure does (subprocess, no pre-seeded PYTHONPATH). Catches
standalone-import regressions that pre-seeded-sys.path unit tests miss.

Run from repo root:
    python3 -m unittest tests.test_prep_cli -v
"""
import pathlib
import re
import subprocess
import sys
import tempfile
import unittest

REPO = pathlib.Path(__file__).resolve().parent.parent
SKILL = REPO / "skills" / "dnd" if (REPO / "skills" / "dnd").is_dir() else REPO
SCRIPTS = SKILL / "scripts" / "prep"
SPINE_MD = SKILL / "templates" / "spine.md"


class PrepCLITests(unittest.TestCase):
    def test_schema_cli_validates_example_bible(self):
        text = SPINE_MD.read_text(encoding="utf-8")
        block = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
        self.assertIsNotNone(block, "spine.md must embed a ```json example bible")

        tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        )
        try:
            tmp.write(block.group(1))
            tmp.close()

            result = subprocess.run(
                [sys.executable, str(SCRIPTS / "schema.py"), "--bible", tmp.name],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(
                result.returncode, 0, f"stdout={result.stdout!r} stderr={result.stderr!r}"
            )
            self.assertIn("VALID", result.stdout)
        finally:
            pathlib.Path(tmp.name).unlink(missing_ok=True)

    def test_bestiary_cli_lists_level_appropriate_monsters(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / "bestiary.py"), "--level", "1"],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(
            result.returncode, 0, f"stdout={result.stdout!r} stderr={result.stderr!r}"
        )
        self.assertIn("Goblin", result.stdout)

    def test_milestone_cli_marks_pending_level_up(self):
        tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        )
        try:
            tmp.write("- **Alignment:** LG | **XP:** 0 / 900\n")
            tmp.close()

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "milestone.py"),
                    "--sheet",
                    tmp.name,
                    "--level",
                    "3",
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(
                result.returncode, 0, f"stdout={result.stdout!r} stderr={result.stderr!r}"
            )
            updated = pathlib.Path(tmp.name).read_text(encoding="utf-8")
            self.assertIn("⚠ LEVEL UP PENDING (Level 3)", updated)
        finally:
            pathlib.Path(tmp.name).unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
