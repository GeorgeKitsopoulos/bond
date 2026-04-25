# Architecture

This document defines the intended repository-level architecture of Bond in its current corrective phase.

It is not a description of idealized future magic.
It is not a transcript.
It is not a code walkthrough.

Its purpose is to define:

- major subsystem roles
- major subsystem boundaries
- architectural constraints
- the direction of corrective redesign

This document may describe architecture that is only partially implemented today, but it must not pretend those boundaries already exist in code when they do not.

## Architecture principles

Bond should follow these principles:

- repository-first structure
- explicit subsystem boundaries
- deterministic local grounding where possible
- truthful capability boundaries
- controlled execution
- modularity over god-files
- migration away from environment-specific assumptions
- Linux Mint first, broader portability later

## High-level system shape

Bond should be understood as a layered local assistant system with these major concerns:

1. entry points
2. orchestration
3. parsing and normalization
4. policy and capability truth
5. execution and probes
6. memory and retained knowledge
7. document knowledge ingestion and retrieval
8. configuration and path resolution
9. testing and validation
10. trust and explainability (later layer)
11. extension/plugin boundary (later layer)
12. interaction modes (later layer)
13. context awareness (later layer)

These concerns must not collapse into one central file.

### Routing and dispatch flow

The routing and dispatch model within Bond should follow a layered pattern:

1. Deterministic pre-filter — rule-based, no model inference required
2. Structured dispatcher — 3B-class model, schema-constrained output only
3. Policy gate — deterministic validation of dispatcher recommendations
4. Specialist — appropriately-sized model for the actual task domain
5. Optional output refinement — formatting pass only, not re-reasoning

This pattern keeps each layer narrow and replaceable. The 3B model handles coordination only; real reasoning remains with 7B-class specialists, and planning should not assume any heavyweight local tier.

Current de facto baseline local roster:

- qwen2.5:3b-instruct
- gemma2:2b
- qwen2.5:7b-instruct
- nomic-embed-text:latest

Architecture interpretation for this baseline: `qwen2.5:3b-instruct` and `gemma2:2b` cover cheap front/support/hygiene roles, `qwen2.5:7b-instruct` is the main local workhorse for most substantial reasoning and planning work, and `nomic-embed-text:latest` is the semantic retrieval baseline. There is no current heavyweight local model tier in the architecture baseline.

Difficult work is expected to be handled by the existing roster through stronger system design, decomposition, retrieval grounding, policy gates, validation, and narrower specialist contracts rather than a larger local model assumption.

Route keys defined in `config/router/profiles.json` are dispatch targets, not capability assertions.

See `docs/archive/analysis/Bond_Router_Agent_Redesign_Updated.md` for the detailed design.

## Entry points

Entry points are the user-facing or tool-facing ways Bond is invoked.

Examples include:

- CLI entry commands
- transitional wrapper scripts
- future service entry points
- future desktop integration entry points

Entry points should:

- accept input
- normalize invocation form at a high level
- hand work to the orchestrator

Entry points should not:

- contain large policy engines
- contain memory logic
- contain execution logic
- contain broad capability claims
- become the place where assistant behavior is improvised

## Orchestration layer

The orchestration layer is the central coordinator.

Its job is to:

- receive normalized user intent input
- select the next subsystem path
- coordinate parse → policy → execution → response
- enforce top-level control flow
- keep response assembly coherent

The orchestration layer should not:

- directly implement every heuristic
- directly perform action parsing in detail
- directly define capability truth
- directly execute risky actions without policy approval
- become a god-file containing all assistant logic

A current project reality is that the orchestrator is too heavy.
That should be corrected over time by moving logic into dedicated modules.

## Parsing and normalization layer

This layer is responsible for turning raw input into structured interpretation candidates.

Its responsibilities include:

- wake/invocation normalization
- input cleanup and normalization
- language-form normalization
- multilingual normalization and invocation alias resolution
- Unicode/casefold matching with mixed-script-safe token handling
- candidate intent parsing
- candidate target extraction
- mixed-language detection signals
- ambiguity detection signals

This layer should produce structured interpretation results.

This layer should not:

- decide final action permission
- invent capabilities
- execute actions
- pretend ambiguous guesses are decisions
- bypass policy

The parse layer should produce possibilities and structure, not authority.

## Language and localization layer

Bond should treat language surface behavior as a dedicated layer that sits above language-neutral internal contracts.

Language-facing behavior may vary by locale and conversation language, but intent, capability, policy, and execution contracts remain language-neutral.

