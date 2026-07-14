"""test_prep_example.py — the worked example in templates/spine.md stays valid.

Run from repo root:
    python3 -m unittest tests.test_prep_example -v
"""
import json
import pathlib
import re
import sys
import unittest

REPO = pathlib.Path(__file__).resolve().parent.parent
SKILL = REPO / "skills" / "dnd" if (REPO / "skills" / "dnd").is_dir() else REPO
sys.path.insert(0, str(SKILL / "scripts"))

from prep import bestiary, schema

SPINE_MD = SKILL / "templates" / "spine.md"


class SpineExampleTests(unittest.TestCase):
    def test_embedded_example_is_valid(self):
        text = SPINE_MD.read_text(encoding="utf-8")
        block = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
        self.assertIsNotNone(block, "spine.md must embed a ```json example bible")
        bible = json.loads(block.group(1))
        errs = schema.validate_bible(bible, bestiary.load_monsters())
        self.assertEqual(errs, [], f"example bible invalid: {errs}")


if __name__ == "__main__":
    unittest.main()
