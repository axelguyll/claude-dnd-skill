# Campaign Bible — Spine

*Authored once during `/dm:dnd prep`, before the first session. The spine is the
generator's output: a validated sequence of 6-8 beats spanning a full arc,
L1-8, checked against `prep/schema.py::validate_bible` and the vendored SRD
bestiary (`prep/bestiary.py`) before it's ever shown to the host. Once
accepted, the spine seeds `state.md → ## Campaign Arc` (dynamic arc format);
this file is the durable source the arc pointer is derived from.*

## Top-level shape

```text
{
  "theme": "<one sentence — what this story is ultimately about>",
  "resolution": "<committed endpoint shape if the party succeeds>",
  "causal_thread": "<the one line of cause-and-effect connecting beat 1 to the final beat>",
  "beats": ["<beat object>", "..."]
}
```

- **theme** / **resolution** — carried forward verbatim into the dynamic arc
  block in `state.md`.
- **causal_thread** — not validated by schema; a prep-time authoring aid that
  keeps `world_pressure` escalating instead of episodic.
- **beats** — 6 to 8 beat objects (`schema._MIN_BEATS`..`_MAX_BEATS`).

## Beat object shape

Each beat is validated independently and as part of the sequence:

| field | type | rule |
|---|---|---|
| `id` | int | sequential `1..n`, no gaps |
| `act` | int | one of `1`, `2`, `3`; non-decreasing across beats; all three acts must appear |
| `label` | str | non-empty prose (e.g. "Inciting Incident") |
| `situation` | str | non-empty prose — what the party walks into |
| `what_changes` | str | non-empty prose — before vs. after this beat lands |
| `world_pressure` | str | non-empty prose — the faction/NPC move that makes this beat feel inevitable |
| `level_up_to` | int or null | if set, must be `2..8` and strictly greater than any prior beat's `level_up_to`; the **final beat's `level_up_to` must not be null** — the arc must end leveled |
| `gear` | list of str | may be empty; any entry present must be a non-empty string |
| `threats` | list of str | monster names; each must resolve via `bestiary.find_monster` and its CR must be in-band for the party's level *during* that beat (see below) |
| `secret` | str or null | key must always be present, even when there is nothing hidden at this beat |
| `status` | str | `pending` at authoring time; the running procedure advances this as beats resolve |

### Party level during a beat

`schema.party_levels(beats)` computes the level the party is **at while
playing** each beat — before that beat's own `level_up_to` applies. The party
starts at level 1; a beat's `level_up_to` only affects levels for *later*
beats, not the beat that grants it. This is why beat 1 can send the party into
a Goblin fight while also carrying `level_up_to: 2` — they fight beat 1 at
level 1, and arrive at beat 2 already level 2.

### Threat banding

A threat is legal for a beat if its CR falls in `bestiary.band_for_level(lvl)`:
floor is `0.125` for levels 1-3 (keeps CR-1/8 minions legal), else `level / 4`;
ceiling is `level + 2`. CR-0 creatures are never combat threats. Threats named
in a beat that resolve to an unknown monster, or whose CR falls outside this
band for that beat's level, fail validation.

## Worked example

Six beats, three acts (2/2/2), leveling L1 → L8, every threat in-band for the
level the party is at during that beat.

<!-- Regression tests (test_prep_example.py, test_prep_cli.py) validate the FIRST ```json block in this file. Keep this the only json fence, or they will check the wrong block. -->
```json
{
  "theme": "t",
  "resolution": "r",
  "causal_thread": "c",
  "beats": [
    {
      "id": 1,
      "act": 1,
      "label": "Inciting Incident",
      "situation": "s",
      "what_changes": "w",
      "world_pressure": "p",
      "level_up_to": 2,
      "gear": ["torch"],
      "threats": ["Goblin"],
      "secret": null,
      "status": "pending"
    },
    {
      "id": 2,
      "act": 1,
      "label": "Complication",
      "situation": "s",
      "what_changes": "w",
      "world_pressure": "p",
      "level_up_to": 3,
      "gear": [],
      "threats": ["Bugbear"],
      "secret": "a hidden cult",
      "status": "pending"
    },
    {
      "id": 3,
      "act": 2,
      "label": "Rising Action",
      "situation": "s",
      "what_changes": "w",
      "world_pressure": "p",
      "level_up_to": 4,
      "gear": [],
      "threats": ["Ogre"],
      "secret": null,
      "status": "pending"
    },
    {
      "id": 4,
      "act": 2,
      "label": "Midpoint",
      "situation": "s",
      "what_changes": "w",
      "world_pressure": "p",
      "level_up_to": 6,
      "gear": [],
      "threats": [],
      "secret": null,
      "status": "pending"
    },
    {
      "id": 5,
      "act": 3,
      "label": "All Is Lost",
      "situation": "s",
      "what_changes": "w",
      "world_pressure": "p",
      "level_up_to": 7,
      "gear": [],
      "threats": ["Young Green Dragon"],
      "secret": null,
      "status": "pending"
    },
    {
      "id": 6,
      "act": 3,
      "label": "Final Confrontation",
      "situation": "s",
      "what_changes": "w",
      "world_pressure": "p",
      "level_up_to": 8,
      "gear": ["dragon hoard"],
      "threats": ["Young Blue Dragon"],
      "secret": null,
      "status": "pending"
    }
  ]
}
```

`tests/test_prep_example.py` pins this example valid — any change to
`prep/schema.py`'s rules or the SRD bestiary CR bands must keep this example
passing `validate_bible`, or be paired with an update here.
