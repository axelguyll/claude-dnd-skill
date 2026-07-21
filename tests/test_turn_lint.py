"""test_turn_lint.py — detector + transcript-parsing tests for the log-only turn lint.

Run from repo root:
    python3 -m unittest tests.test_turn_lint -v
"""
import json
import os
import pathlib
import sys
import tempfile
import unittest

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "skills" / "dnd" / "scripts"))

import turn_lint  # noqa: E402

FLAGS_PLAYERS = {"roll_mode": "players"}
FLAGS_AUTO = {"roll_mode": "auto"}


class RoteCloserTests(unittest.TestCase):
    def test_flags_stock_closer(self):
        text = "The reeve turns away. Holg — what do you do?"
        self.assertEqual(len(turn_lint.check_rote_closer(text)), 1)

    def test_flags_whats_your_move(self):
        self.assertEqual(
            len(turn_lint.check_rote_closer("The door creaks. What's your move?")), 1)

    def test_allows_real_options_closer(self):
        text = "The gate is shut. Fight, or find another way out — or something else?"
        self.assertEqual(turn_lint.check_rote_closer(text), [])

    def test_only_scans_turn_end(self):
        text = ("Early on he asked 'what do you do for coin?' and laughed. "
                + "The night market unfolds ahead of you. " * 20)
        self.assertEqual(turn_lint.check_rote_closer(text), [])


class DcLeakTests(unittest.TestCase):
    def test_flags_dc_number(self):
        out = turn_lint.check_dc_leak("Make a DC 15 Strength check to hold the gate.")
        self.assertEqual(len(out), 1)
        self.assertIn("DC 15", out[0]["detail"])

    def test_tutor_line_exempt(self):
        text = "> ◈ Tutor: You failed by 3 — the lock was DC 15 against your +2."
        self.assertEqual(turn_lint.check_dc_leak(text), [])

    def test_spell_save_dc_exempt(self):
        text = "The goblin rolls against your spell save DC 13 and shrieks."
        self.assertEqual(turn_lint.check_dc_leak(text), [])

    def test_clean_narration_passes(self):
        self.assertEqual(turn_lint.check_dc_leak("The lock gives. You're in."), [])


