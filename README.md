# Unofficial D&D Claude Dungeon Master
> **Ruleset:** D&D 5e — **2014 (SRD 5.1)** by default; **2024 (SRD 5.2)** opt-in per campaign. Choose at `/dm:dnd new` time; legacy campaigns are auto-prompted to migrate (with backup) on first load. See the [Ruleset section](#ruleset) for mechanic differences and dataset details.

> Claude runs the game. You play.

An unofficial D&D 5e Dungeon Master skill for [Claude Code](https://claude.ai/code) — persistent campaigns, full 5e mechanics, and a terminal-native DM that rolls dice, voices NPCs, tracks state, and runs combat entirely in the chat.

Built for solo and small-table play driven from the terminal.

---

## What This Is

You run `/dm:dnd load my-campaign` in Claude Code. Claude becomes your DM — rolling dice, voicing NPCs, tracking HP and conditions, and running combat. Narration, NPC dialogue, and dice math all render as structured chat prose: NPC speech in its own visually distinct block, hidden rolls resolved silently, stat changes persisted to plain markdown files.

There are two ways to play, and they serve different needs:

**Improvised campaigns** — Claude generates the world from scratch and auto-creates a committed three-act narrative arc from the setting, factions, and threats it just built. The arc gives the story a defined shape without scripting what happens — beats are defined by consequence ("what changes") not by event, so Claude stays flexible on how each beat lands while committing to the fact that it must. The arc advances across sessions, can be revised when players redirect the story, and continues into a new arc when all six beats resolve. This is Claude as a full creative collaborator: world-builder, improv partner, and story architect in one.

**Structured campaigns** — Use `/dm:dnd import` to drop in a pre-written source (official WotC modules, published third-party campaigns, or a custom DM-written document in PDF, markdown, DOCX, or plain text format). Claude reads and chunks the source, extracts the structure type (linear, hub-and-spoke, or faction-web), and builds all campaign files automatically — acts, chapters, key story beats, telegraph scenes, NPCs, factions, locations, and quest hooks. The campaign runs with enforced deterministic structure: required beats must land in each chapter, Claude telegraphs before delivering them, and steers with world pressure rather than walls when players drift. Drop in the Lost Mine of Phandelver and Claude will run it chapter by chapter with the same twelve DM standards applied to every scene.

Both modes share the same DM engine. The [twelve applied behavioral standards](https://github.com/neuralinitiative/claude-dnd-skill/blob/main/SKILL.md#what-makes-a-great-dm--applied-standards) are enforced as hard constraints in every session regardless of which mode you're in — improvised or structured, the DM improvises within situations, lets choices matter, makes every NPC a person, and controls pace deliberately.

It also manages a deep web of campaign data without overloading the LLM — coherent and complete, without burning tokens on context that isn't needed yet:

- **DM instructions** — split across three files with staggered load timing; core rules always in the system prompt, script syntax and command procedures loaded once at session start
- **Campaign data** — NPC roster indexed at load, full entries pulled only when a character becomes relevant; quest hooks and worldbuilding text in cold storage until called for
- **Imported modules** — a published book is kept as a lazily-loaded corpus, not inlined: the act/chapter tree, quest/location bank, and per-chapter source text load on demand, so a long module runs chapter by chapter without sitting whole in context
- **Session history** — archived as continuity summaries, not raw transcripts; full campaign history available for reference without front-loading token weight
- **Compaction resilience** — a compact Live State Flags block in `state.md` anchors faction stances, player cover, and NPC dispositions; re-read at any claim to keep world continuity grounded in source files rather than Claude's increasingly lossy impression of them
- **Autosave** — continuity (state flags, relationship graph, session tail) is checkpointed behind the scenes at scene boundaries and on a turn cadence, so a context compaction never loses your place; toggle with `/dm:dnd autosave on|off`, with an optional Stop hook for a deterministic per-turn backstop

A campaign can run dozens of sessions deep — with coherent recall of past events, NPC attitudes, and long-tail consequences — without the context bloat that forces other implementations to summarize, forget, or reset.

It is not an official Wizards of the Coast product. It uses Claude as the DM engine. It takes the rules seriously and the storytelling even more seriously.

---

## Using a different LLM?

This skill is built specifically for Claude Code. If you want to run the same framework on a different model — local inference, OpenRouter, or any OpenAI-compatible endpoint — check out [open-tabletop-gm](https://github.com/neuralinitiative/open-tabletop-gm), the model-agnostic version extracted from this repo. It trades some Claude-specific integration depth for broader model support and includes a probe tool for benchmarking narration quality across models.

If you'd rather skip the install entirely and play in a browser, [neuralinitiative.ai](https://neuralinitiative.ai) is the hosted version — same design DNA, sign in with Google, top up an account balance, play. Trades self-hosting (and lower per-session cost) for zero setup and a more refined GUI.

If you're on Claude Code, you're in the right place.

---

## Features

- **Persistent campaigns** — state, NPCs, quests, and characters survive across sessions in plain markdown files
- **Two campaign modes** — improvised (Claude generates world + dynamic arc) or structured (import pre-written material and enforce its beats)
- **Dynamic narrative arc** — auto-generated at `/dm:dnd new` from the world's threat, factions, and setting; three acts, six beats defined by consequence not event; arc tracked across sessions, revised when players redirect the story, continued into a new arc when complete
- **Campaign relationship graph** — typed-edge graph alongside the markdown campaign files, with verbatim source-anchors on every edge; `scene-context` query auto-pulled at `/dm:dnd load` to surface who-knows-whom in the current scene without re-reading full NPC files; designed to hold long-session continuity when context compaction strips files out of scope. Background research and the A/B replay study that motivated it: [`docs/research/graph/`](docs/research/graph/)
- **Campaign import** — `/dm:dnd import` accepts PDF, markdown, DOCX, or plain text; extracts structure type, acts, chapters, key beats, telegraph scenes, NPCs, factions, and quest hooks; builds all campaign files automatically and keeps the full source as a lazily-loaded corpus so even a long module loads chapter by chapter
- **Portable characters** — bring your character into any campaign; level up, grow your stat tree, and carry your inventory and loot — or start fresh each time
- **Full D&D 5e mechanics** — initiative, attacks, saving throws, spell slots, milestone levelling, short/long rests
- **Atmospheric DM** — dark fantasy tone, distinct NPC voices, hidden rolls, a world that reacts to choices
- **Enforced roll handling** — choose at game start whether players roll their own d20s (DM calls for the roll and waits for the stated result) or the DM rolls openly; the DM never silently auto-rolls a PC
- **SRD spell/feature lookup** — bundled 5e dataset with supplemental entries for non-SRD content (Xanathar's, Tasha's, subclass features); `lookup.py` resolves descriptions locally, with a wikidot fallback for anything not in the local data
- **Tutor / learning mode** — enable per-session for automatic hint blocks after every scene, decision point, and roll; ideal for players new to D&D
- **Combat tracker** — auto-rolled initiative, turn order, conditions and concentration tracked per-campaign, inline dice math
- **Helper scripts** — dice rolling, ability scores, combat, character stat derivation, conditions/tracker, calendar, SRD data sync, SRD lookup, supplemental data builder

---

## How It Works

```
Claude Code CLI  ──→  /dm:dnd commands  ──→  campaign files (~/.claude/dnd/)
                                              state.md · world.md · npcs.md
                                              session-log.md · characters/
```

Everything happens in the terminal: Claude narrates in chat, resolves rolls through the bundled scripts, and persists all state to plain files under the data root. No servers, no browser, no extra devices.

---

## Prerequisites

- [Claude Code](https://claude.ai/code) CLI installed
- Python 3.10+
- `pip3 install pymupdf` (campaign import from PDF — column-aware extraction so multi-column modules segment into chapters correctly; falls back to poppler's `pdftotext` if absent)

---

## Installation

Install it as a Claude Code plugin:

```
/plugin marketplace add neuralinitiative/claude-dnd-skill
/plugin install dm@neural-initiative
```

Then invoke it as **`/dm:dnd`** (plugin skills are namespaced `plugin:skill` — the `dm` plugin provides the `dnd` skill), or just describe what you want once a campaign is loaded. Update with `/plugin update dm`.

> **Upgrading from a v1 standalone install?** As of v2.0.0 the skill is
> plugin-only — the old `~/.claude/skills/dnd` standalone (`/dnd`) is replaced by
> the plugin (`/dm:dnd`). **Your campaigns and characters are untouched** — they
> live under `~/.claude/dnd/` (or `$DND_CAMPAIGN_ROOT`), entirely separate from
> the skill code. Install the plugin above, then optionally run the one-time
> helper to retire the old install:
> `python3 <plugin>/skills/dnd/scripts/migrate_v1_to_v2.py`. Full guide:
> **[MIGRATING.md](MIGRATING.md)**.

---

## Versioning & updates

The skill tracks releases via a top-level `VERSION` file and per-release notes in [`CHANGELOG.md`](CHANGELOG.md). The current version is in `VERSION`; significant changes — new commands, new mechanics, behavior changes — get a CHANGELOG entry.

**To check for updates:**

```bash
/dm:dnd update --check    # shows local vs. remote version + commit diff, no pull
/dm:dnd update            # pulls if you're behind (fast-forward only; refuses on dirty tree)
```

**Plugin installs update through the plugin manager** — run `/plugin update dm` instead. `/dm:dnd update` detects a plugin install and points you there rather than git-pulling under the manager's tracked state.

The `--check` output includes both sides' version strings so you can see at a glance whether you've fallen behind. After updating, restart Claude Code so the new `SKILL.md` and command procedures load.

The skill follows [semantic versioning](https://semver.org/): `MAJOR.MINOR.PATCH`. Breaking changes that require campaign-data migration bump MAJOR; new opt-in features bump MINOR; bug fixes bump PATCH. Active campaigns continue to work across MINOR/PATCH bumps without action.

---

## Quick Start

**Improvised campaign** — Claude builds the world and generates a narrative arc:

```
/dm:dnd new my-campaign         # generates world seed, factions, NPCs, dynamic story arc
/dm:dnd character new           # create a character
/dm:dnd load my-campaign        # start a session
```

**Structured campaign** — import a pre-written or published module:

```
/dm:dnd import my-campaign path/to/module.pdf   # extract structure and build campaign files
/dm:dnd load my-campaign                        # start a session — Claude enforces the arc
```

Once loaded, type naturally — no `/dm:dnd` prefix needed. The DM interprets everything as in-game action.

---

## Campaign Commands

| Command | Description |
|---------|-------------|
| `/dm:dnd new <name>` | Create a new campaign — generates world seed, NPCs, starting location, and dynamic narrative arc |
| `/dm:dnd import <name> <source>` | Import a pre-written campaign from PDF, markdown, DOCX, or plain text; extracts structure and builds all campaign files |
| `/dm:dnd load <name>` | Load an existing campaign and enter DM mode |
| `/dm:dnd save` | Write session events to log, update state and character files |
| `/dm:dnd end` | Save session, append recap, close out the session |
| `/dm:dnd abandon` | Exit without saving — discards all unsaved changes from this session |
| `/dm:dnd list` | List all campaigns with last session date and count |
| `/dm:dnd recap` | In-character 3–5 sentence recap of the last session |
| `/dm:dnd world` | Display world lore |
| `/dm:dnd quests` | Show active quests and open threads |
| `/dm:dnd arc status` | Show the current narrative arc, completed beats, and steering notes |
| `/dm:dnd arc advance <beat>` | Mark a beat complete and update arc tracking (dynamic arcs only) |
| `/dm:dnd arc revise` | Revise outstanding beats when a player choice significantly redirects the story |
| `/dm:dnd arc new` | Generate a new arc from the consequences of a completed one |
| `/dm:dnd tutor on` | Enable tutor / learning mode for this session |
| `/dm:dnd tutor off` | Disable tutor / learning mode |
| `/dm:dnd data sync` | Rebuild bundled SRD dataset from upstream sources (only needed for new upstream content) |
| `/dm:dnd data status` | Show current dataset record counts and upstream SHA |
| `/dm:dnd update` | Pull latest skill changes from `origin/main` (refuses on dirty tree, fast-forward only) |
| `/dm:dnd update --check` | Show local-vs-remote version and commit-diff without pulling |
| `/dm:dnd path [<new>\|reset]` | View or relocate campaign storage via `DND_CAMPAIGN_ROOT` |
| `/dm:dnd graph init` | Initialize the campaign relationship graph (proposes seed nodes + edges; asks for approval) |
| `/dm:dnd graph scene-context --place <id> [--present id1,id2]` | Focused subgraph for the current scene; primary in-session query |
| `/dm:dnd graph add-edge --from <id> --to <id> --type T --since N` | Record a relationship shift mid-session |
| `/dm:dnd graph close-edge --id <id> --at-session N` | Mark an edge as ended (alliance broke, NPC moved away, etc.) |
| `/dm:dnd graph extract [--last-session-only]` | Run a Haiku pass over session-log to propose new edges (review-then-apply) |

---

## Narrative Arc System

Both campaign modes use the same six-beat three-act structure tracked in `state.md`. The arc type determines how it's populated and enforced.

### Structural foundations

The dynamic arc draws from several overlapping frameworks in story structure and tabletop adventure design:

- **Three-act structure** — the classical division of setup, confrontation, and resolution, present in dramatic theory from Aristotle through modern screenwriting. The six beats are two per act, giving each phase a complicating turn rather than a flat arc through it.
- **Dan Harmon's Story Circle** — an 8-step story engine (derived from Campbell's Hero's Journey) that emphasizes a character crossing into an unfamiliar situation, finding something, paying a price to take it, and returning changed. The Midpoint Shift and All Is Lost beats are direct reflections of this — the moment the story reveals its actual shape, and the cost the protagonist must pay before they can act on it.
- **Beats as consequences, not events** — the key adaptation for tabletop play. In a scripted story, a beat is a scene ("the hero finds the letter"). In a tabletop arc, a beat is a consequence ("the party realizes the threat was built to outlast any single person"). Dozens of different scenes could deliver the same consequence. This gives the DM genuine flexibility while keeping the story's shape committed.
- **Hub-and-spoke adventure structure** — used by the structured arc type for non-linear published modules. Players approach each spoke location in any order; each spoke has its own chapter beats; the central convergence point doesn't open until all required spokes resolve. This matches how most well-designed published campaigns are actually constructed and lets Claude enforce beats at chapter granularity without forcing a linear path.

### Improvised (type: dynamic)

Generated automatically at `/dm:dnd new` from the world's threat, factions, and Three Truths. Beats are defined by `what_changes` — the narrative consequence that must land — not by a specific event. This gives the DM flexibility on *how* each beat arrives while committing to *that* it must.

| Act | Beat | What it marks |
|-----|------|---------------|
| 1 | Inciting Incident | The threat becomes personal |
| 1 | Complication | The problem is bigger than it first appeared |
| 2 | Midpoint Shift | What the party thought they were doing changes |
| 2 | All Is Lost | A genuine setback — something fails or collapses |
| 3 | Final Confrontation | The decisive moment the campaign turns on |
| 3 | Resolution | What's different about the world and characters after |

Arc beats are tracked at `/dm:dnd end` and marked complete via `/dm:dnd arc advance`. When a major player choice redirects the story, `/dm:dnd arc revise` updates outstanding beats to fit the new direction. When all six beats resolve, `/dm:dnd arc new` generates a new arc from the consequences of the first — same world, new story question.

### Structured (type: structured)

Populated by `/dm:dnd import` from the source material. Acts contain chapter-level key beats, telegraph scenes (setup scenes that naturally constrain choices toward each beat), and branching notes. Claude telegraphs before delivering any required beat, steers with world pressure rather than hard walls when players drift, and marks beats complete as each chapter resolves.

The two arc types are mutually exclusive per campaign and fully compatible with all other systems — combat, levelling, and NPC attitudes all behave identically regardless of arc type.

---

## Character Commands

| Command | Description |
|---------|-------------|
| `/dm:dnd character new` | Create a character — guided point buy or rolled stats |
| `/dm:dnd character sheet [name]` | Display a character sheet |
| `/dm:dnd level up [name]` | Level up a character — applies class features, HP roll |

### Character Creation

The creation flow walks through:
1. Name, race, class, background
2. **Point buy** (validates against 27-point budget) or **rolled** (3 arrays of 4d6kh3 to choose from)
3. Racial bonuses applied automatically
4. Derived stats calculated via `character.py`
5. Starting equipment assigned by class + background
6. Sheet written to `characters/<name>.md`

---

## Combat System

```
/dm:dnd combat start
```

1. Identifies all combatants, collects DEX mods, HP, AC
2. Auto-rolls initiative for **every combatant** including PCs — turn order printed in chat
3. Tracks HP, conditions, turn order across rounds
4. Resolves NPC/monster attacks inline with full dice math:
   ```
   Goblin attacks: d20(14) + 4 = 18 vs AC 16 — hit! 1d6(3) + 2 = 5 piercing
   ```
5. PC attack/skill/save rolls follow the campaign's roll mode (see [Dice & Roll Handling](#dice--roll-handling)) — under the default `players` mode the DM calls for each PC roll by name and waits; under `auto` it rolls them openly. The DM always resolves NPC/monster rolls.

---

## Dice & Roll Handling

How a player's own d20s (attacks, checks, saves, death saves) get rolled is chosen **at game start** and stored as `roll_mode` in `state.md → ## Session Flags`. Both `/dm:dnd new` and `/dm:dnd load` ask **"Dice rolls?"** so you confirm it each session.

| Mode | Behavior |
|------|----------|
| **`players`** (default) | The DM calls for each PC d20 **by name and waits** for the player to state their result — it never rolls a player's character for them. If a roll doesn't come back, the DM asks for the number again rather than silently auto-rolling. |
| **`auto`** | The DM rolls PC d20s openly with full math shown inline (`Piper — Perception: d20+5 = 18`), no waiting. Good for solo or fast play. |

**Initiative is always DM-rolled** for every combatant (PCs and NPCs) regardless of mode, as are all NPC/monster rolls.

---

## NPC System

```
/dm:dnd npc Osk             # portray an existing NPC or generate a new one
/dm:dnd npc attitude Osk friendly   # shift attitude on the 5-step scale
```

Every NPC gets: role, stat block, demeanor, motivation, secret, and a speech quirk. Attitudes shift on a 5-step scale: `hostile → unfriendly → neutral → friendly → allied`. Changes are logged with reason and date in `npcs.md`.

---

## Resting

```
/dm:dnd rest short    # 1 hour — spend Hit Dice, recharge some features
/dm:dnd rest long     # 8 hours — full HP, half Hit Dice back, all spell slots
```

Long rests advance the in-world clock in `state.md`.

---

## Scripts Reference

All scripts live in `${CLAUDE_SKILL_DIR}/scripts/`.

### `dice.py` — All dice rolls

```bash
python3 scripts/dice.py d20+5
python3 scripts/dice.py 2d6+3
python3 scripts/dice.py d20 adv          # advantage
python3 scripts/dice.py d20+3 dis        # disadvantage + modifier
python3 scripts/dice.py 4d6kh3          # keep highest 3 (ability score roll)
python3 scripts/dice.py d20 --silent    # integer only (for hidden rolls)
```

Flags nat 20 (`CRITICAL HIT`) and nat 1 (`FUMBLE`) automatically.

### `ability-scores.py` — Character creation

```bash
python3 scripts/ability-scores.py roll                          # 3 arrays to choose from
python3 scripts/ability-scores.py pointbuy                     # print cost table
python3 scripts/ability-scores.py pointbuy --check STR=15 DEX=10 CON=15 INT=8 WIS=11 CHA=12
python3 scripts/ability-scores.py modifiers STR=15 DEX=10 CON=15 INT=8 WIS=11 CHA=12
```

### `combat.py` — Initiative and attack resolution

```bash
# Roll initiative for all combatants and print tracker
python3 scripts/combat.py init '[
  {"name":"Aldric","dex_mod":1,"hp":18,"ac":17,"type":"pc"},
  {"name":"Skeleton","dex_mod":2,"hp":13,"ac":13,"type":"npc"}
]'

# Reprint tracker from saved state
python3 scripts/combat.py tracker '<state_json>' <round_num>

# Resolve a single attack
python3 scripts/combat.py attack --atk 5 --ac 13 --dmg 1d8+3
```

`init` outputs a `STATE_JSON:` line — save this to `state.md` under `## Active Combat` for persistence between turns.

### `build_supplemental.py` — Extend the SRD dataset with non-SRD content

Run after creating or importing a character to fetch descriptions for spells and features not in the core SRD:

```bash
# Scan a character file and fetch anything missing
python3 scripts/build_supplemental.py --character ~/.claude/dnd/campaigns/<name>/characters/<charname>.md

# Scan all characters in a campaign at once
python3 scripts/build_supplemental.py --campaign <campaign-name>

# Add a specific entry by name
python3 scripts/build_supplemental.py --add "Toll the Dead" spell
python3 scripts/build_supplemental.py --add "Halo of Spores" feature

# See what's currently cached
python3 scripts/build_supplemental.py --list

# Preview what would be fetched without writing
python3 scripts/build_supplemental.py --campaign <name> --dry-run
```

Fetches from `dnd5e.wikidot.com` with a polite request delay. Uses Python stdlib only — no extra dependencies. Writes to `data/dnd5e_supplemental.json`, which `lookup.py` merges at load time.

---

### `character.py` — Stat derivation and levelling

```bash
# Full stat block from raw scores
python3 scripts/character.py calc --class fighter --level 2 \
    STR=16 DEX=12 CON=15 INT=10 WIS=11 CHA=13 \
    --proficient STR CON Athletics Intimidation Perception Survival

# Level-up
python3 scripts/character.py levelup --class fighter --from 2 --hp-roll 8 --con-mod 2

# XP tracking
python3 scripts/character.py xp --level 2 --gained 150
```

---

## File Layout

```
${CLAUDE_SKILL_DIR}/
├── SKILL.md                  # Skill definition and DM instructions
├── SKILL-scripts.md          # Script and tool syntax reference
├── SKILL-commands.md         # /dm:dnd command procedures
├── README.md                 # This file
├── data/
│   ├── dnd5e_srd.json        # Bundled 5e SRD dataset (1453 records — spells, features, equipment, monsters)
│   └── dnd5e_supplemental.json  # Non-SRD content (Xanathar's, subclass features, etc.)
├── scripts/
│   ├── dice.py
│   ├── ability-scores.py
│   ├── combat.py
│   ├── character.py
│   ├── tracker.py
│   ├── calendar.py
│   ├── lookup.py             # SRD + supplemental query API
│   ├── build_srd.py          # Fetches upstream 5e data and builds dnd5e_srd.json
│   ├── sync_srd.py           # Checks upstream SHAs; rebuilds only on new commits
│   └── build_supplemental.py # Fetches non-SRD entries from wikidot for a character or campaign
└── templates/
    ├── character-sheet.md
    ├── state.md
    ├── world.md
    ├── npcs.md
    └── session-log.md

~/.claude/dnd/campaigns/<name>/
├── state.md                  # Current location, party status, active quests, arc tracking
├── world.md                  # World lore, setting details, adventure nodes
├── npcs.md                   # NPC index with stat blocks and attitudes
├── session-log.md            # Session history and recaps (last 2 sessions; older archived)
├── session-log-archive.md    # Full session history archive
├── session_tail.json         # Last session's final beats — continuity tail written at save
└── characters/
    ├── Aldric.md
    └── Mira.md
```

---

## DM Philosophy

The skill is designed around a set of hard constraints, not aspirational notes:

- **Improvise over script** — the world is a sandbox; player choices always find a "yes, and..."
- **Consequences are real** — NPCs remember conversations; factions shift; failure is possible
- **Economy of description** — two sharp sensory details beat a paragraph of exposition
- **Every NPC is a person** — even minor characters get a verbal tic, a contradiction, a goal
- **Hidden rolls stay hidden** — Perception, Insight, and Stealth roll silently; only the outcome is narrated
- **The arc bends, never breaks** — when players redirect the story, beats revise to fit the new direction; the committed shape is a guide, not a cage
- **Calibrates to this specific player across sessions** — DM Style Notes accumulate table-specific patterns from calibration feedback; what lands for this party, what splits the table, what to lean into; read at every session load and updated at every end
- **The world moves between sessions** — factions act while the party is occupied; NPCs pursue their own goals; doors that were kicked in stay broken; the player arrives to a world with weight, not a scene that was paused waiting for them

---

## Ruleset

Each campaign declares its ruleset on the `state.md` header line: `**Ruleset:** 2014` (SRD 5.1) or `**Ruleset:** 2024` (SRD 5.2). `/dm:dnd new` asks for the ruleset at creation time; `/dm:dnd load` reads the field on every session. Legacy campaigns (predating the field) default to **2014** and are offered a one-time migration with a timestamped backup.

### 2014 dataset (default)

`data/dnd5e_srd.json` — built from `5e-bits/5e-database` (`main` branch, 2014 SRD) and `foundryvtt/dnd5e` (`master` branch). 1,453 records: 319 spells, 237 equipment, 362 magic items, 15 conditions, 334 monsters, 186 features.

### 2024 dataset (opt-in)

`data/dnd5e_srd_2024.json` — built from `5e-bits/5e-database` (`src/2024/en/`), `foundryvtt/dnd5e` (`packs/_source/spells24/`, `packs/_source/actors24/`, `packs/_source/classfeatures24/`). All foundry content is CC-BY-4.0, with `_source` and `_license` provenance preserved on every record. Approximately 1,420+ records: 341 native 2024 spells, 376 native 2024 monsters, 8 weapon mastery properties, 9 species, 24 subspecies, 17 origin/general/fighting-style feats, 4 backgrounds, plus equipment / magic items / features. Build with `python3 scripts/build_srd.py --ruleset 2024` (one-time, ~3 min).

### Mechanic differences applied at the table

| Mechanic | 2014 | 2024 |
|---|---|---|
| Subclass timing | varies by class (1/2/3) | level 3 universally |
| ASI source | race | background |
| Origin feat | n/a | granted at level 1 by background |
| Weapon mastery | n/a | 8 properties (Vex, Topple, Sap, Cleave, Graze, Nick, Push, Slow) |
| Exhaustion | 6-level table with varied effects | 1 stack = -2 to all d20 rolls (cumulative); death at level 6 |
| Stealth disadvantage on heavy armor | yes | yes (unchanged) |
| Healing word range | 60 ft | 60 ft (unchanged) |

Combat resolution, dice rolling, initiative, AC/HP derivation, XP tables, cantrip damage scaling, and rest recovery are identical between editions and require no per-ruleset branching in the engine.

### Backwards compatibility

Existing campaigns continue to load unchanged. The first time a legacy campaign is loaded under the new code path, `migrate_ruleset.py` detects the missing `**Ruleset:**` field and prompts the DM. The migrator:

- Backs up `state.md` to `state.md.backup-pre-ruleset-<timestamp>` before any write
- Injects the chosen ruleset into the header line
- Is idempotent — re-running on a migrated campaign is a clean no-op
- Has a `--check` mode for non-mutating detection (used by `/dm:dnd load`)

Character files inherit ruleset from their campaign at runtime via `paths.campaign_ruleset()`; no per-character migration is required.

If you want to switch a legacy campaign to 2024, run the migrator manually:

```bash
python3 scripts/migrate_ruleset.py <campaign-name> --ruleset 2024 --yes
```

Note: switching an in-progress 2014 campaign to 2024 mid-arc is not recommended — character builds (origin feats, background ASIs, weapon mastery for martial classes) were locked in under 2014 rules. The migrator simply stamps the field; rebuilding characters under 2024 is a separate manual exercise.

---

## License

[AGPL-3.0-or-later](LICENSE). Copyright (c) 2026 Neural Initiative LLC.

Self-hosting and modification are explicitly welcome — fork, run, change as you like. The AGPL specifically protects against re-hosting this as a closed-source SaaS without sharing modifications back. For most users this distinction never matters.
