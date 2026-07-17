# claude-dnd-skill

Prose-instruction-driven D&D 5e DM skill. The three `skills/dnd/SKILL*.md` docs are the
program; scripts are deterministic helpers. Map: `docs/ARCHITECTURE.md`. Glossary:
`CONTEXT.md`. Never touch `~/.claude/dnd/campaigns/` (live campaign data).

## Live install (how edits reach play)

The running plugin's skill dir is a **symlink into this working tree**:
`~/.claude/plugins/cache/neural-initiative/dm/2.3.0/skills/dnd -> <repo>/skills/dnd`
(the F1 fix, 2026-07-14). Edits here go live at the **next session start** — the harness
caches SKILL.md per session, so an in-flight DM session won't see them (F1 staleness).
Two warnings: never run `/plugin update dm` (the plugin manager would replace the cache
dir and sever the symlink — reinstall the symlink if it ever happens), and
`update_skill.py`'s default version check points at **upstream** neuralinitiative, not
this fork — its output is not authoritative for this install.

## Agent skills

### Issue tracker
GitHub Issues on origin fork via `gh`; external PRs not triaged. See `docs/agents/issue-tracker.md`.

### Triage labels
Default vocabulary (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`). See `docs/agents/triage-labels.md`.

### Domain docs
Single-context: `CONTEXT.md` at root + `docs/adr/`. See `docs/agents/domain.md`.
