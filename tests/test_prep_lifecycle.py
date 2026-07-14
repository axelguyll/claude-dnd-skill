"""test_prep_lifecycle.py — invariants on the prep lifecycle wiring:
the authored arc template block, and the prep/load/beat-complete prose.

Run from repo root:
    python3 -m unittest tests.test_prep_lifecycle -v
"""
import pathlib
import unittest

REPO = pathlib.Path(__file__).resolve().parent.parent
DND = REPO / "skills" / "dnd"
STATE_TPL = (DND / "templates" / "state.md").read_text(encoding="utf-8")
CMDS = (DND / "SKILL-commands.md").read_text(encoding="utf-8")


class AuthoredArcTemplateTests(unittest.TestCase):
    def test_authored_arc_block_present(self):
        self.assertIn("AUTHORED ARC", STATE_TPL)
        self.assertIn("type: authored", STATE_TPL)

    def test_authored_block_points_at_spine_file(self):
        self.assertIn("spine_file: spine.json", STATE_TPL)

    def test_authored_block_has_beat_window_fields(self):
        idx = STATE_TPL.find("AUTHORED ARC")
        section = STATE_TPL[idx: idx + 900]
        for field in ("current_beat:", "outstanding_beats:", "beats:", "steering_notes:"):
            self.assertIn(field, section)


if __name__ == "__main__":
    unittest.main()
