"""Guard: the display companion is gone. These tokens must not reappear in the
canonical skill docs or the state template. Mirrors DMVoiceTests (content-assertion
guard) in test_prep_skill_prose.py — prevents silent reversion, not a behavior test."""
import pathlib
import re
import unittest

SKILL_DIR = pathlib.Path(__file__).resolve().parents[1] / "skills" / "dnd"

# Flag/path forms of the removed feature. Prose words are NOT here — the
# narration/NPC block separation survives as a writing rule (Approach B), so
# "NPC block" / "NPC dialogue" / bare "NPC" must stay legal. Likewise
# "roll_mode" (players/auto is still a terminal concept), "dice.py", and
# "--silent" (hidden-roll mechanic) survive.
FORBIDDEN = [
    "display/",          # ${CLAUDE_SKILL_DIR}/display/... paths
    "send.py",
    "push_stats",
    "check_input",
    "autorun",           # also catches autorun_interval, autorun_wait
    "_display_running",
    "dice-request",      # --dice-request flag and /dice-request endpoint
    "--stat-",
    "--npc",             # the flag; the prose word "NPC" is allowed
    "--tutor",           # the send flag; tutor_mode as a chat feature may survive
    "--dice",            # send.py routing flag
    "--dc ",             # display dice-request DC leak (trailing space: not "--dc]" etc.)
    "--player",          # phone-tab routing flag; see _strip_allowed for --players
    "start-display",
    "dm_help",
    "tts_voice",
    "TTS",
    "sfx_",              # sfx_languages flag
    "SFX",
]

# Word-boundary patterns for tokens that substring-match innocent words
# (plain "LAN" would flag "Beat 2b LANDED").
FORBIDDEN_RE = [
    re.compile(r"\bLAN\b"),
    re.compile(r"--lan\b"),
]

# xp.py's `calc --players N` is a party-size argument, not display routing.
_ALLOWED_SUBSTRINGS = ["--players"]

TARGETS = [
    SKILL_DIR / "SKILL.md",
    SKILL_DIR / "SKILL-commands.md",
    SKILL_DIR / "SKILL-scripts.md",
    SKILL_DIR / "templates" / "state.md",
]


def _strip_allowed(line: str) -> str:
    for allowed in _ALLOWED_SUBSTRINGS:
        line = line.replace(allowed, "")
    return line


class NoDisplayRefsTests(unittest.TestCase):
    def test_no_forbidden_tokens(self):
        hits = []
        for path in TARGETS:
            text = path.read_text(encoding="utf-8")
            for i, line in enumerate(text.splitlines(), 1):
                stripped = _strip_allowed(line)
                for tok in FORBIDDEN:
                    if tok in stripped:
                        hits.append(f"{path.name}:{i}: {tok!r} in {line.strip()[:80]}")
                for pat in FORBIDDEN_RE:
                    if pat.search(stripped):
                        hits.append(f"{path.name}:{i}: {pat.pattern!r} in {line.strip()[:80]}")
        self.assertEqual(hits, [], "display refs remain:\n" + "\n".join(hits))


if __name__ == "__main__":
    unittest.main()