class RollNotFinalTests(unittest.TestCase):
    REQUEST = "Give me a Wisdom (Perception) check — d20 plus your Wisdom."
    PADDING = "The alley smells of rain and old rope, and somewhere a shutter bangs. " * 8

    def test_flags_request_followed_by_narration(self):
        out = turn_lint.check_roll_not_final(self.REQUEST + " " + self.PADDING, "players")
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["detector"], "roll_not_final")

    def test_request_at_turn_end_passes(self):
        text = self.PADDING + " " + self.REQUEST
        self.assertEqual(turn_lint.check_roll_not_final(text, "players"), [])

    def test_short_option_tail_allowed(self):
        text = self.REQUEST + " …or you can back away quietly instead."
        self.assertEqual(turn_lint.check_roll_not_final(text, "players"), [])

    def test_auto_mode_skipped(self):
        text = self.REQUEST + " " + self.PADDING
        self.assertEqual(turn_lint.check_roll_not_final(text, "auto"), [])

    def test_no_request_no_finding(self):
        self.assertEqual(turn_lint.check_roll_not_final(self.PADDING, "players"), [])

    def test_flags_lead_in_hedge_hand_over(self):
        text = ("That's the kind of thing a man doesn't just hand over. "
                "Give me a Charisma (Persuasion) check")
        out = turn_lint.check_roll_not_final(text, "players")
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["detector"], "roll_not_final")
        self.assertIn("lead-in", out[0]["detail"])

    def test_flags_lead_in_hedge_not_exactly_slow(self):
        text = ("bold, but Fenna's not exactly slow. "
                "Give me a Charisma (Deception) check.")
        out = turn_lint.check_roll_not_final(text, "players")
        self.assertEqual(len(out), 1)
        self.assertIn("lead-in", out[0]["detail"])

    def test_known_miss_different_reasons_not_flagged(self):
        # KNOWN MISS, accepted deliberately: an earlier version had a
        # `different reasons? to` pattern hardcoded to this exact fixture.
        # It had no general relationship to odds/outcome language ("you two
        # have different reasons to be here" is innocuous) and was dropped
        # as overfitting on code review. This fixture is not caught by any
        # of the four general categories and that is expected, not a bug —
        # see check_roll_not_final's docstring for the recall tradeoff.
        text = ("He's not you though — different man, different reasons to "
                "hold something back. Give me another Charisma (Persuasion) check.")
        self.assertEqual(turn_lint.check_roll_not_final(text, "players"), [])

    def test_flags_lead_in_canonical_wont_win_on_skill(self):
        text = ("He looks you over, unimpressed — this isn't going to win on "
                "skill. Give me a Charisma (Persuasion) check.")
        out = turn_lint.check_roll_not_final(text, "players")
        self.assertEqual(len(out), 1)
        self.assertIn("lead-in", out[0]["detail"])

    def test_physical_attempt_lead_in_allowed_brace_door(self):
        text = ("You brace your shoulder against the door. "
                "Give me a Strength (Athletics) check.")
        self.assertEqual(turn_lint.check_roll_not_final(text, "players"), [])

    def test_physical_attempt_lead_in_allowed_slip_toward_rail(self):
        text = ("You slip toward the rail, keeping the crates between you "
                "and the lamplight. Give me a Dexterity (Stealth) check.")
        self.assertEqual(turn_lint.check_roll_not_final(text, "players"), [])

    def test_bare_request_no_lead_in_allowed(self):
        text = "Give me a Wisdom (Perception) check."
        self.assertEqual(turn_lint.check_roll_not_final(text, "players"), [])

    def test_earlier_beat_lead_in_out_of_lookback_window(self):
        text = (
            "This isn't going to win on skill, not against him.\n\n"
            + "The tavern settles into evening noise. " * 15
            + "\n\n"
            + "You brace your shoulder against the door. "
            "Give me a Strength (Athletics) check."
        )
        self.assertEqual(turn_lint.check_roll_not_final(text, "players"), [])

    # -- calibration: coordinator-supplied cases, added on review --------

    def test_scenery_description_not_flagged(self):
        text = ("The lock is old and the corridor is dark. "
                "Give me a Dexterity (Sleight of Hand) check.")
        self.assertEqual(turn_lint.check_roll_not_final(text, "players"), [])

    def test_flags_attributive_difficulty_hard_man_to_like(self):
        """Fires via difficulty predication, not target resistance.

        Named for the category that actually matches: predication is checked
        first and its attributive branch ("a hard <noun> to <verb>") claims
        this string, so _TARGET_RESISTANCE never sees it. The previous name
        claimed to guard target-resistance framing and would have passed with
        that regex deleted outright.
        """
        text = "Garrick is a hard man to like. Give me a Charisma (Persuasion) check."
        out = turn_lint.check_roll_not_final(text, "players")
        self.assertEqual(len(out), 1)
        self.assertIn("difficulty predication", out[0]["detail"])

    def test_flags_target_resistance_on_its_own_category(self):
        """A phrasing only _TARGET_RESISTANCE can claim — deleting it fails this."""
        text = ("The steward is on his guard tonight. "
                "Give me a Charisma (Deception) check.")
        out = turn_lint.check_roll_not_final(text, "players")
        self.assertEqual(len(out), 1)
        self.assertIn("target-resistance framing", out[0]["detail"])

    def test_typographic_apostrophe_still_matches(self):
        """U+2019 must not silently disable the contraction-based categories.

        Asserts the *category* (negated-ease claims this string first), so the
        test fails if the apostrophe fold silently breaks for that category
        while another one keeps the count at 1.
        """
        for apostrophe in ("'", "’"):
            with self.subTest(apostrophe=apostrophe):
                text = (f"This isn{apostrophe}t going to be easy. "
                        "Give me a Strength (Athletics) check.")
                out = turn_lint.check_roll_not_final(text, "players")
                self.assertEqual(len(out), 1)
                self.assertIn("negated-ease", out[0]["detail"])

    def test_physical_attempt_lead_in_allowed_stairs(self):
        text = ("You take the stairs two at a time. "
                "Give me a Dexterity (Acrobatics) check.")
        self.assertEqual(turn_lint.check_roll_not_final(text, "players"), [])

    # -- invented violations: novel phrasings, none drawn from the fixtures
    # above, to demonstrate the categories generalize rather than memorize.

    def test_flags_invented_lock_looks_tricky(self):
        text = "This lock looks tricky. Give me a Dexterity (Sleight of Hand) check."
        out = turn_lint.check_roll_not_final(text, "players")
        self.assertEqual(len(out), 1)
        self.assertIn("difficulty predication", out[0]["detail"])

    def test_flags_invented_odds_arent_great(self):
        text = "The odds aren't great here. Give me a Wisdom (Insight) check."
        out = turn_lint.check_roll_not_final(text, "players")
        self.assertEqual(len(out), 1)
        self.assertIn("difficulty predication", out[0]["detail"])

    def test_removed_lexicon_vocabulary_stays_clean(self):
        """Regression guard for the *removed* bare difficulty lexicon only.

        These six broke that version (hard|easy|simple|chance matched
        regardless of grammatical role) — 6 false positives out of 6. They pin
        the old lexicon's vocabulary; the general permitted-narration property
        is asserted by test_permitted_narration_probe_suite, which probes the
        surviving categories with fresh phrasings.
        """
        permitted = [
            "You push hard against the door, shoulder set. "
            "Give me a Strength (Athletics) check.",
            "You take a chance on the loose rail and swing out over the drop. "
            "Give me a Dexterity (Acrobatics) check.",
            "You keep it simple — hand over the coin, say nothing else. "
            "Give me a Charisma (Deception) check.",
            "The rain is coming down hard now. Give me a Wisdom (Perception) check.",
            "You go easy on the latch, barely breathing. "
            "Give me a Dexterity (Sleight of Hand) check.",
            "It has been a long day and a hard road. Give me a Constitution save.",
        ]
        for text in permitted:
            with self.subTest(text=text[:40]):
                out = [f for f in turn_lint.check_roll_not_final(text, "players")
                       if "lead-in" in f["detail"]]
                self.assertEqual(out, [], f"false positive on permitted narration: {text}")

    def test_flags_invented_sharp_not_easily_fooled(self):
        text = ("She's sharp, and not easily fooled by a pretty face. "
                "Give me a Charisma (Deception) check.")
        out = turn_lint.check_roll_not_final(text, "players")
        self.assertEqual(len(out), 1)
        self.assertIn("target-resistance framing", out[0]["detail"])

    def test_permitted_narration_probe_suite(self):
        """Fresh permitted narration against the SURVIVING categories.

        2026-07-20 Pass A probes, verified by executing each detector: the
        first six fired 6/6 on _TARGET_RESISTANCE's bare single-word arms
        (guarded/wary/careful/sharp/suspicious — the removed category-2 defect
        with different words); the rest fired on literal-physical perception
        senses, negated futures, and intensifier restatements.
        """
        permitted = [
            # bare target-resistance vocabulary in permitted roles
            "You pick your way along the ledge, careful of the loose stones. "
            "Give me a Dexterity (Acrobatics) check.",
            "You keep a wary eye on the door while you work. "
            "Give me a Dexterity (Sleight of Hand) check.",
            "A sharp crack comes from the rafters above you. "
            "Give me a Wisdom (Perception) check.",
            "The blade is sharp and freshly oiled. "
            "Give me an Intelligence (Investigation) check.",
            "Two men stand at the guarded gate ahead. "
            "Give me a Dexterity (Stealth) check.",
            "You slip the suspicious package under your coat. "
            "Give me a Dexterity (Sleight of Hand) check.",
            # literal physical senses of rough/steep (texture, terrain)
            "The rope feels rough against your palms. "
            "Give me a Strength (Athletics) check.",
            "The trail looks steep past the treeline. "
            "Give me a Constitution save.",
            # negated futures that pre-judge nothing
            "The storm isn't going to break before nightfall. "
            "Give me a Wisdom (Survival) check.",
            "He wasn't going to wait forever, and you both knew it. "
            "Give me a Charisma (Persuasion) check.",
            # intensifier restatement, not negated ease
            "The rain doesn't just fall here — it hammers. "
            "Give me a Wisdom (Perception) check.",
        ]
        for text in permitted:
            with self.subTest(text=text[:44]):
                out = [f for f in turn_lint.check_roll_not_final(text, "players")
                       if "lead-in" in f["detail"]]
                self.assertEqual(out, [], f"false positive on permitted narration: {text}")

    def test_flags_target_resistance_not_easily_fooled_construction(self):
        text = ("The moneylender is quick-witted and patient. "
                "Give me a Charisma (Deception) check.")
        out = turn_lint.check_roll_not_final(text, "players")
        self.assertEqual(len(out), 1)
        self.assertIn("target-resistance framing", out[0]["detail"])

    def test_flags_target_resistance_sharp_eyed(self):
        text = ("The quartermaster is a sharp-eyed old soldier. "
                "Give me a Dexterity (Sleight of Hand) check.")
        out = turn_lint.check_roll_not_final(text, "players")
        self.assertEqual(len(out), 1)
        self.assertIn("target-resistance framing", out[0]["detail"])

    def test_flags_outcome_prejudgment_work_class_verb(self):
        text = ("Flattery isn't going to work on her. "
                "Give me a Charisma (Persuasion) check.")
        out = turn_lint.check_roll_not_final(text, "players")
        self.assertEqual(len(out), 1)
        self.assertIn("outcome pre-judgment", out[0]["detail"])

    def test_flags_outcome_prejudgment_target_wont_listen(self):
        text = ("He wasn't going to listen to reason. "
                "Give me a Charisma (Persuasion) check.")
        out = turn_lint.check_roll_not_final(text, "players")
        self.assertEqual(len(out), 1)
        self.assertIn("outcome pre-judgment", out[0]["detail"])

    def test_flags_negated_ease_doesnt_just_open(self):
        text = ("That door doesn't just open for strangers. "
                "Give me a Strength (Athletics) check.")
        out = turn_lint.check_roll_not_final(text, "players")
        self.assertEqual(len(out), 1)
        self.assertIn("negated-ease", out[0]["detail"])

    def test_flags_invented_no_way_hes_just_handing_it_over(self):
        text = ("No way he's just handing it over. "
                "Give me a Charisma (Persuasion) check.")
        out = turn_lint.check_roll_not_final(text, "players")
        self.assertEqual(len(out), 1)
        self.assertIn("outcome pre-judgment", out[0]["detail"])

    # -- trigger coverage: a request the trigger misses silences BOTH halves
    # of roll_not_final, including the deterministic trailing check.

    def test_trigger_i_need_a_check_form(self):
        text = ("I need a Charisma (Persuasion) check from you. "
                + self.PADDING)
        out = turn_lint.check_roll_not_final(text, "players")
        self.assertEqual(len(out), 1)
        self.assertIn("followed by", out[0]["detail"])

    def test_trigger_lets_see_a_check_form(self):
        text = ("Let's see a Dexterity (Sleight of Hand) check. "
                + self.PADDING)
        out = turn_lint.check_roll_not_final(text, "players")
        self.assertEqual(len(out), 1)

    def test_trigger_bare_ability_skill_check_form(self):
        text = ("Charisma (Persuasion) check, whenever you're ready. "
                + self.PADDING)
        out = turn_lint.check_roll_not_final(text, "players")
        self.assertEqual(len(out), 1)

    def test_trigger_house_forms_hedged_lead_in_caught(self):
        text = ("The steward is on his guard tonight. "
                "I need a Charisma (Deception) check.")
        out = turn_lint.check_roll_not_final(text, "players")
        self.assertEqual(len(out), 1)
        self.assertIn("lead-in", out[0]["detail"])

    def test_trigger_not_fooled_by_close_check_narration(self):
        """'check' in plain narration is not a roll request."""
        for text in ("That was a close check. " + self.PADDING,
                     "I need you to check on the horses before dawn. "
                     + self.PADDING,
                     "The last check nearly cost you the lantern. "
                     + self.PADDING):
            with self.subTest(text=text[:40]):
                self.assertEqual(
                    turn_lint.check_roll_not_final(text, "players"), [])


