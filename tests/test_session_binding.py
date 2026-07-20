"""Play-session binding for the autosave Stop hook.

    python3 -m unittest tests.test_session_binding -v

The hook gates only on "is a campaign active", which is equally true in a dev
session that happens to have one loaded. On 2026-07-20 that caused two real
problems in one afternoon: the hook asked a code-editing session to flush
continuity anchors into a live campaign, and the turn lint recorded a finding
against a dev turn that merely *quoted* a roll request — the first entry ever
written to a lint log was a false positive about the lint itself.

`/dm:dnd load` rewrites active-campaign.json from scratch (SKILL-commands.md:109),
so the marker carries no session id until a hook run claims it. First Stop after a
load binds; every other session no-ops.
"""

import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "skills", "dnd", "scripts")
)

import autosave_checkpoint as ac  # noqa: E402

REPO = pathlib.Path(__file__).resolve().parent.parent
HOOK = REPO / "skills" / "dnd" / "scripts" / "autosave_checkpoint.py"


def _user(text):
    return {"type": "user", "message": {"role": "user", "content": text}}


def _assistant(text):
    return {"type": "assistant",
            "message": {"role": "assistant",
                        "content": [{"type": "text", "text": text}]}}


def _tool_result(text):
    return {"type": "user",
            "message": {"role": "user",
                        "content": [{"type": "tool_result", "content": text}]}}


def _write_jsonl(path, entries):
    with open(path, "w", encoding="utf-8") as f:
        for e in entries:
            f.write(json.dumps(e) + "\n")


class SessionBindingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.marker = os.path.join(self.tmp.name, ac.ACTIVE_MARKER)
        self._write({"name": "thornwake", "skill_dir": "/somewhere"})

    def _write(self, obj):
        with open(self.marker, "w", encoding="utf-8") as f:
            json.dump(obj, f)

    def _read(self):
        with open(self.marker, encoding="utf-8") as f:
            return json.load(f)

    def test_fresh_marker_has_no_binding(self):
        self.assertIsNone(ac.bound_session(self.marker))

    def test_claim_writes_the_session_id(self):
        ac.claim_session(self.marker, "play-1")
        self.assertEqual(ac.bound_session(self.marker), "play-1")

    def test_claim_preserves_existing_keys(self):
        """skill_dir is the post-compaction recovery anchor — must survive."""
        ac.claim_session(self.marker, "play-1")
        data = self._read()
        self.assertEqual(data["name"], "thornwake")
        self.assertEqual(data["skill_dir"], "/somewhere")

    def test_unbound_marker_admits_any_session(self):
        self.assertTrue(ac.session_owns_campaign(self.marker, "play-1"))

    def test_bound_marker_admits_the_owner(self):
        ac.claim_session(self.marker, "play-1")
        self.assertTrue(ac.session_owns_campaign(self.marker, "play-1"))

    def test_bound_marker_rejects_a_different_session(self):
        """The regression: a dev session must not act on a loaded campaign."""
        ac.claim_session(self.marker, "play-1")
        self.assertFalse(ac.session_owns_campaign(self.marker, "dev-2"))

    def test_reload_clears_the_binding(self):
        """/dm:dnd load rewrites the marker, so the next session rebinds."""
        ac.claim_session(self.marker, "play-1")
        self._write({"name": "thornwake", "skill_dir": "/somewhere"})
        self.assertIsNone(ac.bound_session(self.marker))
        self.assertTrue(ac.session_owns_campaign(self.marker, "play-2"))

    def test_missing_session_id_does_not_bind_or_block(self):
        """Manual CLI runs have no session_id — they must stay usable."""
        self.assertTrue(ac.session_owns_campaign(self.marker, None))
        self.assertIsNone(ac.bound_session(self.marker))

    def test_missing_marker_is_not_owned_by_anyone(self):
        os.unlink(self.marker)
        self.assertTrue(ac.session_owns_campaign(self.marker, "any"))

    def test_unreadable_marker_does_not_raise(self):
        with open(self.marker, "w", encoding="utf-8") as f:
            f.write("{ not json")
        self.assertIsNone(ac.bound_session(self.marker))
        self.assertTrue(ac.session_owns_campaign(self.marker, "any"))


