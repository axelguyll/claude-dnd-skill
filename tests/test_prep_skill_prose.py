"""test_prep_skill_prose.py — structural invariants on the forked SKILL prose:
milestone leveling replaced XP awards, and the new commands exist.

Run from repo root:
    python3 -m unittest tests.test_prep_skill_prose -v
"""
import pathlib
import unittest

REPO = pathlib.Path(__file__).resolve().parent.parent
DND = REPO / "skills" / "dnd"
SKILL = (DND / "SKILL.md").read_text(encoding="utf-8")
CMDS = (DND / "SKILL-commands.md").read_text(encoding="utf-8")
SCRIPTS = (DND / "SKILL-scripts.md").read_text(encoding="utf-8")


class SkillProseTests(unittest.TestCase):
    def test_xp_awards_section_replaced_by_milestone(self):
        self.assertNotIn("## XP Awards", SKILL)
        self.assertIn("## Milestone Leveling", SKILL)

    def test_milestone_section_disclaims_xp(self):
        idx = SKILL.find("## Milestone Leveling")
        section = SKILL[idx: idx + 1500]
        self.assertIn("no XP", section)

    def test_prep_and_beat_commands_exist(self):
        self.assertIn("/dm:dnd prep", CMDS)
        self.assertIn("/dm:dnd beat complete", CMDS)

    def test_deed_cite_rule_present(self):
        self.assertIn("cite a deed", CMDS)

    def test_level_up_gate_reconciled_for_milestone(self):
        # milestone campaigns must bypass the /dm:dnd level up XP gate
        self.assertIn("Milestone campaigns bypass this gate", CMDS)

    def test_beat_complete_handles_multi_level_jump(self):
        # milestone jumps can span >1 level (e.g. 4 -> 6); the procedure must loop
        idx = CMDS.find("/dm:dnd beat complete")
        end = CMDS.find("## `/dm:dnd save", idx)
        section = CMDS[idx:end]
        self.assertIn("once per level", section)

    def test_beat_complete_clears_pending_marker(self):
        idx = CMDS.find("/dm:dnd beat complete")
        end = CMDS.find("## `/dm:dnd save", idx)
        section = CMDS[idx:end]
        self.assertIn("--clear", section)

    def test_combat_end_awards_no_xp(self):
        self.assertNotIn("⭐ XP Awarded", CMDS)
        self.assertNotIn("send XP summary", CMDS)

    def test_xp_award_script_deprecated(self):
        # xp.py award must be signposted as deprecated under milestone leveling
        idx = SCRIPTS.find("xp.py")
        self.assertNotEqual(idx, -1)
        self.assertIn("deprecated", SCRIPTS.lower())


class DMVoiceTests(unittest.TestCase):
    """Guards for the 2026-07-15 DM voice overhaul (spec A-G). These pin prompt
    content against silent reversion; the real acceptance check is a live
    read-through, not these assertions."""

    def test_a_persona_is_plain_spoken_not_dark(self):
        self.assertNotIn("dark, immersive", SKILL)
        self.assertIn("talk like a real person running a game", SKILL)

    def test_c_tone_follows_scene_not_theme(self):
        self.assertIn("Tone follows the scene, not the theme", SKILL)

    def test_b_length_follows_scene_heat(self):
        self.assertIn("Length follows the scene's heat", SKILL)

    def test_d_read_aloud_and_spoken_sentences(self):
        self.assertIn("would you actually say this", SKILL)
        self.assertIn("not book-style fragments", SKILL)

    def test_e_npc_speech_always_its_own_block(self):
        self.assertNotIn("don't need a separate block", SKILL)
        self.assertIn("Always put NPC speech in its own", SKILL)

    def test_f_no_rote_what_do_you_do(self):
        self.assertIn("Don't tag every turn with", SKILL)

    def test_g_phonetic_hint_for_invented_names(self):
        self.assertIn("pronunciation hint the first time an invented name appears", SKILL)


class DMAuthenticityTests(unittest.TestCase):
    """Guards for the 6 authenticity adjudication rules (spec:
    docs/superpowers/specs/2026-07-15-dm-authenticity-rules-design.md).
    Content pins only — true acceptance is a live read-through."""

    def test_rule1_phantom_items_refused(self):
        self.assertIn("Inventory and the enemy roster are ground truth", SKILL)

    def test_rule2_hidden_dc(self):
        self.assertIn("Never state the DC", SKILL)
        self.assertIn("stays behind the screen", SKILL)

    def test_rule3_context_driven_rolls(self):
        self.assertIn("Stakes decide whether a roll happens", SKILL)

    def test_rule4a_nat_only_auto_on_attacks(self):
        self.assertIn("Natural 1 and 20 are automatic only on attack rolls", SKILL)

    def test_rule4b_fail_forward_with_puzzle_carveout(self):
        self.assertIn("A failed roll complicates", SKILL)
        self.assertIn("does not apply to puzzles", SKILL)

    def test_rule5_voice_conditions_and_name_dice(self):
        self.assertIn("Voice an active condition's mechanical effect and name the dice", SKILL)
        self.assertIn("advantage and disadvantage never stack", SKILL)

    def test_rule7_ability_skill_selection_and_full_name(self):
        self.assertIn("the fiction decides which ability and skill apply", SKILL)
        self.assertIn("Ability (Skill)", SKILL)


class DMDashboardProseTests(unittest.TestCase):
    """Bucket B: NPC speech renders as a concrete blockquoted, bold-labeled
    block, and a sound-cue block type bridges narration to the asset hub."""

    def test_npc_block_format_is_concrete(self):
        # The rule must say HOW, not just "in its own block".
        self.assertIn("bold speaker-labeled", SKILL)

    def test_sound_cue_block_exists(self):
        self.assertIn("🔊 **Cue:**", SKILL)

    def test_sound_cue_points_at_asset_hub(self):
        self.assertIn("assets.html", SKILL)

    def test_sound_cue_forbids_inventing_cues(self):
        idx = SKILL.find("🔊 **Cue:**")
        self.assertNotEqual(idx, -1)
        window = SKILL[idx - 400: idx + 400]
        self.assertIn("never invent a cue", window)


if __name__ == "__main__":
    unittest.main()
