# ARCHITECTURE — claude-dnd-skill

*Written 2026-07-16 (Fable review, Session A). The anti-drift map: what each piece is, how
data flows between them, and where the prose and the scripts must agree. Update this file
whenever a subsystem, file contract, or lifecycle step changes.*

Companion: `Vault\projects\claude-dnd-skill-compass.md` (fragile links + open questions +
read-order). Domain glossary: `CONTEXT.md` (Session B, pending).

---

## 1. What this thing is

A **prose-instruction-driven DM**. The "program" is three markdown documents under
`skills/dnd/` that a model executes at the table; ~35 Python scripts are deterministic
helpers (dice, HP, initiative, data lookup, rendering, prep bible generation). The prose
is the primary artifact — reviewing DM behavior means reviewing prose.

Two roots, strictly separated:

- **Code root** — `${CLAUDE_SKILL_DIR}` = `skills/dnd/` (prose docs, `scripts/`, `data/`,
  `templates/`). Read-only at play time except `data/dnd5e_supplemental.json`.
- **Data root** — `~/.claude/dnd/` (or `$DND_CAMPAIGN_ROOT`), holding
  `campaigns/<name>/*` and the global character roster `characters/*.md`. Never inside
  the plugin, so it survives updates. Resolution: `scripts/paths.py`.

`${CLAUDE_SKILL_DIR}` is substituted to an absolute path only in SKILL.md; the other two
prose docs are read verbatim, so every command copied from them needs manual substitution
(SKILL.md:8-21). This is a standing operational trap the prose warns about explicitly.

---

## 2. The three prose docs

| Doc | Lines | Governs | Loaded |
|---|---|---|---|
| `SKILL.md` | 347 | DM behavior contract: the 13 "Great DM" standards, narration principles, ruleset 2014/2024 handling, dice convention/`roll_mode`, arc-steering rules (structured + dynamic), per-turn combat sequence, milestone leveling, tutor mode, compaction re-read ladder, autosave micro-save rule | Always (skill entry) |
| `SKILL-commands.md` | 852 | Every `/dm:dnd` command as a step-by-step procedure: new, load, import, prep, beat complete, save, end, abandon, character *, level up, npc *, registry, combat, rest, recap, arc *, graph *, oracle *, tutor, autosave, data, path, update, list | At `/dm:dnd load` / before any command |
| `SKILL-scripts.md` | 384 | Canonical CLI syntax for every helper script + when to run each | At `/dm:dnd load` |

**Overlaps (places where two docs state the same rule and can diverge):**
- Dice/crit semantics: SKILL.md:268-284 and SKILL-scripts.md:10-27 (currently consistent).
- Weapon-mastery invocation: SKILL.md:44 says `tracker.py effect-start`; the real syntax is
  `tracker.py -c <camp> effect start` (tracker.py:386-387, SKILL-scripts.md:117-121).
- Autosave: SKILL.md:223 (micro-save rule) + SKILL-commands.md:835-851 (toggle) +
  SKILL-scripts.md:307-324 (hook) — three-way description of one mechanism.
- Arc rules: SKILL.md:225-266 (behavioral steering) vs SKILL-commands.md:696-733 (arc
  command mechanics) — intentional split (behavior vs procedure), but both carry beat
  semantics.
- Milestone leveling: SKILL.md:307-317, SKILL-commands.md:346-363 (`beat complete`), and
  the XP-gate bypass at SKILL-commands.md:584.

---

## 3. Script inventory (one line each)

### Table-time mechanics (`skills/dnd/scripts/`)
| Script | Does | Reads / writes |
|---|---|---|
| `dice.py` | All die rolls (adv/dis, kh, `--attack` crit flag, `--silent`, `--label`) | stateless |
| `combat.py` | Initiative (`init` → STATE_JSON), tracker reprint, `attack` resolution, 2024 weapon `mastery` | stateless (state carried as JSON in `state.md → ## Active Combat`) |
| `tracker.py` | Conditions, concentration, timed effects, death saves | RW `<campaign>/tracker.json` |
| `calendar.py` | In-world date/time; `advance`, `rest short/long`, `set` | RW `<campaign>/calendar.json` |
| `character.py` | Stat-block calc, level-up HP math, XP tracking (legacy) | stateless |
| `ability-scores.py` | 4d6kh3 arrays, point-buy validation | stateless |
| `lookup.py` | Query bundled SRD (spell/item/feature/condition/monster), per-ruleset | R `data/dnd5e_srd*.json`, supplemental |
| `xp.py` | **Deprecated** (milestone fork) — XP calc/award for legacy campaigns | RW character sheets |
| `session_recap.py` | Deterministic party state-diff (`snapshot` / `diff`) — anti-hallucination recap | RW `<campaign>/.recap/`, R sheets + tracker.json |
| `oracle.py` | Solo/improv oracles: Mythic chaos factor, yes/no, event focus, scene words | RW `chaos_factor` in state.md |
| `campaign_search.py` | Keyword search across campaign files before full Reads | R campaign files |

