# Bond Project Master Plan

This document is the master repository-level plan for Bond.

It is the broadest planning document in the repository.
It exists to connect:

- current project reality
- corrective architecture direction
- staged engineering work
- later expansion paths

It is not a changelog.
It is not a transcript.
It is not proof of completion.

Its purpose is to define the intended program shape and the order in which Bond should become a serious local assistant system.

## Master rule

Bond must not expand in surface area faster than it improves in truthfulness, grounding, control, and maintainability.

If there is a conflict between:

- broader features
- and stronger foundations

the foundations win.

## Project identity

Bond is intended to become:

- a local assistant
- repository-first
- Linux Mint-first
- modular
- system-aware
- memory-capable
- action-capable under strict control
- progressively portable

Bond is not intended to become:

- a fake all-powerful assistant
- a prompt-only illusion layer
- an uncontrolled shell wrapper
- a UI shell hiding a weak core

## Primary long-term goal

Build Bond into a serious local assistant that can:

- understand user requests more naturally
- inspect local system state truthfully
- answer with grounded knowledge
- perform controlled local actions
- retain useful memory without corrupting current truth
- expose honest capability boundaries
- later support richer interfaces without compromising the core

## Program-shape objectives

The long-term repository/program shape should include:

1. a clear package structure
2. clean entry points
3. explicit subsystem boundaries
4. structured configuration and path resolution
5. a policy-gated execution model
6. real system probes
7. typed memory roles
8. meaningful behavioral tests
9. controlled deployment shape
10. later service and desktop integration
11. later voice/multimodal layers
12. later broader portability
13. operational survivability requirements
14. schema and data contract governance
15. health diagnostics and degraded-mode transparency
16. release, update, and rollback governance

## Current reality anchor

All planning in this document must stay anchored to current reality:

- Bond has a real codebase
- Bond has a real repository
- Bond has real tests
- Bond has real documentation effort underway
- Bond does not yet have reliable general assistant behavior
- Bond does not yet have strong enough capability honesty
- Bond does not yet have clean enough decision boundaries
- Bond does not yet have mature packaging or deployment

This plan must never be read as “already complete.”

## Planning priorities

The project must prioritize work in this order:

1. documentation and repository truth
2. structural clarity and maintainability
3. path and runtime normalization
4. decision-stack correction
5. grounding and capability truth
6. memory quality
7. testing quality
8. packaging and deployment shape
9. service and desktop layers
10. voice/multimodal work
11. broader portability

## Workstream A — Documentation and repository truth

Objective: make the repository sufficient to explain the project without transcript dependence.

This workstream includes:

- README quality
- architecture contract
- behavior contract
- state definition
- path contract
- testing doctrine
- master planning
- planning-interface definition for external Gitea coordination
- changelog discipline
- roadmap discipline

Required outcomes:

- core repository docs align with each other
- durable project knowledge moves out of chat/transcript dependence
- collaborators and LLMs can understand the project from the repo itself
- Gitea project metadata can be populated from repository truth
- the boundary between repository truth and external planning metadata is explicit and enforced

## Workstream B — Project structure and package shape

Objective: make Bond look and behave like a maintainable software project.

This workstream includes:

- package structure clarity
- source tree normalization
- clearer module ownership
- pyproject and entry-point direction
- boundary between source, runtime, config, memory, and state

Required outcomes:

- package structure is explicit
- install/update/uninstall direction is documentable
- repository is ready for tighter tooling and future packaging

## Workstream C — Path and runtime normalization

Objective: remove environment-specific assumptions from the architecture.

This workstream includes:

- central path resolution
- runtime root definition
- config/state/memory/log/archive separation
- legacy path isolation
- migration handling

Required outcomes:

- hardcoded paths are removed or isolated
- legacy live paths remain migration facts only
- repository-relative and install-time logic become the norm

## Workstream D — Entry points and invocation model

Objective: define how Bond is invoked as a real assistant-facing program.

This workstream includes:

- CLI entry-point design
- wrapper transition plan
- alias/invocation normalization
- future service entry readiness
- English and Greek invocation forms
- robust invocation alias resolver for English/Greek/mixed addressing
- Unicode/casefold normalization and mixed-language handling in text-first paths
- language-neutral internal contracts for intent/capability/policy/execution
- bilingual memory/retrieval support planning and locale/message catalog readiness
- explicit no-voice dependency for text-first Greek support

Examples of intended invocation direction include:

