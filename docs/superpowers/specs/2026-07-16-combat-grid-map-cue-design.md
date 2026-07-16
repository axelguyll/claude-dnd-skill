# Combat Grid + Map Cue — Design

*2026-07-16. Features 2 and 3 of the post-reprobe wave, designed together: the map cue
fires at the same moment the grid activates. Feature 1 (NPC supporting cast) is specced
separately in `2026-07-16-npc-supporting-cast-design.md`.*

## Problem

Prep generates `map-list.md` (encounter-scene maps the host acquires and projects), but
play time has no cue telling the host when to put a map up or take it down — ambient
sound has one (`🔊 **Cue:**`, SKILL.md Active DM Mode); maps don't. And combat itself is
pure theater of the mind: combat.py tracks initiative/HP/AC, tracker.py tracks
conditions, but **positions are not modeled**, so range, movement, and AoE are
adjudicated by feel.

## Decision (approach locked before design)

**Text-descriptor grid, not image vision.** Claude never sees the projected map's
pixels. Each shopping-list map gets a coordinate spec (chess-style A1 tile labels,
letter+number, non-square dimensions fine). The physical projected map is the players'
display; Claude's text grid is the rules engine; the shared tile labels bridge them.
The spec is rules truth; the image is decoration.

## Architecture

Three new pieces, wired into the existing pipeline:

| Piece | Kind | Role |
|---|---|---|
| `maps/<handle>.grid.json` | data, per mapped scene | grid spec: dims + terrain |
| `scripts/grid.py` | stateless helper (like combat.py) | distance / movement / range / AoE math |
| `scripts/render_map.py` | render script (like render_tracker.py) | player-facing `map.html` on the projector |

Plus two prose contracts: the **map cue block** and the **mapped-combat additions** to
the per-turn sequence. Positions ride the existing STATE_JSON pipeline — no new
persistence mechanism.

## The map cue (Feature 2)

