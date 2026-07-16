# D&D Skill — Scripts Reference

Full syntax for all Python helper scripts. Load this file once at `/dm:dnd load`, then it stays in context for the session.

> **Path note:** commands below use `${CLAUDE_SKILL_DIR}` for the skill directory. This file is read verbatim, so that token is **not** auto-expanded here — substitute the absolute skill-dir path (from `SKILL.md`) before running any command, or it will fail with a broken `/scripts/…` path.

---

## Dice Script — `scripts/dice.py`

**MANDATORY.** Every die roll you resolve — NPC attacks, saves, damage, ability score gen, and PC rolls under `roll_mode: auto` — must be produced by invoking this script via Bash. **Never sample dice mentally or with inline `random` calls.** (Under `roll_mode: players`, PC d20s are not rolled at all — the player states their result; see SKILL.md "Dice convention".)

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/dice.py d20+5
python3 ${CLAUDE_SKILL_DIR}/scripts/dice.py 2d6+3
python3 ${CLAUDE_SKILL_DIR}/scripts/dice.py 4d6kh3        # ability score roll
python3 ${CLAUDE_SKILL_DIR}/scripts/dice.py d20 adv       # advantage
python3 ${CLAUDE_SKILL_DIR}/scripts/dice.py d20+3 dis     # disadvantage + modifier
python3 ${CLAUDE_SKILL_DIR}/scripts/dice.py d20 --silent  # returns integer only
python3 ${CLAUDE_SKILL_DIR}/scripts/dice.py d20+6 --attack # attack roll: crit/fumble on nat 20/1

# Pass --label to annotate what the roll is for:
python3 ${CLAUDE_SKILL_DIR}/scripts/dice.py d20+4 --label "Perception check"
python3 ${CLAUDE_SKILL_DIR}/scripts/dice.py d20+6 adv --attack --label "Attack — Goblin Boss vs Piper"
python3 ${CLAUDE_SKILL_DIR}/scripts/dice.py 2d8+3 --label "Greataxe damage"
```

A nat 20/1 auto-hits/misses and crits **only on attack rolls**. Pass `--attack` to flag nat 20 as CRITICAL HIT and nat 1 as FUMBLE. A bare d20 is treated as a check or save — it prints a neutral `(nat 20)` / `(nat 1)` note, no crit claim (RAW: nat 20/1 are not auto-success/fail on checks and saves). Most attacks resolve through `combat.py`, which already applies this — reach for `dice.py --attack` only for an ad-hoc attack rolled outside the combat tracker.

---

## Ability Scores Script — `scripts/ability-scores.py`
```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/ability-scores.py roll
python3 ${CLAUDE_SKILL_DIR}/scripts/ability-scores.py pointbuy
python3 ${CLAUDE_SKILL_DIR}/scripts/ability-scores.py pointbuy --check STR=15 DEX=10 CON=15 INT=8 WIS=11 CHA=12
python3 ${CLAUDE_SKILL_DIR}/scripts/ability-scores.py modifiers STR=15 DEX=10 CON=15 INT=8 WIS=11 CHA=12
```
Roll mode: generates 3 arrays (4d6kh3 × 6 each). Point buy mode: prints cost table; `--check` validates against the 27-point budget.

---

## XP Script — `scripts/xp.py`
> **Deprecated under milestone leveling.** This fork does not award XP; leveling is milestone-only (`/dm:dnd beat complete`). `xp.py` is retained only for legacy campaigns and is not part of the live flow.

Awards XP for combat and qualifying non-combat encounters. Reads character files from the campaign directory and updates XP. All tables (difficulty thresholds, CR→XP, monster multipliers, level advancement) are codified in the script — the DM only decides the difficulty tier or provides a monster list.

```bash
# Preview — no files modified:
python3 ${CLAUDE_SKILL_DIR}/scripts/xp.py calc --level 3 --players 2 --difficulty hard --type combat
python3 ${CLAUDE_SKILL_DIR}/scripts/xp.py calc --level 3 --players 2 --monsters "goblin:1/4:3,hobgoblin:1:1"

