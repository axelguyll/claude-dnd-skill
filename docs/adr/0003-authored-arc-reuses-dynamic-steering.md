# Authored arcs reuse the dynamic steering rules via a state.md mirror

**Status:** accepted (restated 2026-07-16)

The authored arc has no steering section of its own in SKILL.md. Instead, `/dm:dnd prep`
writes a dynamic-*format* window into `state.md → ## Campaign Arc` (templates/state.md:151-171:
`current_beat`, a `beats:` mirror with `what_changes`/`world_pressure`/`status`, and
`steering_notes`), and the table applies the existing dynamic steering rules
(SKILL.md:243-266) to it. The heavy spine (`situation`/`level_up_to`/`threats`/`gear`/
`secret`) stays in `spine.json`, read only at `/dm:dnd beat complete`.

## Considered options

- Authored-specific steering section in SKILL.md: clearer, but duplicates nine rules that
  would then drift apart.
- Reuse dynamic rules via format mirror (chosen): one steering rule set; authored differs
  only in id type (int) and in what `beat complete` does.

## Consequences

- One source of truth for steering behavior; prep only has to emit the right shape.
- The mirror is a dual-write (spine.json ↔ state.md beats) with no validator — the
  fork's highest-risk drift point (compass fragile-links register; Session E target).
- `current_beat` is a string in dynamic arcs and an int in authored ones — consumers must
  tolerate both.
