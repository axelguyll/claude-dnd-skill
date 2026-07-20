# /dm:dnd Command Index

Loaded at session start **instead of** `SKILL-commands.md` (1000+ lines whose
procedures each fire at most once per session — the same lazy-loading
discipline the skill applies to world-nodes.md, arc.md, spine.json, and
chapter sources). The per-turn play loop (narration principles, dice
convention, combat sequence, micro-save) lives in `SKILL.md` and stays hot;
nothing in the commands file is needed mid-turn.

**The contract — read the section, every time.** Before executing ANY
`/dm:dnd` command, Read its full section from `SKILL-commands.md` first:
Grep `SKILL-commands.md` for the command's `## ` header, then Read from that
line to the next `## ` header. **Never execute a command procedure from
memory, from a context summary, or from this index** — the one-liners below
are routing labels, not procedures, and a remembered procedure after
compaction is exactly the failure this contract exists to prevent. Path
note: sections are read verbatim, so substitute `${CLAUDE_SKILL_DIR}` with
the absolute skill dir (from SKILL.md) before running any command they
contain.

| Command | Purpose |
|---|---|
| `/dm:dnd new` | Create a campaign via the world-gen interview (legacy path — no leveling) |
| `/dm:dnd load` | Start a play session: picker, session flags, active marker, state reads, recap |
| `/dm:dnd import` | Import a published module as a structured campaign (arc.md + lazy corpus) |
| `/dm:dnd prep` | Generate an authored campaign Bible: world, spine, seeded state, shopping lists |
| `/dm:dnd beat complete` | Complete a spine beat: mirror check, milestone leveling, gear |
| `/dm:dnd save` | Persist session state: log entry, flags, graph sweep, tail, log archival |
| `/dm:dnd end` | End the session: save, calibration, world state, arc + pre-emption checks |
| `/dm:dnd abandon` | End without saving |
| `/dm:dnd data` | SRD dataset sync / status |
| `/dm:dnd path` | Move or reset the campaign data root |
| `/dm:dnd update` | Pull skill updates (upstream-fork caveat applies) |
| `/dm:dnd list` | Campaign summary table (via `paths.py list-campaigns`) |
| `/dm:dnd character new` | Guided character creation |
| `/dm:dnd character sheet` | Render a character sheet |
| `/dm:dnd character import` | Copy a character from another campaign |
| `/dm:dnd level up` | Apply one level: HP, features, milestone gate |
| `/dm:dnd npc` | Show or generate an NPC's full entry |
| `/dm:dnd npc attitude` | Shift an NPC disposition |
| `/dm:dnd npc rename` | Rename an NPC across files, graph, and registry |
| `/dm:dnd registry` | Cross-campaign name registry subcommands |
| `/dm:dnd characters` | List the party's PCs |
| `/dm:dnd roll` | Dice roll passthrough (`dice.py`) |
| `/dm:dnd combat start` | Combat: initiative, tracker, the per-turn combat loop |
| `/dm:dnd rest` | Short / long rest resolution |
| `/dm:dnd recap` | Deliver a session recap |
| `/dm:dnd world` | World summary |
| `/dm:dnd quests` | Quest / thread status |
| `/dm:dnd arc` | Arc status / advance / revise / view (landing-path templates live here) |
| `/dm:dnd graph` | Campaign relationship graph subcommands (scene-context, extract, …) |
| `/dm:dnd oracle` | Solo / improv oracle tools |
| `recap snapshot` | Precomputed party state-diff — load machinery (`recap diff` too) |
| `/dm:dnd tutor on` | Tutor mode toggle (`/dm:dnd tutor off` in the same section) |
| `/dm:dnd autosave on` | Autosave toggle (`/dm:dnd autosave off` in the same section) |
