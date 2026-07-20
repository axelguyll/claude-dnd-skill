"""
Guard tests for the autosave Stop-hook installer.

    python3 -m unittest tests.test_install_autosave_hook -v

The hook command is written into ~/.claude/settings.json and executed by the
harness in whatever shell it spawns — cmd/PowerShell on Windows, sh on POSIX.
Nothing about that shell is guaranteed to match the shell the installer ran in.
A bare interpreter name is therefore a PATH bet, and on Windows `python3` loses
it: Git Bash ships a shim, PowerShell does not. The hook then fails silently on
every turn and the only symptom is an absence — no lint log, no error anywhere.
"""

import os
import shlex
import sys
import unittest

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "skills", "dnd", "scripts")
)

import install_autosave_hook as installer  # noqa: E402


class TestCheckpointCommand(unittest.TestCase):
    def _interpreter(self) -> str:
        # shlex with posix=False keeps Windows path quoting intact.
        parts = shlex.split(installer.checkpoint_command(), posix=False)
        self.assertTrue(parts, "checkpoint_command() returned nothing")
        return parts[0].strip('"')

    def test_interpreter_is_an_existing_executable(self):
        """The regression: `python3` resolves in Git Bash, not in PowerShell."""
        interp = self._interpreter()
        self.assertTrue(
            os.path.isfile(interp),
            f"hook interpreter {interp!r} is not an existing file — a bare name "
            f"makes the hook depend on the harness shell's PATH",
        )

    def test_interpreter_is_absolute(self):
        interp = self._interpreter()
        self.assertTrue(
            os.path.isabs(interp),
            f"hook interpreter {interp!r} must be an absolute path",
        )

    def test_script_path_is_absolute_and_exists(self):
        parts = shlex.split(installer.checkpoint_command(), posix=False)
        script = parts[-1].strip('"')
        self.assertTrue(os.path.isabs(script), f"script path {script!r} must be absolute")
        self.assertTrue(os.path.isfile(script), f"script path {script!r} does not exist")

    def test_command_is_quoted_for_spaces(self):
        """Both halves live under paths with spaces on a default Windows install."""
        cmd = installer.checkpoint_command()
        for part in shlex.split(cmd, posix=False):
            if " " in part.strip('"'):
                self.assertTrue(
                    part.startswith('"') and part.endswith('"'),
                    f"path with spaces must be quoted: {part!r}",
                )


if __name__ == "__main__":
    unittest.main()