# Award after a combat encounter — difficulty-rated (use when full monster list is unavailable):
python3 ${CLAUDE_SKILL_DIR}/scripts/xp.py award \
  --campaign <name> --characters "Max of Thraxx,Ethros the 19th" --difficulty hard --type combat

# Award after a combat encounter — exact CR calculation (preferred for standard combats):
python3 ${CLAUDE_SKILL_DIR}/scripts/xp.py award \
  --campaign <name> --characters "Max of Thraxx,Ethros the 19th" \
  --monsters "goblin:1/4:3,hobgoblin:1:1" --note "Ambush in the alley"

# Award for a qualifying non-combat encounter:
python3 ${CLAUDE_SKILL_DIR}/scripts/xp.py award \
  --campaign <name> --characters "Max of Thraxx,Ethros the 19th" --difficulty medium --type noncombat \
  --note "guild informant interrogation"
```

**Difficulty tiers:** `easy` `medium` `hard` `deadly`
**Encounter types:** `combat` `noncombat` (both use the same difficulty threshold table)
**Monster CR formats:** `1/4`, `0.25`, `1/2`, `0.5`, `1/8`, `0.125`, or integer (`1`, `5`, `10`)
**Monster count:** omit for 1 (e.g. `"dragon:10"`); explicit for groups (e.g. `"goblin:1/4:3"`)
**Monster multiplier** (applied automatically): ×1 (1), ×1.5 (2), ×2 (3–6), ×2.5 (7–10), ×3 (11–14), ×4 (15+)

`award` updates the character file XP field and flags LEVEL UP PENDING if a threshold is crossed. The `--note` label prints to terminal only — not stored.

---

## Combat Script — `scripts/combat.py`
```bash
# Roll initiative and print tracker
python3 ${CLAUDE_SKILL_DIR}/scripts/combat.py init '<JSON>'
# JSON: [{"name":"Flerb","dex_mod":0,"hp":12,"ac":16,"type":"pc"}, ...]

# Reprint tracker from saved state
python3 ${CLAUDE_SKILL_DIR}/scripts/combat.py tracker '<JSON>' <round_num>

# Resolve a single attack
python3 ${CLAUDE_SKILL_DIR}/scripts/combat.py attack --atk 4 --ac 15 --dmg 2d6+2
```
`init` outputs `STATE_JSON:` line — store in `state.md` under `## Active Combat` between turns.

---

## Character Script — `scripts/character.py`
```bash
# Full stat block from raw scores
python3 ${CLAUDE_SKILL_DIR}/scripts/character.py calc --class fighter --level 1 \
    STR=15 DEX=10 CON=15 INT=9 WIS=11 CHA=14 \
    --proficient STR CON Athletics Intimidation Perception Survival

# Level-up HP and bonus calculation
python3 ${CLAUDE_SKILL_DIR}/scripts/character.py levelup --class fighter --from 1 --hp-roll 7 --con-mod 2

# XP tracking
python3 ${CLAUDE_SKILL_DIR}/scripts/character.py xp --level 1 --gained 150
```

---

## Tracker Script — `scripts/tracker.py`
Tracks conditions, concentration, timed effects, and death saves. State persists at `~/.claude/dnd/campaigns/<name>/tracker.json`.