New bullet in SKILL.md narration principles, beside the sound-cue bullet, same
contract (standalone block, never buried in narration, only handles that exist on the
campaign's map list, **never invented**):

```
🗺 **Map:** *<handle>*                      ← mapped tactical scene begins
🗺 **Map:** *down — theater of the mind*    ← combat ends / scene leaves the map
```

The up-cue fires at combat start on a mapped scene (with `/dm:dnd combat start` or the
natural-language equivalent). The down-cue fires when combat ends or the scene moves
off the map — same moment `## Active Combat` is cleared.

## The grid spec (Feature 3)

`<campaign>/maps/<handle>.grid.json`:

```json
{
  "handle": "cavern",
  "cols": 18,
  "rows": 24,
  "terrain": [
    {"tiles": "C3-D5", "kind": "rubble", "difficult": true},
    {"tiles": "F1",    "kind": "pillar", "impassable": true, "blocks_los": true}
  ],
  "notes": "underground stream crosses mid-map, 10 ft wide"
}
```

- `cols` map to letters (A…), `rows` to numbers (1…). Tiles are 5 ft. Non-square fine.
- `tiles` is a single tile (`F1`) or a rectangular range (`C3-D5`).
- Terrain flags: `difficult` (costs double movement), `impassable` (blocks pathing),
  `blocks_los` (advisory — see LoS below). `kind` is free text.
- `notes` is free prose for Claude's scene reasoning.

**Authoring — hybrid:**

1. **Prep-time default.** Prep step 4 (asset shopping lists) also writes a grid spec
   per map-list entry, under the same spoiler discipline: terrain only, never why the
   party goes there or what happens. Validated by `grid.py validate <file>` as a hard
   gate (mirrors the schema.py pattern — never proceed on INVALID).
2. **First-use confirm.** On the first up-cue for a handle, ask the host one line:
   *"spec says 18×24 — match your map? give real dims if not."* On override, rewrite
   `cols`/`rows`; if the dims shift substantially, re-fit the terrain regions
   proportionally (prose judgment, not a script). Confirmation is once per handle —
   record it by adding `"confirmed": true` to the spec.
3. **Fallback.** Listed handle with no grid.json (prep predates this feature, or the
   pass was skipped): build the spec at combat start through the same host exchange,
   then validate and save. Same file, same downstream path.

## `grid.py` (stateless math engine)

Positions are inputs, never stored by the script — same statelessness contract as
combat.py. All commands take `--spec <file>` where terrain matters.

| Command | Behavior |
|---|---|
| `grid.py validate <file>` | schema + bounds check; exit non-zero on INVALID with listed errors |
| `grid.py dist C4 F7` | distance in feet. 5 ft/tile, **diagonals 5 ft** (2014 PHB default) |
| `grid.py move --from C4 --to F6 --speed 30 --spec <f>` | cheapest-path cost (difficult ×2, impassable excluded, off-grid excluded). Prints `OK cost=25ft` or `ILLEGAL cost=40ft` plus the furthest reachable tile toward the target |
| `grid.py range --from C4 --to F7 --ft 60` | `IN RANGE` / `OUT OF RANGE (dist=Nft)` |
| `grid.py aoe --shape sphere\|cube\|cone\|line --origin D4 --size 20 [--dir N\|NE\|E\|…]` | affected tile list. Sphere/cube exact; cone/line are grid approximations (documented v1 simplification) |

**Not in v1:** line-of-sight and cover computation. `blocks_los` markers exist in the
spec for Claude's reasoning; cover is adjudicated in prose. Opportunity attacks are
likewise prose-adjudicated (Claude sees the path cost output and the positions; the
script does not model threat reach).

## Position state

STATE_JSON gains two optional per-combatant fields:

- `"pos": "C4"` — current tile. Present only in mapped combats.
- `"hidden": true` — combatant exists in the tracker but is not rendered on the
  player-facing map. (Unrevealed enemies may alternatively be kept out of STATE_JSON
  entirely until revealed — DM's call; both work.)

Positions persist exactly where combat state already persists: the STATE_JSON block in
`state.md → ## Active Combat`, written back every turn at step d2. Mid-combat
compaction recovery therefore covers positions with no new mechanism — the compaction
re-read ladder's mid-combat entry gains the word "positions."

**Constraint on existing scripts:** combat.py (init and reorder paths) and
render_tracker.py must pass unrecognized combatant fields through untouched. Verify at
plan time; fix if either strips them. render_tracker.py additionally shows a position
column when `pos` is present.

## `render_map.py` (player-facing projector page)

Separate script — render_assets.py stays static (audio loops must never be
interrupted by a regen), render_tracker.py stays the host-side dashboard. One purpose
per script, matching the existing render pattern.

```
render_map.py --campaign <name> --handle <handle> --state '<STATE_JSON>' --round <n>
render_map.py --campaign <name> --clear
```

- Writes `<campaign>/map.html`: `maps/<handle>.png` full-screen (fit-to-screen, dark
  background), grid overlay (lines + A1 edge labels, laid proportionally over the
  image per the spec's dims — image edges are assumed to be grid edges), and a token
  marker per combatant at its `pos` (PC vs NPC visually distinct; `hidden` skipped).
- Meta-refresh like tracker.html; regenerated every turn at step d2.
- `--clear` writes the idle screen ("theater of the mind", near-black). **Host
  workflow: map.html lives on the projector permanently** — idle between fights,
  lights up at combat start, clears at the down-cue. The chat cue block remains the
  host-side signal and covers hosts projecting images manually instead.
- Map image missing from `maps/`: grid-only render — labels, lines, and tokens on the
  dark background. Playable without the art.
- Combatant with no `pos`: listed in a sidebar strip ("off-map / unplaced"), not drawn.

## Play-flow wiring

**Activation rule:** the grid activates only when a tactical scene begins at a location
matching a map-list handle (or the host explicitly says which listed map to use).
Improvised fights elsewhere stay pure theater of the mind — no invented cue, no
invented grid, exactly like the sound-cue rule.

**`/dm:dnd combat start` on a mapped scene** (additions):
1. Emit the up-cue block.
2. Load/confirm the grid spec (first-use confirm or fallback authoring above).
3. Collect starting positions: place NPCs per the fiction; players state theirs
   (default them to a sensible entry edge if they don't care). Include `pos` in the
   init JSON.
4. `combat.py init` as today; STATE_JSON now carries positions; first render_map.py.

**Per-turn sequence** (SKILL.md) additions:
- Step b gains movement: a player states a move ("I move to E3") → validate via
  `grid.py move`; on ILLEGAL, narrate the constraint in fiction and let them re-choose
  (the furthest-reachable output is the fallback offer). Claude moves all NPCs and
  validates its own moves the same way. Range/AoE claims resolve through `grid.py
  range` / `aoe` before rolling — script-first rule applies to position math.
- Step d2 gains one line: mapped combat → after render_tracker.py, run render_map.py
  with the same STATE_JSON.

**Combat end** (`combat start` step 5 additions): emit the down-cue, run
`render_map.py --clear`. Positions vanish with the `## Active Combat` block —
no separate cleanup.

**Position authority:** players declare intent in chat; Claude is the sole writer of
`pos` values, validated through grid.py. Mirrors the roll_mode philosophy without
needing a new session flag.

## Files touched

- New: `skills/dnd/scripts/grid.py`, `skills/dnd/scripts/render_map.py`,
  `<campaign>/maps/<handle>.grid.json` (per campaign, authored at prep).
- `skills/dnd/SKILL.md` — map-cue bullet; per-turn steps b and d2; compaction ladder
  mid-combat entry (+ "positions").
- `skills/dnd/SKILL-commands.md` — prep step 4 (grid-spec authoring + validate gate);
  `combat start` (cue, spec load, placement, end-of-combat additions).
- `skills/dnd/SKILL-scripts.md` — grid.py and render_map.py syntax.
- `skills/dnd/scripts/combat.py`, `render_tracker.py` — field pass-through (verify
  first); tracker position column.
- `skills/dnd/templates/map-list.md` — entry footer notes its grid spec sidecar.
- `docs/ARCHITECTURE.md`, `CONTEXT.md` — new scripts, terms *map cue*, *mapped
  combat*, *grid spec*.

## Error handling

- Invalid grid spec at prep → hard gate, fix and re-run (never proceed INVALID).
- Missing spec at play → fallback authoring path (above).
- Missing map image → grid-only render.
- ILLEGAL move → in-fiction constraint + re-choose; never silently clamp.
- Handle not on the map list → no cue, no grid, theater of the mind.
- Mid-combat compaction → recover order/HP/positions from `## Active Combat`,
  conditions from `tracker.py status` (existing ladder, one word added).

## Testing

- **pytest, grid.py:** dist incl. diagonals; move budget with difficult terrain;
  impassable pathing (blocked corridor forces the long way); off-grid and non-square
  bounds; aoe tile sets per shape; validate accepts the template and rejects
  malformed dims/tiles.
- **pytest, render_map.py:** STATE_JSON parse; `hidden` skipped; no-`pos` sidebar;
  idle screen on `--clear`; missing-image grid-only fallback.
- **pytest, pass-through:** combat.py init/reorder and render_tracker.py preserve
  `pos`/`hidden` fields end-to-end.
- **Prose acceptance:** probe session per docs/probes methodology — scripted fight on
  a mapped scene exercising cue up, placement, an illegal move, an AoE, hidden reveal,
  cue down.