### Campaign graph
| Script | Does | Reads / writes |
|---|---|---|
| `campaign_graph.py` | Typed-edge relationship graph: add-node/add-edge/close-edge/**supersede-edge**/list/show/subgraph/scene-context/extract/extract-apply | RW `<campaign>/graph.json` |
| `graph_extract_deterministic.py` | Zero-LLM edge extraction from session-log (verb table; ~95% precision / ~50% recall) | R `data/graph/verb_table_seed.yaml`, session-log |
| `scripts/graph/*` (3 files) | Research harnesses: A/B replay experiment, Reddit corpus collect/extract | offline, not in play loop |

### Prep phase (`scripts/prep/`)
| Script | Does | Reads / writes |
|---|---|---|
| `premise.py` | Rolls tone (from `data/tones.yaml`) + 4 orthogonal premise axes (`data/premise-seeds.yaml`) → scaffold to reconcile | stateless, seedable |
| `bestiary.py` | CR-band math → legal monster candidates for `--level` | R `data/dnd5e_srd.json` |
| `schema.py` | Hard validation gate for `spine.json` (beat ids, acts, monotonic `level_up_to`, threat bands, cross-refs) | R bible JSON |
| `milestone.py` | Set/clear `⚠ LEVEL UP PENDING (Level N)` marker on a sheet | RW character sheet |

### Rendering (host-side HTML, written into the campaign dir)
| Script | Does | Reads / writes |
|---|---|---|
| `render_tracker.py` | Combat dashboard `<campaign>/tracker.html` (meta-refresh), each combat turn | R tracker.json, W tracker.html |
| `render_assets.py` | Asset hub `<campaign>/assets.html` (maps + ambient toggles) from shopping lists | R map-list.md, ambient-list.md; W assets.html; ensures `maps/`, `sounds/` |

> The old `display/` companion (TTS/network audio stack) was **torn down**
> (docs/superpowers/plans/2026-07-15-display-companion-teardown.md); the guard test
> `tests/test_no_display_refs.py` bans its tokens from ever reappearing in the prose.

### Data pipeline
| Script | Does |
|---|---|
| `build_srd.py` | Build `data/dnd5e_srd.json` (1453 records) from 5e-bits + FoundryVTT; `--ruleset 2024` builds `dnd5e_srd_2024.json` (not committed — built on demand, ~3 min) |
| `sync_srd.py` | Check upstream SHAs, rebuild only if stale |
| `data_pull.py` | Raw fetch helper for 5e-bits files |
| `build_supplemental.py` | Scan a character sheet for non-SRD spells/features; fetch from dnd5e.wikidot.com into `data/dnd5e_supplemental.json` |

### Infrastructure / lifecycle
| Script | Does |
|---|---|
| `paths.py` | Canonical path resolution. **Is also a CLI**: `campaign-ruleset`, `srd-path`, `runtime-dir`, `campaign-dir` (paths.py:199-211) |
| `path_config.py` | View/set/reset `DND_CAMPAIGN_ROOT` (shell rc / setx persistence) |
| `migrate_ruleset.py` | One-time `**Ruleset:**` field injection with backup; exit 0/1/2 = migrated/needs/missing |
| `migrate_v1_to_v2.py` | Legacy standalone-install → plugin migration |
| `name_registry.py` | Cross-campaign name uniqueness: rebuild/list/lookup/check (exit 1 = duplicate)/add/retire → `~/.claude/dnd/.name_registry.json` |
| `npc_rename.py` | Campaign-wide rename across md files + graph.json, backup-first, dry-run |
| `autosave_checkpoint.py` | Stop-hook target: snapshots state.md every turn to runtime dir; every N turns emits a block decision prompting a continuity flush. Reads `<runtime-dir>/active-campaign.json` + `autosave` flag |
| `install_autosave_hook.py` | Opt-in installer for the Stop hook (writes `~/.claude/settings.json`) |
| `import_campaign.py` | Source-text extraction for `/dm:dnd import` (PyMuPDF column-aware; pdftotext fallback), chunking |
| `corpus_check.py` | Validate lazy-corpus layout (source-index ↔ source/<id>.md ↔ arc.md) |
| `update_skill.py` | `git pull --ff-only` self-update with dirty-tree refusal |
| `scripts/bump_version.py` (repo root) | Release version bump |

