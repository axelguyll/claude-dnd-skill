"""test_combat_passthrough.py — combat.py must pass unknown combatant fields
(pos, hidden) through initiative untouched: positions ride STATE_JSON from
init through every render. Guard against a future initiative_order rewrite
that rebuilds dicts and silently strips them. Spec:
docs/superpowers/specs/2026-07-16-combat-grid-map-cue-design.md
"""
import contextlib
import io
import pathlib
import sys
import unittest

SCRIPTS = pathlib.Path(__file__).resolve().parent.parent / "skills" / "dnd" / "scripts"
sys.path.insert(0, str(SCRIPTS))
import combat  # noqa: E402


class PassThroughTests(unittest.TestCase):
    def test_initiative_order_preserves_pos_and_hidden(self):
        combatants = [
            {"name": "Piper", "dex_mod": 2, "hp": 18, "ac": 15, "type": "pc",
             "pos": "C4"},
            {"name": "Lurker", "dex_mod": 1, "hp": 30, "ac": 13, "type": "npc",
             "pos": "A1", "hidden": True},
        ]
        ordered = combat.initiative_order(combatants)
        by_name = {c["name"]: c for c in ordered}
        self.assertEqual(by_name["Piper"]["pos"], "C4")
        self.assertEqual(by_name["Lurker"]["pos"], "A1")
        self.assertTrue(by_name["Lurker"]["hidden"])

    def test_print_tracker_tolerates_new_fields(self):
        combatants = [{"name": "Piper", "dex_mod": 2, "hp": 18, "ac": 15,
                       "type": "pc", "pos": "C4", "hidden": False}]
        ordered = combat.initiative_order(combatants)
        with contextlib.redirect_stdout(io.StringIO()):
            combat.print_tracker(ordered, 1)   # must not raise


if __name__ == "__main__":
    unittest.main()
