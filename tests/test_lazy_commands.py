"""Lazy-loading contract for SKILL-commands.md (Pass B M15).

The 1029-line commands file was loaded whole at session start although each
procedure fires at most once per session. The skill lazy-loads all campaign
data; its own biggest file gets the same discipline: a compact index loads
at session start, and each command's section is Read on invocation.

Run from repo root:
    python -m unittest tests.test_lazy_commands -v
"""
import pathlib
import re
import unittest

REPO = pathlib.Path(__file__).resolve().parent.parent
DND = REPO / "skills" / "dnd"
SKILL = (DND / "SKILL.md").read_text(encoding="utf-8")
CMDS = (DND / "SKILL-commands.md").read_text(encoding="utf-8")
INDEX_PATH = DND / "SKILL-commands-index.md"


class CommandIndexTests(unittest.TestCase):
    def test_index_file_exists(self):
        self.assertTrue(INDEX_PATH.exists(), "SKILL-commands-index.md missing")

    def test_index_covers_every_command_section(self):
        """Every `## `-level command header in SKILL-commands.md must appear
        in the index — this is the drift guard for future command additions."""
        index = INDEX_PATH.read_text(encoding="utf-8")
        for line in CMDS.splitlines():
            m = re.match(r"^## `([^`]+)`", line)
            if not m:
                continue
            command = re.split(r'[<\["]', m.group(1))[0].strip()
            with self.subTest(command=command):
                self.assertIn(command, index,
                              f"command {command!r} missing from the index")

    def test_index_has_mandatory_section_read_contract(self):
        index = INDEX_PATH.read_text(encoding="utf-8")
        self.assertIn("Read its full section", index)
        self.assertIn("never", index.lower())

    def test_commands_file_no_longer_instructs_whole_file_load(self):
        self.assertNotIn("Load this file at `/dm:dnd load`", CMDS)
        first_lines = "\n".join(CMDS.splitlines()[:8])
        self.assertIn("SKILL-commands-index.md", first_lines)

    def test_skill_md_load_instruction_uses_the_index(self):
        self.assertNotIn("Load both at `/dm:dnd load`", SKILL)
        self.assertIn("SKILL-commands-index.md", SKILL)


if __name__ == "__main__":
    unittest.main()
