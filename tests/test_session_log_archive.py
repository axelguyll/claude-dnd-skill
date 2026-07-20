"""session_log_archive.py — deterministic session-log file surgery at save.

The save procedure's "keep the 2 newest entries, append older ones to the
archive" step was performed by the model with Edit calls on every save past
session 3 (Pass A finding 1.4). The cut-and-append is deterministic; only
the 3-5 bullet continuity summary needs the model.

Run from repo root:
    python -m unittest tests.test_session_log_archive -v
"""
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

REPO = pathlib.Path(__file__).resolve().parent.parent
SCRIPTS = REPO / "skills" / "dnd" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import session_log_archive as sla  # noqa: E402

PREAMBLE = """# Session Log — probe-camp

---

## Session Template

---

## Session X — <date>
(template body)

"""


def _entry(n, body="- something happened"):
    return f"## Session {n} — 2026-07-{10 + n:02d}\n**Location:** docks\n{body}\n\n"


class SplitEntriesTests(unittest.TestCase):
    def test_splits_numeric_session_entries(self):
        text = PREAMBLE + _entry(1) + _entry(2) + _entry(3)
        preamble, entries = sla.split_entries(text)
        self.assertEqual([n for n, _ in entries], [1, 2, 3])
        self.assertIn("Session Template", preamble)
        self.assertIn("Session X", preamble)

    def test_template_headers_are_not_entries(self):
        preamble, entries = sla.split_entries(PREAMBLE)
        self.assertEqual(entries, [])

    def test_entry_bodies_are_complete(self):
        text = PREAMBLE + _entry(1, "- fact A\n### Key Events\n- fought a troll")
        _, entries = sla.split_entries(text)
        self.assertIn("fought a troll", entries[0][1])


class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.camp = pathlib.Path(self.tmp.name)
        self.log = self.camp / "session-log.md"
        self.archive = self.camp / "session-log-archive.md"

    def _write_log(self, *nums):
        self.log.write_text(
            PREAMBLE + "".join(_entry(n) for n in nums), encoding="utf-8")

    def test_keeps_two_newest_archives_the_rest(self):
        self._write_log(1, 2, 3, 4)
        archived = sla.archive_old_entries(self.camp, keep=2)
        self.assertEqual(archived, [1, 2])
        live = self.log.read_text(encoding="utf-8")
        self.assertNotIn("## Session 1 ", live)
        self.assertNotIn("## Session 2 ", live)
        self.assertIn("## Session 3 ", live)
        self.assertIn("## Session 4 ", live)
        arch = self.archive.read_text(encoding="utf-8")
        self.assertIn("## Session 1 ", arch)
        self.assertIn("## Session 2 ", arch)

    def test_preamble_survives(self):
        self._write_log(1, 2, 3)
        sla.archive_old_entries(self.camp, keep=2)
        live = self.log.read_text(encoding="utf-8")
        self.assertIn("Session Template", live)
        self.assertIn("## Session X — <date>", live)

    def test_archive_is_append_only(self):
        self.archive.write_text("# Archive\n\n## Session 0 — old\n- ancient\n",
                                encoding="utf-8")
        self._write_log(1, 2, 3)
        sla.archive_old_entries(self.camp, keep=2)
        arch = self.archive.read_text(encoding="utf-8")
        self.assertIn("## Session 0 — old", arch)
        self.assertIn("- ancient", arch)
        self.assertLess(arch.index("Session 0"), arch.index("Session 1"))

    def test_idempotent_on_rerun(self):
        self._write_log(1, 2, 3, 4)
        sla.archive_old_entries(self.camp, keep=2)
        live_before = self.log.read_text(encoding="utf-8")
        arch_before = self.archive.read_text(encoding="utf-8")
        archived = sla.archive_old_entries(self.camp, keep=2)
        self.assertEqual(archived, [])
        self.assertEqual(self.log.read_text(encoding="utf-8"), live_before)
        self.assertEqual(self.archive.read_text(encoding="utf-8"), arch_before)

    def test_two_or_fewer_entries_is_a_noop(self):
        self._write_log(1, 2)
        original = self.log.read_text(encoding="utf-8")
        self.assertEqual(sla.archive_old_entries(self.camp, keep=2), [])
        self.assertEqual(self.log.read_text(encoding="utf-8"), original)
        self.assertFalse(self.archive.exists())

    def test_missing_log_is_a_noop(self):
        self.assertEqual(sla.archive_old_entries(self.camp, keep=2), [])


class CliTests(unittest.TestCase):
    CAMPAIGN = "archive-probe"

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = pathlib.Path(self.tmp.name)
        self.camp = root / "campaigns" / self.CAMPAIGN
        self.camp.mkdir(parents=True)
        (self.camp / "session-log.md").write_text(
            PREAMBLE + "".join(_entry(n) for n in (1, 2, 3)),
            encoding="utf-8")
        self.env = dict(os.environ)
        self.env["DND_CAMPAIGN_ROOT"] = str(root)

    def test_cli_archives_and_reports(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / "session_log_archive.py"),
             "--campaign", self.CAMPAIGN],
            capture_output=True, text=True, env=self.env, cwd=str(REPO))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("1", result.stdout)
        self.assertTrue((self.camp / "session-log-archive.md").exists())


if __name__ == "__main__":
    unittest.main()