class PcAutoRollTests(unittest.TestCase):
    def test_flags_transcript_style_resolved_check(self):
        # Verbatim shape of the session-1 violation.
        line = "**Roll:** Wisdom (Animal Handling), d20+0 → **19**"
        out = turn_lint.check_pc_auto_roll(line, "players")
        self.assertEqual(len(out), 1)
        self.assertIn("skill check", out[0]["detail"])

    def test_flags_resolved_save(self):
        line = "**Roll:** Dexterity save, d20+2 -> 11"
        self.assertEqual(len(turn_lint.check_pc_auto_roll(line, "players")), 1)

    def test_npc_attack_format_passes(self):
        line = "Goblin attacks: d20+4 = 17 vs AC 16 — hit! 1d6+2 = 5 piercing damage"
        self.assertEqual(turn_lint.check_pc_auto_roll(line, "players"), [])

    def test_auto_mode_skipped(self):
        line = "**Roll:** Wisdom (Perception), d20+0 → **12**"
        self.assertEqual(turn_lint.check_pc_auto_roll(line, "auto"), [])

    # -- house format: SKILL.md's canonical inline roll line, attributed by
    # PC name from campaign data instead of format-guessing.

    def test_flags_house_format_pc_roll(self):
        line = "Piper — Perception: d20+5 = 18"
        out = turn_lint.check_pc_auto_roll(line, "players", pc_names={"piper"})
        self.assertEqual(len(out), 1)
        self.assertIn("Piper", out[0]["detail"])

    def test_flags_house_format_bold_name_arrow(self):
        line = "**Piper** — Stealth: d20+3 → 14"
        self.assertEqual(
            len(turn_lint.check_pc_auto_roll(line, "players",
                                             pc_names={"piper"})), 1)

    def test_house_format_npc_line_passes(self):
        line = "Goblin — Perception: d20+2 = 11"
        self.assertEqual(
            turn_lint.check_pc_auto_roll(line, "players", pc_names={"piper"}), [])

    def test_house_format_multiword_pc_name(self):
        line = "Piper Vale — Insight: d20+1 -> 14"
        self.assertEqual(
            len(turn_lint.check_pc_auto_roll(line, "players",
                                             pc_names={"piper vale"})), 1)

    def test_pc_name_in_prose_without_roll_passes(self):
        text = "Piper — quick as ever — ducks behind the cart."
        self.assertEqual(
            turn_lint.check_pc_auto_roll(text, "players", pc_names={"piper"}), [])

    def test_pc_name_mid_line_of_npc_roll_passes(self):
        """Attribution requires the name at line start, not anywhere in it."""
        line = "The guard swings at Piper: d20+4 = 17 vs AC 15"
        self.assertEqual(
            turn_lint.check_pc_auto_roll(line, "players", pc_names={"piper"}), [])

    def test_no_pc_names_keeps_legacy_behavior(self):
        line = "Piper — Perception: d20+5 = 18"
        self.assertEqual(turn_lint.check_pc_auto_roll(line, "players"), [])


