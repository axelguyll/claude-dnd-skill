# Heavy stores stay out of the load path; state.md carries light windows

**Status:** accepted (restated 2026-07-16)

Campaign data is split into an always-loaded hot path (state.md, world.md, npcs.md index,
character sheets) and lazy heavy stores read only on a specific trigger: `spine.json` at
`beat complete`, `arc.md` on chapter advance, `source/<id>.md` before running its
chapter, `npcs-full.md` before voicing an NPC, `world-nodes.md` per current act,
session logs never at load. state.md carries a light mirror/pointer window for each
(authored beats mirror, structured chapter window) so play never needs the heavy file.

## Considered options

- Load everything at `/dm:dnd load`: simple, one source of truth, but burns context on
  material most sessions never touch and worsens compaction behavior.
- Lazy layer + inline windows (chosen): cheap loads, targeted re-reads after compaction.

## Consequences

- Every window is a dual-write with its heavy store (spine↔state beats, arc.md↔state
  chapter window) and none has a validator — drift here is silent and steers play wrong.
  This is the accepted cost; Session E stress-tests it.
- The compaction re-read ladder (SKILL.md:213-221) exists *because* of this split: the
  smallest section that answers a claim is re-read, never the whole store.
