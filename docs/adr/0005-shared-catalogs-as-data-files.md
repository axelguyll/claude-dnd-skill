# Tone and premise catalogs are data files, not prose

**Status:** accepted (2026-07-15, prep premise-variance work; recorded 2026-07-16)

The seven-tone catalog (`data/tones.yaml`) and the four-axis premise seed bank
(`data/premise-seeds.yaml`) are YAML data files consumed by `scripts/prep/premise.py`,
not lists inlined in SKILL prose. tones.yaml is the single source of truth for *both*
`/dm:dnd prep` and `/dm:dnd new` ("Edit here, never inline in SKILL-commands.md",
tones.yaml:2-3). Premise variance is forced by *rolling* orthogonal axes and reconciling,
never by free-associating — free association converges on the model's default register.

## Consequences

- Adding a tone or premise axis is a data edit plus tests (`test_tones_catalog`), no
  prose surgery; prose references tones only by id.
- The prose must not restate catalog contents (a copy would drift); SKILL-commands.md
  lists tone ids in the `prep`/`new` signatures — those enumerations are the one place a
  new tone still requires a prose touch.
