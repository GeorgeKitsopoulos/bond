# Current State

This document defines the actual current state of the Bond project at the repository level.

It is not a roadmap.
It is not a wishlist.
It is not a transcript.

It is a strict statement of what is true right now.

This file exists to prevent drift between:

- what the system actually does
- what the documentation claims
- what future plans suggest

## Current Checkpoint

Date: 9 May 2026 (Stage 2F-F-B current; earlier April 2026 Stage 2E / 61/61 checkpoint preserved below)

Current baseline note:

- Stage 2F-F-B maintenance readiness report probe integration is the current repository checkpoint.
- Compile and integrated selftest baseline is {"ok": true, "passed": 242, "failed": 0, "total": 242}.
- Stage 2F-F-B is integrated/current as report integration only: the explicit maintenance/readiness report now consumes package_update_status, storage_hygiene, and boot_service_health.
- The integration remains read-only and does not add planning, fixes, actions, privileged execution, package update execution, cleanup execution, service mutation, or maintenance automation.
- Explicit maintenance/readiness report integration exists; maintenance planning, privileged execution, repair/update/cleanup actions, dashboarding, and broad normal-answer probe backing remain future work.
- The older April 2026 Stage 2E / 61/61 checkpoint is preserved below as historical context.

P0B update (source/config/deploy sanitation):

- removed unused legacy summarizer module from active source after reference verification
- sanitized remaining active source/deploy local-path debt in allowed P0B targets
- normalized systemd user unit examples to portable `%h`-based paths
- Stage 2F remains paused until P0C and P0E gates are addressed

P0C update (public documentation consolidation):

- public documentation was consolidated into human engineering language
- public-facing tool-specific prompt scaffolding was removed from current tracked docs
- contributor and maintainer workflow guidance was consolidated into tool-agnostic documents
- validation baseline remains passing at compile and selftest 61/61
- Stage 2F remains paused until P0D and P0E gates are addressed

P0D update (historical documentation archival):

- historical design analysis and implementation reports were moved into `docs/archive/`
- all archived markdown files received historical-warning banners to prevent them from acting as current truth
- local/private path markers in archived documentation were sanitized with neutral placeholders
- archive guidance and public-safety rules were added in `docs/archive/README.md`
- current documentation index was updated to reference the archive without treating it as current project truth
- validation baseline remains passing at compile and selftest 61/61 after P0D application
- Stage 2F was paused until the P0E gate was addressed

P0E update (Gitea and roadmap reconciliation):

- local Gitea tracker state was reconciled with repository roadmap/state documentation
- target tracker milestones were created and opened: `P0`, `M1`, `M2`, `M3`, `M4`, `M5`, `M6`, and `Later / Backlog`
- legacy Phase 1-6 milestones were closed as historical tracker structure and were not deleted
- issue #2 was closed as completed with reconciliation context
- issues #1, #5, #6, and #7 were moved to `M1`
- issues #3 and #4 were moved to `M2`
- validation baseline remains passing at compile and selftest 61/61 after P0E application
- Stage 2F may resume after P0E validation
- P0F remains required before any public GitHub release

P0F preparation update (current-doc reference cleanup):

- stale current-doc references to removed pre-archive analysis/report paths were cleaned
- stale references to removed tool-specific workflow docs were removed or redirected to current workflow docs
- validation baseline remains passing at compile and selftest 61/61 after this cleanup

## Implemented and validated now

- repository-relative wrappers and path substrate are implemented
- deterministic Stage 2A routing is implemented
- Stage 2B policy gate is implemented
- Stage 2C action contract is implemented
- Stage 2D confirmation token flow is implemented for high-risk confirmation-required requests
- action dry-run support is implemented through both `BOND_ACTION_DRY_RUN` and explicit dry-run language
- high-risk action confirmation-required responses are implemented
- confirmation is short-lived and exact-token based; confirmed requests still pass through routing, policy, action contract, and executor safety checks

