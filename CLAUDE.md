# claude-dnd-skill

Prose-instruction-driven D&D 5e DM skill. The three `skills/dnd/SKILL*.md` docs are the
program; scripts are deterministic helpers. Map: `docs/ARCHITECTURE.md`. Glossary:
`CONTEXT.md`. Never touch `~/.claude/dnd/campaigns/` (live campaign data).

## Agent skills

### Issue tracker
GitHub Issues on origin fork via `gh`; external PRs not triaged. See `docs/agents/issue-tracker.md`.

### Triage labels
Default vocabulary (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`). See `docs/agents/triage-labels.md`.

### Domain docs
Single-context: `CONTEXT.md` at root + `docs/adr/`. See `docs/agents/domain.md`.