```bash
CAMP=my-campaign

# Timed effects — duration: 10r (rounds), 60m (minutes), 8h (hours), indef
# Append 'conc' to mark as concentration (auto-sets concentration field)
python3 ${CLAUDE_SKILL_DIR}/scripts/tracker.py -c $CAMP effect start "Max of Thraxx" "Web" 10r conc
python3 ${CLAUDE_SKILL_DIR}/scripts/tracker.py -c $CAMP effect start "Ethros the 19th" "Disguise Self" 1h
python3 ${CLAUDE_SKILL_DIR}/scripts/tracker.py -c $CAMP effect start "Ethros the 19th" "Hunter's Mark" indef
python3 ${CLAUDE_SKILL_DIR}/scripts/tracker.py -c $CAMP effect end   "Max of Thraxx" "Web"   # narrative end (broken/dispelled)
python3 ${CLAUDE_SKILL_DIR}/scripts/tracker.py -c $CAMP effect tick  "Max of Thraxx"         # call on actor's turn — decrements rounds, prints expiry

# Conditions
python3 ${CLAUDE_SKILL_DIR}/scripts/tracker.py -c $CAMP condition add "Ethros the 19th" poisoned
python3 ${CLAUDE_SKILL_DIR}/scripts/tracker.py -c $CAMP condition remove "Ethros the 19th" poisoned
python3 ${CLAUDE_SKILL_DIR}/scripts/tracker.py -c $CAMP condition clear "Ethros the 19th"

# Concentration (auto-clears previous if switching spells)
python3 ${CLAUDE_SKILL_DIR}/scripts/tracker.py -c $CAMP concentrate "Max of Thraxx" "Bless"
python3 ${CLAUDE_SKILL_DIR}/scripts/tracker.py -c $CAMP concentrate "Max of Thraxx" break

# Death saves
python3 ${CLAUDE_SKILL_DIR}/scripts/tracker.py -c $CAMP saves "Ethros the 19th" success
python3 ${CLAUDE_SKILL_DIR}/scripts/tracker.py -c $CAMP saves "Ethros the 19th" failure
python3 ${CLAUDE_SKILL_DIR}/scripts/tracker.py -c $CAMP saves "Ethros the 19th" stable
python3 ${CLAUDE_SKILL_DIR}/scripts/tracker.py -c $CAMP saves "Ethros the 19th" reset

# Status / clear
python3 ${CLAUDE_SKILL_DIR}/scripts/tracker.py -c $CAMP status
python3 ${CLAUDE_SKILL_DIR}/scripts/tracker.py -c $CAMP status "Ethros the 19th"
python3 ${CLAUDE_SKILL_DIR}/scripts/tracker.py -c $CAMP clear           # conditions + concentration + effects
python3 ${CLAUDE_SKILL_DIR}/scripts/tracker.py -c $CAMP clear --all     # also clears death saves
```

**When to run:** condition applied/removed; caster begins/loses concentration (immediately, not end of turn); PC drops to 0 HP; each death save rolled; end of encounter → `clear`.

---

## Calendar Script — `scripts/calendar.py`
```bash
# One-time setup (run during /dm:dnd new):
python3 ${CLAUDE_SKILL_DIR}/scripts/calendar.py -c $CAMP init \
    --date "15 Harvestmoon 1247" \
    --time "morning" \
    --months "Frostfall,Deepwinter,Thawmonth,Seedtime,Bloomtide,Highsun,Harvestmoon,Duskfall" \
    --month-length 30 \
    --day-names "Sunday,Moonday,Ironday,Windday,Earthday,Fireday,Starday"

# Time advancement
python3 ${CLAUDE_SKILL_DIR}/scripts/calendar.py -c $CAMP advance 8 hours
python3 ${CLAUDE_SKILL_DIR}/scripts/calendar.py -c $CAMP advance 2 days
python3 ${CLAUDE_SKILL_DIR}/scripts/calendar.py -c $CAMP rest short   # +1 hour
python3 ${CLAUDE_SKILL_DIR}/scripts/calendar.py -c $CAMP rest long    # +8 hours

# Query / manual set
python3 ${CLAUDE_SKILL_DIR}/scripts/calendar.py -c $CAMP now
python3 ${CLAUDE_SKILL_DIR}/scripts/calendar.py -c $CAMP set "22 Harvestmoon 1247" evening
python3 ${CLAUDE_SKILL_DIR}/scripts/calendar.py -c $CAMP time night
python3 ${CLAUDE_SKILL_DIR}/scripts/calendar.py -c $CAMP events
```

**When to run:** after every rest; after significant travel or time skip; when manually updating `state.md` date — use `calendar.py set` to keep them in sync.

---