class TranscriptClaimGuardTests(unittest.TestCase):
    """Only a session whose user actually ran `/dm:dnd load` may claim.

    The claim race: a dev session's Stop event landing between `/dm:dnd load`
    (which strips the session id) and the play session's first turn-end used
    to claim the campaign, silently killing snapshot + lint for play.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.transcript = os.path.join(self.tmp.name, "session.jsonl")

    def _check(self, entries, campaign="thornwake"):
        _write_jsonl(self.transcript, entries)
        return ac.transcript_loaded_campaign(self.transcript, campaign)

    def test_bare_load_command_counts(self):
        """Picker-flow load carries no name argument."""
        self.assertTrue(self._check([_user("/dm:dnd load")]))

    def test_load_with_matching_name_counts(self):
        self.assertTrue(self._check([_user("/dm:dnd load thornwake")]))

    def test_load_name_match_is_case_insensitive(self):
        self.assertTrue(self._check([_user("/dm:dnd load Thornwake")]))

    def test_load_of_a_different_campaign_does_not_count(self):
        self.assertFalse(self._check([_user("/dm:dnd load skelia")]))

    def test_no_load_command_does_not_count(self):
        self.assertFalse(self._check(
            [_user("fix the lint detector"), _assistant("On it.")]))

    def test_load_quoted_in_assistant_text_does_not_count(self):
        """A dev session *discussing* the load command must not claim."""
        self.assertFalse(self._check(
            [_user("why is the marker stale?"),
             _assistant("Because `/dm:dnd load thornwake` rewrites it.")]))

    def test_load_inside_tool_result_does_not_count(self):
        self.assertFalse(self._check(
            [_user("read the commands doc"),
             _tool_result("…run /dm:dnd load thornwake to begin…")]))

    def test_missing_transcript_does_not_count(self):
        self.assertFalse(
            ac.transcript_loaded_campaign(
                os.path.join(self.tmp.name, "nope.jsonl"), "thornwake"))

    def test_no_transcript_path_does_not_count(self):
        self.assertFalse(ac.transcript_loaded_campaign(None, "thornwake"))


class HookClaimRaceTests(unittest.TestCase):
    """End-to-end through the hook: the dev session must lose the race."""

    CAMPAIGN = "race-probe"

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = pathlib.Path(self.tmp.name)
        camp = root / "campaigns" / self.CAMPAIGN
        camp.mkdir(parents=True)
        (camp / "state.md").write_text(
            "# State\n\n## Session Flags\n- roll_mode: players\n",
            encoding="utf-8")
        self.runtime = root / ".runtime"
        self.runtime.mkdir()
        self.marker = self.runtime / ac.ACTIVE_MARKER
        self.marker.write_text(
            json.dumps({"name": self.CAMPAIGN, "skill_dir": "/somewhere"}),
            encoding="utf-8")
        self.env = dict(os.environ)
        self.env["DND_CAMPAIGN_ROOT"] = str(root)
        self.env["DND_RUNTIME_DIR"] = str(self.runtime)

        self.play_transcript = root / "play.jsonl"
        _write_jsonl(self.play_transcript,
                     [_user(f"/dm:dnd load {self.CAMPAIGN}"),
                      _assistant("Welcome back to the campaign.")])
        self.dev_transcript = root / "dev.jsonl"
        _write_jsonl(self.dev_transcript,
                     [_user("tighten the lint regexes"),
                      _assistant("The hook fires after `/dm:dnd load`.")])

    def _run_hook(self, session_id, transcript):
        payload = json.dumps({"session_id": session_id,
                              "transcript_path": str(transcript),
                              "hook_event_name": "Stop",
                              "stop_hook_active": False})
        return subprocess.run(
            [sys.executable, str(HOOK)], input=payload,
            capture_output=True, text=True, env=self.env, cwd=str(REPO))

    def _bound(self):
        return json.loads(self.marker.read_text(encoding="utf-8")).get("session_id")

    def test_dev_session_cannot_claim(self):
        result = self._run_hook("dev-1", self.dev_transcript)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIsNone(self._bound())
        self.assertFalse(
            list(self.runtime.glob("*.autocheckpoint.md")),
            "dev session acted on the campaign (snapshot written)")

    def test_play_session_claims(self):
        result = self._run_hook("play-1", self.play_transcript)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self._bound(), "play-1")
        self.assertTrue(list(self.runtime.glob("*.autocheckpoint.md")))

    def test_dev_stop_before_play_stop_loses_the_race(self):
        """The original failure ordering: dev's Stop lands first."""
        self._run_hook("dev-1", self.dev_transcript)
        self._run_hook("play-1", self.play_transcript)
        self.assertEqual(self._bound(), "play-1")

    def test_bound_owner_keeps_acting_without_reproving_load(self):
        self._run_hook("play-1", self.play_transcript)
        for snap in self.runtime.glob("*.autocheckpoint.md"):
            snap.unlink()
        result = self._run_hook("play-1", self.play_transcript)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(list(self.runtime.glob("*.autocheckpoint.md")))


if __name__ == "__main__":
    unittest.main()
