"""test_prep_mirror_check.py — spine.json vs state.md authored-mirror drift detection.

Run from repo root:
    python3 -m unittest tests.test_prep_mirror_check -v
"""
import pathlib
import sys
import unittest

REPO = pathlib.Path(__file__).resolve().parent.parent
SKILL = REPO / "skills" / "dnd" if (REPO / "skills" / "dnd").is_dir() else REPO
sys.path.insert(0, str(SKILL / "scripts"))

from prep import mirror_check


def _spine(statuses):
    return {"beats": [{"id": i + 1, "status": s} for i, s in enumerate(statuses)]}


def _state_md(current_beat, beat_statuses):
    beats = "\n".join(
        f"  - id: {i + 1}\n    status: {s}" for i, s in enumerate(beat_statuses)
    )
    return f"""# Campaign: t
## Campaign Arc
```yaml
type: authored
current_beat: {current_beat}
beats:
{beats}
```
## Session Flags
"""


class LoadMirrorTests(unittest.TestCase):
    def test_parses_live_authored_block(self):
        mirror = mirror_check.load_mirror(_state_md(1, ["current", "pending"]))
        self.assertEqual(mirror["type"], "authored")
        self.assertEqual(mirror["current_beat"], 1)

    def test_commented_template_lines_are_ignored(self):
        text = _state_md(1, ["current"]).replace(
            "type: authored", "type: authored\n# type: structured"
        )
        mirror = mirror_check.load_mirror(text)
        self.assertEqual(mirror["type"], "authored")

    def test_no_arc_block_returns_none(self):
        self.assertIsNone(mirror_check.load_mirror("# Campaign: t\n## Session Flags\n"))


class CompareTests(unittest.TestCase):
    def test_in_sync_passes(self):
        spine = _spine(["complete", "current", "pending"])
        mirror = mirror_check.load_mirror(
            _state_md(2, ["complete", "current", "pending"])
        )
        self.assertEqual(mirror_check.compare(spine, mirror), [])

    def test_status_drift_flagged(self):
        spine = _spine(["complete", "current", "pending"])
        mirror = mirror_check.load_mirror(
            _state_md(1, ["current", "pending", "pending"])
        )
        errs = mirror_check.compare(spine, mirror)
        self.assertTrue(any("status differs" in e for e in errs))

    def test_current_beat_drift_flagged(self):
        spine = _spine(["complete", "current", "pending"])
        mirror = mirror_check.load_mirror(
            _state_md(3, ["complete", "current", "pending"])
        )
        errs = mirror_check.compare(spine, mirror)
        self.assertTrue(any("current_beat differs" in e for e in errs))

    def test_missing_mirror_beat_flagged(self):
        spine = _spine(["current", "pending", "pending"])
        mirror = mirror_check.load_mirror(_state_md(1, ["current", "pending"]))
        errs = mirror_check.compare(spine, mirror)
        self.assertTrue(any("missing from state.md mirror" in e for e in errs))

    def test_non_authored_block_flagged(self):
        spine = _spine(["current"])
        errs = mirror_check.compare(spine, {"type": "dynamic"})
        self.assertTrue(any("no live `type: authored` block" in e for e in errs))

    def test_completed_arc_null_current_passes(self):
        spine = _spine(["complete", "complete"])
        mirror = mirror_check.load_mirror(_state_md("null", ["complete", "complete"]))
        self.assertEqual(mirror_check.compare(spine, mirror), [])


if __name__ == "__main__":
    unittest.main()