### Data files (`skills/dnd/data/`)
`dnd5e_srd.json` (bundled 2014 SRD), `dnd5e_supplemental.json` (wikidot fetches),
`tones.yaml` (shared 7-tone catalog: heroic/mythic/grimdark/horror/intrigue/
swashbuckling/cosmic), `premise-seeds.yaml` (4-axis premise bank),
`graph/verb_table_seed.yaml` (deterministic extractor patterns).
`dnd5e_srd_2024.json` is generated on demand, not committed.

### Templates (`skills/dnd/templates/`)
`state.md` (all four arc-format blocks; Live State Flags; Deeds; Session Flags),
`world.md`, `npcs.md`, `session-log.md`, `character-sheet.md`, `arc.md` (structured tree),
`spine.md` (authored-bible schema doc), `map-list.md`, `ambient-list.md`.

---

## 4. Campaign state stores (who owns what)

All under `~/.claude/dnd/campaigns/<name>/` unless noted:

| File | Owner / writer | Read when |
|---|---|---|
| `state.md` | DM prose (save/end/micro-save); seeded by new/import/prep | Fully at load; targeted sections re-read after compaction |
| `world.md` | new/import/prep; rarely updated after | Fully at load |
| `world-nodes.md` | import (structured only) | Lazy — current act's nodes on demand |
| `npcs.md` (index) / `npcs-full.md` | DM prose as NPCs appear/change | Index at load; full entry before voicing an NPC |
| `session-log.md` / `session-log-archive.md` | save (keeps 2 recent entries; older → archive) | NOT at load; recap/explicit request |
| `characters/<pc>.md` (+ global roster `~/.claude/dnd/characters/`) | character new/import, level up, per-turn HP/slots persistence | At load |
| `spine.json` (authored) | prep; `beat complete` flips statuses | Only at `beat complete` |
| `arc.md` (structured) | import; save syncs chapter statuses | Only on chapter advance / broad-arc question |
| `source/<id>.md` + `source-index.md` (structured) | import (lazy corpus) | One chapter file before running its scenes |
| `graph.json` | campaign_graph.py (live add-edge, save sweep, extract-apply) | scene-context at load step 6 + on demand |
| `tracker.json` | tracker.py | Per combat turn; merged by render/recap |
| `calendar.json` | calendar.py | Rests, travel, time skips |
| `.recap/last.json`, `prev.json` | session_recap.py snapshot/diff | Recap diff |
| `session_tail.json` / `session-tail.md` | save (prose-written), verified at end | Compaction survival; no script consumer in the play loop (npc_rename + autosave read it incidentally) |
| `map-list.md`, `ambient-list.md` | prep step 4 | render_assets.py; host reads them |
| `tracker.html`, `assets.html` | render scripts | Host's browser only |
| `~/.claude/dnd/.name_registry.json` | name_registry.py | Name checks at new/npc/rename |
| `<runtime-dir>/active-campaign.json` | load step 5 | autosave_checkpoint.py |

---

## 5. Lifecycle — load → play → save → compaction

