"""test_prep_schema.py — bible validation: party-level chain + full validator.

Run from repo root:
    python3 -m unittest tests.test_prep_schema -v
"""
import pathlib
import sys
import unittest

REPO = pathlib.Path(__file__).resolve().parent.parent
SKILL = REPO / "skills" / "dnd" if (REPO / "skills" / "dnd").is_dir() else REPO
sys.path.insert(0, str(SKILL / "scripts"))

from prep import schema


class PartyLevelTests(unittest.TestCase):
    def test_level_holds_until_a_beat_levels_then_carries(self):
        beats = [
            {"level_up_to": None},   # beat 1: at level 1
            {"level_up_to": 2},      # beat 2: still 1 while playing, becomes 2 after
            {"level_up_to": None},   # beat 3: at level 2
            {"level_up_to": 4},      # beat 4: at level 2, becomes 4 after
        ]
        self.assertEqual(schema.party_levels(beats), [1, 1, 2, 2])

    def test_start_level_seeds_the_chain(self):
        beats = [
            {"level_up_to": None},   # beat 1: at level 3
            {"level_up_to": 4},      # beat 2: at 3 while playing, becomes 4 after
            {"level_up_to": None},   # beat 3: at level 4
        ]
        self.assertEqual(schema.party_levels(beats, start_level=3), [3, 3, 4])


class ParseThreatTests(unittest.TestCase):
    def test_bare_name_means_one(self):
        self.assertEqual(schema.parse_threat("Goblin"), (1, "Goblin"))

    def test_count_prefix_splits(self):
        self.assertEqual(schema.parse_threat("3x Goblin"), (3, "Goblin"))

    def test_zero_count_parses_as_zero(self):
        self.assertEqual(schema.parse_threat("0x Goblin"), (0, "Goblin"))


def _valid_beats():
    # 6 beats, 3 acts (2/2/2), L1->8, threats in band for each beat's party level.
    return [
        {"id": 1, "act": 1, "label": "Inciting Incident", "situation": "s",
         "what_changes": "w", "world_pressure": "p", "level_up_to": 2,
         "gear": ["torch"], "threats": ["Goblin"], "secret": None, "status": "pending"},
        {"id": 2, "act": 1, "label": "Complication", "situation": "s",
         "what_changes": "w", "world_pressure": "p", "level_up_to": 3,
         "gear": [], "threats": ["Bugbear"], "secret": "a hidden cult", "status": "pending"},
        {"id": 3, "act": 2, "label": "Rising Action", "situation": "s",
         "what_changes": "w", "world_pressure": "p", "level_up_to": 4,
         "gear": [], "threats": ["Ogre"], "secret": None, "status": "pending"},
        {"id": 4, "act": 2, "label": "Midpoint", "situation": "s",
         "what_changes": "w", "world_pressure": "p", "level_up_to": 6,
         "gear": [], "threats": [], "secret": None, "status": "pending"},
        {"id": 5, "act": 3, "label": "All Is Lost", "situation": "s",
         "what_changes": "w", "world_pressure": "p", "level_up_to": 7,
         "gear": [], "threats": ["Young Green Dragon"], "secret": None, "status": "pending"},
        {"id": 6, "act": 3, "label": "Final Confrontation", "situation": "s",
         "what_changes": "w", "world_pressure": "p", "level_up_to": 8,
         "gear": ["dragon hoard"], "threats": ["Young Blue Dragon"], "secret": None,
         "status": "pending"},
    ]


def _bible(beats, party=None):
    return {
        "theme": "t",
        "resolution": "r",
        "causal_thread": "c",
        "party": party if party is not None else {"size": 4, "start_level": 1},
        "beats": beats,
    }


class ValidateBibleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from prep import bestiary
        cls.monsters = bestiary.load_monsters()

    def test_valid_bible_passes(self):
        self.assertEqual(schema.validate_bible(_bible(_valid_beats()), self.monsters), [])

    def test_missing_party_block_flagged(self):
        bible = _bible(_valid_beats())
        del bible["party"]
        errs = schema.validate_bible(bible, self.monsters)
        self.assertTrue(any("party block required" in e for e in errs))

    def test_party_size_out_of_range_flagged(self):
        errs = schema.validate_bible(
            _bible(_valid_beats(), party={"size": 0, "start_level": 1}), self.monsters
        )
        self.assertTrue(any("party.size" in e for e in errs))

    def test_party_start_level_out_of_range_flagged(self):
        # 8 leaves no room to level — the arc must end above start_level
        errs = schema.validate_bible(
            _bible(_valid_beats(), party={"size": 4, "start_level": 8}), self.monsters
        )
        self.assertTrue(any("party.start_level" in e for e in errs))

    def test_level_up_to_must_exceed_start_level(self):
        # An L3 party cannot have beats that "level up to" 2 or 3.
        errs = schema.validate_bible(
            _bible(_valid_beats(), party={"size": 4, "start_level": 3}), self.monsters
        )
        self.assertTrue(any("must exceed party.start_level" in e for e in errs))

    def test_start_level_shifts_threat_band(self):
        # The C2 failure mode inverted: at start_level 5, a lone Goblin (CR 1/4)
        # is below the level-5 band floor and must now FAIL validation.
        beats = _valid_beats()
        for b in beats:
            b["level_up_to"] = None
        beats[3]["level_up_to"] = 6
        beats[5]["level_up_to"] = 8
        errs = schema.validate_bible(
            _bible(beats, party={"size": 4, "start_level": 5}), self.monsters
        )
        self.assertTrue(any("Goblin" in e and "out of band" in e for e in errs))

    def test_count_prefixed_threat_valid(self):
        beats = _valid_beats()
        beats[0]["threats"] = ["3x Goblin"]
        self.assertEqual(schema.validate_bible(_bible(beats), self.monsters), [])

    def test_zero_count_threat_flagged(self):
        beats = _valid_beats()
        beats[0]["threats"] = ["0x Goblin"]
        errs = schema.validate_bible(_bible(beats), self.monsters)
        self.assertTrue(any("count" in e for e in errs))

    def test_count_prefixed_unknown_name_flagged(self):
        beats = _valid_beats()
        beats[0]["threats"] = ["3x Goblim"]  # typo behind a count prefix
        errs = schema.validate_bible(_bible(beats), self.monsters)
        self.assertTrue(any("unknown monster" in e for e in errs))

    def test_beat_count_out_of_range(self):
        errs = schema.validate_bible(_bible(_valid_beats()[:4]), self.monsters)
        self.assertTrue(any("beat count" in e for e in errs))

    def test_non_monotonic_level_up_to(self):
        beats = _valid_beats()
        beats[2]["level_up_to"] = 2  # 3 -> 2, not increasing
        errs = schema.validate_bible(_bible(beats), self.monsters)
        self.assertTrue(any("increasing" in e for e in errs))

    def test_final_beat_level_up_to_must_not_be_null(self):
        beats = _valid_beats()
        beats[-1]["level_up_to"] = None
        errs = schema.validate_bible(_bible(beats), self.monsters)
        self.assertTrue(any("final beat" in e for e in errs))

    def test_threat_out_of_band(self):
        beats = _valid_beats()
        beats[0]["threats"] = ["Young Red Dragon"]  # CR 10 at party level 1
        errs = schema.validate_bible(_bible(beats), self.monsters)
        self.assertTrue(any("out of band" in e for e in errs))

    def test_unknown_threat_name(self):
        beats = _valid_beats()
        beats[0]["threats"] = ["Goblim"]  # typo, not in bestiary
        errs = schema.validate_bible(_bible(beats), self.monsters)
        self.assertTrue(any("unknown monster" in e for e in errs))

    def test_missing_secret_key_flagged(self):
        beats = _valid_beats()
        del beats[0]["secret"]
        errs = schema.validate_bible(_bible(beats), self.monsters)
        self.assertTrue(any("secret" in e for e in errs))

    def test_empty_gear_entry_flagged(self):
        beats = _valid_beats()
        beats[0]["gear"] = [""]
        errs = schema.validate_bible(_bible(beats), self.monsters)
        self.assertTrue(any("gear" in e for e in errs))

    def test_malformed_act_returns_error_not_crash(self):
        beats = _valid_beats()
        del beats[0]["act"]  # act -> None, not orderable against ints
        errs = schema.validate_bible(_bible(beats), self.monsters)  # must not raise
        self.assertTrue(any("act values must be in" in e for e in errs))

    def test_string_level_up_to_returns_error_not_crash(self):
        beats = _valid_beats()
        beats[0]["level_up_to"] = "3"  # string, not int
        errs = schema.validate_bible(_bible(beats), self.monsters)  # must not raise
        self.assertTrue(any("level_up_to" in e for e in errs))

    def test_gear_as_bare_string_flagged(self):
        beats = _valid_beats()
        beats[0]["gear"] = "torch"  # bare string, not a list
        errs = schema.validate_bible(_bible(beats), self.monsters)
        self.assertTrue(any("gear must be a list" in e for e in errs))

    def test_threats_as_bare_string_flagged(self):
        beats = _valid_beats()
        beats[0]["threats"] = "Goblin"  # bare string, not a list
        errs = schema.validate_bible(_bible(beats), self.monsters)
        self.assertTrue(any("threats must be a list" in e for e in errs))

    def test_invalid_status_flagged(self):
        beats = _valid_beats()
        beats[0]["status"] = "in-progress"  # not a legal status
        errs = schema.validate_bible(_bible(beats), self.monsters)
        self.assertTrue(any("status" in e for e in errs))

    def test_missing_status_flagged(self):
        beats = _valid_beats()
        del beats[0]["status"]
        errs = schema.validate_bible(_bible(beats), self.monsters)
        self.assertTrue(any("status" in e for e in errs))

    def test_unhashable_status_returns_error_not_crash(self):
        beats = _valid_beats()
        beats[0]["status"] = ["pending"]  # list, unhashable — must not crash
        errs = schema.validate_bible(_bible(beats), self.monsters)  # must not raise
        self.assertTrue(any("status" in e for e in errs))

    def test_two_current_beats_flagged(self):
        beats = _valid_beats()
        beats[0]["status"] = "current"
        beats[1]["status"] = "current"  # two playheads — impossible
        errs = schema.validate_bible(_bible(beats), self.monsters)
        self.assertTrue(any("current" in e for e in errs))

    def test_complete_after_current_flagged(self):
        # The F4 bug: on beat 2 while a later beat is already complete.
        beats = _valid_beats()
        beats[1]["status"] = "current"
        beats[4]["status"] = "complete"
        errs = schema.validate_bible(_bible(beats), self.monsters)
        self.assertTrue(any("status order" in e for e in errs))

    def test_pending_before_resolved_flagged(self):
        # A pending beat cannot precede a completed one.
        beats = _valid_beats()
        beats[0]["status"] = "pending"
        beats[1]["status"] = "complete"
        errs = schema.validate_bible(_bible(beats), self.monsters)
        self.assertTrue(any("status order" in e for e in errs))

    def test_coherent_midplay_spine_passes(self):
        # Resolved prefix, one current, pending tail — a real mid-play state.
        beats = _valid_beats()
        beats[0]["status"] = "complete"
        beats[1]["status"] = "skipped"
        beats[2]["status"] = "current"
        # beats 4..6 stay pending
        self.assertEqual(schema.validate_bible(_bible(beats), self.monsters), [])

    def test_terminal_all_complete_passes(self):
        beats = _valid_beats()
        for b in beats:
            b["status"] = "complete"
        self.assertEqual(schema.validate_bible(_bible(beats), self.monsters), [])


if __name__ == "__main__":
    unittest.main()