## Campaign Search — `scripts/campaign_search.py`
Keyword search across campaign files. Use this **before** loading full files into context when looking up a specific past event, NPC detail, or plot thread.

```bash
CAMP=my-campaign

# Search all default files (state, log, archive, world, npcs):
python3 ${CLAUDE_SKILL_DIR}/scripts/campaign_search.py -c $CAMP Lasswater

# Narrow to specific files:
python3 ${CLAUDE_SKILL_DIR}/scripts/campaign_search.py -c $CAMP "merchant letter" --files log,archive

# Multi-keyword AND search:
python3 ${CLAUDE_SKILL_DIR}/scripts/campaign_search.py -c $CAMP VARETH Kel

# More context lines around each match:
python3 ${CLAUDE_SKILL_DIR}/scripts/campaign_search.py -c $CAMP Harwick -C 6
```

File keys: `state`, `log`, `archive`, `world`, `seeds`, `npcs`, `npcsfull`
Default files searched: state, log, archive, world, npcs

**When to use:** Any time a player asks about a past event, NPC detail, location, or plot thread that may not be in active context. Run this first — only escalate to a full `Read` if the search returns insufficient context.

---

## Session Recap — `scripts/session_recap.py`

Deterministic state-diff between two character snapshots. Computes the mechanical change set (HP/temp/level/hit dice/death saves/conditions/concentration/exhaustion/inspiration/spell slots) from data so narration never recomputes it — recaps are the single thing an LLM is most likely to hallucinate. Reads `<campaign>/characters/*.md` and merges live `tracker.json` conditions/concentration. Zero LLM calls.

```bash
CAMP=my-campaign

# Snapshot the party now — sets the baseline (writes to <campaign>/.recap/,
# rolling last → prev). Run this at session START (e.g. /dm:dnd load) so there
# is a baseline to diff against later.
python3 ${CLAUDE_SKILL_DIR}/scripts/session_recap.py snapshot --campaign $CAMP

# Diff the baseline against current state → one-paragraph summary, then ADVANCE
# the baseline to "now" so the next diff chains from here. Run at /dm:dnd save
# (end of session) for a since-start recap, or each turn for a since-last-turn
# recap — either way it advances, so consecutive diffs never re-report old deltas.
python3 ${CLAUDE_SKILL_DIR}/scripts/session_recap.py diff --campaign $CAMP
# → "Aldric: took 18 damage (30→12 HP); gained Poisoned; spent 2 level 1 slots."

# Same comparison without moving the baseline (ad-hoc "what changed so far?"):
python3 ${CLAUDE_SKILL_DIR}/scripts/session_recap.py diff --campaign $CAMP --no-roll

# Structured change list instead of prose:
python3 ${CLAUDE_SKILL_DIR}/scripts/session_recap.py diff --campaign $CAMP --json

# Diff two snapshot files directly (no campaign lookup):
python3 ${CLAUDE_SKILL_DIR}/scripts/session_recap.py diff-files before.json after.json
```

---

## Oracle — `scripts/oracle.py`

Dice-driven solo/improv oracles (Mythic chaos factor, Ironsworn yes/no, Random Event Focus, scene-meaning word pairs). Keeps pacing transparent and rollable instead of invented. Rolls are stdlib-random and seedable (`--seed N`). The chaos factor persists in `state.md → ## Session Flags` as `chaos_factor: N`. Zero LLM calls.

```bash
CAMP=my-campaign

# Chaos factor (1-9): show / set / adjust (persisted to state.md)
python3 ${CLAUDE_SKILL_DIR}/scripts/oracle.py chaos --campaign $CAMP
python3 ${CLAUDE_SKILL_DIR}/scripts/oracle.py chaos set --campaign $CAMP --value 7
python3 ${CLAUDE_SKILL_DIR}/scripts/oracle.py chaos adjust --campaign $CAMP --pc-lost

# Yes/no oracle — likelihood + chaos modifier → verdict + d100
python3 ${CLAUDE_SKILL_DIR}/scripts/oracle.py ask --likelihood likely --campaign $CAMP
# → "NO-BUT  (d100=82, likelihood=likely, chaos=8)"

# Random Event Focus (d100 → direction label)
python3 ${CLAUDE_SKILL_DIR}/scripts/oracle.py event

# Scene-meaning word pair (action / subject)
python3 ${CLAUDE_SKILL_DIR}/scripts/oracle.py scene
```

