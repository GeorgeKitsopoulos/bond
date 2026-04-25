# Gitea Project Management

This document defines how Gitea planning artifacts map to repository-governed engineering work.

## Core mapping

- issues = tasks
- milestones = roadmap-aligned workstreams
- repo docs = truth

Planning data in Gitea is operationally useful, but repository documentation and code remain the source of truth for architecture, behavior, safety, capability, and testing contracts.

Repository truth sources:

- Architecture and routing design: `docs/ARCHITECTURE.md`
- Capability registry and doctrine: `docs/CAPABILITIES.md`
- Master plan and workstreams: `docs/BOND_PROJECT_MASTER_PLAN.md`
- Roadmap and exit criteria: `ROADMAP.md`
- Current state: `docs/STATE.md`
- Routing design authority: `docs/archive/analysis/Bond_Router_Agent_Redesign_Updated.md`
- Capability expansion design: `docs/archive/analysis/Bond_Capability_Expansion_Plan.md`

## Repository metadata recommendations

Repository description recommendation:

`Local-first AI assistant for Linux Mint with guarded actions, deterministic system probes, structured memory, and repo-first architecture.`

Recommended topics:

- `ai-assistant`
- `local-first`
- `linux-mint`
- `python`
- `offline-ai`
- `system-automation`
- `memory-system`
- `deterministic-tools`
- `gitea`
- `cinnamon`

## Wiki strategy

Use a small wiki only.

Repository docs remain canonical.
Every wiki page should link back to canonical repository docs.

## Issue templates to create later

- bug report
- design/spec proposal
- docs gap
- behavior regression
- implementation task

## Label system

Labels should be explicit, composable, and stable enough to support filtering and release planning.

Recommended label groups:

- type:bug
- type:feature
- type:docs
- type:refactor
- type:test
- type:infra
- priority:p0
- priority:p1
- priority:p2
- priority:p3
- status:blocked
- status:needs-info
- status:ready
- status:in-progress
- status:review
- status:done
- risk:low
- risk:medium
- risk:high
- risk:privacy
- risk:trust
- area:parser
- area:policy
- area:execution
- area:probes
- area:memory
- area:docs
- area:testing
- area:packaging
- area:service
- area:applet
- area:voice
- area:router
- area:capabilities
- area:trust
- area:extensibility
- area:plugins
- area:modes
- area:context
- area:gitea-workflow
- area:release
- area:schemas
- area:integrity

Current practical baseline after P0E reconciliation:

- area labels remain active and useful
- type labels remain active and useful
- priority labels should use `priority:p1`, `priority:p2`, and similar p-series labels
- status labels may use `status:ready`, `status:needs-info`, and `status:done`
- old `critical:*` and `priority:high/medium/low` labels should be treated as legacy unless intentionally retained on historical issues

Label rules:

- Every issue should have exactly one type label.
- Every issue should have exactly one priority label.
- Every issue should have at least one area label.
- Risk labels are required for behavior, execution, or safety-related changes.
- Status labels must reflect current workflow state and be updated when state changes.

## Issue structure

Issues should define implementation-scoped tasks, not vague intentions.

Required issue fields:

- Title: short, action-oriented, and specific.
- Problem statement: what is wrong or missing right now.
- Scope: what is included and explicitly excluded.
- Acceptance criteria: objective completion checks.
- Documentation impact: which repository docs must be updated.
- Test impact: required tests to add or adjust.
- Risk notes: failure modes and safety implications.
- Dependencies: blocking issues, external inputs, or prerequisite milestones.

Issue writing rules:

- Do not describe behavior that is not implemented as if it already exists.
- Do not encode architectural truth only in issue comments.
- Keep issue text consistent with repository contracts in architecture, behavior, testing, and capability documents.
- If issue intent changes materially, update the issue body and related repository docs in the same work cycle.

## Milestone mapping

Milestones represent repository workstreams and should map directly to roadmap checkpoints.

Current milestone structure:

- P0: Repository Cleanup and Public Migration Preparation
- M1: Router, Policy, and Execution Safety Foundations
- M2: Capability Registry and Tool Boundary
- M3: Memory and Knowledge Substrate
- M4: Greek Language and Locale Support
- M5: Service/Applet/Voice Interfaces
- M6: Packaging and Public Release
- Later / Backlog

Legacy tracker history:

- old Phase 1-6 milestones are legacy tracker history
- those legacy milestones should remain closed and should not be deleted
- closed legacy milestones preserve planning continuity while current work uses the roadmap-aligned milestone model

Recommended roadmap-aligned mapping:

- P0 tracks cleanup/reconciliation/publication-prep work
- M1-M6 track active engineering workstreams
- Later / Backlog tracks deferred non-blocking work

Milestone rules:

- Every issue must be assigned to one milestone or explicitly marked unplanned.
- Milestone scope should be constrained by documented exit criteria in the roadmap.
- Closing a milestone requires validating exit criteria against repository state, not issue count alone.
- Cross-milestone spillover must be re-scoped explicitly, not silently carried.

Synchronization note: milestone scope and exit criteria are defined in `ROADMAP.md`. If Gitea milestone descriptions diverge from `ROADMAP.md`, the roadmap takes precedence. Gitea milestones coordinate work; they do not define exit criteria.

## Repository-truth rule

No logic lives ONLY in issues.

Any logic that affects architecture, behavior, capability, safety, probes, memory, or testing must be represented in repository documentation and/or code. Issue trackers coordinate work; they do not define the system alone.
