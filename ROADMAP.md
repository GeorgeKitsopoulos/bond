# Roadmap

This file defines the staged development roadmap for Bond at the repository level.

It is not a transcript, not a changelog, and not a speculative wish list.
Its purpose is to show the intended order of serious work so the repository can act as the primary operational source of truth.

The roadmap reflects the current project reality:

- Bond has a real base
- Bond is still in a transitional repository-first phase
- core decision behavior is not yet reliable enough
- documentation and maintenance discipline still need to catch up with actual project history
- future features must not be treated as current capabilities

## Roadmap rules

The roadmap should be read with these rules:

- stages describe intended work order, not proof of completion
- items remain incomplete until implemented and validated
- this file should not claim work is done unless the repository actually reflects it
- documentation work is part of engineering, not optional polish
- assistant-facing features must not outrun truth, safety, or maintainability
- Linux Mint remains the primary target until the architecture is strong enough to generalize safely

## P0 - Repository Cleanup and Public Migration Preparation

P0A-P0E are completed and validated. Stage 2F work may resume after P0E validation.

P0F remains required before any public GitHub release.

P0A - Boundary and map (completed)

- add publication boundary policy
- add staged cleanup plan
- keep Stage 2F paused during cleanup
- document current Gitea/docs mismatch

P0B - Source/config/deploy sanitation (completed)

- sanitize path debt in active source, tests, and deploy artifacts
- isolate/remove legacy local fallbacks where confirmed
- keep compile and full selftest green

P0C - Public documentation consolidation (completed)

- rewrite/merge public-facing docs for human readers
- remove deprecated workflow truth from public docs
- keep internal local workflow artifacts out of public-facing documentation

P0D - Historical analysis preservation (completed)

- preserve analysis and reports as historical rationale/record
- archive/move historical material so it cannot be mistaken for current truth
- sanitize historical material if it remains public

P0E - Gitea/docs reconciliation

- reconcile roadmap/state documentation with tracker milestones/issues
- close, rewrite, or map stale tracker items without erasing planning history
- completed: tracker state now reconciled with the roadmap milestone model
- legacy Phase 1-6 milestones remain closed as tracker history

P0F - Public GitHub preparation

- prepare clean public tree
- add/verify GitHub Actions
- publish from a fresh sanitized first public commit

Reconciliation note: Gitea milestones were reconciled to the roadmap model during P0E. Legacy Phase 1-6 milestones remain closed as tracker history.

## Milestone roadmap (integrated)

This milestone view is the primary tracking index for near-term planning. It integrates with the detailed stage descriptions below and does not replace their engineering detail.

### Milestone status snapshot (repository evidence)

This snapshot is a repository-side read/update view. It does not overwrite external tracker metadata.

| Milestone | Status | Read state | Progress |
|-----------|--------|------------|----------|
| M0 - Docs + Repo structure | closed | read | 100% ██████████ |
| M1 - CLI + packaging baseline | in progress | read | 55% ██████░░░░ |
| M2 - Policy + capability registry | in progress | read | 80% ████████░░ |
| M3 - Parser fixes | open | unread | 30% ███░░░░░░░ |
| M4 - Probes + telemetry | open | unread | 35% ████░░░░░░ |
| M5 - Memory + corrections | open | read | 45% █████░░░░░ |
| M6 - Testing expansion | open | read | 60% ██████░░░░ |
| M7 - Service layer | open | unread | 10% █░░░░░░░░░ |
| M8 - Applet | open | unread | 5% ░░░░░░░░░░ |
| M9 - Voice | open | unread | 5% ░░░░░░░░░░ |
| M10 - Integrity, release, and survivability hardening | open | unread | 15% ██░░░░░░░░ |

Status update rules:

- completed milestones remain listed and are marked `closed` + `read`; they are never removed from this snapshot
- milestone progress should be updated incrementally from repository evidence (docs, tests, code), not guessed from issue count
- if external milestone tools differ, this snapshot remains a repo-local operational view and does not overwrite external records

Canonical governance docs for this roadmap track:

- `docs/SURVIVABILITY.md`
- `docs/SCHEMAS.md`
- `docs/RELEASE_PROCESS.md`

### M0 - Docs + Repo structure

Goal:

- establish repository documentation as the durable operational source of truth

Exit criteria:

- README, architecture, behavior, capability, memory, and probe documents define explicit contracts
- repository documentation is internally cross-consistent for current phase claims
- roadmap and changelog structure are clear enough to support milestone-driven work
- survivability, schema-registry, and release-governance docs exist as canonical references and are linked from planning docs

### M1 - CLI + packaging baseline

Goal:

- define and stabilize the CLI-facing entry model and transitional packaging baseline

Exit criteria:

- CLI invocation model is documented and bounded
- packaging/install/update direction is documented with no false claims of maturity
- repository-first execution and install assumptions are explicit
- update lifecycle expectations reference schema checkpoints, rollback notes, and release-governance rules
- package metadata, explicit entry point, and local controlled install lifecycle are documented
- Stage 1 local controlled install via `pipx`/isolated environment is explicit and bounded
- Stage 2 platform adapters direction is documented without changing Python core contracts

### M2 - Policy + capability registry

Goal:

- enforce explicit policy outcomes and capability truth through a registry-backed contract

Current checkpoint note:

- Stage 2B policy gate, Stage 2C action contract/dry-run behavior, and Stage 2D confirmation-token flow are implemented and covered in integrated selftests.
- capability registry implementation remains open; this milestone is not complete.

Exit criteria:

- policy decision outcomes and reason codes are documented and constrained
- capability registry fields and initial capability states are defined
- unsupported capability claims are explicitly prohibited by contract
- capability classes (inspector, handoff, bounded_mutator, privileged_lane) are defined
- rootless-first doctrine is documented as a hard design constraint
- registry schema includes rootless, side_effects, backends, degraded_modes, result_schema, error_schema, and audit_tag fields
- capability discovery contracts are defined for `what can you do?` answers from capability registry + probes
- high-level explanation capability contracts are defined with hidden chain-of-thought non-disclosure boundaries

#### Routing contract

- routing dispatch pattern is documented (pre-filter → dispatcher → policy gate → specialist → optional refinement)
- route keys in `config/router/profiles.json` are treated as configured route targets and are reviewed against live installed roster and runtime availability
- dispatcher role is constrained to structured output only; it does not answer the user directly
- policy gate behavior is documented as deterministic validation, not model-based safety guessing
- current lean roster is explicitly documented as qwen2.5:3b-instruct, gemma2:2b, qwen2.5:7b-instruct, and nomic-embed-text:latest
- no current heavyweight local model tier is assumed in routing or capability planning
- roadmap success depends on using the current roster better, not assuming a larger local model later absorbs complexity

### M3 - Parser fixes

Goal:

- improve parser reliability while keeping parsing strictly separate from policy authority

Exit criteria:

- parse result schema is documented and used as the parser output contract
- ambiguity and mixed-intent signals are extracted explicitly rather than implied
- parser behavior does not approve or execute actions
- Greek/mixed-language invocation normalization and language-state contracts are documented

### M4 - Probes + telemetry

Goal:

- establish deterministic probe-grounded system inspection with practical telemetry direction

Exit criteria:

- probe categories and probe output schema are documented
- probe usage is defined as deterministic and safety-bounded
- telemetry/service direction is documented without claiming final implementation
- three probe layers are defined: Layer 0 (authoritative OS facts), Layer 1 (user-environment facts), Layer 2 (derived assistant-usable facts)
- the model is documented as reasoning from Layer 2 only, not from raw Layer 0/1 scan dumps
- probe documentation distinguishes configured route targets, installed local model inventory, and runtime availability/reachability
- default app/backend resolution follows documented evidence ranking: explicit default handler → desktop/session API fact → desktop entry match → installed binary presence → heuristic fallback
- documentation and planning remain compatible with the current lean roster, with qwen2.5:7b-instruct as the highest-capability local baseline and no heavyweight local fallback assumed
- probe and telemetry direction includes startup health-check expectations and explicit degraded-mode visibility requirements
- context/probe truth requirements are defined for `what can you do here?` answers based on current environment/session evidence