- `bond hey`
- `bond open downloads`
- `bond show me the weather`
- `hey bond`
- `μποντ δώσε μου τα σημερινά νέα`

Required outcomes:

- invocation model is explicit
- entry points remain thin
- old invocation forms are treated as transitional when appropriate
- Greek/mixed-language invocation and normalization contracts are explicit and testable
- text-first Greek support planning does not depend on voice delivery layers

## Workstream E — Decision-stack correction

Objective: fix the behavioral core without restarting the whole project from zero.

This workstream includes:

- lighter orchestration
- dedicated parsing logic
- dedicated policy classification
- explicit capability truth
- narrow execution boundary
- stricter mixed-intent handling
- better ambiguity handling
- less lexical hijacking

Required outcomes:

- parsing, policy, capability truth, and execution are separated more cleanly
- unsupported capabilities stop being implied
- ambiguous inputs stop becoming confident wrong actions
- dangerous actions are handled more safely

### Routing stack direction

The routing and dispatch model should follow a layered pattern:

1. Deterministic pre-filter — rule-based, no model inference required
2. Structured dispatcher — 3B-class model, schema-constrained output only, never answering the user directly
3. Policy gate — deterministic validation of dispatcher output; decides what is *allowed*, not what seems appropriate
4. Specialist — appropriately-sized 7B-class model for the actual task domain
5. Optional output refinement — formatting pass only, not re-reasoning

The 3B dispatcher role is viable only because it is narrow: structured delegation, not sovereign reasoning.

Current de facto baseline local roster:

- qwen2.5:3b-instruct
- gemma2:2b
- qwen2.5:7b-instruct
- nomic-embed-text:latest

Planning rule: the project must be designed around the current lean roster by default. `qwen2.5:7b-instruct` is the highest-capability local baseline currently assumed. No current heavyweight local model tier should be assumed in planning.

If stronger behavior is needed, the first response is architectural improvement rather than baseline model inflation. Heavier tasks must be decomposed and scaffolded for the existing roster, with retrieval, validation, and tool/policy structure as compensating mechanisms. Future model changes are conditional and not part of the current default plan.

Route keys defined in `config/router/profiles.json` are dispatch targets, not capability assertions.

See `docs/archive/analysis/Bond_Router_Agent_Redesign_Updated.md` for the authoritative design.

## Workstream F — Capability truth system

Objective: make Bond honest about what it can and cannot do.

This workstream includes:

- explicit capability representation
- direct capability-question answers
- policy integration
- user-facing unsupported-feature explanations
- future-capability distinction

Required outcomes:

- Bond can state current capabilities truthfully
- future ambitions are not presented as present reality
- documentation and behavior align more closely

### Rootless-first and adapter direction

Capability architecture must adopt rootless-first as a hard design constraint, not merely a preference:

- prefer user-space APIs, XDG user dirs, desktop handlers, portals, and app handoff
- prefer user-level background services where persistent automation is needed
- privilege escalation must always route through the explicit privileged lane
- privileged actions require policy gate approval and confirmation

The capability registry should describe adapters per platform. The assistant layer must not treat raw shell commands as the native abstraction. Each capability class (inspector, handoff, bounded_mutator, privileged_lane) maps to bounded adapter contracts.

Degraded modes must be declared explicitly when preferred adapters are unavailable, rather than silently falling back to less safe behavior.

See `docs/CAPABILITIES.md` for the current registry and `docs/archive/analysis/Bond_Capability_Expansion_Plan.md` for the full expansion design.

## Workstream G — System-probe and grounding layer

Objective: make Bond rely more on real local truth.

This workstream includes:

- probe registry direction
- deterministic system information gathering
- package inspection
- environment inspection
- filesystem inspection
- session/desktop inspection where appropriate
- tool-availability inspection

Required outcomes:

- system answers become more grounded
- environment state is not fabricated
- probes are structured rather than hidden shell improvisation

### System fact hierarchy direction

System facts must be organized into three layers:

- **Layer 0 — authoritative OS facts**: collected once from `os-release`, kernel, session type, desktop environment, user identity, XDG directories, PATH-resolved tools, portal availability. Ground truth.
- **Layer 1 — user-environment facts**: refreshable facts including default apps, installed package formats, clipboard availability, D-Bus/session bus presence, notification capability.
- **Layer 2 — derived assistant-usable facts**: not raw scan output, but derived truths such as "can open URIs safely" or "cannot mutate system network config without privilege". This is the layer the model should reason from.

