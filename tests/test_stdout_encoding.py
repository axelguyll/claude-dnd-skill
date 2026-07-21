"""test_stdout_encoding.py — regression test for the Windows cp1252 crash.

Scripts under skills/dnd/scripts/ print non-ASCII characters (arrows, check
marks, em dashes, ...) that raise UnicodeEncodeError on a Windows console
defaulting to cp1252 with no UTF-8 override:

    python -c "import sys; sys.stdout.reconfigure(encoding='cp1252'); print('Saved -> test')"

The fix is the repo's existing idiom (see combat.py, and turn_lint.py /
session_audit.py's main()):

    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")

Run from repo root:
    python -m unittest tests.test_stdout_encoding -v
"""
import ast
import os
import pathlib
import subprocess
import sys
import unittest

REPO = pathlib.Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO / "skills" / "dnd" / "scripts"
DICE = SCRIPTS_DIR / "dice.py"

_GUARD_SNIPPETS = (
    'reconfigure(encoding="utf-8")',
    "reconfigure(encoding='utf-8')",
)

# Attribute-call method names that write to a stream or a logger.
_OUTPUT_METHODS = {"write", "debug", "info", "warning", "warn", "error",
                    "critical", "exception", "log"}


def _print_aliases(tree: ast.AST) -> set:
    """Module-level `def foo(...): print(...)`-style one-line wrappers (e.g.
    a `_say` helper). Generalized so a future print alias is still caught,
    not just a literal print()/write()/logging call."""
    aliases = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            body = [n for n in node.body
                    if not (isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant))]
            if len(body) == 1 and isinstance(body[0], ast.Expr):
                call = body[0].value
                if (isinstance(call, ast.Call) and isinstance(call.func, ast.Name)
                        and call.func.id == "print"):
                    aliases.add(node.name)
    return aliases


def _is_output_call(node: ast.AST, aliases: set) -> bool:
    if not isinstance(node, ast.Call):
        return False
    f = node.func
    if isinstance(f, ast.Name):
        return f.id == "print" or f.id in aliases
    if isinstance(f, ast.Attribute):
        return f.attr in _OUTPUT_METHODS
    return False


def _has_entry_point(tree: ast.AST, text: str) -> bool:
    if any(isinstance(n, ast.FunctionDef) and n.name == "main" for n in ast.walk(tree)):
        return True
    return '__name__ == "__main__"' in text or "__name__ == '__main__'" in text


def _needs_guard(path: pathlib.Path) -> bool:
    """True if this script is runnable and prints non-ASCII text via
    print/stdout-write/logging (directly, across multiple lines, or through
    a same-file print alias)."""
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text, filename=str(path))
    if not _has_entry_point(tree, text):
        return False
    aliases = _print_aliases(tree)
    for node in ast.walk(tree):
        if _is_output_call(node, aliases):
            seg = ast.get_source_segment(text, node)
            if seg and any(ord(c) > 127 for c in seg):
                return True
    return False


def _has_guard(path: pathlib.Path) -> bool:
    text = path.read_text(encoding="utf-8")
    return any(snippet in text for snippet in _GUARD_SNIPPETS)


class StdoutEncodingInvariantTests(unittest.TestCase):
    """Every runnable script that prints non-ASCII must reconfigure
    stdout/stderr to utf-8, or it dies with UnicodeEncodeError on a cp1252
    console. This scans the directory rather than naming files, so it also
    catches a future script that adds a non-ASCII print without the guard."""

    def test_scripts_with_nonascii_output_have_utf8_guard(self):
        missing = []
        for path in sorted(SCRIPTS_DIR.glob("*.py")):
            if _needs_guard(path) and not _has_guard(path):
                missing.append(path.name)
        self.assertEqual(
            missing, [],
            "scripts print non-ASCII text without the stdout/stderr utf-8 "
            "reconfigure guard (see combat.py, or turn_lint.py's / "
            f"session_audit.py's main() for the idiom): {missing}")


class Cp1252SubprocessTests(unittest.TestCase):
    """The actual crash, not just the guard's presence as text: dice.py's
    advantage-roll line prints 'Takes roll {taken} -> Total: {chosen}' with a
    real arrow character. Forcing PYTHONIOENCODING=cp1252 reproduces the
    Windows-console default that has no UTF-8 override."""

    def test_dice_advantage_roll_survives_forced_cp1252(self):
        env = dict(os.environ)
        env["PYTHONIOENCODING"] = "cp1252"
        result = subprocess.run(
            [sys.executable, str(DICE), "d20 adv"],
            capture_output=True, text=True, env=env, cwd=str(REPO))
        self.assertEqual(
            result.returncode, 0,
            f"dice.py crashed under forced cp1252 stdout/stderr:\n"
            f"stdout={result.stdout!r}\nstderr={result.stderr!r}")


if __name__ == "__main__":
    unittest.main()
