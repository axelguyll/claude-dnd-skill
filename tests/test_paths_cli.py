"""paths.py CLI — list-campaigns and set-active.

Pass A findings 1.7/1.8/1.9: the campaign list, the mtime sort, and the
active-marker write are deterministic, and the marker is load-bearing for
three subsystems (session binding, turn lint, snapshot) while
claim_session() silently gives up on a parse error — so the most fragile
writer in the stack (a model hand-write) must not produce it.

Run from repo root:
    python -m unittest tests.test_paths_cli -v
"""
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import time
import unittest

REPO = pathlib.Path(__file__).resolve().parent.parent
PATHS = REPO / "skills" / "dnd" / "scripts" / "paths.py"


class PathsCliTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = pathlib.Path(self.tmp.name)
        self.campaigns = self.root / "campaigns"
        self.campaigns.mkdir()
        self.runtime = self.root / ".runtime"
        self.env = dict(os.environ)
        self.env["DND_CAMPAIGN_ROOT"] = str(self.root)
        self.env["DND_RUNTIME_DIR"] = str(self.runtime)

    def _campaign(self, name, session_count=None, age_hours=0):
        camp = self.campaigns / name
        camp.mkdir()
        if session_count is not None:
            state = camp / "state.md"
            state.write_text(
                f"# Campaign: {name}\nSession count: {session_count}\n"
                f"Last session: 2026-07-19\n",
                encoding="utf-8")
            if age_hours:
                old = time.time() - age_hours * 3600
                os.utime(state, (old, old))
        return camp

    def _run(self, *args):
        return subprocess.run(
            [sys.executable, str(PATHS), *args],
            capture_output=True, text=True, env=self.env, cwd=str(REPO))


class ListCampaignsTests(PathsCliTestCase):
    def test_lists_most_recently_played_first(self):
        self._campaign("older-camp", session_count=7, age_hours=48)
        self._campaign("newer-camp", session_count=2, age_hours=1)
        result = self._run("list-campaigns")
        self.assertEqual(result.returncode, 0, result.stderr)
        lines = result.stdout.strip().splitlines()
        self.assertEqual(len(lines), 2)
        self.assertTrue(lines[0].startswith("newer-camp\t"))
        self.assertTrue(lines[1].startswith("older-camp\t"))

    def test_fields_are_name_mtime_sessions(self):
        self._campaign("solo-camp", session_count=5)
        result = self._run("list-campaigns")
        fields = result.stdout.strip().split("\t")
        self.assertEqual(fields[0], "solo-camp")
        self.assertRegex(fields[1], r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$")
        self.assertEqual(fields[2], "5")

    def test_campaign_without_state_still_listed(self):
        self._campaign("broken-camp", session_count=None)
        result = self._run("list-campaigns")
        self.assertEqual(result.returncode, 0, result.stderr)
        line = result.stdout.strip()
        self.assertTrue(line.startswith("broken-camp\t"))
        self.assertTrue(line.endswith("\t0"))

    def test_empty_campaigns_dir(self):
        result = self._run("list-campaigns")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "")


class SetActiveTests(PathsCliTestCase):
    def _marker(self):
        return json.loads(
            (self.runtime / "active-campaign.json").read_text(encoding="utf-8"))

    def test_writes_marker_with_name_and_skill_dir(self):
        self._campaign("thornwake", session_count=3)
        result = self._run("set-active", "thornwake",
                           "--skill-dir", "/somewhere/skills/dnd")
        self.assertEqual(result.returncode, 0, result.stderr)
        data = self._marker()
        self.assertEqual(data["name"], "thornwake")
        self.assertEqual(data["skill_dir"], "/somewhere/skills/dnd")

    def test_marker_carries_no_session_id(self):
        """The load contract: an unbound marker is what lets the play
        session claim the campaign."""
        self._campaign("thornwake", session_count=3)
        self.runtime.mkdir(parents=True, exist_ok=True)
        (self.runtime / "active-campaign.json").write_text(
            json.dumps({"name": "old", "session_id": "stale-dev"}),
            encoding="utf-8")
        self._run("set-active", "thornwake", "--skill-dir", "/x")
        data = self._marker()
        self.assertNotIn("session_id", data)

    def test_default_skill_dir_is_the_install(self):
        self._campaign("thornwake", session_count=1)
        result = self._run("set-active", "thornwake")
        self.assertEqual(result.returncode, 0, result.stderr)
        skill_dir = pathlib.Path(self._marker()["skill_dir"])
        self.assertTrue((skill_dir / "scripts" / "paths.py").exists())

    def test_unknown_campaign_fails_without_writing(self):
        result = self._run("set-active", "no-such-campaign", "--skill-dir", "/x")
        self.assertEqual(result.returncode, 1)
        self.assertFalse((self.runtime / "active-campaign.json").exists())


if __name__ == "__main__":
    unittest.main()