Probes must populate Layer 0 and Layer 1. The capability truth layer derives Layer 2. The model must never be exposed to raw Layer 0/1 scan dumps without Layer 2 derivation.

Default app/backend resolution rule: evidence ranking must follow this order — (1) explicit default handler, (2) desktop/session API fact, (3) desktop entry match, (4) installed binary presence, (5) heuristic fallback. "Binary exists" is not equivalent to "default app".

Model/runtime truth distinction rule: probe and capability truth must separately track configured route targets, installed local model inventory, and runtime availability. Configured route targets are not installation proof. Installed local model inventory is not runtime-health proof. Runtime availability is a separate fact from both configuration and inventory.

See `docs/archive/analysis/Bond_Capability_Expansion_Plan.md` for the full three-layer design.

## Workstream H — Memory, document knowledge, and local learning discipline

Objective: build a trustworthy, typed, and retrievable knowledge architecture without letting memory degrade assistant quality or conflating ingestion with model adaptation.

This workstream includes:

- layered memory ontology with explicit strata: Live Truth Layer, Durable Fact Layer, Episodic Operational Memory, Document Knowledge Memory, Correction Memory, and Learned Model Adaptation Layer boundary
- explicit Correction Memory as a first-class record type with override authority
- document knowledge memory as a first-class stratum, separate from durable fact memory
- ingestion pipeline for files placed into the local knowledge folder: classify, parse, chunk, embed, index, retrieve with provenance
- provenance and trust discipline on all memory and document records: source type, source reference, confidence, verification status, stale-after, and supersession tracking
- semantic document retrieval over the chunk and embedding index, replacing shallow lexical lookup for document knowledge
- reindexing, supersession, and deletion propagation: hash-based change detection drives incremental reindexing; deleted source files propagate to chunk and embedding removal
- fact and correction promotion rules: gated promotion from logs and document content into durable facts, requiring repeated confirmation, trusted source, explicit user approval, or stability over time
- archive and history retrieval discipline: archive is history and recovery, not automatic current truth; archive retrieval is opt-in and query-driven
- adaptation registry and curated training boundary: adaptation must be sparse, curated, versioned, and reversible; a registry of active adaptations must exist

Required outcomes:

- memory is selective and typed; each stratum has explicit authority and lifecycle rules
- current Live Truth Layer outranks archive and history for current-state questions
- document knowledge becomes a first-class layer with its own ingestion pipeline and retrieval interface
- files dropped into the knowledge folder go to ingestion and retrieval first; they are not automatic model training targets
- Correction Memory becomes explicit with override authority over superseded facts in the same domain
- provenance becomes required on all memory and document records; records without provenance are not valid
- semantic retrieval replaces shallow lexical lookup for document knowledge queries
- model adaptation is explicitly delayed until after ingestion, retrieval, provenance, and correction discipline are stable and reliable

Memory and ingestion sequencing rule: implement in this order:
1. formalize memory ontology and enrich fact/correction schemas
2. build document knowledge ingestion pipeline and chunk store
3. add semantic retrieval over document knowledge
4. implement gated promotion and correction authority
5. improve archive and history retrieval
6. only then introduce curated local model adaptation

Baseline model constraint: the plan must remain compatible with the current lean local model set and assume no current heavyweight local model tier. If stronger behavior is needed, the default response is architectural improvement and tighter decomposition around the existing roster. No ingestion or retrieval component should depend on a large hosted model as a baseline requirement.

## Workstream I — Testing and regression system

Objective: make tests enforce actual assistant quality.

This workstream includes:

- subsystem tests
- behavioral tests
- capability honesty tests
- action policy tests
- safety tests
- mixed-intent tests
- lexical hijack tests
- system-probe tests
- memory behavior tests

Required outcomes:

- passing tests mean more
- fixed failures turn into regression protection
- testing becomes a gate rather than a suggestion

## Workstream J — Packaging and controlled deployment

Objective: move Bond toward a cleaner deployable shape without pretending distribution maturity too early.

This workstream includes:

- Python core first (`pyproject.toml`, metadata, dependencies, entry points)
- Stage 1 local controlled install through `pipx` or equivalent isolated environment
- Stage 2 platform adapters layered on top of the unchanged Python core
- install/update/uninstall documentation with explicit lifecycle boundaries
- integration surfaces (service/applet/desktop hooks) separated from packaging core
- Android treated as a separate product layer, not equivalent to desktop Linux packaging
- no Flatpak/AppImage as core Stage 1 path
- no hidden model roster change assumptions in packaging direction
- compatibility with repository-first development