Language and localization architecture is defined at contract level in `docs/GREEK_LANGUAGE_SUPPORT.md`.
Greek-specific dictionaries or phrase maps should not be embedded as architecture truth in this document.

## Policy layer

The policy layer decides what kind of thing the parsed request is and what is allowed next.

Its responsibilities include classification such as:

- deterministic info request
- deterministic action request
- ambiguous request
- unsupported request
- blocked request
- risky request
- mixed-intent request
- future-capability request

Its responsibilities also include:

- deciding whether a request can proceed
- deciding whether clarification or refusal is required
- deciding whether execution is allowed
- deciding whether a capability must be described as unsupported

The policy layer should not:

- perform raw parsing
- fabricate execution success
- use vague “best effort” guesses for unsafe actions
- silently upgrade ambiguity into authority

## Capability truth layer

This layer exists so Bond can answer honestly about what it can and cannot do.

Its responsibilities include representing:

- what Bond can do now
- what Bond can partly do
- what Bond cannot do
- what requires new tooling
- what is blocked by safety or policy
- what is future design rather than present capability

This layer should be explicit.

It should not be left to model improvisation.

The capability truth layer should be usable by:

- direct capability questions
- policy decisions
- user-facing limitation explanations
- documentation alignment work

### Rootless-first capability ordering

Capabilities must be exposed in this order of preference:

1. deterministic and read-only
2. deterministic and rootless with explicit user intent
3. rootless interactive handoff through standard platform APIs
4. rootless write actions with confirmation
5. privileged actions only in a distinct, explicit lane

Privilege escalation is never implicit. Rootless-first is both a safety posture and a portability posture.

See `docs/CAPABILITIES.md` for the capability registry and `docs/archive/analysis/Bond_Capability_Expansion_Plan.md` for the full expansion design.

## Trust and explainability layer

Bond should provide truthful, high-level explanation metadata for routing, source class, policy outcomes, and uncertainty without exposing hidden chain-of-thought.

See `docs/TRUST_EXTENSIBILITY.md` for the trust/explainability specification and user-facing boundaries.

## Plugin and extension boundary

Plugins are future adapters and are not currently implemented.
When introduced, plugins must register capabilities, declare risk and permissions, expose health signals, and remain behind policy gates.
Plugins must not bypass policy or mutate core behavior silently.

## Interaction mode layer

Mode should be an explicit routing context (for example chat, command, troubleshooting, development) that shapes evidence expectations and response style.
Mode is never a safety bypass.

## Execution layer

The execution layer is responsible for carrying out policy-approved deterministic actions.

Its responsibilities include:

- performing allowed actions
- calling allowed local commands or tools
- returning structured execution results
- failing explicitly when execution cannot proceed

The execution layer should not:

- decide policy
- invent targets
- guess missing meaning
- claim success before success is known
- broaden scope beyond what policy approved

Execution must be subordinate to policy and grounded in real outcomes.

## System-probe layer

The system-probe layer is the grounded local information-gathering layer.

Its purpose is to gather real machine state using deterministic tools.

Examples of probe domains may include:

- filesystem state
- environment state
- package inventory
- session or desktop information
- network-related inspectable state where appropriate
- configuration presence
- runtime availability of known tools

The probe layer should:

- use real commands or deterministic local APIs
- return structured data
- support truthfulness in responses

The probe layer should not:

- be confused with arbitrary unrestricted shell use
- bypass policy
- pretend unsupported probes succeeded
- become a hidden execution backdoor

### System fact hierarchy

System facts should be collected and understood in three layers:

- **Layer 0 — authoritative OS facts**: immutable or near-immutable facts from `os-release`, kernel, architecture, session type, desktop environment, user identity, XDG directories, PATH-resolved tools, and portal availability. These are collected once and treated as ground truth.
- **Layer 1 — user-environment facts**: changeable facts including default browser, mail app, file manager, terminal, editor, installed app formats, clipboard availability, and notification capability. These should be refreshed periodically.
- **Layer 2 — derived assistant-usable facts**: not raw scan results, but derived truths such as "can open URIs safely", "can compose email via portal", "cannot mutate system network config without privilege". This is the layer the model should reason from.

Probes populate Layer 0 and Layer 1. The capability truth layer derives Layer 2 from those inputs.

Probing and interpretation are separate stages. Layer 0 and Layer 1 are evidence collection layers; Layer 2 is the interpreted assistant-usable layer. Layer 0/1 probe outputs must not be dumped raw to the model.

Default app/backend resolution must rank evidence in this order: (1) explicit default handler, (2) desktop/session API fact, (3) desktop entry match, (4) installed binary presence, (5) heuristic fallback. Binary presence alone is not proof of default-handler truth.

