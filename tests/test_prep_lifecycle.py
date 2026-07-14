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


class PrepScaffoldProseTests(unittest.TestCase):
    def _prep_section(self):
        idx = CMDS.find("## `/dm:dnd prep")
        end = CMDS.find("## `/dm:dnd beat complete", idx)
        return CMDS[idx:end]

    def test_prep_writes_canonical_spine_json(self):
        self.assertIn("spine.json", self._prep_section())

    def test_prep_scaffolds_state_md(self):
        sec = self._prep_section()
        self.assertIn("state.md", sec)
        self.assertIn("Session count: 0", sec)

    def test_prep_seeds_authored_arc(self):
        self.assertIn("type: authored", self._prep_section())

    def test_prep_scaffolds_supporting_files(self):
        sec = self._prep_section()
        self.assertIn("npcs.md", sec)
        self.assertIn("session-log.md", sec)


class BeatCompleteSyncProseTests(unittest.TestCase):
    def _beat_section(self):
        idx = CMDS.find("## `/dm:dnd beat complete")
        end = CMDS.find("\n---", idx)
        return CMDS[idx:end]

    def test_beat_updates_state_window(self):
        sec = self._beat_section()
        self.assertIn("current_beat", sec)
        self.assertIn("outstanding_beats", sec)

    def test_beat_updates_both_spine_and_state(self):
        sec = self._beat_section()
        self.assertIn("spine.json", sec)
        self.assertIn("steering_notes", sec)


class LoadAuthoredProseTests(unittest.TestCase):
    def _load_section(self):
        idx = CMDS.find("## `/dm:dnd load")
        end = CMDS.find("## `/dm:dnd import", idx)
        return CMDS[idx:end]

    def test_load_mentions_authored_arc(self):
        self.assertIn("type: authored", self._load_section())

    def test_load_does_not_read_spine_at_load(self):
        sec = self._load_section()
        # the spine is off the hot path — load must say so
        self.assertIn("spine.json (authored campaigns only)", sec)
        self.assertIn("beat complete", sec)


class LegacyDeprecationProseTests(unittest.TestCase):
    def test_new_command_signposted_legacy(self):
        idx = CMDS.find("## `/dm:dnd new")
        section = CMDS[idx: idx + 400]
        self.assertIn("legacy", section.lower())
        self.assertIn("prep", section.lower())

    def test_import_command_signposted_legacy(self):
        idx = CMDS.find("## `/dm:dnd import")
        self.assertNotEqual(idx, -1)
        section = CMDS[idx: idx + 400]
        self.assertIn("legacy", section.lower())


if __name__ == "__main__":
    unittest.main()