Required outcomes:

- deployment is more deliberate
- copy-paste script sprawl is reduced
- packaging direction is explicit before implementation expands
- Stage 1 and Stage 2 boundaries remain explicit and non-overclaiming

## Workstream N — System integrity and survivability

Objective: define schema versioning, rollback, resource governance, secrets handling, release governance, and health diagnostics before Bond is treated as stable.

This workstream includes:

- schema versioning and migration checkpoints across persisted stores
- snapshot and rollback discipline for risky updates and migrations
- resource governance with task budgets, timeouts, and cancellation
- secrets and credential boundaries separate from logs, docs, and memory
- release/update governance with validation and rollback notes
- health diagnostics and degraded-mode reporting surfaces

Required outcomes:

- survivability contracts are explicit and versioned in canonical docs
- updates and migrations are validated, logged, and rollback-aware
- degraded operation is detectable and explainable rather than silent
- stable-state claims are gated by governance and validation evidence

## Workstream O — Trust, explainability, and extensibility boundaries

Objective: define explainability/trust, action transparency, capability discovery, plugin/extension architecture, multi-profile groundwork, context awareness, policy feedback, and interaction modes as explicit design contracts before claiming those layers as implemented.

This workstream includes:

- explainability and trust metadata boundaries for user-visible rationale without exposing hidden chain-of-thought
- action transparency and preview requirements for mutating/high-risk actions, including side effects and confirmation signals
- capability discovery contracts grounded in capability registry + probes, not model improvisation
- plugin/extension architecture contracts: capability registration, permission/risk declaration, health visibility, isolation boundaries, and policy-gated behavior
- multi-profile groundwork: profile identity, per-profile memory boundaries, and shared-vs-private data separation
- context-awareness contracts: source-declared context with explicit consent and probe requirements
- policy feedback loop design through structured corrections and reviewable policy rules
- explicit interaction mode contracts where mode shapes routing/evidence/answer style but never bypasses safety

Required outcomes:

- trust and explainability behavior is defined in canonical docs with clear non-disclosure boundaries for hidden reasoning
- capability discovery and action preview semantics are documented as contracts, not implied behavior
- extension and multi-profile direction is bounded and does not overclaim implementation readiness
- context-aware and mode-aware behavior remains subordinate to capability truth and policy safety

## Workstream K — Service mode and desktop integration

Objective: prepare for a more assistant-like runtime presence after the core is stronger.

This workstream includes:

- possible user-service direction
- runtime supervision direction
- telemetry/timing exposure
- desktop integration planning
- Cinnamon-facing integration later

Required outcomes:

- service mode is treated as a later structured layer
- desktop integration is not allowed to outrun core correctness
- telemetry is truthful rather than theatrical

## Workstream L — Voice and multimodal direction

Objective: define the later expansion path for richer interaction.

This workstream includes:

- voice architecture direction
- wake/invocation handling separation from core parsing
- local-first considerations
- guardrail preservation under richer interfaces

Required outcomes:

- voice is planned as a later layer
- the core remains valid in text-first mode
- multimodal expansion does not excuse weak foundations

## Workstream M — Broader portability

Objective: reduce future pain when expanding beyond the primary environment.

This workstream includes:

- Linux Mint as the reference platform
- broader Linux portability
- later Android direction
- later Windows direction
- portability-aware path and packaging design

Required outcomes:

- portability emerges from sound structure
- cross-platform ambition does not distort present priorities

## Detailed implementation-direction requirements

The project plan must remain specific enough to guide implementation later.

### 1. Parsing direction

The parse layer should eventually produce structured outputs describing things such as:

- normalized invocation form
- language/variant normalization result
- intent candidates
- target candidates
- ambiguity indicators
- mixed-intent indicators

Parsing should not determine final authority.

### 2. Policy direction

The policy layer should eventually classify requests into categories such as:

- allowed deterministic info
- allowed deterministic action
- ambiguous
- unsupported
- blocked
- risky
- mixed-intent
- future-capability

Policy should determine:

- proceed
- refuse
- clarify
- explain limitation

### 3. Capability representation direction

Capability truth should eventually distinguish:

- implemented now
- partially implemented
- not implemented
- blocked by policy
- planned only

This distinction must be explicit and reusable.