Model truth must distinguish configured route targets, installed local model inventory, and runtime availability. Configured route targets are not installation proof; installed inventory is not routing-correctness proof; runtime availability is a separate fact from both configuration and inventory.

## Memory layer

The memory layer is responsible for retained project/user/system knowledge. Memory is explicitly typed across distinct strata. Treating all memory as one undifferentiated pool produces unreliable retrieval and truth-ranking failures.

The memory strata are:

- **Live Truth Layer** — the result of a real-time probe against the live environment. Live truth outranks stored memory for current-state questions. It is ephemeral and re-probeable rather than a stored record.
- **Durable Fact Layer** — structured, validated facts about the system, preferences, and configuration. These carry provenance, confidence, verification status, and stale-after metadata.
- **Episodic operational memory** — time-ordered records of actions, conversations, and recent events. Useful for continuity but low authority for stable truth.
- **Episodic Operational Memory** — time-ordered records of actions, conversations, and recent events. Useful for continuity but low authority for stable truth.
- **Document Knowledge Memory** — content extracted from ingested documents. This is a separate stratum from durable facts. Document chunks do not automatically become facts. Document knowledge memory is retrieval-first and requires its own ingestion pipeline.
- **Correction Memory** — explicit corrections to prior facts or assumptions. Corrections must override older conflicting facts in the same domain and must propagate to retrieval ranking.
- **Learned Model Adaptation Layer** — the only layer that changes model behavior through fine-tuning or adapter-based adaptation. This layer must be sparse, curated, versioned, and reversible.

The memory layer must:

- distinguish memory types clearly using the strata above
- apply live truth as the highest-authority source for current-state questions
- treat correction memory as explicit and first-class with override priority
- treat archive as history, not automatic current truth; archive retrieval must be opt-in
- treat reflection as hypothesis, not evidence; reflection must not rank as fact
- keep retrieval lane-based and selective — different question types require different retrieval paths
- avoid hijacking unrelated prompts

The memory layer must not:

- override a live probe result with a stored memory for a current-state question
- treat document knowledge memory as equivalent to durable fact memory
- promote incidental log entries into durable facts without gated promotion
- conflate learned model adaptation with document ingestion or memory storage
- flood responses with loosely related history or archive content

See `docs/MEMORY.md` for the full canonical memory specification, strata definitions, retrieval lanes, schemas, and promotion rules.

## Document knowledge and ingestion layer

Document knowledge ingestion is a first-class architectural concern, separate from the memory layer. This layer is responsible for making local documents, files, and knowledge corpora retrievable by the assistant with full provenance.

This layer's responsibilities include:

- file classification by type and modality
- parsing by modality: native text extraction for documents with text layers, selective OCR for scans and image-heavy pages, and visual interpretation for standalone images and diagrams
- chunking and indexing of parsed content into retrievable units
- provenance tracking: every chunk must carry source file reference, extraction method, ingestion timestamp, file hash, confidence, and modality annotation
- semantic retrieval interface over the chunk and embedding index
- document change detection and reindexing: hash-based change detection drives incremental reindexing when source files are updated or removed
- deletion propagation: when a source file is removed, all associated chunks and embeddings must be removed from active retrieval

This layer's non-responsibilities — things that must not be conflated with document ingestion:

- document ingestion is not a substitute for live probes; it answers questions about document content, not current live system state
- document chunks are not synonymous with durable facts; ingested content does not automatically produce durable fact records
- document ingestion is not automatic model training; placing a file in the knowledge folder causes parsing, chunking, and indexing for retrieval, not fine-tuning or adapter modification
- this layer does not encompass voice or interface multimodality; multimodal here refers specifically to document modalities such as PDFs, scanned images, and screenshots

Current-state note: the document knowledge and ingestion layer is not yet implemented. The architecture defines the target. See `docs/KNOWLEDGE_INGESTION.md` for the full canonical ingestion lifecycle, provenance schema, retrieval architecture, multimodal handling, and drop-folder semantics.

## Configuration and path layer

This layer is responsible for path resolution and configuration discovery.

Its responsibilities include:

- repository-relative path understanding
- install-time path discovery
- config resolution
- runtime/state/memory path separation
- migration handling for transitional layouts where needed

This layer should not:

- hardcode one user’s environment as architecture
- silently assume earlier loose-script paths are still canonical
- mix runtime data and source-tree assumptions carelessly

## Testing and validation layer

This layer defines how the architecture is checked.

Its responsibilities include:

- subsystem tests
- behavioral tests
- regression coverage
- validation of documentation-relevant expectations where possible

