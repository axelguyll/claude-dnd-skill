# Milestone-only leveling; XP machinery retained but uncalled

**Status:** accepted (inherited from dm-app ADR-0016 / spec decision A; restated 2026-07-16)

This fork levels the party exclusively on beat completion: `/dm:dnd beat complete` reads
the spine beat's absolute `level_up_to` and stamps `⚠ LEVEL UP PENDING (Level N)` on each
sheet (`scripts/prep/milestone.py`); the marker is the sole authorization at
`/dm:dnd level up` (SKILL-commands.md:584). `xp.py` and `character.py xp` are deprecated
but kept so legacy campaigns' sheets remain readable — deleting them would break loads of
pre-fork campaigns.

## Consequences

- Only **authored** campaigns level; legacy `new`/`import` campaigns have no leveling
  path at all (SKILL-commands.md:11) — accepted, since `prep` is the intended path.
- The retained XP surface is a standing confusion source: XP still appears in
  live-sounding prose (SKILL.md:183-184, 301) despite the "no XP counter" rule
  (SKILL.md:309). Flagged in CONTEXT.md; cleanup pending owner approval.
- `level_up_to` is absolute, never a delta — absolutes self-heal, deltas compound errors.