#### Capability adapter phases

- adapter boundary concept is documented: capability contracts map to platform-specific adapter implementations
- degraded mode handling is defined: adapters must declare degraded paths when preferred backends are unavailable
- Linux adapter family is documented as the canonical baseline (XDG, portals, D-Bus, user-level systemd)
- adapter schema fields (backends, degraded_modes) are present in the capability registry

### M5 - Memory + corrections

Goal:

- define structured memory records and correction ingestion so memory improves truthfulness rather than adding noise

Exit criteria:

- memory record types and schemas are documented
- correction ingestion flow is documented with update rules for prior claims
- retrieval priority rules distinguish current truth from history
- memory-related stores are covered by schema-version and migration-path requirements to prevent silent drift
- bilingual retrieval metadata requirements are defined for Greek and English retrieval grounding

### M6 - Testing expansion

Goal:

- expand testing to validate assistant behavior contracts, not only subsystem survival

Exit criteria:

- behavioral test categories are documented for policy, safety, capability honesty, and probe correctness
- mixed-intent, dangerous-action refusal, and unsupported-capability behavior are covered by test direction
- test expectations are aligned with documented behavior contracts
- Greek and mixed-language regression suite requirements are documented

Current checkpoint note:

- integrated selftest baseline currently passes 60/60 with coverage for routing, policy, action-contract/dry-run, mixed-intent rejection, high-risk confirmation-required, parser-contract preflight behavior, events bucket, and core memory flows
- integrated selftest baseline now includes confirmation-token flow coverage (token creation, invalid/expired/consumed handling, confirmed dry-run, and non-reuse)
- Stage 2E improves parser honesty and preflight failure behavior but does not expand the executor or implement capability registry
- this does not imply full behavioral coverage or assistant maturity

### M7 - Service layer

Goal:

- define and prepare a bounded service/daemon layer after core decision behavior is stable enough

Exit criteria:

- service mode boundaries and supervision direction are documented
- background lifecycle expectations are documented without bypassing policy controls
- service direction remains subordinate to core correctness and safety contracts
- service integration remains separate from packaging core and platform adapter concerns
- service design references `docs/SERVICE.md`

### M8 - Applet

Goal:

- define desktop applet integration as a thin interface over a policy-safe core

Exit criteria:

- applet-facing responsibilities and non-responsibilities are documented
- applet layer does not introduce unsupported capability claims
- applet work is explicitly sequenced after core policy/parse/probe reliability milestones
- future GUI locale/message catalog readiness is documented for localized user-facing strings
- applet integration remains separate from packaging core and platform adapter lifecycle
- applet integration contracts reference `docs/APPLET.md`

### M9 - Voice

Goal:

- define voice interaction as a later interface layer on top of a trustworthy text-first core

Exit criteria:

- voice scope and guardrail constraints are documented
- wake/invocation handling remains consistent with parser and policy contracts
- voice plans do not bypass safety, capability honesty, or deterministic grounding requirements
- voice remains optional and later; Greek text support is not blocked by voice
- voice-layer contracts reference `docs/VOICE.md`

### M10 - Integrity, release, and survivability hardening

Goal:

- define and harden integrity, schema governance, release governance, and survivability requirements before stable treatment

Exit criteria:

- survivability requirements are documented and aligned with planning, state, and testing docs
- schema/data contract registry is defined with migration and compatibility rules
- release/update governance is documented with validation and rollback requirements
- integrity/degraded-mode expectations are explicit and do not claim implementation completion
- plugin/extension groundwork contracts are defined (registration, permissions/risk declaration, policy gating, health, and failure boundaries)
- multi-profile groundwork contracts are defined (profile identity, per-profile memory boundaries, and shared-vs-private data rules)

## Stage 0 — Repository-first documentation baseline

Objective: make the repository understandable without requiring prior chat history.

Required outcomes:

- README acts as a real project front page
- changelog discipline is defined
- roadmap is explicit and staged
- core docs are cross-consistent
- repository docs begin absorbing durable knowledge that previously lived only in transcript history
- Gitea-side project metadata can be populated from a stable documentation base

Why this stage exists:

Bond already has code and project direction, but the repository still under-documents too much of the real system, the real constraints, and the actual plan.

## Stage 1 — Repository operating model and maintenance discipline

Objective: make the repository behave like a maintainable software project rather than a loose engineering notebook.

Required outcomes:

- installation, update, and uninstall flows are documented
- development workflow expectations are documented
- contributor workflow constraints are documented in `docs/DEVELOPMENT.md`
- issue labels, milestones, and release discipline can be defined from repository docs
- packaging direction is documented clearly enough to constrain future implementation
- repo truth is prioritized over scattered runtime assumptions

Key constraints:

- avoid pretending the project is already distribution-grade packaged
- avoid documenting fantasy deployment flows that do not exist yet
- keep development workflow strict and bounded

## Stage 2 — Path, layout, and runtime normalization

Objective: finish the transition away from environment-specific loose-script assumptions.

Required outcomes:

- hardcoded paths are removed or isolated
- repository-relative and install-time path resolution are clearly defined
- runtime, config, state, memory, logs, and archive roles are documented and separated
- current live paths are treated as migration facts, not architectural ideals
- wrapper/entry behavior is aligned with the new project layout

Key constraints:

- preserve working behavior during migration
- do not break the only functioning local instance recklessly
- distinguish migration compatibility from final architecture

## Stage 3 — Entry points, command surface, and assistant invocation

Objective: define how Bond is invoked as a real assistant-facing program.

Required outcomes:

- Bond-facing CLI entry model is documented
- repository-level command entry design is documented
- alias and invocation normalization goals are documented
- assistant invocation forms are clarified for English and Greek usage
- old wrapper behavior is treated as transitional where appropriate

Examples of intended invocation direction include forms such as:

- `bond hey`
- `bond open downloads`
- `bond show me the weather`
- `hey bond`
- `μποντ άνοιξε τις λήψεις μου`

Key constraints:

- do not confuse invocation design with voice-product design
- do not claim natural-language robustness before it is actually implemented
- keep interface truth above convenience theater

## Stage 4 — Decision-stack refactor

Objective: correct the central behavioral weaknesses without discarding the whole architecture.

Required outcomes:

- parsing, action policy, capability truth, and execution are separated more explicitly
- central orchestration becomes simpler and less heuristic-heavy
- unsupported actions stop being presented as available
- ambiguous actions stop being guessed too aggressively
- general assistant sanity becomes a first-class engineering target

Subsystems expected to be clarified or redesigned include:

- orchestrator / run layer
- action parsing
- action policy classification
- capability truth layer
- execution boundary
- system-probe integration
- memory retrieval gating

Key constraints:

- preserve modularity
- avoid god-files
- avoid fake multi-agent theater (narrow contract-bound routed roles are acceptable; uncontrolled persona-based or boundary-free agent behavior is not)
- favor explicit boundaries over hidden heuristic drift

### Target routing pattern

The decision stack should converge on this layered routing architecture:

1. Deterministic pre-filter — rule-based, no model inference required; handles hard overrides, risk flagging, and type classification
2. Structured dispatcher (3B-class) — normalizes intent, classifies task type, recommends specialist; always returns schema-constrained output, never answers the user directly
3. Policy gate — validates dispatcher output deterministically; decides what is allowed, not what seems appropriate
4. Specialist (7B-class) — performs the actual task within its domain contract
5. Optional output refinement — formatting/readability pass, not re-reasoning

No current heavyweight local model tier is part of the baseline; complex work should be handled through decomposition, retrieval grounding, policy gates, validation, and narrower specialist contracts around the current lean roster.

See `docs/archive/analysis/Bond_Router_Agent_Redesign_Updated.md` for the detailed design.

## Stage 5 — Capability grounding and system probes

Objective: make Bond answer and act based on real local truth rather than guesswork.