- Stage 2E parser contract and action preflight is implemented (`src/bond/ai_parse_contract.py`)
- action-looking requests with no parsed safe executable action shape now fail closed as `action_not_parsed` before executor
- parser preflight does not expand executor capability
- high-risk Stage 2D confirmation behavior remains intact
- Stage 2E parser-contract and action-preflight coverage remains present; Stage 2F-A started with `src/bond/ai_capabilities.py` as the static code-level capability registry foundation
- Stage 2F-B complete/current: read-only capability questions are answered from the static registry through `src/bond/ai_capability_answer.py` and `ai_run.py` integration
- Post-Stage 2F-B correction: describe_capabilities registry wording now reflects that read-only assistant answer integration exists; dynamic context-aware discovery remains planned.
- Stage 2F-C telemetry-driven guardrail hardening complete/current: assistant-invocation stripping, high-risk natural command shaping, mixed-intent preemption safeguards, expanded capability aliases, and single-action dry-run step metadata are implemented in deterministic paths.
- Stage 2F-C2 regression cleanup complete/current: capability interception now runs after policy/action gating, additional model/language capability aliases are covered, restart-the-laptop phrasing now follows confirmation-required high-risk handling, and trivial social check-ins avoid model fallback.
- Stage 2F-C3 edge case cleanup complete/current: bare capability noun phrases ("installed models", "local models") are now recognized and answered deterministically without question markers; time queries and project-state queries return bounded deterministic answers instead of timing out on model fallback.
- Stage 2F-C4 deterministic diagnostic cleanup integrated/current: deterministic handling is hardened for adversarial high-risk phrasing, Greek polite high-risk commands, Greek destructive mixed-intent classification, unsupported-capability truthfulness prompts, Greek model inventory wording, and exploratory capability questions.
- Stage 2F-C5 strict timeout and diagnostic-expectation cleanup integrated/current: deterministic handling is hardened for Greek voice/memory capability-question forms, unsupported reminder/file/email request surfaces, high-risk capability-question wording, social-checkin wording expectations, and name-query answer-path expectations.
- Stage 2F-C5 follow-up strict timeout cleanup integrated/current: the remaining strict broad-regression timeout edges are closed for Greek "can you answer in Greek?" language-policy wording and unsupported create-folder/write-file side-effect requests.
- `notify me to stretch` remains a current bounded action dry-run path (not an unsupported capability).
- `απάντα ελληνικά` remains a registry-backed language-policy capability answer (`apply_response_language_policy`) and is not evidence of complete Greek language-state architecture.
- Greek support remains transitional and centralized in normalization/alias/intent handling; final language-state architecture is not complete.
- Stage 2F-D-A probe foundation is now integrated/current: the legacy broad system scanner has been replaced by a structured probe CLI wrapper, and current probes are `host_baseline`, `session_baseline`, `tool_inventory`, `router_config_models`, `ollama_model_inventory`, and `model_truth`.
- Stage 2F-D-A2 cleanup/hardening is integrated/current: CI now uses Node 24-compatible official GitHub Actions majors (`actions/checkout@v5`, `actions/setup-python@v6`) with the transition opt-in `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24`, and integrated selftests now include workflow/docs formatting hygiene checks plus a bounded `model_truth` future-answer-shape readiness check.
- Stage 2F-D-B is integrated/current as a narrow step: existing read-only `model_truth` probe data is now appended only in bounded `query_model` capability answers for model-inventory/model-identity questions.
- Stage 2F-D-B preserves fact-first handling for precise model fact queries (for example, `what model does stuart use?`) while keeping model capability/inventory question surfaces on `answer_path=capability_answer`.
- Stage 2F-D-B keeps configured route targets distinct from installed local model inventory; inventory may be unavailable when Ollama is missing, down, or times out.
- Stage 2F-D-B does not prove currently answering model identity, runtime health, model quality, or privileged/system capability.
- Stage 2F-D-C is integrated/current as a narrow hardening step: bounded `model_truth` capability-answer fallbacks now use explicit unavailable/unknown wording for unavailable inventory, validation failure, and probe exception paths.
- Stage 2F-D-C preserves bounded scope: no new probes, no broadened probe-backed answers, and no changes to the model roster.
- Stage 2F-D-C clarifies that when installed inventory is unavailable in a run, missing/extra installed-model sets are unknown for that run.
- Stage 2F-D-D is integrated/current as a bounded explicit context-capability step: explicit context-capability questions can now return bounded probe-informed answers from existing read-only probes (`host_baseline`, `session_baseline`, `tool_inventory`, `model_truth`).
- Stage 2F-D-D preserves boundaries: general capability discovery remains not dynamically probe-backed, and normal assistant answers remain not broadly probe-backed.
- Stage 2F-D-D adds no new probes, no new actions, no privileged lane, no maintenance advisor, no voice/applet/service layer, and no document RAG ingestion/execution path.
- Stage 2F-E-A is integrated/current as a structural boundary step: capability-question classification is now separated from capability answer generation through `src/bond/ai_capability_classifier.py`.
- Stage 2F-E-A preserves current behavior for context/general/specific capability questions while adding no new aliases, probes, or actions.
- Stage 2F-E-B is integrated/current: transitional linguistic intent normalization contract is now recorded in code and docs.
- Stage 2F-E-B preserves classifier and answer behavior unchanged.
- Stage 2F-E-B records that deterministic aliases are transitional scaffolding, not the final smart linguistic layer.
- Stage 2F-E-B does not implement smart linguistic support.
- Stage 2F-E-B does not implement semantic classification.
- Stage 2F-E-B does not implement model-based classification.
- Stage 2F-E-B adds no new aliases, probes, actions, or execution authority.
- Stage 2F-E-C is integrated/current: a bounded explicit read-only maintenance/readiness report is available.
- Stage 2F-E-C remains partial and read-only.
- Stage 2F-E-C uses existing read-only probes only.
- Stage 2F-E-C added no new probes, actions, writes, deletes, fixes, package installs, service restarts, privileged operations, or autonomous repair.
- Stage 2F-E-C does not inspect real package freshness, logs, or storage usage.
- Stage 2F-E-E is integrated/current as a validation-trust cleanup: selftest pass accounting no longer double-counts memory tests, and selftest accounting integrity is guarded.
- Stage 2F-F-B is integrated/current as report integration only for bounded read-only maintenance probes (`package_update_status`, `storage_hygiene`, `boot_service_health`).
- Explicit maintenance/readiness report integration exists; maintenance planning, privileged execution, repair/update/cleanup actions, dashboarding, and broad normal-answer probe backing remain future work.
- Normal assistant answers are not yet dynamically probe-backed; general capability discovery is still not dynamically probe-backed.
- Temporary dev/test telemetry exists behind `BOND_DEV_TELEMETRY=1`. It emits one JSON line to stderr with elapsed_ms and safe routing/decision metadata for testing. Normal Bond answers remain telemetry-free by default, and final product behavior must not include telemetry in assistant answers.
- capability-registry honesty tests now verify planned/unsupported capabilities are not reported as available
- current integrated selftest summary from latest run: {"ok": true, "passed": 242, "failed": 0, "total": 242}