class CampaignPcNamesTests(unittest.TestCase):
    def _campaign(self, files):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        camp = pathlib.Path(tmp.name)
        chars = camp / "characters"
        chars.mkdir()
        for fname, header in files.items():
            (chars / fname).write_text(header, encoding="utf-8")
        return camp

    def test_names_from_filenames_and_headers(self):
        camp = self._campaign({
            "Piper.md": "# Piper — Level 3 Rogue\n",
            "Holg_Ironjaw.md": "# Holg Ironjaw (Barbarian 2)\n",
        })
        names = turn_lint.campaign_pc_names(camp)
        self.assertIn("piper", names)
        self.assertIn("holg ironjaw", names)

    def test_missing_characters_dir_is_empty(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.assertEqual(turn_lint.campaign_pc_names(pathlib.Path(tmp.name)),
                         set())


class UnknownCueTests(unittest.TestCase):
    AMBIENT = {"underwatch-town", "crypt-drips"}
    MAPS = {"cavern-large"}

    def test_known_sound_cue_passes(self):
        text = "🔊 **Cue:** *underwatch-town*"
        self.assertEqual(turn_lint.check_unknown_cue(text, self.AMBIENT, self.MAPS), [])

    def test_unknown_sound_cue_flagged(self):
        text = "🔊 **Cue:** *battle-drums*"
        out = turn_lint.check_unknown_cue(text, self.AMBIENT, self.MAPS)
        self.assertEqual(len(out), 1)
        self.assertIn("battle-drums", out[0]["detail"])

    def test_map_down_cue_always_allowed(self):
        text = "🗺 **Map:** *down — theater of the mind*"
        self.assertEqual(turn_lint.check_unknown_cue(text, self.AMBIENT, self.MAPS), [])

    def test_unknown_map_cue_flagged(self):
        text = "🗺 **Map:** *volcano-lair*"
        self.assertEqual(
            len(turn_lint.check_unknown_cue(text, self.AMBIENT, self.MAPS)), 1)

    def test_down_prefixed_unknown_map_cue_flagged(self):
        """Whitelist bug: `startswith("down")` exempted any handle starting
        with those four letters, not just the genuine down-cue. A map named
        `downfall-ruins` (not on map-list) must still be flagged."""
        text = "🗺 **Map:** *downfall-ruins*"
        self.assertEqual(
            len(turn_lint.check_unknown_cue(text, self.AMBIENT, self.MAPS)), 1)

    def test_down_prefixed_unknown_map_cue_flagged_second_handle(self):
        text = "🗺 **Map:** *downtown-docks*"
        self.assertEqual(
            len(turn_lint.check_unknown_cue(text, self.AMBIENT, self.MAPS)), 1)

    def test_map_down_cue_ascii_hyphen_allowed(self):
        text = "🗺 **Map:** *down - theater of the mind*"
        self.assertEqual(turn_lint.check_unknown_cue(text, self.AMBIENT, self.MAPS), [])

    def test_map_down_cue_trailing_free_text_allowed(self):
        text = "🗺 **Map:** *down — theater of the mind, back to the tavern*"
        self.assertEqual(turn_lint.check_unknown_cue(text, self.AMBIENT, self.MAPS), [])


def _make_campaign(test, files):
    """Write `files` (relative path -> content) into a fresh temp campaign
    dir and register cleanup on `test`. Mirrors CampaignPcNamesTests._campaign."""
    tmp = tempfile.TemporaryDirectory()
    test.addCleanup(tmp.cleanup)
    camp = pathlib.Path(tmp.name)
    for rel, content in files.items():
        p = camp / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    return camp


WORLD_MD_FIXTURE = """# World: Thornwake

## World Foundations

### Geography
- **Notable features:** the River Aldwyn (forded at Reachwater); the Greyhorn Downs, barrow-mounds said to hold a sleeping king

The Grey King sleeps beneath the Greyhorn Downs. Reachwater sits at the ford,
and the Grey King's oath binds the whole valley to him.
"""

NPCS_MD_FIXTURE = """# NPCs — Thornwake

| Name | Role | Faction | Location | Attitude | Notes |
|------|------|---------|----------|----------|-------|
| Bram Vane | Reeve | Reachwater Council | Reeve's Hall | neutral | over-explains |
| Wick | message-runner | independent | Ford Market | neutral | knows every rumor |

### Bram Vane
- **Role:** Reeve of Reachwater | **Location:** Reeve's Hall

### Personality
- **Trustworthy ↔ Deceptive:** trustworthy

### Relationships
- **Knows:** Wick — trusts him

### Notes
"""


class NameInventoryTests(unittest.TestCase):
    """build_name_inventory: campaign-grounded capitalized-term extraction
    from world.md / npcs.md. No AI judgment — pure frequency + structural
    rules (anti-pattern 10)."""

    def test_missing_files_yields_empty_inventory(self):
        camp = _make_campaign(self, {"state.md": "# state\n"})
        self.assertEqual(turn_lint.build_name_inventory(camp), {})

    def test_multi_word_phrase_included_from_single_mention(self):
        camp = _make_campaign(
            self, {"world.md": WORLD_MD_FIXTURE, "npcs.md": NPCS_MD_FIXTURE})
        inv = turn_lint.build_name_inventory(camp)
        self.assertIn("greyhorn downs", inv)
        self.assertIn("river aldwyn", inv)
        self.assertIn("grey king", inv)

    def test_single_word_needs_two_occurrences(self):
        camp = _make_campaign(
            self, {"world.md": WORLD_MD_FIXTURE, "npcs.md": NPCS_MD_FIXTURE})
        inv = turn_lint.build_name_inventory(camp)
        self.assertIn("reachwater", inv)  # recurs several times

    def test_npc_table_name_included_even_if_single_mention(self):
        camp = _make_campaign(
            self, {"world.md": WORLD_MD_FIXTURE, "npcs.md": NPCS_MD_FIXTURE})
        inv = turn_lint.build_name_inventory(camp)
        self.assertIn("wick", inv)

    def test_structural_labels_excluded(self):
        camp = _make_campaign(
            self, {"world.md": WORLD_MD_FIXTURE, "npcs.md": NPCS_MD_FIXTURE})
        inv = turn_lint.build_name_inventory(camp)
        for noise in ("location", "role", "notes", "personality",
                      "relationships", "notable features",
                      "world foundations"):
            self.assertNotIn(noise, inv)

    def test_common_stopwords_excluded(self):
        camp = _make_campaign(
            self, {"world.md": WORLD_MD_FIXTURE, "npcs.md": NPCS_MD_FIXTURE})
        inv = turn_lint.build_name_inventory(camp)
        self.assertNotIn("the", inv)


class FirstUseGlossPermittedTests(unittest.TestCase):
    """Permitted side, written first (anti-pattern 4): correctly glossed
    first uses in several syntactic shapes, bare second uses, and campaigns
    with no inventory — all must produce zero findings."""

    INV = {"warden": "Warden", "aldwyn": "Aldwyn", "grey king": "Grey King",
           "greyhorn downs": "Greyhorn Downs", "reachwater": "Reachwater",
           "marren": "Marren"}

    def test_gloss_after_name_appositive_comma(self):
        text = "The Warden, a grey-cloaked officer, waves you through."
        out, seen = turn_lint.check_first_use_gloss(text, self.INV)
        self.assertEqual(out, [])
        self.assertIn("warden", seen)

    def test_gloss_before_name_dash_appositive(self):
        # Anti-pattern 1: the gloss may legitimately precede the name.
        text = "A grey-cloaked officer — the Warden — waves you through."
        out, seen = turn_lint.check_first_use_gloss(text, self.INV)
        self.assertEqual(out, [])

    def test_gloss_via_sign_reading(self):
        text = "A sign reading The Aldwyn hangs over what looks like a tavern."
        out, seen = turn_lint.check_first_use_gloss(text, self.INV)
        self.assertEqual(out, [])

    def test_gloss_via_called_construction(self):
        text = "The village called Reachwater sprawls along the ford."
        out, seen = turn_lint.check_first_use_gloss(text, self.INV)
        self.assertEqual(out, [])

    def test_gloss_via_known_as(self):
        text = "The old ruin known as Greyhorn Downs looms to the east."
        out, seen = turn_lint.check_first_use_gloss(text, self.INV)
        self.assertEqual(out, [])

    def test_second_use_bare_is_permitted(self):
        text = "The Warden nods and steps aside without a word."
        out, seen = turn_lint.check_first_use_gloss(text, self.INV, {"warden"})
        self.assertEqual(out, [])

    def test_sentence_initial_common_word_not_in_inventory(self):
        text = "The rain falls hard on the tin roof all through the night."
        out, seen = turn_lint.check_first_use_gloss(text, self.INV)
        self.assertEqual(out, [])
        self.assertEqual(seen, set())

    def test_no_inventory_files_means_inert(self):
        out, seen = turn_lint.check_first_use_gloss("The Warden appears.", {})
        self.assertEqual(out, [])
        self.assertEqual(seen, set())


class FirstUseGlossViolationTests(unittest.TestCase):
    """Violation side: bare first use, mixed glossed/unglossed, and the real
    observed failure shape — several inventory names in an opener, none
    glossed."""

    INV = FirstUseGlossPermittedTests.INV

    def test_bare_first_use_in_narration(self):
        text = "The Warden waves you through without a word."
        out, seen = turn_lint.check_first_use_gloss(text, self.INV)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["detector"], "first_use_gloss")
        self.assertIn("Warden", out[0]["detail"])

    def test_multiple_first_uses_one_glossed_one_not(self):
        text = ("The Warden, a grey-cloaked officer, waves you in. "
                "Marren watches from the doorway and says nothing.")
        out, seen = turn_lint.check_first_use_gloss(text, self.INV)
        self.assertEqual(len(out), 1)
        self.assertIn("Marren", out[0]["detail"])

    def test_observed_failure_shape_several_names_none_glossed(self):
        text = ("The Grey King stirs beneath the Greyhorn Downs as "
                "Reachwater sleeps on, unaware of what is coming.")
        out, seen = turn_lint.check_first_use_gloss(text, self.INV)
        self.assertEqual(len(out), 3)
        details = {v["detail"] for v in out}
        self.assertEqual(len(details), 3)