Required outcomes:

- system-probe model is documented
- capability registry direction is documented
- deterministic information probes are separated from freeform model answers
- environment, package, session, filesystem, and other local inspections are treated as structured grounded inputs where appropriate
- unsupported capabilities are explicitly identified instead of implied

Key constraints:

- more system awareness must not become uncontrolled shell freedom
- actions must remain policy-gated
- truthfulness is more important than appearing broadly capable

### Capability expansion direction

The capability stack should expand using:

- rootless-first doctrine as a hard design constraint, not a preference
- capability classes: inspector (read-only), handoff (platform delegation), bounded_mutator (scoped write with confirmation), privileged_lane (explicit escalation lane)
- three-layer system fact hierarchy: Layer 0 (authoritative), Layer 1 (user-environment), Layer 2 (derived assistant-usable)
- typed adapter contracts per capability: each capability maps to platform-specific adapter implementations
- degraded mode declarations: capabilities must name fallback paths when preferred adapters are unavailable

The capability registry in `docs/CAPABILITIES.md` is the canonical truth source. The model must reason from Layer 2 facts only.

See `docs/archive/analysis/Bond_Capability_Expansion_Plan.md` for the full design.

## Stage 6 — Memory architecture, document knowledge, and ingestion discipline

Objective: build a typed, provenance-tracked, retrieval-first knowledge architecture without letting memory hijack unrelated prompts or conflating document ingestion with model adaptation.

Required outcomes:

- typed memory roles are documented clearly: Live Truth Layer, Durable Fact Layer, Episodic Operational Memory, Document Knowledge Memory, Correction Memory, and Learned Model Adaptation Layer boundary
- explicit Correction Memory is defined as a first-class record type with override authority over superseded facts in the same domain
- Document Knowledge Memory is first-class: it is a separate stratum from durable fact memory, with its own ingestion pipeline and retrieval interface
- ingestion lifecycle is documented end-to-end: file detection, type classification, parsing by modality, normalization, chunking, embedding, indexing, and validation
- semantic retrieval is the target for document knowledge: lexical-only lookup is insufficient; embedding-based or hybrid retrieval is the target
- provenance and trust metadata are required on all memory and document records: source type, source reference, confidence, verification status, stale-after, modality, and extraction method
- file change, supersession, and deletion behavior are documented: hash-based change detection drives incremental reindexing; source file deletion propagates to chunk and embedding removal
- files dropped into the knowledge folder default to ingestion and retrieval, not automatic model training; this distinction is explicit
- archive and history retrieval discipline is documented: archive is history and recovery, not automatic current truth; archive retrieval is opt-in and query-driven
- model adaptation comes only after ingestion, retrieval, provenance, and correction discipline are stable and reliable

Key constraints:

- do not turn memory into a catch-all dump
- do not let archive or history outrank current verified live state
- do not treat reflection as evidence; reflection is not evidence of system state or verified fact; it is hypothesis and lesson
- do not conflate document knowledge with durable facts; an ingested document is not a durable fact record
- do not conflate ingestion with model training; ingestion produces retrievable chunks, not adapter weights

Multimodal document parsing clarification: multimodal handling for PDFs, scanned images, and standalone image files belongs to this stage as part of the document knowledge ingestion pipeline. Voice, conversational, and interface-level multimodality remain later-stage work defined in Stage 10.

Sequencing within Stage 6:

1. formalize memory ontology and enrich fact/correction schemas with provenance fields
2. build document knowledge ingestion pipeline and chunk store
3. add semantic retrieval over document knowledge
4. implement gated fact and correction promotion
5. improve archive and history retrieval discipline
6. only then introduce curated local model adaptation, if needed

## Stage 7 — Behavioral testing and sanity enforcement

Objective: make testing reflect real assistant quality, not merely subsystem survival.

Required outcomes:

- behavioral test classes are documented
- unsupported-capability honesty is tested
- dangerous-action refusal is tested
- mixed-intent handling is tested
- lexical hijack resistance is tested
- system-probe correctness is tested
- project-versus-general-assistant separation is tested