Each capability should declare its class (inspector, handoff, bounded_mutator, or privileged_lane), rootless status, side effects, adapter backends, and degraded modes. The full schema is defined in `docs/CAPABILITIES.md`.

### 4. Execution direction

Execution should eventually accept only policy-approved operations and return structured results such as:

- success
- failure
- partial result
- explicit execution error

Execution must not invent success.

### 5. Probe direction

Probes should eventually be structured by domain, for example:

- filesystem
- environment
- packages
- session/desktop
- runtime tools
- configuration presence

Probe use must remain controlled.

Probes must be organized around the three-layer system fact hierarchy (Layer 0 authoritative, Layer 1 user-environment, Layer 2 derived assistant-usable). The model reasons from Layer 2 only. Probe outputs must not be dumped directly to the model as unstructured scan results.

### 6. Memory and document knowledge direction

Memory must distinguish typed records across explicit strata:

- **Live Truth Layer** — real-time probe results; highest authority for current-state questions; ephemeral and re-probeable
- **Durable Fact Layer** — structured, validated, provenance-tracked facts; stable across sessions; carry confidence, verification status, stale-after, and superseded-by metadata
- **Episodic Operational Memory** — time-ordered operational records; useful for continuity; low authority for stable truth
- **Document Knowledge Memory** — content extracted from ingested documents; retrieval-first; chunked and source-linked; not the same as durable facts; requires its own ingestion pipeline
- **Correction Memory** — explicit corrections to prior facts or assumptions; must override older conflicting facts in the same domain; must propagate to retrieval ranking
- **Learned Model Adaptation Layer** — curated, versioned, reversible behavior shaping; the only layer that changes model behavior; must be sparse and explicitly gated

Retrieval must be lane-based and selective. Different question types require different retrieval paths:

- Live Truth Layer lookup for current-state questions
- Durable Fact Layer lookup for stable configuration and preference questions
- recent episodic lookup for continuity and recent-activity questions
- Document Knowledge Memory retrieval for knowledge corpus questions
- archive and history lookup for historical queries only, opt-in

Ingestion direction: document ingestion must follow a pipeline of file detection, type classification, parsing by modality, normalization, chunking, embedding, indexing, and validation. Provenance must be tracked at every stage. Hash-based change detection drives reindexing. Deletion must propagate to the chunk and embedding index.

Multimodal document parsing: native text extraction is preferred for PDFs with text layers. Selective OCR is applied for scanned or image-heavy pages only. Visual language model interpretation is applied for standalone images and diagrams where neither native extraction nor OCR produces useful content. All three extraction methods are distinct in fidelity and must not be flattened into one undifferentiated text blob.

Retrieval lanes: Document Knowledge Memory retrieval uses semantic or hybrid search over the chunk index, not lexical-only matching. Document Knowledge Memory retrieval must be isolated from episodic operational logs and must not be dominated by unrelated recent activity records.

Promotion rules: logs and document content may produce candidate facts or corrections, but promotion to durable memory requires gating: repeated confirmation, trusted-source origin, explicit user approval, or stability over time.

Ingestion vs training distinction: placing a file in the knowledge folder is an ingestion event, not a training event. The default pipeline is detect → parse → chunk → index → retrieve with provenance. Fine-tuning or adapter-based adaptation is a separate, explicitly-triggered operation that applies only after ingestion, retrieval, and correction discipline are stable.

History and archive: archive retrieval is opt-in and query-driven. Archive records describe past state, not current truth. They are lower authority than live truth and durable facts for all current-state or stable-state questions.

Reflection discipline: reflection is not evidence. Reflection records are hypothesis and lesson outputs. They must not rank as fact, must not override durable facts or live probe results for truth questions, and must not be treated as verified memory.

Baseline model constraint: this plan must remain compatible with the current lean local model set and assume no current heavyweight local model tier as baseline architecture.

### 7. Telemetry direction

Telemetry should eventually expose truthful timing and execution visibility such as:

- total response time
- execution duration where relevant
- model/runtime latency where measurable

It must not expose fake “reasoning theater.”

### 8. Packaging direction

Packaging should eventually define:

- package metadata
- entry points
- runtime layout expectations
- install/update/uninstall behavior
- repository-to-runtime relationship

## Things that must not happen

The project must not drift into:

