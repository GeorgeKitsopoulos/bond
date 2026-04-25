# Bond Documentation Index

Repository documentation is the canonical source of project truth. Historical design analysis and implementation reports are archived in `docs/archive/` for reference but are not current project truth. Gitea issues and milestones coordinate work, but they do not replace repository truth.

Current project truth should be read from this maintained set first:

- `README.md`
- `ROADMAP.md`
- `CHANGELOG.md`
- `docs/STATE.md`
- `docs/ARCHITECTURE.md`
- `docs/BEHAVIOR_CONTRACT.md`
- `docs/CAPABILITIES.md`
- `docs/SCHEMAS.md`
- `docs/TESTING.md`
- `docs/PUBLICATION_BOUNDARY.md`
- `docs/CLEANUP_PLAN.md`

## Core canonical docs

- `docs/ARCHITECTURE.md`: subsystem boundaries, layer responsibilities, and architecture direction.
- `docs/BEHAVIOR_CONTRACT.md`: behavior rules, safety constraints, and response guarantees.
- `docs/CAPABILITIES.md`: canonical capability registry, classes, status, and execution expectations.
- `docs/MEMORY.md`: memory strata, retrieval lanes, ranking rules, and correction authority.
- `docs/KNOWLEDGE_INGESTION.md`: ingestion/retrieval architecture and document-knowledge boundaries.
- `docs/PROBES.md`: deterministic probe hierarchy, schema, and evidence ranking.
- `docs/CURRENT_PATHS.md`: canonical path and location truth for the current phase.
- `docs/PACKAGING_STRATEGY.md`: layered packaging direction for Python core, platform adapters, and integration-surface boundaries.
- `docs/TESTING.md`: testing doctrine, behavior checks, and regression expectations.
- `docs/GREEK_LANGUAGE_SUPPORT.md`: text-first Greek and mixed-language normalization, policy, retrieval, and localization planning contracts.
- `docs/TRUST_EXTENSIBILITY.md`: trust/explainability, capability discovery, extension boundaries, context-awareness, and interaction-mode design contracts.
- `docs/SURVIVABILITY.md`: operational resilience requirements and degraded-mode governance direction.
- `docs/SCHEMAS.md`: canonical schema and data-contract registry with migration/compatibility rules.
- `docs/PUBLICATION_BOUNDARY.md`: public/private repository boundary policy for publication safety.

## Operational and workflow docs

- `docs/INSTALLATION.md`: install/update/uninstall operating model.
- `docs/SERVICE.md`: optional future service-mode contracts, IPC boundary, and responsibility scope.
- `docs/APPLET.md`: Cinnamon applet integration scope, transport order, UI state model, and cache boundaries.
- `docs/VOICE.md`: optional voice-layer pipeline and safety-boundary constraints.
- `docs/DEVELOPMENT.md`: main contributor workflow and validation process.
- `docs/LLM_OPERATING_GUIDE.md`: AI-assisted maintainer workflow guidance in tool-agnostic form.
- `docs/CURRENT_PATHS.md`: portable path-resolution and runtime-path reference.
- `docs/CHANGE_REVIEW_TEMPLATE.md`: template for change proposals and structured reviews.
- `docs/REVIEW_CHECKLIST.md`: mandatory review checklist and gating reminders.
- `docs/COMMIT_MESSAGE_GUIDE.md`: commit message standards and truthfulness rules.
- `docs/REPOSITORY_REVIEW_NOTE_TEMPLATE.md`: template for repository review notes.
- `docs/RELEASE_PROCESS.md`: release/update/version governance and meaningful checkpoint rules.

## Planning and state docs

- `README.md`: project front door and high-level orientation.
- `ROADMAP.md`: high-level sequencing and near/medium-term direction.
- `CHANGELOG.md`: chronological record of meaningful repository changes.
- `docs/BOND_PROJECT_MASTER_PLAN.md`: master staged plan and workstream sequencing.
- `docs/STATE.md`: point-in-time reality snapshot and known gaps.
- `docs/CLEANUP_PLAN.md`: staged cleanup plan required before Stage 2F work.
- `docs/PLANNING_INTERFACE.md`: boundary between repo truth and external planning systems.
- `docs/GITEA_PROJECT_MANAGEMENT.md`: Gitea issue/milestone/label process guidance.

## Historical documentation archive

- `docs/archive/README.md`: archive usage guidance and public-safety rules.
- `docs/archive/analysis/`: historical design analysis and planning rationale (preserved for reference, not current truth).
- `docs/archive/reports/`: historical implementation notes and migration reports (preserved for reference, not current truth).

## Rule for future docs

Create a new canonical doc only when the topic has a stable boundary. Keep raw analysis in `docs/archive/analysis/`. Do not let archived files become the only place where active architecture is defined. Update `README.md`, `docs/DOCS_INDEX.md`, `docs/BOND_PROJECT_MASTER_PLAN.md`, and affected subsystem docs whenever a new canonical doc is added.