Testing must eventually cover more than “the subsystem did not crash.”

It must increasingly validate:

- assistant sanity
- capability honesty
- policy correctness
- execution boundary discipline
- lexical hijack resistance
- dangerous-action refusal
- system-probe correctness
- repository-local review declaration gating via `scripts/bond-reviewcheck` and `make reviewcheck`
- developer-facing review and prompt-reference helper via `scripts/bond-dev-help`

## Documentation relationship

The architecture documentation must stay aligned with:

- `STATE.md`
- `BEHAVIOR_CONTRACT.md`
- `CURRENT_PATHS.md`
- `TESTING.md`
- `INSTALLATION.md`
- `BOND_PROJECT_MASTER_PLAN.md`
- `PLANNING_INTERFACE.md`
- `MEMORY.md` (canonical memory specification: strata, retrieval lanes, schemas, promotion rules)
- `KNOWLEDGE_INGESTION.md` (canonical document ingestion, provenance, and retrieval design)
- `CAPABILITIES.md` (capability registry and doctrine)
- `ROADMAP.md` (milestone and stage alignment)
- `docs/archive/analysis/Bond_Router_Agent_Redesign_Updated.md` (routing/dispatch design authority)
- `docs/archive/analysis/Bond_Capability_Expansion_Plan.md` (capability expansion design authority)

The architecture document does not override higher-priority repository truth outside architectural scope.

In particular:

- behavioral and safety constraints are governed by `BEHAVIOR_CONTRACT.md`
- current-state claims are governed by `STATE.md`
- path truth is governed by `CURRENT_PATHS.md`
- external planning boundaries are governed by `PLANNING_INTERFACE.md`

If architecture direction changes materially, related documents must be updated in the same change rather than left to drift.

## Current architectural problems

The current project state still includes these architectural weaknesses:

- too much logic concentrated in central orchestration
- too many heuristics mixed together
- weak separation between parsing, policy, and execution
- weak capability-truth discipline
- underdeveloped system-probe usage
- memory retrieval that can still overreach
- transitional path assumptions still leaking into behavior
- no first-class document knowledge layer; there is no ingestion pipeline, no chunk store, no embedding index, and no semantic retrieval path for documents
- weak provenance discipline; memory and document records do not carry sufficient source type, confidence, verification status, or stale-after metadata
- retrieval for knowledge is still shallow and lexical; there is no semantic or hybrid retrieval path
- no reindex or version discipline for document content; file changes are not tracked or propagated to a chunk index
- correction memory is not yet first-class; corrections are stored but do not have override authority in retrieval
- risk of conflating document ingestion with model learning; the boundary between ingestion, memory, and adaptation is not yet enforced in code

This document exists partly to constrain corrective redesign against those weaknesses.

## Corrective direction

The architectural correction direction is:

- simplify the orchestrator
- push parsing into dedicated parsing logic
- push action classification into policy
- make capability truth explicit
- keep execution narrow and policy-gated
- make probes real and structured
- make memory more selective and typed using the layered strata defined in `docs/MEMORY.md`
- build the document knowledge and ingestion layer as a first-class architectural component
- enforce provenance discipline across all memory and document records
- replace shallow lexical retrieval for document knowledge with semantic or hybrid retrieval
- make correction memory first-class with explicit override authority
- enforce the boundary between document ingestion, memory storage, and model adaptation
- make configuration/path resolution cleaner and less environment-specific

## Architecture constraints

The project should not solve its current problems by:

- creating one larger central file
- hiding logic in prompt-like text blobs
- pretending unsupported behavior exists
- replacing grounded subsystems with vague model output
- introducing fake multi-agent complexity without real boundaries (narrow contract-bound routed roles are acceptable; uncontrolled persona-based or boundary-free agent behavior is not)
- prioritizing UI polish over core truthfulness

# Execution Contracts (MANDATORY)

Execution contracts define the required schemas for parse, policy, and execution interfaces. These contracts exist to prevent hidden coupling, reduce behavioral drift, and keep subsystem communication auditable.

## Parse Result Schema

The parse layer must return a structured parse result object with these fields:

- `raw_text`: original user input string before normalization.
- `normalized_text`: normalized text used by downstream parsing logic.
- `wake_invoked`: boolean flag indicating whether wake/invocation form was detected.
- `language_hint`: one of `en`, `el`, `mixed`, or `unknown`.
- `intent_candidates`: ordered list of possible intent classifications with parser confidence metadata.
- `action_candidates`: ordered list of extracted `ActionCandidate` objects.
- `question_candidates`: list of extracted question/query forms that may require non-action handling.
- `explicit_paths`: list of explicit filesystem-like path strings detected in the input.
- `named_targets`: list of recognized non-path targets (for example known app/tool labels).
- `ambiguity_flags`: list of parse-time ambiguity markers describing collisions or uncertainty.
- `safety_flags`: list of parse-time safety-relevant markers (for example privileged location mention or potentially dangerous verb).

