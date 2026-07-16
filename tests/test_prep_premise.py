"""test_prep_premise.py — the premise composer rolls orthogonal axes and emits
a reconcile-instruction scaffold. Determinism is seeded so the roll is testable."""
import pathlib
import random
import subprocess
import sys
import unittest

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "skills" / "dnd" / "scripts" / "prep"))

import premise  # noqa: E402

SCRIPT = REPO / "skills" / "dnd" / "scripts" / "prep" / "premise.py"


class RollTests(unittest.TestCase):
    def setUp(self):
        self.tones = premise.load_tones()
        self.seeds = premise.load_seeds()

    def test_seeded_roll_is_deterministic(self):
        a = premise.roll_premise("grimdark", self.tones, self.seeds, random.Random(42))
        b = premise.roll_premise("grimdark", self.tones, self.seeds, random.Random(42))
        self.assertEqual(a, b)

    def test_roll_has_all_four_axes(self):
        r = premise.roll_premise("heroic", self.tones, self.seeds, random.Random(1))
        for axis in ("setting", "conflict", "antagonist", "twist"):
            self.assertTrue(r[axis].strip())

    def test_roll_carries_tone_mood_note(self):
        r = premise.roll_premise("cosmic", self.tones, self.seeds, random.Random(1))
        self.assertEqual(r["tone"], "cosmic")
        self.assertTrue(r["mood_note"].strip())

    def test_unknown_tone_raises(self):
        with self.assertRaises(KeyError):
            premise.roll_premise("nope", self.tones, self.seeds, random.Random(1))

    def test_blank_tone_rolls_from_catalog(self):
        ids = {t["id"] for t in self.tones}
        r = premise.roll_premise(None, self.tones, self.seeds, random.Random(9))
        self.assertIn(r["tone"], ids)
        self.assertTrue(r["mood_note"].strip())

    def test_scaffold_contains_axes_and_instruction(self):
        r = premise.roll_premise("intrigue", self.tones, self.seeds, random.Random(7))
        out = premise.format_scaffold(r)
        self.assertIn(r["setting"], out)
        self.assertIn(r["antagonist"], out)
        self.assertIn(r["tone"], out)  # resolved tone reported for world.md
        self.assertIn("Reconcile into ONE coherent premise", out)
        self.assertIn("Do not default to the nearest cliché", out)

    def test_scaffold_names_the_target_trope(self):
        r = premise.roll_premise("grimdark", self.tones, self.seeds, random.Random(2))
        self.assertIn("sealed-mine", premise.format_scaffold(r))


class CliTests(unittest.TestCase):
    def test_cli_good_tone_exit_zero(self):
        p = subprocess.run([sys.executable, str(SCRIPT), "--tone", "horror", "--seed", "3"],
                           capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("Reconcile into ONE coherent premise", p.stdout)

    def test_cli_no_tone_rolls_and_exits_zero(self):
        p = subprocess.run([sys.executable, str(SCRIPT), "--seed", "5"],
                           capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("Reconcile into ONE coherent premise", p.stdout)

    def test_cli_bad_tone_exit_nonzero(self):
        p = subprocess.run([sys.executable, str(SCRIPT), "--tone", "bogus"],
                           capture_output=True, text=True)
        self.assertNotEqual(p.returncode, 0)


if __name__ == "__main__":
    unittest.main()
