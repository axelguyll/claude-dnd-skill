# NPC Supporting-Cast Tier — Design

*2026-07-16. Feature 1 of the post-reprobe wave (independent of the combat-grid/map-cue
pair, specced separately in `2026-07-16-combat-grid-map-cue-design.md`).*

## Problem

Campaign creation seeds exactly 3 full NPCs (`/dm:dnd new` step 11,
SKILL-commands.md); prep's NPC layer (step 1.5) is coverage-driven ("every NPC named in
world.md, minimum 3") and usually lands 4–6. Either way, the opening world can feel
underpopulated for a 20–30 hour campaign: the party walks into a settlement where only
faction leaders and mystery actors have names.

3 was never a cap — the roster grows on demand during play, and the npcs.md index /
npcs-full.md full-entry split already guards drift. The gap is **opening-cast breadth**,
not the growth mechanism. Bumping the full-entry count is the wrong fix: full entries
are expensive by design (prep tokens, npcs-full.md bloat, and the read-before-dialogue
rule pays for every unused entry).

## Decision

Add a second, cheaper tier: the **supporting cast** — index-only NPCs seeded at
creation, promoted to full entries on demand during play.

### Tier definitions

| Tier | Storage | Fields | Seeded |
|---|---|---|---|
| **Core** | npcs.md row + npcs-full.md section | All (stats, personality axes, secret, ≥2 relationships, schedule, …) | `new`: 3 with relationship web. Prep: coverage rule, min 3 (unchanged) |
| **Supporting** | npcs.md row only | Name, Role, Faction (or "independent"), Location, Attitude, Notes = **one distinct trait** | 6–8, both sites |

A supporting-cast row's Notes field must carry one memorable, playable trait — a verbal
tic, visible contradiction, or small motivation (*"innkeeper; counts coins twice, hums
when lying"*). This is Standard 5 (Make Every NPC Memorable) applied at seed time.

Supporting cast are exempt from the relationship-web requirement (that is a full-entry
field). They **do** go through the name-registry uniqueness check, same as core NPCs —
they are named canon from the moment they're written.

### Tier membership convention

An NPC is core iff a section for them exists in npcs-full.md. No new column, no tier
marker in the index table — a marker would be a second copy of the same fact and would
drift at promotion time. The existing read-before-dialogue rule already phrases the
check as "if one exists" (SKILL.md, Active DM Mode), so the convention is
already how the prose thinks.

### Seeding sites

1. **`/dm:dnd new` — new step 11.5** (after the 3-NPC relationship web, before quest
   seeds): generate 6–8 supporting-cast rows anchored to the settlement and Three
   Truths locations — the places the party will actually walk (innkeeper, gate
   sergeant, fence, ferryman, market fixture). One index row each; registry check each;
   no full entries.
2. **`/dm:dnd prep` — step 1.5 addendum**: after the coverage-driven full entries,
   run the same supporting-cast pass anchored to the settlement and Adventure Nodes.
   Same counts, same fields, same registry check. The asset-pass spoiler discipline
   does not apply here (NPCs are world layer, not host-facing assets).

### Promotion rule

Extends the existing read-before-dialogue bullet in SKILL.md (Active DM Mode): when a
scene centers on an index-only NPC, or before their first substantive dialogue, author
their full entry in npcs-full.md **then** — all fields including personality axes and
≥2 relationships — before writing the dialogue. Registry already has the name.
Demotion does not exist; promotion is one-way.

This is the existing on-demand growth path made explicit, not new machinery. Play-time
improvised NPCs (named on the fly during a scene) enter as supporting-cast rows by
default and follow the same promotion rule.

## Files touched

- `skills/dnd/SKILL-commands.md` — `new` step 11.5; prep step 1.5 addendum.
- `skills/dnd/SKILL.md` — promotion sentence added to the read-before-dialogue bullet.
- `skills/dnd/templates/npcs.md` — header note: index rows without a full entry are
  supporting cast; promote before substantive dialogue.
- `CONTEXT.md` — glossary term *supporting cast* (and *promotion* if absent).
- `docs/ARCHITECTURE.md` — NPC-layer description updated (its header requires this on
  any lifecycle-step change).

## Error handling / edge cases

- **Registry collision on a supporting name** — same handling as core NPCs: regenerate
  the name, re-check.
- **Supporting NPC named in world.md by prep** — coverage rule wins: anyone named in
  world.md gets a full entry (step 1.5 unchanged); the supporting pass adds *new*
  names only.
- **Player latches onto a supporting NPC** — exactly the intended path: Standard 5
  says honour it; the promotion rule says how.

## Testing

Prose-level feature — no scripts change. Acceptance via a probe session per
docs/probes methodology: run `new` and `prep` on a scratch campaign root, verify
6–8 supporting rows appear with one-trait Notes, no npcs-full.md sections for them,
registry entries present; then force a scene on one and verify promotion happens
before dialogue.