- central god-files
- undocumented implicit logic
- unsupported-capability theater
- fake multi-agent complexity (narrow contract-bound routed roles are acceptable; uncontrolled persona-based or boundary-free agent behavior is not)
- UI polish masking weak behavior
- transcript dependence as the permanent project memory
- portability claims without structural basis

## Near-term execution order

The next serious repository direction should continue in roughly this order:

1. strengthen core docs
2. define install/update/uninstall and packaging direction
3. define Gitea project-management structure
4. tighten architecture and behavior contracts
5. align code with those contracts
6. expand testing around real observed failures
7. improve packaging/deployment shape
8. define later service/desktop/voice paths from a stronger core

## Success condition

This master plan is succeeding when:

---

## Cross-document alignment

- Routing design authority: `docs/archive/analysis/Bond_Router_Agent_Redesign_Updated.md`
- Capability expansion design authority: `docs/archive/analysis/Bond_Capability_Expansion_Plan.md`
- Architecture: `docs/ARCHITECTURE.md`
- Memory system specification: `docs/MEMORY.md`
- Document knowledge ingestion and retrieval design: `docs/KNOWLEDGE_INGESTION.md`
- Capability registry: `docs/CAPABILITIES.md`
- Current state: `docs/STATE.md`
- Roadmap: `ROADMAP.md`
- Gitea planning: `docs/GITEA_PROJECT_MANAGEMENT.md`
- System integrity and survivability: `docs/SURVIVABILITY.md`
- Schema and data contract registry: `docs/SCHEMAS.md`
- Release, update, and version governance: `docs/RELEASE_PROCESS.md`
- Packaging strategy: `docs/PACKAGING_STRATEGY.md`
- Service mode contracts: `docs/SERVICE.md`
- Cinnamon applet integration contracts: `docs/APPLET.md`
- Voice layer contracts: `docs/VOICE.md`
- Contributor workflow discipline: `docs/DEVELOPMENT.md` and `docs/LLM_OPERATING_GUIDE.md`
- Control, trust, and extensibility specification: `docs/TRUST_EXTENSIBILITY.md`
- Greek language support and localization specification: `docs/GREEK_LANGUAGE_SUPPORT.md`

- the repository can explain the project clearly
- architecture, behavior, testing, and state docs agree with each other
- future implementation work can be broken into bounded issues
- Bond becomes more truthful and grounded over time
- transcript dependence keeps decreasing
- new capability layers no longer outrun core correctness

## Summary

Bond should be built as:

- a real local assistant
- with explicit boundaries
- with grounded system awareness
- with controlled actions
- with selective memory
- with meaningful tests
- with disciplined repository operations
- with later richer interfaces only after the core is trustworthy

That is the master project direction.

## Installation and packaging track

Bond must transition from a repository-only development model to a controlled installation and packaging system.

This track defines the required steps to achieve that.

### Objectives

- define a clear Stage 1 installation model for local controlled install
- define a controlled update mechanism
- define an explicit uninstall process
- eliminate legacy path sprawl and script duplication
- align runtime layout with architectural design
- define Stage 2 platform adapters without changing Python core contracts
- keep Android as a separate product layer

### Constraints

All implementation must align with:

- `docs/INSTALLATION.md`
- `docs/CURRENT_PATHS.md`
- `docs/ARCHITECTURE.md`
- `docs/PACKAGING_STRATEGY.md`

Stage direction constraints:

- Stage 1 is Python core first with `pipx`/isolated local install and explicit entry points
- Stage 2 adds platform adapters on top of the core
- Flatpak/AppImage are not core Stage 1 solutions
- integration surfaces remain separate from packaging core
- packaging direction must not imply any hidden model roster change

Packaging must not be implemented in a way that:

- reintroduces hardcoded paths
- hides runtime behavior
- creates uncontrolled system side effects
- bypasses validation or testing

### Required implementation steps

1. define CLI entry point (`bond`)
2. formalize runtime directory structure
3. define configuration resolution strategy
4. separate source vs runtime vs state vs memory paths
5. define install script or packaging mechanism
6. define update workflow (repository → system)
7. define uninstall workflow (full cleanup with defined retention rules)
8. integrate validation (selftest/smoke) into install/update process

### Validation requirements

Any installation or packaging solution must:

- successfully install Bond in a clean environment
- expose the expected entry command(s)
- pass defined validation checks (e.g. smoke tests)
- correctly resolve all runtime paths
- avoid dependency on previous manual setup

### Status

This track is not yet implemented.

It must be completed after the decision stack (parser/policy/capability/execution) is stabilized.
