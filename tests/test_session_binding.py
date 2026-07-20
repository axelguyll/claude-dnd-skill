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
import sys
import tempfile
import unittest

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "skills", "dnd", "scripts")
)

import autosave_checkpoint as ac  # noqa: E402


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


if __name__ == "__main__":
    unittest.main()
