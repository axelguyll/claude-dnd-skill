# Graft in SKILL prose and templates, not upstream Python

**Status:** accepted (founding constraint, dm-app ADR-0016; restated 2026-07-16)

This repo is a fork of `neuralinitiative/claude-dnd-skill` (AGPL-3.0) that must stay
cleanly mergeable with upstream. All fork-specific behavior (milestone leveling, deed
ledger, spine grafting) therefore lands in SKILL prose and templates; upstream Python is
left untouched wherever possible, and fork-owned scripts live in separate paths
(`scripts/prep/`).

## Consequences

- Upstream merges stay small and mechanical.
- Behavioral overrides are enforced only by prose (e.g. `xp.py` is *uncalled*, not
  deleted) — so prose/script drift is the fork's characteristic failure mode, and prose
  contracts need periodic verification against actual CLIs (docs/ARCHITECTURE.md §7).
- AGPL-3.0 is accepted: personal use, never closed-sourced or hosted.
