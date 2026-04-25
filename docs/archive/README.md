# Documentation Archive

This directory keeps historical design analysis and implementation reports.

Archived documents are preserved because they contain useful reasoning, tradeoffs, decisions, and migration history. They are not the current source of truth for the project.

For current project status, use:

- `README.md`
- `ROADMAP.md`
- `CHANGELOG.md`
- `docs/STATE.md`
- `docs/ARCHITECTURE.md`
- `docs/BEHAVIOR_CONTRACT.md`
- `docs/CAPABILITIES.md`
- `docs/SCHEMAS.md`
- `docs/TESTING.md`
- `docs/DEVELOPMENT.md`
- `docs/PUBLICATION_BOUNDARY.md`
- `docs/CLEANUP_PLAN.md`

## Archive sections

- `analysis/` contains historical design analysis and planning rationale.
- `reports/` contains historical implementation notes and migration reports.

## How to use archived documents

Archived documents can explain why a design exists or what alternatives were considered. They should not be used to override current code, tests, or current documentation.

When an archived document contains a useful decision that should remain active, extract the decision into a current document instead of treating the archived file as active policy.

## Public-safety rule

Archived documents must not expose real local paths, private machine details, credentials, runtime logs, private assistant memory, or local planning system data. Use placeholders such as `<repo>`, `<config-home>`, `<data-home>`, `<state-home>`, `<cache-home>`, `<archive-root>`, `<user>`, and `<host>`.