class FirstUseGlossExclusionTests(unittest.TestCase):
    """Scope clauses that must hold: NPC dialogue, PC names, already-seen
    ledger entries, and the canonical cue-block lines."""

    INV = FirstUseGlossPermittedTests.INV

    def test_npc_dialogue_exempt_from_gloss_but_registers_seen(self):
        text = '> **Wick:** "The Warden is already at the gate."'
        out, seen = turn_lint.check_first_use_gloss(text, self.INV)
        self.assertEqual(out, [])
        self.assertIn("warden", seen)

    def test_pc_name_exempt(self):
        text = "The Warden waves you through without a word."
        out, seen = turn_lint.check_first_use_gloss(
            text, self.INV, pc_names={"warden"})
        self.assertEqual(out, [])
        self.assertNotIn("warden", seen)

    def test_already_seen_name_never_refires(self):
        text = "The Warden scowls and turns away without another word today."
        out, seen = turn_lint.check_first_use_gloss(
            text, self.INV, seen_names={"warden"})
        self.assertEqual(out, [])

    def test_map_cue_line_not_scanned(self):
        text = "🗺 **Map:** *Greyhorn Downs*"
        out, seen = turn_lint.check_first_use_gloss(text, self.INV)
        self.assertEqual(out, [])
        self.assertEqual(seen, set())

    def test_sound_cue_line_not_scanned(self):
        text = "🔊 **Cue:** *Reachwater*"
        out, seen = turn_lint.check_first_use_gloss(text, self.INV)
        self.assertEqual(out, [])
        self.assertEqual(seen, set())


class SeenNamesLedgerTests(unittest.TestCase):
    def test_round_trip(self):
        camp = _make_campaign(self, {"state.md": "# s\n"})
        turn_lint.save_seen_names(camp, {"warden", "reachwater"}, True)
        self.assertEqual(turn_lint.load_seen_names(camp),
                         {"warden", "reachwater"})

    def test_missing_ledger_is_empty(self):
        camp = _make_campaign(self, {"state.md": "# s\n"})
        self.assertEqual(turn_lint.load_seen_names(camp), set())

    def test_records_has_inventory_flag(self):
        camp = _make_campaign(self, {"state.md": "# s\n"})
        turn_lint.save_seen_names(camp, set(), False)
        data = json.loads((camp / turn_lint.SEEN_NAMES_LOG).read_text())
        self.assertFalse(data["has_inventory"])


class RunAndLogFirstUseGlossTests(unittest.TestCase):
    """Wiring through run_and_log: ledger persistence, cross-turn
    non-refiring, and inertness-without-inventory surfaced in the ledger."""

    def _run(self, root, campaign, files, turn_text):
        camp = pathlib.Path(root) / "campaigns" / campaign
        camp.mkdir(parents=True, exist_ok=True)
        for rel, content in files.items():
            (camp / rel).write_text(content, encoding="utf-8")
        transcript = camp / "session.jsonl"
        transcript.write_text(_jsonl(_user("hi"), _assistant_text(turn_text)),
                             encoding="utf-8")
        return turn_lint.run_and_log(
            {"transcript_path": str(transcript), "session_id": "s1"}, campaign)

    def _with_root(self, fn):
        with tempfile.TemporaryDirectory() as root:
            old = os.environ.get("DND_CAMPAIGN_ROOT")
            os.environ["DND_CAMPAIGN_ROOT"] = root
            try:
                fn(root)
            finally:
                if old is None:
                    del os.environ["DND_CAMPAIGN_ROOT"]
                else:
                    os.environ["DND_CAMPAIGN_ROOT"] = old

    def test_unglossed_first_use_logged(self):
        def body(root):
            n = self._run(root, "gloss-camp", {
                "state.md": "# s\n\n## Session Flags\nroll_mode: players\n",
                "world.md": WORLD_MD_FIXTURE,
                "npcs.md": NPCS_MD_FIXTURE,
            }, "The Grey King stirs. You should leave before he wakes.")
            self.assertEqual(n, 1)
            camp = pathlib.Path(root) / "campaigns" / "gloss-camp"
            log = [json.loads(l) for l in
                   (camp / turn_lint.LOG_NAME).read_text().splitlines()]
            self.assertEqual(log[0]["detector"], "first_use_gloss")
            ledger = json.loads((camp / turn_lint.SEEN_NAMES_LOG).read_text())
            self.assertIn("grey king", ledger["seen"])
            self.assertTrue(ledger["has_inventory"])
        self._with_root(body)

    def test_second_turn_does_not_refire_for_same_name(self):
        def body(root):
            self._run(root, "gloss-camp2", {
                "state.md": "# s\n\n## Session Flags\nroll_mode: players\n",
                "world.md": WORLD_MD_FIXTURE,
                "npcs.md": NPCS_MD_FIXTURE,
            }, "The Grey King stirs.")
            n2 = self._run(root, "gloss-camp2", {},
                           "The Grey King stirs again, restless.")
            self.assertEqual(n2, 0)
        self._with_root(body)

    def test_inert_without_inventory_recorded_in_ledger(self):
        def body(root):
            n = self._run(root, "no-inv-camp", {
                "state.md": "# s\n\n## Session Flags\nroll_mode: players\n",
            }, "The Warden waves you through without a word.")
            self.assertEqual(n, 0)
            camp = pathlib.Path(root) / "campaigns" / "no-inv-camp"
            ledger = json.loads((camp / turn_lint.SEEN_NAMES_LOG).read_text())
            self.assertFalse(ledger["has_inventory"])
            self.assertEqual(ledger["seen"], [])
        self._with_root(body)


def _jsonl(*objs) -> str:
    return "\n".join(json.dumps(o) for o in objs) + "\n"


def _user(text):
    return {"type": "user", "message": {"role": "user", "content": text}}


def _assistant_text(text):
    return {"type": "assistant",
            "message": {"role": "assistant",
                        "content": [{"type": "text", "text": text}]}}


def _tool_use(command):
    return {"type": "assistant",
            "message": {"role": "assistant",
                        "content": [{"type": "tool_use", "name": "Bash",
                                     "input": {"command": command}}]}}


def _tool_result():
    return {"type": "user",
            "message": {"role": "user",
                        "content": [{"type": "tool_result", "content": "ok"}]}}