Likelihoods: `sure-thing`, `likely`, `50/50`, `unlikely`, `no-way`. Verdict suffixes: `-and` (extreme, on doubles), `-but` (qualified, near threshold).

---

## Deterministic Graph Extraction — `scripts/graph_extract_deterministic.py`

Zero-LLM relationship extractor. Pattern-matches session-log sentences against the bundled verb-table seed (`data/graph/verb_table_seed.yaml`) and emits typed edge proposals in the exact shape `campaign_graph.py` consumes. ~50% recall (clean subject-verb-object only), ~95% precision, no Claude API call. Usually driven through `campaign_graph.py extract --deterministic` rather than directly:

```bash
CAMP=my-campaign

# Propose edges (stdout), no writes:
python3 ${CLAUDE_SKILL_DIR}/scripts/campaign_graph.py extract --campaign $CAMP --deterministic

# One-shot auto-apply high-confidence proposals into graph.json (idempotent):
python3 ${CLAUDE_SKILL_DIR}/scripts/campaign_graph.py extract --campaign $CAMP \
    --deterministic --apply --min-confidence high
```

---

## Data Commands — `scripts/sync_srd.py`, `scripts/build_srd.py`, and `scripts/lookup.py`

Dataset is bundled at `${CLAUDE_SKILL_DIR}/data/dnd5e_srd.json`. No runtime download required.

```bash
# Check / rebuild dataset (only needed when upstream sources update):
python3 ${CLAUDE_SKILL_DIR}/scripts/sync_srd.py             # rebuild if 5e-bits or FoundryVTT has new commits
python3 ${CLAUDE_SKILL_DIR}/scripts/sync_srd.py --check     # check upstream SHAs, don't rebuild
python3 ${CLAUDE_SKILL_DIR}/scripts/sync_srd.py --force     # always rebuild
python3 ${CLAUDE_SKILL_DIR}/scripts/build_srd.py --status   # show current dataset metadata

# Lookup during play (CLI):
python3 ${CLAUDE_SKILL_DIR}/scripts/lookup.py spell "fireball"
python3 ${CLAUDE_SKILL_DIR}/scripts/lookup.py item "cloak of protection"
python3 ${CLAUDE_SKILL_DIR}/scripts/lookup.py feature "sneak attack"
python3 ${CLAUDE_SKILL_DIR}/scripts/lookup.py condition "poisoned"
python3 ${CLAUDE_SKILL_DIR}/scripts/lookup.py monster "goblin"
python3 ${CLAUDE_SKILL_DIR}/scripts/lookup.py monster "dragon" --all   # all fuzzy matches

# Programmatic:
from lookup import lookup, lookup_record, lookup_with_level
lookup("fireball", category="spell")                  # → formatted string
lookup_with_level("sneak attack", category="feature", level=3)  # → level-resolved string
```

**When to use:** combat (monster stat blocks before using them); spellcasting (range, components, duration, at-higher-levels); conditions (rule text before applying); loot and equipment; NPC generation (monster stat block as mechanical base).

---

## Continuity Autosave — `scripts/autosave_checkpoint.py`, `scripts/install_autosave_hook.py`

Behind-the-scenes continuity checkpoint for long sessions, so a context compaction never loses the player's place. Two layers; see the *Continuity micro-save* rule in SKILL.md and the `/dm:dnd autosave` command.