## Partial, open, or not implemented yet

- no privileged execution lane implementation
- action parser remains heuristic and partial
- action catalog and executor remain narrow/rootless
- no dynamic probe-backed capability discovery yet in normal assistant answers; current capability-answer integration is read-only and does not authorize execution, with bounded probe detail limited to explicit model/context capability questions
- probes now have a first structured read-only foundation, but the broader planned probe surface remains partial
- memory retrieval remains shallow/lexical relative to the documented target architecture
- no document ingestion/drop-folder knowledge pipeline yet
- no service/daemon, applet, voice, or final packaging implementation yet
- no system maintenance advisor implementation yet
- no safe OS update/upgrade planner yet
- no monthly health report generation yet
- no graphical maintenance dashboard yet

## Blockers

- public/private boundary cleanup must be completed before Stage 2F
- source/config path sanitation must be completed before Stage 2F
- documentation consolidation must be completed before Stage 2F
- Gitea/docs reconciliation gate is satisfied in P0E

- routing contract and capability schema not yet applied to code
- Layer 0/1/2 system fact hierarchy not yet implemented in probe layer
- adapter boundary design not yet formalized in source
- P0F public GitHub preparation remains open for publication/release readiness

## Core truth

Bond is:

- a local AI assistant project under active restructuring
- repository-backed but still in a transitional phase
- functionally real but behaviorally unreliable in general assistant use
- partially aligned with long-term architecture, but not yet correct at the decision level

Bond is not:

- a finished assistant
- a trustworthy system automation layer
- a complete natural-language interface
- a properly packaged or deployable application
- a consistent or safe general-purpose assistant

## What is currently working

These are capabilities that exist in some real, testable form:

- repository structure exists and is usable
- git-based workflow is active
- core modules exist under `src/bond/`
- selftests currently pass
- memory system exists with:
  - logs
  - facts
  - archive separation
  - rotation and retention
- changelog/backup tooling exists
- some deterministic command execution paths exist
- some project-specific query grounding works
- repository documentation has begun to replace transcript-only knowledge

## What is partially working

These areas exist but are not reliable or complete:

- action execution (inconsistent behavior)
- command parsing (too heuristic and error-prone)
- assistant responses (sometimes correct, often misleading)
- system interaction (not consistently grounded in real tools)
- memory retrieval (improved, but still overreaches)
- mixed-intent handling (inconsistent rejection or splitting)
- path handling (improved, but still tied to transitional assumptions)

## What is not working correctly

These are confirmed weaknesses based on live testing:

- general assistant sanity is unreliable
- capability honesty is weak (claims unsupported abilities)
- natural-language action parsing is inaccurate
- target resolution is inconsistent or incorrect
- execution boundaries are unclear
- lexical hijacking is common (keywords trigger wrong modes)
- mixed-intent handling is inconsistent
- dangerous actions are not reliably blocked or refused
- system-probe usage is minimal or absent in many cases
- environment awareness is partially fabricated instead of grounded

## Architecture reality

The current architecture:

- is modular in structure
- is not clean in responsibility boundaries
- still relies too heavily on heuristics in central logic
- lacks a strict separation between:
  - parsing
  - policy
  - capability truth
  - execution

The orchestrator layer is too heavy and contains logic that should be moved into dedicated subsystems.

## Documentation reality

The repository now contains structured documentation, but:

- important constraints still exist only in transcript history
- some docs describe intent better than reality
- install/update/uninstall flows are not fully defined
- subsystem contracts are not fully specified
- packaging and entry points are not fully documented
- external Gitea planning data exists outside the repository and is not locally authoritative unless explicitly fetched

Planning and design analysis documents have been preserved in the repository archive:

- `docs/archive/analysis/Bond_Router_Agent_Redesign_Updated.md` — historical routing/dispatch design analysis
- `docs/archive/analysis/Bond_Capability_Expansion_Plan.md` — historical capability expansion design analysis

These archived documents preserve design reasoning. Their content is being consolidated into the scoped current canonical docs.

The repository is improving, but not yet self-sufficient.

## Runtime reality

The current system:

- still depends on a transitional local setup
- still reflects earlier loose-script structure in parts
- has not completed path normalization
- is not cleanly installable as a standalone program
- is not isolated from user-specific environment assumptions
- model/runtime truth is still under-specified in docs and implementation: configured route model strings must not be mistaken for installed or reachable runtime models
- probe documentation was previously too thin and is now being corrected toward a canonical three-layer specification
- default app/backend resolution evidence ranking is not yet fully formalized in implementation

### Canonical baseline local model roster

The current project baseline local roster is:

- qwen2.5:3b-instruct
- gemma2:2b
- qwen2.5:7b-instruct
- nomic-embed-text:latest

Model role mapping for this baseline:

- `qwen2.5:3b-instruct` is the default small-model baseline for coordination-adjacent, routing-adjacent, schema-constrained front tasks, and lightweight interaction work.
- `gemma2:2b` is the ultra-light baseline for cheap support tasks such as memory hygiene, narrow classification, and other low-cost helper work where acceptable quality can be maintained.
- `qwen2.5:7b-instruct` is the main local workhorse baseline for the majority of meaningful reasoning, technical work, research synthesis, planning, and other heavier local tasks.
- `nomic-embed-text:latest` is the baseline embedding model for semantic retrieval and document knowledge indexing.

Baseline rule:

- this roster is the de facto documented baseline and should be designed around by default
- no local heavyweight model tier is currently part of the project baseline
- heavy lifting must be achieved through decomposition, stricter routing, retrieval, validation, and bounded specialist contracts around the existing roster
- the roster should only change if the project hits a real wall or if a clearly justified replacement is intentionally adopted

This section documents the current project baseline roster and design center of gravity, not a claim that runtime health was freshly probed in that exact moment.

## Testing reality

Current tests:

- verify that subsystems do not break
- do not guarantee correct assistant behavior
- do not cover:
  - general assistant sanity
  - capability honesty
  - unsafe action refusal
  - mixed-intent handling
  - lexical hijack resistance

Passing tests does not mean the assistant is behaving correctly.

## Memory reality

Memory exists and has structure, but it is still fundamentally shallow and weak in these specific ways:

- **Fact storage is schema-light.** Current fact records do not carry confidence, verification status, stale-after timestamps, superseded-by references, or provenance metadata. The schema is insufficient for reliable truth-ranking.
- **Retrieval is still mostly lexical and heuristic.** There is no semantic retrieval path. Ranking is based on simple ordering and record type, not relevance scores or embedding similarity.
- **Correction memory is not first-class.** Corrections are stored but do not have override authority in retrieval. A correction does not yet reliably outrank the older fact it supersedes.
- **Reflection is not strong enough to count as verified memory improvement.** Reflections are hypothesis and lesson outputs. They must not be treated as evidence. The current implementation does not enforce this distinction.
- **Archive is mostly retention hygiene and metadata, not rich historical retrieval.** Archive rotation manages file size and recency. It is not a queryable historical knowledge store.
- **Document knowledge is not first-class yet.** There is no ingestion pipeline, no chunk store, no embedding index, and no semantic retrieval path for documents. This entire stratum is absent.
- **Active context is useful for session continuity but too lossy to be the central knowledge representation.** It loses structure, provenance, and confidence information, and must not be treated as the primary memory surface.

Memory is also still too eager to activate and can hijack unrelated prompts. The distinction between Live Truth Layer, Durable Fact Layer, Episodic Operational Memory, Document Knowledge Memory, and Correction Memory is not yet enforced in behavior.

## Document knowledge reality

Bond does not yet have a first-class document knowledge store. This is an identified architectural gap, not a roadmap aspiration. Specifically:

- No complete ingestion pipeline exists. There is no file detection, type classification, modality-based parsing, chunking, embedding, or validation pipeline in the current implementation.
- No strong reindexing, supersession, or deletion propagation exists. File changes are not hash-tracked. Stale chunks cannot be replaced. Source file deletion does not propagate to any chunk or index removal.
- Provenance discipline is not yet strong enough. Knowledge units do not carry source file reference, extraction method, ingestion timestamp, file hash, modality annotation, or confidence at the level required by the target architecture.
- Document retrieval is not yet strong semantic retrieval. There is no embedding-based or hybrid retrieval path for document content. Retrieval over documents is lexical at best.

The target architecture for document knowledge ingestion and retrieval is defined in `docs/KNOWLEDGE_INGESTION.md`. That document defines the target. This section defines the current gap.

## System interaction reality

Bond does not yet properly use:

- package inspection tools
- environment inspection tools
- system information tools
- desktop/session inspection

Bond also does not yet properly inspect or reason over:

- package update state
- package-manager health
- Trash/cache size
- duplicate-file candidates
- boot/service health
- `systemd-analyze blame`
- failed units or journal warning summaries

Any future maintenance feature must start as read-only inspection and recommendation. Applying system updates, deleting files, emptying Trash, or changing services must remain outside current capability until the privileged lane and confirmation/audit/rollback contracts exist.

Much of its behavior is still model-driven rather than system-grounded.

## Safety reality

Safety exists in partial form:

- some path blocking exists
- some dangerous cases are handled

But:

- refusal logic is inconsistent
- dangerous actions are sometimes misinterpreted
- system-level impact is not reliably controlled

## Conclusion

Bond currently has:

- a real base
- real structure
- real progress

But it also has:

- unreliable assistant behavior
- weak decision boundaries
- incomplete documentation
- transitional runtime assumptions

The project is not in a polishing phase.

It is in a corrective phase.

## Immediate implication

All future work must assume:

- current behavior is not trustworthy enough
- documentation must reflect reality, not intention
- architecture must be tightened before features expand
- repository must become the true source of project knowledge

This document must stay aligned with actual system behavior.

If reality changes, this file must be updated.

## Cross-document alignment

- Architecture: `docs/ARCHITECTURE.md`
- Memory system specification: `docs/MEMORY.md`
- Document knowledge ingestion design: `docs/KNOWLEDGE_INGESTION.md`
- Capability registry: `docs/CAPABILITIES.md`
- Master plan: `docs/BOND_PROJECT_MASTER_PLAN.md`
- Roadmap: `ROADMAP.md`
- Historical routing design archive: `docs/archive/analysis/Bond_Router_Agent_Redesign_Updated.md`
- Historical capability expansion design archive: `docs/archive/analysis/Bond_Capability_Expansion_Plan.md`

## Installation state

Bond does not yet have a finalized packaging or installation system.

However, installation, update, and uninstall behavior are no longer undefined.

They are explicitly described in:

- `docs/INSTALLATION.md`

This means:

- installation is expected to be repository-driven
- updates must be controlled and validated
- uninstall must be explicit and not leave uncontrolled residue
- legacy runtime sprawl is considered transitional debt

The project must not regress into ad-hoc script distribution.

Any future packaging work must align with the constraints defined in the installation document.
