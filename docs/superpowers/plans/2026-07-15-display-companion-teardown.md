# Display Companion Teardown — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove the display companion feature entirely from `claude-dnd-skill`, leaving a clean terminal-only DM skill with no dangling references.

**Architecture:** Approach **B** (of 3 weighed — see decision record). Delete the display *network layer* (server, phone client, autorun, audio, TTS, `send.py`, `push_stats.py`) but **keep the narration-vs-NPC block separation as a terminal prose convention**, preserving the just-shipped voice-overhaul investment. `send.py --stat-*` is a display **mirror**, not a source of truth — `tracker.py` (conditions/effects, per-campaign file), the character-sheet markdown (HP/slots/XP), and `state.md` live flags persist all real state independently. So the teardown loses **zero persistent state**; narration simply becomes Claude's chat prose instead of a `send.py` push.

**Tech Stack:** Python 3.14 (`skills/dnd/scripts/`, `tests/`), Markdown skill docs (`skills/dnd/SKILL*.md`), Claude Code plugin manifests.

## Global Constraints

- **Repo:** `C:\Users\axelg_p6dxxyr\Projects\experimental\claude-dnd-skill`; canonical branch = `main`. Do the teardown on a feature branch, not `main`.
- **Zero persistent state may be lost.** Real state lives in: `tracker.py` (per-campaign conditions/concentration/effects/death-saves), character-sheet markdown `characters/<PC>.md` (HP/slots/XP), `state.md` live flags. Verified this session. Do NOT touch these.
- **Keep the narration/NPC block *discipline*** as a prose writing-rule when `send.py --npc` goes away (Approach B). The voice-overhaul spec (`docs/superpowers/specs/2026-07-15-dm-voice-overhaul-design.md`, shipped 2026-07-15, `DMVoiceTests` green) depends on narration and NPC dialogue rendering as visually distinct blocks. That split must survive as prose.
- **`S-Drive` rule is irrelevant here** (this repo is not on S-Drive).
- **Skill becomes terminal-only.** `roll_mode: players` (phone/on-screen roller) collapses toward "player tells Claude the roll, or Claude rolls openly (`auto`)." `autorun`/taxi mode and the player-input queue disappear (they only existed to feed phone submissions into context).
- **Two items are explicitly DEFERRED, out of scope for this plan:** (bucket 2) a narration/NPC terminal-UI redesign; (bucket 3) the 5 authenticity adjudication rules (handoff `2026-07-15-dm-authenticity-rules.md`). The teardown hands bucket 2 a clean canvas and simplifies bucket 3 (rule 2's `--dc` leak becomes moot — no phone to leak to).
- **The finish-line is objective:** a grep for display tokens over the 3 canonical docs + `state.md` returns zero, and the full test suite is green. The guard test (Task 1) encodes this.

---

## Coupling map (reconnaissance completed this session)

| Surface | Refs | Action |
|---|---|---|
| `skills/dnd/display/` (~14,200 lines, ~14 files + `templates/`, `icons/`) | whole dir | **Delete** |
| `skills/dnd/SKILL.md` | ~30 | Rewrite turn-loop / dice / narration sections terminal-native |
| `skills/dnd/SKILL-commands.md` | 93 | Strip display/LAN/autorun setup, `display` subcommands |
| `skills/dnd/SKILL-scripts.md` | 55 | Remove send.py/push_stats/check_input syntax blocks |
| `skills/dnd/templates/state.md` | flags | Drop `_display_running`, `autorun`, `roll_mode` phone bits |
| `skills/dnd/scripts/autosave_checkpoint.py`, `name_registry.py`, `oracle.py` | 3 files | Remove reads of dropped Session Flags |
| `tests/test_display_robustness.py` (10), `test_phone_presence.py` (7) | delete | Delete — display-specific |
| `tests/test_autosave_checkpoint.py` (1), `test_milestone_counter.py` (2), `test_oracle.py` (2) | edit | Excise incidental display refs |
| `README.md`, `CHANGELOG.md`, `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `docs/SKILL-tts.md`, `MIGRATING.md`, `scripts/migrate_v1_to_v2.py`, `CONTRIBUTING.md` | ~8 files | De-market / delete / gut (Task 8) |

**Display token set** (the grep guard checks these over SKILL.md, SKILL-commands.md, SKILL-scripts.md, templates/state.md): `display/`, `send.py`, `push_stats`, `check_input`, `autorun`, `_display_running`, `dice-request`, `--dc`, `--stat-`, `--npc`, `--player`, `--dice`, `--tutor`, `LAN`, `start-display`, `_display_running = true`. (Prune this list during Task 1 to tokens that genuinely must be absent — e.g. `--npc` becomes a prose-only concept, so it must NOT appear as a `send.py` flag but MAY appear in prose describing "the NPC block"; the guard should match the flag form `send.py --npc`, not the bare word "NPC".)

---

## File Structure

No new source files except one test file. This is a removal; the structural change is net-negative lines. The one addition:

- **Create:** `tests/test_no_display_refs.py` — the teardown's finish-line guard (asserts the display token set is absent from the 3 docs + `state.md`; mirrors the `DMVoiceTests` content-assertion pattern in `tests/test_prep_skill_prose.py`).

---

### Task 1: Guard test — assert no display refs (RED first)

**Files:**
- Create: `tests/test_no_display_refs.py`
- Reference (read, do not edit yet): `tests/test_prep_skill_prose.py` (mirror its `DMVoiceTests` class shape), `skills/dnd/SKILL.md`, `skills/dnd/SKILL-commands.md`, `skills/dnd/SKILL-scripts.md`, `skills/dnd/templates/state.md`

**Interfaces:**
- Produces: a pytest module the later tasks drive to GREEN. Later tasks consume nothing from it except its pass/fail signal.

- [ ] **Step 1: Finalize the token set.** Read the four target files. From the "Display token set" list above, keep only tokens whose *flag/path form* must be absent. Distinguish: `send.py --npc` (must be absent — it's the deleted mechanism) vs the prose word "NPC" / "NPC block" (must SURVIVE — it's the kept convention). Write the kept tokens as a Python list `FORBIDDEN` in the test. Add an `ALLOWED_PROSE` note in a comment for anything deliberately kept.

- [ ] **Step 2: Write the failing test.**

```python
# tests/test_no_display_refs.py
"""Guard: the display companion is gone. These tokens must not reappear in the
canonical skill docs or the state template. Mirrors DMVoiceTests (content-assertion
guard) in test_prep_skill_prose.py — prevents silent reversion, not a behavior test."""
import pathlib
import unittest

SKILL_DIR = pathlib.Path(__file__).resolve().parents[1] / "skills" / "dnd"

# Flag/path forms of the removed feature. Prose words like "NPC block" are NOT here —
# the narration/NPC block separation survives as a writing rule (Approach B).
FORBIDDEN = [
    "display/",
    "send.py",
    "push_stats",
    "check_input",
    "autorun",
    "_display_running",
    "dice-request",
    "--dc ",
    "--stat-",
    "--player",
    "--dice",
    "--tutor",
    "start-display",
    "LAN mode",
]

TARGETS = [
    SKILL_DIR / "SKILL.md",
    SKILL_DIR / "SKILL-commands.md",
    SKILL_DIR / "SKILL-scripts.md",
    SKILL_DIR / "templates" / "state.md",
]


class NoDisplayRefsTests(unittest.TestCase):
    def test_no_forbidden_tokens(self):
        hits = []
        for path in TARGETS:
            text = path.read_text(encoding="utf-8")
            for i, line in enumerate(text.splitlines(), 1):
                for tok in FORBIDDEN:
                    if tok in line:
                        hits.append(f"{path.name}:{i}: {tok!r} in {line.strip()[:80]}")
        self.assertEqual(hits, [], "display refs remain:\n" + "\n".join(hits))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run it — verify RED.**

Run: `cd "C:\Users\axelg_p6dxxyr\Projects\experimental\claude-dnd-skill" && python -m pytest tests/test_no_display_refs.py -v`
Expected: FAIL — many hits (the docs are still full of these tokens). This confirms the guard actually detects the refs it must later prove gone.

- [ ] **Step 4: Commit the RED guard.**

```bash
git add tests/test_no_display_refs.py
git commit -m "test: add display-ref guard (RED) for terminal-only teardown"
```

---

### Task 2: Rewrite `SKILL.md` to terminal-native

**Files:**
- Modify: `skills/dnd/SKILL.md` — sections: "Player input queue (display companion)" (~`:262`), "Autorun / taxi mode" (~`:267`), "Dice convention" (~`:285`), "Per-player override" (~`:297`), the entire "Display sync" block (~`:304`–`:395`), "Stat flags" table (~`:351`), "Batching rule" (~`:366`), "Per-turn combat sequence" (~`:397`)
- Test: `tests/test_no_display_refs.py` (partial GREEN after this task — SKILL.md clean)

**Interfaces:**
- Produces: a terminal-only turn loop. Later docs (Tasks 3–4) must not reintroduce `send.py`. The kept convention that Tasks 3–4 rely on: NPC dialogue and DM narration are written as **visually distinct prose blocks** in Claude's chat output (no script).

- [ ] **Step 1: Delete the display-only sections.** Remove "Player input queue (display companion)", "Autorun / taxi mode", "Per-player override" (phone Settings), and the whole "Display sync (when `_display_running = true`)" block including the `--stat-*` flags table and the "Batching rule / CRITICAL send.py" note.

- [ ] **Step 2: Rewrite the "Dice convention" section** — drop the display prescribe-roll branch (`send.py --dice-request ... --wait`) and the `--dc` flag entirely. Simplify `roll_mode` to two modes: `players` (call for the roll by name and wait for the player to state the number) and `auto` (Claude rolls openly via `dice.py`, shows math). Remove all phone-routing / on-screen-drawer language. Keep the hidden-roll mechanic (`dice.py --silent`).

- [ ] **Step 3: Rewrite the "Per-turn combat sequence"** to terminal-native:

```
a. Player states their action (typed in chat).
b. Roll all dice (combat.py attack / dice.py). NPC/monster rolls are yours; PC rolls per roll_mode.
c. tracker.py  ← conditions, concentration, death saves if applicable
   tracker.py effect tick <actor>  ← decrement round effects; prints any expiry warnings
d. Write the full narration for this turn as chat prose. Put any NPC speech in its own
   visually distinct block, separate from DM narration (see "Narration principles").
e. Persist stat changes: edit characters/<PC>.md for HP/slots/XP; state.md for live flags,
   at scene boundaries / autosave cadence (unchanged — this was never send.py's job).
```

- [ ] **Step 4: Fold the NPC-block rule into "Narration principles"** (~`:197`) as a prose convention: "Put every NPC's speech in its own block, visually separated from DM narration — never inline dialogue into the narration paragraph. The end-of-turn steer is always narration, never trailing an NPC line." (This is the voice-spec's `--npc` rule, restated as writing guidance.)

- [ ] **Step 5: Run the guard — SKILL.md portion GREEN.**

Run: `python -m pytest tests/test_no_display_refs.py -v`
Expected: still FAIL overall (other docs dirty), but zero hits from `SKILL.md`. Confirm by reading the failure list — no `SKILL.md:` lines.

- [ ] **Step 6: Commit.**

```bash
git add skills/dnd/SKILL.md
git commit -m "refactor: rewrite SKILL.md turn loop terminal-native (drop display sync)"
```

---

### Task 3: Rewrite `SKILL-commands.md` (93 refs)

**Files:**
- Modify: `skills/dnd/SKILL-commands.md`
- Test: `tests/test_no_display_refs.py`

**Interfaces:**
- Consumes: the terminal-only turn loop from Task 2 (no `send.py`).
- Produces: command procedures with no `display start/stop`, LAN, or autorun setup.

- [ ] **Step 1: Read the file in full** (it's the command-procedures doc; 93 display refs). Identify: the `/dm:dnd load` and `/dm:dnd new` session-setup choice (display / LAN / autorun menu), any `display` subcommand section, `display start`/`stop`/`status`, and every `send.py`/`push_stats`/`check_input` reference in procedures.

- [ ] **Step 2: Excise the session-setup display menu.** `/dm:dnd load` and `/dm:dnd new` should no longer offer display/LAN/autorun. If an `AskUserQuestion` menu references these, remove those options (keep Load/New/Import/character-management).

- [ ] **Step 3: Delete the `display` subcommand documentation** entirely (`display start`, `display stop`, `display status`, autorun on/off).

- [ ] **Step 4: Rewrite remaining procedures** that invoked `send.py`/`push_stats.py` to their terminal-native form (write prose; persist via `tracker.py` + markdown), consistent with Task 2's combat sequence.

- [ ] **Step 5: Run the guard — SKILL-commands.md GREEN.**

Run: `python -m pytest tests/test_no_display_refs.py -v`
Expected: zero `SKILL-commands.md:` hits in the failure list.

- [ ] **Step 6: Commit.**

```bash
git add skills/dnd/SKILL-commands.md
git commit -m "refactor: strip display/LAN/autorun from SKILL-commands.md"
```

---

### Task 4: Rewrite `SKILL-scripts.md` (55 refs)

**Files:**
- Modify: `skills/dnd/SKILL-scripts.md`
- Test: `tests/test_no_display_refs.py`

**Interfaces:**
- Consumes: terminal-only conventions from Tasks 2–3.
- Produces: a script-syntax reference documenting only surviving scripts (`dice.py`, `combat.py`, `tracker.py`, `character.py`, `xp.py`, etc.) — no `send.py`, `push_stats.py`, `check_input.py`, `autorun_wait.py`.

- [ ] **Step 1: Read the file in full.** Locate every `send.py` syntax block (`--player`, `--dice`, `--npc`, `--stat-*`, `--dice-request`, milestone flags), `push_stats.py` block, and `check_input.py`/`autorun_wait.py` reference.

- [ ] **Step 2: Delete those blocks.** For milestone/inspiration/XP flags that lived on `send.py` (e.g. `send.py --milestone-award`), check whether an equivalent lives on a surviving script (`xp.py`, `character.py`); if the only home was `send.py`, note the capability moves to DM-edited markdown, and remove the syntax block.

- [ ] **Step 3: Run the guard — SKILL-scripts.md GREEN.**

Run: `python -m pytest tests/test_no_display_refs.py -v`
Expected: guard now PASSES entirely (all 4 target files clean).

- [ ] **Step 4: Commit.**

```bash
git add skills/dnd/SKILL-scripts.md
git commit -m "refactor: remove send.py/push_stats/check_input from SKILL-scripts.md; guard green"
```

---

### Task 5: State schema + scripts that read dropped flags

**Files:**
- Modify: `skills/dnd/templates/state.md` (drop `_display_running`, `autorun`, phone bits of `roll_mode`)
- Modify: `skills/dnd/scripts/autosave_checkpoint.py`, `skills/dnd/scripts/name_registry.py`, `skills/dnd/scripts/oracle.py` (remove reads of dropped flags)
- Test: `tests/` full suite

**Interfaces:**
- Consumes: nothing.
- Produces: a `state.md` template and scripts with no display-flag dependencies. Existing campaign `state.md` files may still carry these flags — the scripts must **tolerate their presence** (ignore, don't crash), just stop *depending* on them.

- [ ] **Step 1: Edit `templates/state.md`** — remove `_display_running` and `autorun` from the `## Session Flags` section. For `roll_mode`, keep the flag (players/auto still meaningful terminal-only) but delete any phone/per-character-phone-override wording.

- [ ] **Step 2: Grep the 3 scripts for the flags.**

Run: `cd "C:\Users\axelg_p6dxxyr\Projects\experimental\claude-dnd-skill" && grep -nE "_display_running|autorun|roll_mode" skills/dnd/scripts/autosave_checkpoint.py skills/dnd/scripts/name_registry.py skills/dnd/scripts/oracle.py`

- [ ] **Step 3: For each hit,** remove the branch that reads/acts on `_display_running` or `autorun`. Leave `roll_mode` reads intact if they only distinguish players/auto. **Preserve backward-compat:** if a script parses `## Session Flags`, ensure an unknown/leftover `autorun:` line in an old campaign file is skipped gracefully, not an error.

- [ ] **Step 4: Run the full suite.**

Run: `python -m pytest tests/ -v`
Expected: PASS (minus the display-specific tests, which Task 7 removes — they may still fail here referencing deleted flags; note which, defer their fix to Task 7). The 3 edited scripts' own tests (`test_autosave_checkpoint`, `test_oracle`) may go RED here — that's expected; Task 7 fixes them.

- [ ] **Step 5: Commit.**

```bash
git add skills/dnd/templates/state.md skills/dnd/scripts/autosave_checkpoint.py skills/dnd/scripts/name_registry.py skills/dnd/scripts/oracle.py
git commit -m "refactor: drop display flags from state schema and scripts that read them"
```

---

### Task 6: Delete the `display/` directory

**Files:**
- Delete: `skills/dnd/display/` (entire directory — `dnd-display-app.py`, `templates/index.html`, `audio.py`, `tts.py`, `send.py`, `push_stats.py`, `check_input.py`, `autorun_wait.py`, `setup_tls.py`, `start-display.sh`, `wrapper.py`, `runtime_paths.py`, `dm_help.py`, `verify_tail.sh`, `write_canonical_tail.py`, `requirements.txt`, `README.md`, `icons/`, `__pycache__/`)

**Interfaces:**
- Consumes: confirmation (from Tasks 2–5) that no surviving doc or script imports from `display/`.

- [ ] **Step 1: Final import/reference check before deleting.**

Run: `cd "C:\Users\axelg_p6dxxyr\Projects\experimental\claude-dnd-skill" && grep -rnE "display/|from display|import.*display|runtime_paths|dm_help" --include=*.py skills/dnd/scripts/ tests/ | grep -v "/display/"`
Expected: only references inside test files Task 7 will delete/fix. If any *surviving* script imports from `display/`, stop and resolve before deleting.

- [ ] **Step 2: Delete the directory.**

```bash
git rm -r skills/dnd/display/
```

- [ ] **Step 3: Run the full suite** to surface anything that imported from `display/`.

Run: `python -m pytest tests/ -v`
Expected: display-specific tests error on import (they're deleted in Task 7); no *surviving* test should fail on a missing `display/` import.

- [ ] **Step 4: Commit.**

```bash
git commit -m "feat: delete display companion directory (~14k lines) — terminal-only"
```

---

### Task 7: Tests — delete display-specific, fix incidental

**Files:**
- Delete: `tests/test_display_robustness.py`, `tests/test_phone_presence.py`
- Modify: `tests/test_autosave_checkpoint.py` (1 ref), `tests/test_milestone_counter.py` (2 refs), `tests/test_oracle.py` (2 refs)

**Interfaces:**
- Produces: a green suite that no longer references the display.

- [ ] **Step 1: Delete the two display-specific test files.**

```bash
git rm tests/test_display_robustness.py tests/test_phone_presence.py
```

- [ ] **Step 2: Fix incidental refs.** In each of `test_autosave_checkpoint.py`, `test_milestone_counter.py`, `test_oracle.py`, find the display reference:

Run: `cd "C:\Users\axelg_p6dxxyr\Projects\experimental\claude-dnd-skill" && grep -nE "display|send\.py|push_stats|_display_running|autorun|dice.request" tests/test_autosave_checkpoint.py tests/test_milestone_counter.py tests/test_oracle.py`

For each hit: if it's a setup line writing a display flag into a fixture, drop that line; if it asserts on display behavior, delete the assertion (or the whole test method if display was its entire subject). Keep the non-display coverage intact.

- [ ] **Step 3: Run the full suite — GREEN.**

Run: `python -m pytest tests/ -v`
Expected: PASS, all files. Note the count (was 71/71 on the prep prose suite + others; expect the total to drop by the deleted display tests).

- [ ] **Step 4: Commit.**

```bash
git add tests/
git commit -m "test: remove display tests; excise incidental display refs; suite green"
```

---

### Task 8: Docs, manifests, marketing

**Files:**
- Modify: `README.md` (de-market — headline currently "with Cinematic Display Companion — Couch Co-op Edition")
- Modify: `CHANGELOG.md` (add teardown entry; scrub top-of-file display marketing; keep deeper history)
- Modify: `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` (descriptions mention "optional live display companion" — remove that clause)
- Delete: `docs/SKILL-tts.md`, `MIGRATING.md` (v1→v2 migration is display-centric — confirm before deleting)
- Modify or delete: `scripts/migrate_v1_to_v2.py` (carries over display auth token / TLS certs — gut the display bits, or delete if the whole script is display-migration)
- Modify: `CONTRIBUTING.md` (mentions display companion + `display/audio.py` i18n contribution path)

**Interfaces:**
- Produces: a repo that reads as terminal-only and doesn't advertise a feature that no longer exists.

- [ ] **Step 1: README** — rewrite the title and the "What is this / How it works" section to describe the terminal-only DM skill. Remove the demo GIF reference (`screenshots/demo-v3.gif`) if it shows the display; remove "players submit actions from their phones" language.

- [ ] **Step 2: Plugin manifests** — edit both `plugin.json` and `marketplace.json` `description` fields to drop "an optional live display companion" / "live display companion".

- [ ] **Step 3: CHANGELOG** — prepend a new entry:

```markdown
## [Unreleased] — 2026-07-15 — Terminal-only: display companion removed

- **Removed the display companion entirely.** The Flask/SSE web app, phone
  companion, on-screen dice drawer, autorun/taxi mode, SFX/audio, and TTS are
  gone (~14,200 lines under `skills/dnd/display/`). This is now a terminal-only
  DM skill. No persistent state is affected — HP/slots/XP live in character
  sheets, conditions/effects in `tracker.py`, live flags in `state.md`. The
  narration-vs-NPC block separation is preserved as a prose writing convention.
  For solo/small-table play driven entirely from the terminal.
```

Also scrub display marketing from the top-of-file intro paragraphs (leave individual historical release entries untouched — they are the record).

- [ ] **Step 4: TTS + migration docs** — read `docs/SKILL-tts.md` and `MIGRATING.md` and `scripts/migrate_v1_to_v2.py`. If wholly display-scoped, `git rm` them. If `migrate_v1_to_v2.py` has non-display migration logic, gut only the display-carryover (device approvals, display auth token, TLS certs) and keep the rest.

- [ ] **Step 5: CONTRIBUTING.md** — remove the "display companion / dice mechanics" and "i18n / language packs for SFX triggers (`display/audio.py`)" contribution bullets.

- [ ] **Step 6: Full orphan-reference sweep.**

Run: `cd "C:\Users\axelg_p6dxxyr\Projects\experimental\claude-dnd-skill" && grep -rniE "display companion|send\.py|push_stats|check_input|autorun|_display_running|dice.request|cinematic|couch co-op|SFX|companion" . | grep -viE "\.git/|CHANGELOG.md|__pycache__" | grep -v "docs/superpowers/plans/2026-07-15-display-companion-teardown.md"`
Expected: zero hits outside the CHANGELOG's historical entries and this plan file. Investigate any remaining hit.

- [ ] **Step 7: Commit.**

```bash
git add -A
git commit -m "docs: de-market README/manifests to terminal-only; remove TTS+migration docs"
```

---

### Task 9: Verify + Review + Finish

**Files:** none (verification only)

- [ ] **Step 1: Guard + full suite green.**

Run: `python -m pytest tests/ -v`
Expected: PASS including `test_no_display_refs.py`.

- [ ] **Step 2: Final orphan grep** (repeat Task 8 Step 6 across the whole repo). Expected zero hits outside CHANGELOG history + this plan.

- [ ] **Step 3: Load-path smoke check.** Confirm the skill's documented load sequence (`/dm:dnd load`) references only surviving scripts. Grep `SKILL.md`, `SKILL-commands.md` for any `${CLAUDE_SKILL_DIR}/display/` path:

Run: `grep -rn 'display/' skills/dnd/SKILL*.md`
Expected: zero.

- [ ] **Step 4: Review the diff.** Dispatch `cavecrew-reviewer` (compressed, isolated) over the branch diff; escalate to `/code-review high` if it flags anything cross-cutting. Fix surfaced bugs before finishing. Optionally run `/simplify` for reuse/efficiency cleanups.

- [ ] **Step 5: Finish the branch** per `superpowers:finishing-a-development-branch` — the work is a coherent, tested removal; present merge/PR options. Remember: F4 schema hardening + voice overhaul + voice spec are ALSO uncommitted on `main` from prior sessions — coordinate so the teardown branch doesn't strand them (check `git status`/`git log` first).

---

## Self-Review (run before executing)

1. **Coverage:** every surface in the coupling map has a task — display dir (T6), SKILL.md (T2), SKILL-commands.md (T3), SKILL-scripts.md (T4), state+scripts (T5), tests (T7), docs/manifests (T8), verify (T9), guard (T1). ✓
2. **Ordering:** guard first (T1), then docs top-down (T2–4) so the guard goes green before the dir is deleted; state/scripts (T5) and dir-delete (T6) after the docs stop referencing them; tests (T7) after the dir is gone so import-errors are expected; docs/marketing (T8) last; verify (T9) closes. ✓
3. **No persistent-state loss:** T5/T6 explicitly preserve `tracker.py`, character markdown, `state.md`. ✓
4. **Voice-spec preserved:** T2 Step 4 restates the `--npc` rule as prose. ✓
5. **Deferred buckets untouched:** no authenticity rules, no narration-UI redesign in scope. ✓

## Execution notes for a Fable-5 run (if chosen)

Fable 5 wants the goal + constraints up front, not step-by-step hand-holding — this plan doc IS that spec. Hand it the whole file and "execute task by task; the guard test is the finish-line; do not touch the persistence surfaces in Global Constraints." Keep the grep guard as the backstop regardless of model — the design assumes no model catches every one of ~200 refs unaided.