`ActionCandidate` must have this structure:

- `verb`: normalized action verb token.
- `object_text`: raw or lightly normalized object phrase associated with the verb.
- `target_label`: canonical target label when resolvable, otherwise empty/null by schema rules.
- `is_explicit_path`: boolean indicating whether the target was expressed as an explicit path.
- `confidence`: parser confidence score for this candidate.
- `source_span`: source span reference for traceability back to input text.
- `modifiers`: normalized modifier list (time qualifiers, location qualifiers, safety-affecting qualifiers, and similar terms).

Rule: Parser extracts structure only; parser does not approve, reject, block, or authorize execution.

---

## Policy Decision Schema

The policy layer must return a policy decision object with these fields:

- `status`: one of `approved`, `rejected`, `clarify`, `unsupported`, `blocked`, or `mixed`.
- `action_class`: canonical class used to route execution or refusal handling.
- `reason_code`: machine-stable reason identifier for policy outcome.
- `user_message`: user-facing explanation consistent with capability truth and safety constraints.
- `approved_target`: approved canonical target when `status=approved`; otherwise null/empty by schema rules.
- `approved_command`: approved execution contract payload when `status=approved`; otherwise null/empty by schema rules.
- `risk_level`: policy risk classification for the decision.
- `requires_confirmation`: boolean indicating whether explicit confirmation is required before execution.

Allowed `reason_code` values:

- `unknown_target`
- `ambiguous_target`
- `unsupported_capability`
- `blocked_path`
- `dangerous_action`
- `mixed_intent_request`

## Execution Result Schema

The execution layer must return a structured execution result object with these fields:

- `ok`: boolean success indicator for the executed operation.
- `action_class`: canonical action class that was executed (or attempted).
- `executor`: executor identifier (module/tool/adapter) that performed the operation.
- `duration_ms`: measured execution duration in milliseconds.
- `stdout`: captured standard output text.
- `stderr`: captured standard error text.
- `exit_code`: process/tool exit code or equivalent executor status code.
- `artifact_paths`: list of generated artifact paths, if any.
- `user_summary`: concise user-safe summary of what occurred.
- `probe_used`: probe identifier(s) used to gather required deterministic context.

## Capability Registry Concept

Capability truth should be represented through a registry model with one record per capability and at least these fields:

- `name`: stable capability identifier.
- `category`: capability category used for grouping and policy matching.
- `status`: current capability state (for example available, partial, planned, blocked, unsupported by current phase rules).
- `execution_mode`: how the capability runs (deterministic probe, guarded action, non-executable informational path, and similar bounded modes).
- `risk_level`: baseline risk classification used by policy.
- `requires_confirmation`: baseline confirmation requirement for this capability.
- `required_tools`: deterministic tools/probes required for reliable operation.
- `read_only`: boolean indicating whether the capability mutates any state.
- `rootless`: boolean indicating whether the capability can run without privilege escalation.
- `side_effects`: list of observable side effects outside the immediate operation scope.
- `interactive`: boolean indicating whether the capability requires active user interaction during execution.
- `needs_gui_session`: boolean indicating whether a GUI/display session is required.
- `needs_network`: boolean indicating whether network access is required.
- `needs_elevated_lane`: boolean indicating whether the capability must route through the privileged execution lane.
- `backends`: map of platform keys to adapter identifiers implementing this capability.
- `degraded_modes`: list of degraded but still usable execution paths when preferred backends are unavailable.
- `result_schema`: identifier for the typed result schema this capability returns on success.
- `error_schema`: identifier for the typed error schema this capability returns on failure.
- `audit_tag`: tag used for audit/log hooks when this capability is executed.

The registry drives:

- policy decisions
- documentation
- testing

No module communicates via implicit strings — all interfaces must follow schema.

## Summary

Bond should evolve toward an architecture where:

- entry points are thin
- orchestration is central but not bloated
- parsing is structured
- policy is explicit
- capability truth is explicit
- execution is grounded
- probes are real
- memory is selective and typed across explicit strata
- document knowledge is ingested, provenance-tracked, and retrievable as a first-class layer
- correction memory has explicit override authority
- document ingestion is distinct from model adaptation
- paths and config are normalized
- tests reflect actual assistant quality

That is the corrective architecture direction for the current phase.