### `/dm:dnd load` (SKILL-commands.md:65-151)
1. Pick campaign (AskUserQuestion if unnamed) → roll_mode question.
2. `migrate_ruleset.py --check` (exit 1 → one-time 2014/2024 stamp prompt with backup).
3. `paths.py campaign-ruleset <name>` → stash; pass `--ruleset` to lookup/supplemental/mastery calls.
4. Read SKILL-scripts.md.
5. Write `active-campaign.json` (autosave hook marker). Read state.md (incl. **DM Style
   Notes** + **Campaign Arc**), world.md in full, npcs.md index, characters/*. **Not**
   loaded: world-nodes.md, arc.md, spine.json, source/, npcs-full.md, session-log.md —
   the lazy layer, each pulled on a specific trigger (see §4).
6. `campaign_graph.py scene-context` at current location. If `# graph not initialized` →
   mandatory init flow: legacy detection → full campaign dir backup → `graph init`
   (approval-gated seed) → validate → optional one-time Continuity Archive compression
   (legacy only).
7. In-character recap (mechanical half *should* come from `session_recap.py diff` per
   SKILL-commands.md:826 — but the load procedure itself never mentions it; see §7.3).
8. Active DM mode.

### Play (SKILL.md Active DM Mode)
- Stakes-gated checks; full "Ability (Skill)" naming; DC never stated; failure complicates
  (except puzzles).
- `roll_mode: players` → PC d20s called for and awaited (hard constraint: never auto-roll);
  `auto` → `dice.py` with shown math. NPC dice always DM-rolled. Initiative always
  `combat.py init`.
- Per-turn combat sequence (SKILL.md:288-303): action → dice → tracker.py (+ `effect tick`)
  → narration (NPC speech in blockquote blocks) → `render_tracker.py` refresh → persist
  HP/slots to sheets.
- Sound cues `🔊 **Cue:**` only from the campaign's ambient list; pronunciation hints on
  first use of hard names; tutor-mode blockquote last if enabled.
- NPC voicing gate: read the NPC's `npcs-full.md` entry first.
- **Micro-save (autosave on, default):** at every scene boundary + every several turns,
  silently flush: Live State Flags → state.md, new relationships → graph, recent beats →
  session tail. Optional Stop hook (`autosave_checkpoint.py`) prompts this on a turn
  cadence as backstop.
- **Compaction re-read ladder** (SKILL.md:213-221): Live State Flags → Current
  Situation/Recent Events → npcs-full entry → Continuity Archive → session-log; imported
  campaigns re-read `source/<id>.md`, never a compacted memory of it. One targeted Read
  per claim.

### `/dm:dnd save` (SKILL-commands.md:366-438)
session-log entry → state.md updates (party status + Inspiration, **Live State Flags**,
Faction Moves, **Deeds ledger** — every stance shift must cite a deed) → structured-arc
window sync into arc.md → **session tail** (`session_tail.json` + `session-tail.md`) →
log archival after session 3 (2 newest entries stay; older → archive with 3-5 bullet
Continuity Archive summaries, compressed against graph.json per the going-forward rule:
relational restatements dropped, mechanical/plot/atmospheric content kept) → **graph
sweep** (propose missed edges, y/pick/skip approval, `--since <session>`).

### `/dm:dnd end` (SKILL-commands.md:442-457)
save + Session Recap block → calibration question → `## DM Style Notes` update → World
State advance (threat stage, factions, date) → **dynamic-arc check**: beats landed? →
`arc advance`; **pre-emption check** — pressure delivered but consequence didn't land →
auto-trigger `arc revise` (cost / secondary-consequence / deferred landing paths) → tail
verification.

### Compaction survival model
Prose-side anchors written continuously (micro-save) + deterministic backstops:
Live State Flags (structured facts), session tail (final-stretch beats), Continuity
Archive (per-session bullets), graph.json (relational truth), tracker.json/calendar.json/
.recap (mechanical truth), and the re-read ladder that forces source reads over compacted
impressions. Weak points: the flags/tail are only as fresh as the last flush, and nothing
in the load path reads the tail files (see compass fragile-links register).

---

## 6. The four arc systems

| Type | Created by | Arc storage | Advanced by | Leveling |
|---|---|---|---|---|
| **sandbox** | `new` (declined arc) or completed-arc opt-out | `type: sandbox` stub in state.md | — | none (legacy `new` has no leveling path) |
| **dynamic** | `new` step 13 (Opus): theme/resolution + 3 acts × 2 beats (1a inciting, 1b complication, 2a midpoint shift, 2b all-is-lost, 3a confrontation, 3b resolution), consequence-shaped `what_changes` | Inline YAML in `state.md → ## Campaign Arc` | `/dm:dnd arc advance/revise/new` at `end`; pre-emption auto-revise; arc N+1 generation on completion | none (legacy) |
| **structured** | `import` (published module) | Pointer window in state.md (`current_chapter_detail` + `next_chapter`); full tree in `arc.md`; module text in lazy corpus `source/` | Chapter sync at `save`; `arc advance/revise` are no-ops | none (legacy) |
| **authored** | `prep` (the current flagship path) | `spine.json` = heavy source (situation/`level_up_to`/`gear`/`threats`/`secret`, schema-validated 6-8 beats, L1→~8); state.md carries a beats mirror + `current_beat` | `/dm:dnd beat complete`: spine status flip → state.md sync → milestone level-ups → gear | **milestone-only** — the only leveling path in this fork |

Steering behavior lives in SKILL.md: structured rules 1-7 (telegraph, world-pressure-not-
walls, beat marking, detour respect, hub-and-spoke, never show the arc, lazy chapter
pulls) and dynamic rules 1-9 (destination, consequences-not-events, pressure-before-beat,
mark-at-end, revise-don't-abandon, non-negotiable 2a, earned 2b, pre-emption→revision,
never show the arc). **Authored arcs reuse the dynamic steering rules** via the
dynamic-format mirror in state.md (template comment, state.md template:151-171) — there is
no authored-specific steering section in SKILL.md.

`/dm:dnd new` and `/dm:dnd import` are both marked **legacy** (no leveling); `prep` is
the intended path for new campaigns.

---

## 7. Prose↔script contract — verified drift points

Checked every script call named in the prose against the actual CLIs (2026-07-16):

1. **`paths.py` contradiction (real).** SKILL-commands.md:512 says "*`paths.py` is not a
   CLI; instead inline-read with `python3 -c ...`*" — but paths.py:199-211 implements a
   CLI (`campaign-ruleset`, `srd-path`, `runtime-dir`, `campaign-dir`), and load step 3
   (SKILL-commands.md:94) + step 5 (line 97) call it as one. The character-new workaround
   is stale; both paths work, but the prose contradicts itself.
2. **`tracker.py effect-start` (SKILL.md:44) — wrong syntax.** Actual:
   `tracker.py -c <camp> effect start <actor> <name> <dur>` (tracker.py:386-387). A model
   following SKILL.md verbatim gets an argparse error at the table mid-combat.
3. **Recap snapshot timing contradiction + unwired procedure.** SKILL-commands.md:823:
   "Take a snapshot at `/dm:dnd end`". SKILL-scripts.md:210-213: "Run this at session
   START (e.g. `/dm:dnd load`)". Worse: neither the `/dm:dnd load` procedure (65-151) nor
   `/dm:dnd end` (442-457) actually contains a snapshot or diff step — the whole
   `session_recap` loop exists only in its own reference section, so it plausibly never
   runs. ("Inject this line at /dm:dnd load" — SKILL-commands.md:826 — has no anchor in
   the load steps.)
4. **Duplicate `/dm:dnd recap` definition.** SKILL-commands.md:685 (read session-log,
   narrate 3-5 sentences) vs SKILL-commands.md:818 (deterministic state-diff subcommands
   `recap snapshot` / `recap diff`). Same command name, two semantics, ~130 lines apart.
5. **`supersede-edge` undocumented.** campaign_graph.py:804 implements it; the
   `/dm:dnd graph` section doesn't list it.
6. **Verified consistent:** `dice.py` flags; `combat.py init/tracker/attack/--mastery/
   mastery`; `tracker.py` subcommands (in SKILL-scripts.md); `calendar.py`; `lookup.py
   --ruleset/--campaign`; `migrate_ruleset.py` exit codes 0/1/2; `name_registry.py check`
   exit semantics; `milestone.py --sheet/--level/--clear`; `bestiary.py --level`;
   `schema.py --bible`; `premise.py --tone/--seed`; `corpus_check.py --campaign`;
   `render_assets.py`/`render_tracker.py` flags; `session_recap.py` subcommands;
   `oracle.py` subcommands; autosave hook pair; tones list in `new` step 6 ==
   `data/tones.yaml` ids.
7. **Model routing table staleness (SKILL.md:181-186):** pins `claude-sonnet-4-6` /
   `claude-opus-4-6` as tiers. Model ids drift; worth a policy ("latest sonnet/opus")
   rather than pins. Also routing is aspirational — nothing enforces it.
8. **`xp.py` tension (minor, documented):** deprecated banner is present everywhere, but
   `/dm:dnd level up` still opens with the XP-gate table (SKILL-commands.md:567-582) and
   `character.py xp` remains advertised (SKILL-scripts.md:104). Consistent for legacy
   campaigns; a fresh reader can mis-take the XP gate as live.

Items 1-5 are candidate fixes for the owner (propose-only per review ground rules);
Sessions C-E should treat them as known background, not re-derive them.

---

## 8. Test surface

`tests/` (24 files, 236 green per last merge): prep pipeline is heavily covered
(schema/bestiary/premise/milestone/lifecycle/CLI-subprocess/prose-content guards), plus
graph, oracle, recap, renderers, corpus, dice `--attack`, import columns, tones catalog,
verb table, autosave checkpoint, and two **prose-guard tests** (`test_no_display_refs.py`
banning the removed display stack; `test_prep_skill_prose.py` DMVoiceTests asserting
SKILL.md content). Prose-guard tests are the only automated check on the primary artifact
— everything else about DM behavior is testable only by probes
(`docs/probes/2026-07-14-prep-dry-run.md` is the model: it caught a real
`ModuleNotFoundError` in `schema.py` that unit tests masked).