```bash
# Opt-in: register the Stop hook (writes ~/.claude/settings.json, idempotent)
python3 ${CLAUDE_SKILL_DIR}/scripts/install_autosave_hook.py
python3 ${CLAUDE_SKILL_DIR}/scripts/install_autosave_hook.py --uninstall
python3 ${CLAUDE_SKILL_DIR}/scripts/install_autosave_hook.py --status

# The hook target (also runnable by hand to force a snapshot or inspect state)
python3 ${CLAUDE_SKILL_DIR}/scripts/autosave_checkpoint.py --status
python3 ${CLAUDE_SKILL_DIR}/scripts/autosave_checkpoint.py --campaign <name> --snapshot-only
```

`autosave_checkpoint.py` runs as a Claude Code **Stop hook** (after each turn). It reads the active campaign from `<runtime-dir>/active-campaign.json` (written at `/dm:dnd load`) and the `autosave` flag from that campaign's `state.md`. It **no-ops** when no campaign is active (e.g. a non-D&D session), when `autosave: off`, or when already inside a hook-driven continuation. Every turn it snapshots `state.md` to the runtime dir; every N turns (default 10, `DND_AUTOSAVE_EVERY` to override) it emits a Stop-hook `block` decision that prompts the DM to flush continuity before yielding. The hook is **opt-in** — the in-model micro-save cadence works without it.

**When to use:** offer `install_autosave_hook.py` to players running long imported modules who hit compaction mid-session. The flag toggle (`/dm:dnd autosave on|off`) is the in-session control.

## Lazy Corpus — `scripts/corpus_check.py`

Imported (structured) campaigns keep the full module text as a lazily-loaded reference layer instead of inlining it. Layout:

```
<campaign>/
  world.md           # load-time core (Foundations, Three Truths, factions)
  world-nodes.md     # lazy: full Quest Seed Bank + Adventure Nodes (per-act read)
  arc.md             # lazy: full act/chapter tree (state.md holds current+next only)
  source-index.md    # chapter-id -> source file -> one-line scope
  source/<id>.md     # lazy: one file per chapter, the module's source text
```

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/corpus_check.py --campaign <name>
```

Validates that every chapter id in `source-index.md` has a matching `source/<id>.md` (and vice-versa) and that `arc.md` exists. Run it at the end of `/dm:dnd import`. A campaign with no `source/` layer (dynamic, sandbox, or a pre-v2.2.0 import) is reported as a clean no-op — nothing to validate, and its load path is unchanged.

---

## Combat-Tracker Render — `scripts/render_tracker.py`

Writes the host-side `tracker.html` (DM dashboard) from the live combat state. Call it at
the end of **each combat turn**, passing the same combatant `STATE_JSON` you pipe through
`combat.py`, ordered so the current actor is first (it becomes the highlighted active row).
Merges persisted conditions/concentration/death-saves from `tracker.json` and shows each
condition's SRD effect inline. The file carries a meta-refresh so the browser tab reloads
itself. No server.

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/render_tracker.py \
  --campaign <name> --state '<STATE_JSON from combat.py>' --round <n>
```

Out of combat, do not call it — leave the last tracker in place.

## Asset-Hub Render — `scripts/render_assets.py`

Writes the host-side `assets.html` (maps + ambient loops) from the prep shopping lists in
the campaign dir (`map-list.md`, `ambient-list.md`). Run once at the end of prep, and again
any time the host adds or renames sound/map files. Controls are pre-wired to the canonical
filenames; an ambient toggle whose file is not yet in `sounds/` simply plays nothing until
the file exists. This file is **static** — it carries no meta-refresh, so a combat-tracker
regen never interrupts a playing ambient loop.

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/render_assets.py --campaign <name>
```

## Premise Script — `scripts/prep/premise.py`

`python3 ${CLAUDE_SKILL_DIR}/scripts/prep/premise.py [--tone <id>] [--seed N]`
Rolls one entry from each of four orthogonal axes (setting × conflict × antagonist ×
twist) from `data/premise-seeds.yaml`, colored by a tone from `data/tones.yaml` (omit
`--tone` to roll one). Prints a labeled scaffold for the DM to reconcile into a coherent
premise. Used by `/dm:dnd prep` step 0.5 when premise is blank; also runnable standalone
to re-roll. `--seed` makes the roll reproducible.