class LastTurnTests(unittest.TestCase):
    def test_collects_text_since_last_genuine_user_message(self):
        transcript = _jsonl(
            _user("hello"),
            _assistant_text("OLD TURN — must not appear"),
            _user("i want to catch the horse"),
            _assistant_text("He moves in low and steady."),
            _tool_use("python3 dice.py d20+0"),
            _tool_result(),
            _assistant_text("**Roll:** d20+0 → 19. The mare settles."),
        )
        with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False,
                                         encoding="utf-8") as f:
            f.write(transcript)
            path = f.name
        try:
            text = turn_lint.last_turn(path)
        finally:
            os.unlink(path)
        self.assertIn("moves in low", text)
        self.assertIn("The mare settles", text)
        self.assertNotIn("OLD TURN", text)

    def test_missing_file_returns_empty(self):
        self.assertEqual(turn_lint.last_turn("/nonexistent/t.jsonl"), "")


class RunAndLogTests(unittest.TestCase):
    def test_writes_findings_to_campaign_log(self):
        with tempfile.TemporaryDirectory() as root:
            camp = pathlib.Path(root) / "campaigns" / "lint-test-camp"
            camp.mkdir(parents=True)
            (camp / "state.md").write_text(
                "# state\n\n## Session Flags\nroll_mode: players\n",
                encoding="utf-8")
            transcript = camp / "session.jsonl"
            transcript.write_text(_jsonl(
                _user("hi"),
                _assistant_text("Make a DC 15 check. Holg — what do you do?"),
            ), encoding="utf-8")
            old = os.environ.get("DND_CAMPAIGN_ROOT")
            os.environ["DND_CAMPAIGN_ROOT"] = root
            try:
                n = turn_lint.run_and_log(
                    {"transcript_path": str(transcript), "session_id": "s1"},
                    "lint-test-camp")
            finally:
                if old is None:
                    del os.environ["DND_CAMPAIGN_ROOT"]
                else:
                    os.environ["DND_CAMPAIGN_ROOT"] = old
            # rote_closer is disabled at the registry level (see lint_turn) —
            # the "what do you do?" tail in this fixture no longer counts.
            self.assertEqual(n, 1)  # dc_leak only
            log = (camp / turn_lint.LOG_NAME).read_text(encoding="utf-8")
            entries = [json.loads(line) for line in log.splitlines()]
            detectors = {e["detector"] for e in entries}
            self.assertEqual(detectors, {"dc_leak"})

    def test_body_crash_writes_lint_error_record(self):
        """A mid-body crash must be distinguishable from a clean turn in the
        file the reviewer already reads — while still returning 0 (the
        never-break-a-turn constraint)."""
        with tempfile.TemporaryDirectory() as root:
            camp = pathlib.Path(root) / "campaigns" / "lint-test-camp"
            camp.mkdir(parents=True)
            (camp / "state.md").write_text(
                "# state\n\n## Session Flags\nroll_mode: players\n",
                encoding="utf-8")
            transcript = camp / "session.jsonl"
            transcript.write_text(_jsonl(
                _user("hi"), _assistant_text("A quiet street.")),
                encoding="utf-8")
            old_root = os.environ.get("DND_CAMPAIGN_ROOT")
            os.environ["DND_CAMPAIGN_ROOT"] = root
            orig_last_turn = turn_lint.last_turn
            turn_lint.last_turn = lambda p: (_ for _ in ()).throw(
                RuntimeError("probe crash"))
            try:
                n = turn_lint.run_and_log(
                    {"transcript_path": str(transcript), "session_id": "s1"},
                    "lint-test-camp")
            finally:
                turn_lint.last_turn = orig_last_turn
                if old_root is None:
                    del os.environ["DND_CAMPAIGN_ROOT"]
                else:
                    os.environ["DND_CAMPAIGN_ROOT"] = old_root
            self.assertEqual(n, 0)
            log = (camp / turn_lint.LOG_NAME).read_text(encoding="utf-8")
            entries = [json.loads(line) for line in log.splitlines()]
            self.assertEqual(len(entries), 1)
            self.assertEqual(entries[0]["detector"], "lint_error")
            self.assertIn("RuntimeError", entries[0]["detail"])

    def test_turn_lint_off_flag_disables(self):
        with tempfile.TemporaryDirectory() as root:
            camp = pathlib.Path(root) / "campaigns" / "lint-test-camp"
            camp.mkdir(parents=True)
            (camp / "state.md").write_text(
                "# state\n\n## Session Flags\nroll_mode: players\nturn_lint: off\n",
                encoding="utf-8")
            transcript = camp / "session.jsonl"
            transcript.write_text(_jsonl(
                _user("hi"), _assistant_text("Make a DC 15 check.")),
                encoding="utf-8")
            old = os.environ.get("DND_CAMPAIGN_ROOT")
            os.environ["DND_CAMPAIGN_ROOT"] = root
            try:
                n = turn_lint.run_and_log(
                    {"transcript_path": str(transcript)}, "lint-test-camp")
            finally:
                if old is None:
                    del os.environ["DND_CAMPAIGN_ROOT"]
                else:
                    os.environ["DND_CAMPAIGN_ROOT"] = old
            self.assertEqual(n, 0)
            self.assertFalse((camp / turn_lint.LOG_NAME).exists())


class AllTurnsTests(unittest.TestCase):
    """Backfill support — lint a whole session, not just its final turn.

    Needed because the Stop hook can be broken or absent while play happens
    (the `python3` interpreter regression, 2026-07-20): the transcript is the
    only surviving record of those turns.
    """

    def _write(self, *objs):
        f = tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False,
                                        encoding="utf-8")
        f.write(_jsonl(*objs))
        f.close()
        self.addCleanup(os.unlink, f.name)
        return f.name

    def test_splits_on_genuine_user_messages(self):
        path = self._write(
            _user("i climb out"), _assistant_text("The shutter gives."),
            _user("i run"), _assistant_text("The alley opens."),
            _user("i stop"), _assistant_text("Rain, and nothing else."),
        )
        self.assertEqual(len(turn_lint.all_turns(path)), 3)

    def test_tool_results_do_not_split_turns(self):
        path = self._write(
            _user("i roll"),
            _assistant_text("Rolling."),
            _tool_use("python3 dice.py d20+3"),
            _tool_result(),
            _assistant_text("19 — the mare settles."),
        )
        turns = turn_lint.all_turns(path)
        self.assertEqual(len(turns), 1)
        self.assertIn("Rolling.", turns[0])
        self.assertIn("the mare settles", turns[0])

    def test_last_turn_matches_final_all_turns_entry(self):
        path = self._write(
            _user("a"), _assistant_text("first"),
            _user("b"), _assistant_text("second"),
        )
        self.assertEqual(turn_lint.all_turns(path)[-1], turn_lint.last_turn(path))

    def test_missing_transcript_returns_empty(self):
        self.assertEqual(turn_lint.all_turns("/no/such/transcript.jsonl"), [])


def _filler(n: int, start: int = 1) -> str:
    """`n` distinct lowercase filler tokens, space-joined — an exact,
    countable narration padding that cannot accidentally match any other
    detector's vocabulary (a Title-Case run, a DC number, roll phrasing,
    closer phrasing). Used to hit precise word-count targets by
    construction rather than by hand-counting prose."""
    return " ".join(f"w{i}" for i in range(start, start + n))