Key constraints:

- passing tests must become more meaningful
- avoid overfitting tests to transcript-specific phrasing only
- test the real failure modes observed during live stress testing

## Stage 8 — Packaging and controlled deployment

Objective: move from repository-only development toward a cleaner installable program shape.

Required outcomes:

- packaging direction is documented before implementation expands
- console entry point direction is documented
- centralized install/update/uninstall expectations are documented
- runtime deployment shape is documented at a practical level
- temporary deployment discipline remains compatible with repository-first development

Key constraints:

- do not overpromise final packaging maturity
- do not mix “temporary controlled install flow” with “finished distribution packaging”
- keep deployability subordinate to correctness and maintainability

## Stage 9 — Service mode, desktop integration, and telemetry

Objective: prepare for a more assistant-like local presence after the core becomes trustworthy enough.

Required outcomes:

- service/daemon direction is documented
- timing/telemetry direction is documented
- desktop integration expectations are documented
- Cinnamon-facing work is framed as a later layer on top of a stronger core
- background/runtime supervision direction is documented without pretending it is already final

Key constraints:

- do not push desktop polish ahead of architectural correctness
- do not hide capability gaps behind interface gloss
- telemetry must be truthful, not theater

## Stage 10 — Voice and multimodal interaction

Objective: define the later path toward voice and broader human interaction layers.

Required outcomes:

- voice direction is documented as a later phase
- wake/invocation considerations are kept separate from core parsing correctness
- local-first and guardrail concerns remain explicit
- multimodal ambitions do not erase the requirement for truthful core behavior

Key constraints:

- voice is not a substitute for fixing the decision stack
- do not build a polished shell around an untrustworthy core
- keep the core usable in text-first mode before expanding outward

## Stage 11 — Broader portability

Objective: prepare for eventual expansion beyond the current primary environment.

Required outcomes:

- Linux Mint remains the reference platform
- broader Linux portability is treated as the next portability target
- Windows and Android platform adapters are treated as later ports, not current assumptions
- Android remains a separate product layer rather than a direct desktop-linux-equivalent packaging target
- path, packaging, and capability design are shaped to reduce future porting pain

Key constraints:

- do not generalize too early
- avoid platform abstraction theater before the Linux-first architecture is sound
- portability should emerge from good structure, not vague claims

## Stage 12 — Mature repository project operations

Objective: make Bond manageable as a serious long-term software project.

Required outcomes:

- release discipline is real
- issue and milestone discipline is real
- repo docs are sufficient for collaborators and future LLM sessions
- transcript dependence is reduced naturally because the repository carries the durable truth
- maintenance overhead is reduced by clarity, structure, and bounded workflows

## What is deliberately not prioritized first

The following are explicitly not first-order priorities until earlier stages are stronger:

---

## Cross-document alignment

- Architecture: `docs/ARCHITECTURE.md`
- Capability registry: `docs/CAPABILITIES.md`
- Master plan: `docs/BOND_PROJECT_MASTER_PLAN.md`
- Current state: `docs/STATE.md`
- Gitea planning: `docs/GITEA_PROJECT_MANAGEMENT.md`
- Routing design authority: `docs/archive/analysis/Bond_Router_Agent_Redesign_Updated.md`
- Capability expansion design: `docs/archive/analysis/Bond_Capability_Expansion_Plan.md`

- polished Cinnamon applet UX
- voice-first interaction
- broad GUI polish
- unrestricted system-wide power
- early Android or Windows port work
- appearance of intelligence at the expense of truthfulness

## Summary

Bond should progress in this order:

1. repository documentation baseline
2. repository operating model
3. path and runtime normalization
4. assistant-facing entry design
5. decision-stack correction
6. capability grounding
7. memory quality
8. behavioral testing
9. packaging and deployment
10. service and desktop integration
11. voice and multimodal layers
12. broader portability
13. mature long-term repo operations

The core rule is simple:

Bond must become more explicit, more grounded, more maintainable, and more truthful before it becomes more ambitious.
