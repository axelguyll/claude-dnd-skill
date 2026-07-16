# Combat Grid + Map Cue — Acceptance Probe

*2026-07-16. Post-implementation probe of branch `feat/combat-grid-map-cue`
(HEAD 1509134). Drives the real scripts end-to-end on a scratch campaign root
(`DND_CAMPAIGN_ROOT` → temp dir; the live `~/.claude/dnd/` was never touched)
and eyeballs the two HTML artifacts in a browser. Spec:
`docs/superpowers/specs/2026-07-16-combat-grid-map-cue-design.md`.*

## Method

Scratch campaign `probe` under a temp `DND_CAMPAIGN_ROOT`. Authored one grid
spec (`cavern`, 12×9, difficult `E4-F6`, impassable stalagmites `H2`/`H3`,
with a deliberately planted spoiler string in `notes`). Combat state carried as
STATE_JSON with four combatants: a PC (`pos` D5), a placed NPC (G5), a **hidden**
ambusher (H2), and an **unplaced** combatant. Exercised every subcommand and both
renderers, then loaded `map.html` and `tracker.html` over a local HTTP server.

## Results — all pass

| Check | Result |
|---|---|
| `grid.py validate` on a good spec | `VALID`, exit 0 |
| `grid.py validate` on bad dims (`cols:30`) | `INVALID` + error, exit 1 (hard gate holds) |
| `dist B3 G5` | `25ft` (Chebyshev, correct) |
| `range` in/out | `IN RANGE (dist=25ft)` / correct ft on all |
| `move D5→G5 speed 30` through rubble | `OK cost=25ft` (difficult ×2 applied) |
| `move` same at speed 15 | `ILLEGAL cost=25ft -- furthest reachable toward G5: E3 (10ft)` |
| `move` onto impassable H2 | `UNREACHABLE H2` |
| `aoe sphere 20 @ F5` | 81 tiles (9×9), clipped to grid, fills impassable tiles (correct — `blocks_los` gates LoS not AoE) |
| `aoe cone 15 NE @ B7` | 15 tiles, widening wedge |
| **Spoiler leak** — `notes`/SECRET/idol/terrain kinds in player `map.html` | **0 hits** — none reach the player page |
| Hidden combatant on `map.html` | absent (spoiler-safe) |
| Placed tokens on `map.html` | PC gold `#d4b24c` @ D5, NPC red `#b0432f` @ G5 |
| Unplaced combatant | listed in `off-map:` strip |
| Grid-only fallback (no image) | renders labels + tokens, no `<image>` |
| Image present | `<image … preserveAspectRatio="none">` href `maps/cavern.png` |
| `render_map.py --clear` | idle "theater of the mind", 0 tokens/images |
| Missing grid spec at play | clean message + exit 1, no traceback |
| `tracker.html` positions | `@ D5` / `@ G5` shown; unplaced shows none |
| DM/player asymmetry | hidden Cave Lurker **shown on DM tracker**, **hidden on player map** — verified side by side in browser |
| Grid geometry (browser) | 12×9, labels A–L / 1–9, viewBox `-0.9 -0.9 13.8 10.8`, tokens at correct tiles |

## Visual (browser, 127.0.0.1 static server)

- **map.html:** HUD "ROUND 1 — CAVERN", clean dark projector aesthetic, Piper
  (gold) at D5, Goblin A (red) at G5, Bat Swarm in the off-map strip, Cave
  Lurker absent. On a tall viewport the wide grid centers with vertical
  margin — expected; it fits-to-projector at the actual display aspect. Not a
  defect.
- **tracker.html:** initiative order 17/12/9/6, active ring on Piper, blue
  `@ tile` markers on the three placed combatants, none on Bat Swarm, HP bars +
  AC correct. Cave Lurker present here (DM-side), confirming the hidden field
  scopes to the player page only.

## Findings

None blocking. The DM-prose behaviors that a script probe cannot exercise (cue
block emission at the right beat, first-use dims confirmation, illegal-move
in-fiction re-choose narration) are covered by the prose-contract tests
(`test_grid_prose.py`) and the whole-branch review; they need a live table
session to observe in situ, deferred to first real play.

**Verdict: branch mechanics are table-ready.**
