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

    def test_example_carries_the_playhead(self):
        # Prep authors beat 1 as current — the state.md mirror is derived from the
        # spine, and mirror_check trips on a fresh campaign otherwise (2026-07-16
        # re-probe finding).
        text = SPINE_MD.read_text(encoding="utf-8")
        block = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
        bible = json.loads(block.group(1))
        statuses = [b["status"] for b in bible["beats"]]
        self.assertEqual(statuses[0], "current")
        self.assertEqual(statuses.count("current"), 1)


if __name__ == "__main__":
    unittest.main()