class NarrationWordCountTests(unittest.TestCase):
    """_narration_word_count: the arithmetic narration_band's cap logic is
    measured against. Written first — the cap logic (below) trusts this
    count, so its exclusions must be right before the bands are worth
    testing at all."""

    def test_counts_plain_narration_words(self):
        text = "The gate creaks open and the wind sweeps through the courtyard."
        self.assertEqual(turn_lint._narration_word_count(text), 11)

    def test_excludes_dialogue_blockquote_lines(self):
        text = ('The reeve steps forward.\n'
                '> **Bram Vane:** "Stay behind me, and keep quiet."\n'
                'He waits for you to nod.')
        self.assertEqual(turn_lint._narration_word_count(text), 10)

    def test_excludes_tutor_line(self):
        text = ('The corridor narrows ahead.\n'
                '> ◈ Tutor: There are at least two ways in.\n'
                'You press on regardless.')
        self.assertEqual(turn_lint._narration_word_count(text), 8)

    def test_excludes_sound_cue_line(self):
        text = ('Footsteps echo down the hall.\n'
                '\U0001f50a **Cue:** *tension-drone*\n'
                'The door swings wide.')
        self.assertEqual(turn_lint._narration_word_count(text), 9)

    def test_excludes_map_cue_line(self):
        text = ('The battle lines form.\n'
                '\U0001f5fa **Map:** *courtyard-skirmish*\n'
                'Steel rings out.')
        self.assertEqual(turn_lint._narration_word_count(text), 7)

    def test_excludes_resolved_bold_roll_line(self):
        text = ('You reach for the latch.\n'
                '**Roll:** d20+3 → 17.\n'
                'It gives way with a click.')
        self.assertEqual(turn_lint._narration_word_count(text), 11)

    def test_excludes_house_format_resolved_roll_line(self):
        text = ('Holg steadies his grip.\n'
                'Holg — Perception: d20+5 = 18\n'
                'He spots the tripwire.')
        self.assertEqual(turn_lint._narration_word_count(text), 8)

    def test_mixed_turn_dialogue_heavy_narration_slice_small(self):
        text = ('A door bangs.\n'
                '> **Wick:** "Wait — don\'t go in there, not yet, please, '
                'I beg you, listen to reason for once in your life."\n'
                'You pause.')
        self.assertEqual(turn_lint._narration_word_count(text), 5)


class CheckNarrationBandPermittedTests(unittest.TestCase):
    """Permitted side, written first (anti-pattern 4): openers within their
    band's cap, a non-opening turn regardless of length or name count
    (Breathe is unbounded and non-openers are never checked), an unknown
    name count taking the most permissive cap, and the tolerance boundary
    itself. All must produce zero findings."""

    def test_hot_opener_within_cap(self):
        self.assertEqual(
            turn_lint.check_narration_band(50, True, 0), [])
        self.assertEqual(
            turn_lint.check_narration_band(50, True, 1), [])

    def test_normal_opener_within_cap(self):
        self.assertEqual(
            turn_lint.check_narration_band(95, True, 2), [])

    def test_normal_opener_three_names_within_cap(self):
        self.assertEqual(
            turn_lint.check_narration_band(100, True, 3), [])

    def test_non_opening_turn_never_flagged_regardless_of_length(self):
        # Breathe is unbounded ("longer is fine") and this isn't even the
        # anchor turn — must pass clean no matter how long or name-dense.
        self.assertEqual(
            turn_lint.check_narration_band(400, False, 6), [])

    def test_unknown_name_count_uses_permissive_cap(self):
        self.assertEqual(
            turn_lint.check_narration_band(95, True, None), [])

    def test_tolerance_boundary_not_flagged(self):
        # Hot cap 60, 5% tolerance -> 63. Exactly at the threshold passes;
        # only strictly exceeding it fires (see CheckNarrationBandViolationTests).
        self.assertEqual(
            turn_lint.check_narration_band(63, True, 1), [])


class CheckNarrationBandViolationTests(unittest.TestCase):
    """Violation side: the real observed failure shape (a 109-word opener
    with 3 inventory names), a plain Hot-band overage, and the independent
    ">3 names" finding that fires regardless of word count."""

    def test_observed_failure_shape_109_words_three_names(self):
        out = turn_lint.check_narration_band(109, True, 3)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["detector"], "narration_band")
        self.assertIn("109", out[0]["detail"])
        self.assertIn("100", out[0]["detail"])

    def test_hot_opener_over_cap(self):
        out = turn_lint.check_narration_band(75, True, 0)
        self.assertEqual(len(out), 1)
        self.assertIn("60", out[0]["detail"])

    def test_hot_opener_single_name_over_cap(self):
        out = turn_lint.check_narration_band(70, True, 1)
        self.assertEqual(len(out), 1)

    def test_more_than_three_names_own_finding(self):
        out = turn_lint.check_narration_band(50, True, 5)
        self.assertEqual(len(out), 1)
        self.assertIn("three is the cap", out[0]["detail"])

    def test_more_than_three_names_independent_of_word_count(self):
        # A word overage would ALSO be true here (200 words) — must still
        # be exactly one finding, not one per condition.
        out = turn_lint.check_narration_band(200, True, 4)
        self.assertEqual(len(out), 1)
        self.assertIn("three is the cap", out[0]["detail"])


class IsFirstTurnTests(unittest.TestCase):
    """is_first_turn: the session-opening anchor. Chosen over reading
    `.lint-health.jsonl` (owned by autosave_checkpoint.py) because the
    transcript is the actual session record and is already what
    run_and_log/main are handed — see is_first_turn's docstring."""

    def _write(self, *objs):
        f = tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False,
                                        encoding="utf-8")
        f.write(_jsonl(*objs))
        f.close()
        self.addCleanup(os.unlink, f.name)
        return f.name

    def test_single_boundary_is_opening(self):
        path = self._write(_user("hi"), _assistant_text("The gate creaks open."))
        self.assertTrue(turn_lint.is_first_turn(path))

    def test_second_boundary_is_not_opening(self):
        path = self._write(
            _user("hi"), _assistant_text("The gate creaks open."),
            _user("i step through"), _assistant_text("Dust motes drift in the light."),
        )
        self.assertFalse(turn_lint.is_first_turn(path))

    def test_tool_result_feedback_not_a_boundary(self):
        path = self._write(
            _user("hi"), _assistant_text("You reach for the latch."),
            _tool_use("python3 dice.py d20+0"), _tool_result(),
            _assistant_text("It gives way with a click."),
        )
        self.assertTrue(turn_lint.is_first_turn(path))

    def test_missing_transcript_is_not_opening(self):
        self.assertFalse(turn_lint.is_first_turn("/nonexistent/t.jsonl"))


