# Cleanup Plan

## Goal

This cleanup makes the repository portable, public-safe, and easier to maintain before any new feature work proceeds.

## Non-negotiable rules

- preserve unique project knowledge
- do not delete analysis just because it is old
- remove or rewrite duplicated, deprecated, or private details
- do not expose secrets, local paths, runtime data, or personal machine information
- keep current tests passing
- do not start Stage 2F until cleanup gates pass

## Phase P0A — Boundary and map

Status: completed (validated).

Scope:

- add publication boundary
- add cleanup plan
- mark Stage 2F paused
- document Gitea/docs mismatch

## Phase P0B — Source/config/deploy sanitation

Status: completed (validated).

Applied in this phase:

- removed unused `src/bond/ai_summarize_system.py` after confirming no active runtime/script/deploy references
- sanitized `src/bond/ai_core.py` archive fallback to neutral path naming while preserving env/config override behavior
- replaced user-home fixture strings in `src/bond/ai_selftest.py` with neutral placeholders
- updated `src/bond/ai_run.py` safe action execution to use the current interpreter
- normalized `deploy/systemd/user/ai-memory-reflect.service` and `deploy/systemd/user/ai-memory-rotate.service` to portable `%h`-based examples
- preserved and expanded selftest coverage; baseline is passing

Required later changes:

- quarantine or remove `src/bond/ai_summarize_system.py` if confirmed unused
- remove or isolate legacy local path fallback in `src/bond/ai_core.py`
- replace user-home test fixtures in `src/bond/ai_selftest.py`
- make `src/bond/ai_run.py` use the current interpreter rather than bare `python3` where appropriate
- normalize `deploy/systemd/user/ai-memory-reflect.service`
- normalize `deploy/systemd/user/ai-memory-rotate.service`
- add missing ignore rules for Python/tool/cache/coverage outputs
- keep compile and selftest green

## Phase P0C — Public documentation consolidation

Status: completed (validated).

Applied in this phase:

- rewrote `README.md` for public human readers
- rewrote `docs/DEVELOPMENT.md` as the main tool-agnostic contributor workflow guide
- rewrote `docs/LLM_OPERATING_GUIDE.md` as an AI-assisted maintainer guide without prompt scaffolding
- sanitized `docs/CURRENT_PATHS.md` to placeholder-based portable path references
- removed obsolete tool-specific prompt/operator workflow files from current tracked public docs

Required later changes:

- rewrite `README.md` for public human readers
- sanitize `docs/CURRENT_PATHS.md`
- rewrite or merge `docs/DEVELOPMENT.md`
- update `docs/DOCS_INDEX.md`
- remove tool-specific workflow documents as current workflow truth
- move useful workflow rules into normal contributor guidance
- keep prompt/session/operator templates private or archive them away from public-facing docs

P0D remains for historical analysis/reports preservation and archiving decisions.

P0E remains for Gitea/docs milestone and issue reconciliation.

## Phase P0D — Historical analysis and reports preservation and archival

Status: completed (validated).

Applied in this phase:

- moved all historical analysis files into `docs/archive/analysis/`
- moved all historical implementation report files into `docs/archive/reports/`
- created `docs/archive/README.md` with archive usage guidance and public-safety rules
- added historical-warning banners to all archived markdown files
- sanitized local/private paths in archived files (replaced user-home paths, system paths, and machine-specific identifiers with neutral placeholders)
- updated `docs/DOCS_INDEX.md` to reference the archive and clarify that archived material is not current truth
- preserved Stage 2E behavior; no product capabilities were added
- validation baseline remains passing: compile and selftest 61/61

Required later changes:

- none; P0D preserved historical design rationale under `docs/archive/analysis/`
- P0D preserved historical implementation records under `docs/archive/reports/`
- P0D has archived historical material so it cannot be mistaken for current truth
- P0D has sanitized local paths in historical material before public release

## Phase P0E — Gitea/docs reconciliation

Status: completed (validated).

Applied in this phase:

- reconciled the actual local Gitea tracker with the repository roadmap model
- created/opened tracker milestones: `P0`, `M1`, `M2`, `M3`, `M4`, `M5`, `M6`, and `Later / Backlog`
- closed legacy `Phase 1` through `Phase 6` milestones as historical tracker structure without deleting them
- closed issue #2 as completed with explicit reconciliation context
- moved remaining open issues into current milestone lanes (`M1` and `M2`)
- verified post-reconciliation tracker state against expected milestone and issue mappings

Required later changes:

- maintain alignment between `ROADMAP.md`, `docs/STATE.md`, and live Gitea milestone/issue state
- keep legacy tracker history preserved (closed, not deleted)

## Phase P0F — Public GitHub preparation

Status: in progress (P0F-A1 completed).

Applied in this phase:

- public-candidate validation surfaced stale current-doc references to removed pre-archive paths and removed tool-specific workflow files
- cleaned current docs to use archive paths or current workflow docs before public candidate recreation

Required later changes:

- prepare clean public tree
- add/verify GitHub Actions
- use a fresh sanitized first public commit
- keep private Gitea/local repo as internal history unless intentionally migrated later

## Cleanup gates before Stage 2F

- compile passes
- full selftest passes
- no hardcoded user path scan hits in active source/deploy/current docs except intentional explanatory examples with placeholders
- no tracked runtime/private files
- public docs no longer use assistant/operator prompt language
- Gitea/docs mismatch gate is satisfied through P0E reconciliation
- Stage 2F may resume after P0E completion and commit
- P0F remains required before any public GitHub release
- git status clean