class NarrationBandFreshCasesTests(unittest.TestCase):
    """Fresh cases invented after implementation, exercising the real
    lint_turn pipeline (text + inventory, not hand-picked ints) rather than
    mirroring the fixtures above (anti-pattern 3). Permitted side must be
    zero false positives; violation side reports the catch count."""

    def _band(self, text, inventory=None, is_opening=True,
             seen_names=frozenset()):
        findings = turn_lint.lint_turn(
            text, FLAGS_AUTO, set(), set(), frozenset(),
            name_inventory=inventory, seen_names=seen_names,
            is_opening_turn=is_opening)
        return [f for f in findings if f["detector"] == "narration_band"]

    # ── permitted (must be zero false positives) ──────────────────────
    def test_fresh_permitted_non_opening_huge_dialogue_many_names(self):
        inv = {"alder": "Alder", "bryn": "Bryn", "casimir": "Casimir",
               "dellwyn": "Dellwyn"}
        text = ("Alder w1 Bryn w2 Casimir w3 Dellwyn w4 "
                + _filler(300, start=5))
        self.assertEqual(self._band(text, inv, is_opening=False), [])

    def test_fresh_permitted_opener_zero_names_at_cap_boundary(self):
        inv = {"alder": "Alder"}  # present in inventory, never mentioned
        text = _filler(60)
        self.assertEqual(self._band(text, inv, is_opening=True), [])

    def test_fresh_permitted_opener_two_names_at_normal_cap_boundary(self):
        inv = {"alder": "Alder", "bryn": "Bryn"}
        text = "Alder w1 Bryn " + _filler(97, start=2)  # 100 words total
        self.assertEqual(self._band(text, inv, is_opening=True), [])

    def test_fresh_permitted_no_inventory_under_permissive_cap(self):
        text = _filler(95)
        self.assertEqual(self._band(text, None, is_opening=True), [])

    def test_fresh_permitted_dialogue_cue_tutor_heavy_narration_slice_small(self):
        inv = {"alder": "Alder"}
        text = ("Alder " + _filler(39) + "\n"
                '> **Wick:** "' + _filler(50, start=100) + '"\n'
                "\U0001f50a **Cue:** *tension-drone*\n"
                '> ◈ Tutor: ' + _filler(30, start=200))
        self.assertEqual(self._band(text, inv, is_opening=True), [])

    # ── violations (catch rate reported in the task summary) ──────────
    def test_fresh_violation_hot_opener_one_name_72_words(self):
        inv = {"alder": "Alder"}
        text = "Alder " + _filler(71)  # 72 words
        out = self._band(text, inv, is_opening=True)
        self.assertEqual(len(out), 1)

    def test_fresh_violation_normal_opener_two_names_108_words(self):
        inv = {"alder": "Alder", "bryn": "Bryn"}
        text = "Alder w1 Bryn " + _filler(105, start=2)  # 108 words
        out = self._band(text, inv, is_opening=True)
        self.assertEqual(len(out), 1)

    def test_fresh_violation_normal_opener_three_names_130_words(self):
        inv = {"alder": "Alder", "bryn": "Bryn", "casimir": "Casimir"}
        text = "Alder w1 Bryn w2 Casimir " + _filler(125, start=3)  # 130 words
        out = self._band(text, inv, is_opening=True)
        self.assertEqual(len(out), 1)

    def test_fresh_violation_five_names_short_narration(self):
        inv = {"alder": "Alder", "bryn": "Bryn", "casimir": "Casimir",
               "dellwyn": "Dellwyn", "esdrel": "Esdrel"}
        text = ("Alder w1 Bryn w2 Casimir w3 Dellwyn w4 Esdrel "
                + _filler(10, start=5))
        out = self._band(text, inv, is_opening=True)
        self.assertEqual(len(out), 1)
        self.assertIn("three is the cap", out[0]["detail"])


class RunAndLogNarrationBandTests(unittest.TestCase):
    """Wiring through run_and_log: health_out population (Task 2's
    proof-of-measurement) and the is_first_turn anchor driving real
    findings end to end, the way autosave_checkpoint.py actually calls it."""

    def _with_root(self, fn):
        with tempfile.TemporaryDirectory() as root:
            old = os.environ.get("DND_CAMPAIGN_ROOT")
            os.environ["DND_CAMPAIGN_ROOT"] = root
            try:
                fn(root)
            finally:
                if old is None:
                    del os.environ["DND_CAMPAIGN_ROOT"]
                else:
                    os.environ["DND_CAMPAIGN_ROOT"] = old

    def test_health_out_populated_on_success(self):
        def body(root):
            camp = pathlib.Path(root) / "campaigns" / "band-camp"
            camp.mkdir(parents=True)
            (camp / "state.md").write_text(
                "# s\n\n## Session Flags\nroll_mode: auto\n", encoding="utf-8")
            transcript = camp / "session.jsonl"
            transcript.write_text(
                _jsonl(_user("hi"), _assistant_text("A quiet street waits.")),
                encoding="utf-8")
            health = {}
            turn_lint.run_and_log(
                {"transcript_path": str(transcript), "session_id": "s1"},
                "band-camp", health_out=health)
            self.assertIn("gloss_inventory", health)
            self.assertFalse(health["gloss_inventory"])
            self.assertEqual(health["narration_words"], 4)
        self._with_root(body)

    def test_health_out_empty_when_lint_off(self):
        def body(root):
            camp = pathlib.Path(root) / "campaigns" / "band-camp-off"
            camp.mkdir(parents=True)
            (camp / "state.md").write_text(
                "# s\n\n## Session Flags\nturn_lint: off\n", encoding="utf-8")
            transcript = camp / "session.jsonl"
            transcript.write_text(
                _jsonl(_user("hi"), _assistant_text("Text.")),
                encoding="utf-8")
            health = {}
            n = turn_lint.run_and_log(
                {"transcript_path": str(transcript), "session_id": "s1"},
                "band-camp-off", health_out=health)
            self.assertEqual(n, 0)
            # Nothing measured — distinguishable from a measured zero.
            self.assertEqual(health, {})
        self._with_root(body)

    def test_opening_turn_over_permissive_cap_logged(self):
        def body(root):
            camp = pathlib.Path(root) / "campaigns" / "band-camp-open"
            camp.mkdir(parents=True)
            (camp / "state.md").write_text(
                "# s\n\n## Session Flags\nroll_mode: auto\n", encoding="utf-8")
            transcript = camp / "session.jsonl"
            long_text = _filler(110)  # no inventory -> permissive cap 100,
                                       # tolerance 105 -> 110 exceeds it
            transcript.write_text(
                _jsonl(_user("hi"), _assistant_text(long_text)),
                encoding="utf-8")
            n = turn_lint.run_and_log(
                {"transcript_path": str(transcript), "session_id": "s1"},
                "band-camp-open")
            self.assertEqual(n, 1)
            log = [json.loads(l) for l in
                  (camp / turn_lint.LOG_NAME).read_text().splitlines()]
            self.assertEqual(log[0]["detector"], "narration_band")
        self._with_root(body)

    def test_second_turn_not_opening_no_finding_even_if_long(self):
        def body(root):
            camp = pathlib.Path(root) / "campaigns" / "band-camp-2nd"
            camp.mkdir(parents=True)
            (camp / "state.md").write_text(
                "# s\n\n## Session Flags\nroll_mode: auto\n", encoding="utf-8")
            transcript = camp / "session.jsonl"
            long_text = _filler(110)
            transcript.write_text(
                _jsonl(_user("hi"), _assistant_text("Short opener.")),
                encoding="utf-8")
            turn_lint.run_and_log(
                {"transcript_path": str(transcript), "session_id": "s1"},
                "band-camp-2nd")
            with open(transcript, "a", encoding="utf-8") as f:
                f.write(_jsonl(_user("i continue"), _assistant_text(long_text)))
            n = turn_lint.run_and_log(
                {"transcript_path": str(transcript), "session_id": "s1"},
                "band-camp-2nd")
            self.assertEqual(n, 0)
            self.assertFalse((camp / turn_lint.LOG_NAME).exists())
        self._with_root(body)


if __name__ == "__main__":
    unittest.main()
