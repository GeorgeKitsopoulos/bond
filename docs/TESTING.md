# Testing

This document defines how testing must work for Bond.

It is not a list of current tests.
It is a definition of what tests are expected to prove.

## Core rule

Passing tests must mean:

- the assistant behaves correctly
- not just that code runs without crashing

If tests pass while behavior is incorrect, the test suite is insufficient.

## Current reality

Current tests:

- validate that subsystems do not break
- validate some internal flows
- confirm that scripts execute

Current tests do not:

- guarantee correct assistant behavior
- guarantee safety
- guarantee capability honesty
- guarantee correct action handling

So current passing tests are necessary but not sufficient.

## Current selftest baseline

Current integrated selftest summary from latest run is 218 passed, 0 failed,
total 218. Coverage includes Stage 2E parser-contract/action-preflight checks,
Stage 2D confirmation-token flow coverage, Stage 2F-A capability-registry
honesty checks, Stage 2F-B capability-answer checks, Stage 2F-C telemetry-
derived guardrail regression checks, Stage 2F-C2 regression-cleanup checks,
Stage 2F-C3 edge-case cleanup checks (bare capability phrases, time queries,
project-state queries), Stage 2F-C4 deterministic diagnostic cleanup checks,
Stage 2F-C5 strict timeout/diagnostic-expectation cleanup checks, the Stage
2F-C5 follow-up strict-timeout cleanup checks, Stage 2F-D-A probe foundation
checks, Stage 2F-D-A2 cleanup/hardening checks, Stage 2F-D-B bounded model-
truth capability-answer integration checks, Stage 2F-D-C bounded model-truth
fallback hardening checks, and Stage 2F-D-D bounded context-capability answer
checks, plus Stage 2F-E-A capability-classifier-boundary checks.

The current integrated suite covers:

- parsed single action recognition
- parsed action chain recognition
- unparsed single action rejection
- partial action chain preflight failure
- mixed intent remains mixed after parsing
- `notify me` fails with `action_not_parsed` before executor
- safe single-action dry-run still works
- safe action-chain dry-run still works
- high-risk confirmation-required flow remains intact
- capability-registry validation and required-entry presence checks
- planned/unsupported capabilities are tested as unavailable
- partial current capabilities are tested as available-with-caveats
- general English capability question handling is tested
- Greek capability question handling is tested
- planned system updates are tested as not available in capability answers
- unsupported timer/clipboard are tested as unavailable in capability answers
- normal chat is tested to ensure capability-answer interception does not trigger
- assistant-prefixed and Greek action phrases are tested to route deterministically through dry-run action paths
- high-risk natural English/Greek commands are tested to return confirmation-required without model-answer fallthrough
- mixed action+question requests are tested to reject as mixed intent without capability-answer/model-answer preemption
- expanded capability aliases (including colloquial/adversarial prompts) are tested to return deterministic registry-backed capability answers
- deterministic social check-in handling is tested to avoid model fallback for trivial prompts
- model and language capability prompts are tested to route as deterministic capability answers
- restart-the-laptop phrasing is tested to return confirmation-required with tokenized high-risk flow
- adversarial high-risk phrasing and confirmation-bypass wording are tested to stay confirmation-required without model fallback
- Greek polite high-risk phrasing and Greek destructive mixed-intent phrasing are tested for deterministic policy routing
- unsupported-capability truthfulness prompts, Greek model-inventory wording, and exploratory capability questions are tested for deterministic registry-backed answers
- harmless quoted/high-risk wording and policy explanations are tested for bounded deterministic direct answers
- Greek voice/memory capability-question forms are tested to remain deterministic capability answers
- unsupported reminder/file/email request surfaces are tested to avoid model-timeout fallback (with reminder as capability answer and unsupported file/email requests as deterministic rejects)
- high-risk capability-question wording is tested to stay capability answers while high-risk imperatives remain confirmation-required
- social/name diagnostics are tested for expected deterministic alignment (`how are you?` includes Bond in direct answer; `what is your name?` remains fact answer)
- `notify me to stretch` is tested to remain the current bounded action dry-run path
- `απάντα ελληνικά` is tested to remain registry-backed `apply_response_language_policy` capability-answer behavior and is not treated as proof of complete Greek language-state architecture
- Greek "can you answer in Greek?" wording is tested to route as the same bounded language-policy capability answer rather than timing out
- unsupported create-folder and write-file side-effect requests are tested to reject deterministically with `action_not_parsed`

Greek support in these tests remains transitional and centered on normalization/alias/intent handling, not final language-state architecture.
Stage 2F-D-A probe foundation tests verify schema validation, structured failure behavior, read-only host/session/tool/router/model probe behavior, CLI JSON output, wrapper execution, no `shell=True` in the new probe code, and no hard requirement for Ollama, GUI, or network.
Stage 2F-D-A2 cleanup/hardening tests verify CI action majors (`actions/checkout@v5`, `actions/setup-python@v6`), CI workflow multi-line hygiene (not collapsed), current docs/workflow multi-line hygiene (not collapsed), bounded `model_truth` future-answer-shape readiness for later integration, and no Stage 2F-D-B overclaim wording in current docs.
Stage 2F-D-B tests verify bounded `model_truth` detail appears only on `query_model` capability answers, telemetry answer paths remain deterministic (`capability_answer` for model capability/inventory surfaces, `fact_answer` for precise model facts), and general capability discovery remains non-probe-expanded.
Stage 2F-D-B tests also verify `model_truth` boundaries: configured route targets and installed local inventory are distinct facts; inventory may be unavailable in a run; and bounded model-truth detail does not prove currently answering model identity, runtime health, model quality, or privileged/system capability.
Stage 2F-D-C tests verify bounded fallback hardening for `model_truth` capability answers: unavailable inventory wording is explicit and does not claim known missing/extra installed-model sets, validation-failure and exception paths use the same unavailable fallback envelope, success path remains bounded, and general capability discovery remains non-probe-expanded.
Stage 2F-D-D tests verify bounded explicit context-capability handling: context detection, context answer shape, plain general capability answers not context-expanded, CLI English context answer behavior, CLI Greek context answer behavior, and probe-exception fallback behavior without exception leakage.
Stage 2F-E-A tests verify classifier boundary behavior: classifier module public contract, context precedence, general capability staying general, specific model-inventory classification, normal chat rejection, backward-compatible helper imports, no probe side effects during classification, and unchanged CLI behavior after classifier split.
Stage 2F-E-B tests verify the transitional linguistic intent contract: linguistic contract module public contract, aliases marked transitional and not final NLP, boundary and scope fields, prohibitions and safety invariants, validation and summary lines, contract module has no runtime coupling to classifier, answer generation, probes, subprocess, network, or file I/O, existing classifier behavior unchanged, and docs recording the contract without overclaim.
Stage 2F-E-C tests verify bounded read-only maintenance/readiness behavior: registry capability shape and planned maintenance capabilities remaining unavailable, classifier detection as specific-only, maintenance answer shape, capability status boundary wording, probe exception fallback without exception leakage, CLI maintenance/readiness report behavior, existing capability paths unchanged, and docs recording the read-only maintenance boundary without overclaim.
Stage 2F-E-C cleanup tests verify classifier-owned explicit capability alias helper behavior, maintenance-readiness explicit alias helper behavior, answer-module removal of maintenance-readiness alias tables, and behavior preservation for maintenance/readiness answers, model inventory answers, context/general capability answers, and normal-chat rejection.
Subprocess timeout behavior is covered by selftests for model invocation, safe-action execution, and selftest subprocess guards.
These C5 checks are strict deterministic guardrails and do not claim that general chat/model timeout behavior is solved.

This baseline is necessary and useful, but it is not proof of final assistant correctness or product maturity.

## Development telemetry for tests

- Enable with `BOND_DEV_TELEMETRY=1`.
- Emits one `BOND_DEV_TELEMETRY` JSON line to stderr.
- Includes elapsed_ms and safe decision metadata.
- Disabled by default.
- Not part of final assistant answer behavior.
- No prompts, user text, memory contents, or environment values are included.

## Test categories

Bond testing must be divided into explicit categories.

# Test Architecture

## Layers

- unit
- behavior
- probe
- integration
- smoke

---

## Failure Corpus (MANDATORY)

- open internet
- start timer
- read clipboard
- show path
- yes open it

---

## Rule

Every behavior rule must map to a test.

### 1. Subsystem tests

These verify internal components.

Examples:

- module import validity
- function execution
- script-level correctness
- basic data handling

These tests confirm that the system is not broken internally.

They do not prove assistant correctness.

### 2. Behavioral tests

These verify how Bond behaves as an assistant.

These must include:

- general prompts (e.g. greetings, simple questions)
- capability questions
- action requests
- ambiguous inputs
- mixed-intent inputs

Behavioral tests must check:

- correctness of interpretation
- correctness of response
- adherence to behavior contract

### 3. Capability honesty tests

These verify that Bond does not claim unsupported abilities.

Examples:

- asking for unsupported features (timers, screenshots, etc.)
- verifying refusal or limitation explanation
- verifying no fabricated execution

### 4. Action policy tests

These verify that actions are classified and handled correctly.

Examples:

- deterministic allowed actions
- ambiguous actions
- unsupported actions
- risky or dangerous actions

Tests must verify:

- correct classification
- correct decision (execute, refuse, clarify)
- no silent reinterpretation

### 5. Safety tests

These verify that dangerous operations are handled correctly.

Examples:

- delete commands
- system shutdown
- process termination
- access to sensitive files

Tests must verify:

- refusal when appropriate
- strict control behavior
- no accidental execution

### 6. Mixed-intent tests

These verify handling of inputs containing multiple requests.

Examples:

- "open terminal and tell me the weather"
- "print path and delete logs"

Tests must verify:

- detection of multiple intents
- correct refusal or structured handling
- no uncontrolled merging

### 7. Lexical hijack tests

These verify that keywords do not override intent.

Examples:

- "test notification"
- "memory test"
- "path test"

Tests must verify:

- correct interpretation
- no unintended mode switching

### 8. System-probe tests

These verify that Bond uses real system data where required.

Examples:

- current directory
- environment variables
- installed packages
- filesystem state
- package update status inspection
- package-manager degraded-state reporting
- Trash/cache size reporting
- duplicate-file candidate reporting
- failed systemd unit reporting
- `systemd-analyze blame` summary reporting
- journal warning summary reporting

Tests must verify:

- real probe usage
- correct output
- no fabricated answers

Concrete expectations that system-probe tests must cover:

- **Layer 0/1/2 separation is enforced.** Layer 0 and Layer 1 probe evidence is collected and normalized, and model-facing reasoning consumes Layer 2 assistant-usable facts rather than raw scan dumps.
- **Configured route targets are not treated as installed-model truth.** A raw route/config string must not be accepted as proof of installed local model inventory.
- **Runtime availability is tested separately from config and inventory.** Tests must distinguish configured route targets, installed local model inventory, and runtime availability.
- **Default app/backend resolution obeys evidence ranking.** Resolution order must be explicit default handler, desktop/session API fact, desktop entry match, installed binary presence, then heuristic fallback.
- **Probe failure never becomes fabricated truth.** Failed probes must return structured uncertainty or error output, not invented factual values.
- **Guessed values are labeled as guesses.** Any heuristic output must be marked as heuristic rather than authoritative.
- **Maintenance probes are read-only.** Package, storage, duplicate, boot, service, and journal probes must not mutate system state.
- **Update planning is not update execution.** A dry-run or simulated package update plan must not apply package changes.
- **Duplicate candidates are not deletion decisions.** Tests must verify that duplicate-file output is framed as candidates with evidence, not automatic cleanup.
- **Maintenance report degradation is explicit.** Missing tools, permission-limited journal access, unavailable package managers, or stale package metadata must be reported as degraded or unavailable, not silently treated as healthy.

### 9. Memory behavior tests

These verify correct use of memory.

Examples:

- relevant retrieval
- no irrelevant injection
- correct prioritization of live vs archive data

Tests must verify:

- memory is used only when needed
- memory does not override real-time truth

Concrete expectations that memory behavior tests must cover:

- **Correction overrides older fact.** When a correction record exists for a domain, retrieval in that domain must return the correction, not the superseded older fact.
- **Live truth outranks archive and history for current-state questions.** A live probe result must take priority over any stored memory record for a question about the present state of the system.
- **Memory does not inject unrelated logs.** An operational log entry unrelated to the current query must not appear as a retrieval result for that query.
- **Reflection is not treated as evidence.** Reflection is not evidence of system state or verified truth. A reflection record must not be served as a factual answer to a truth question. Reflection may influence caution signals but must not override durable facts or live probe results.

### 10. Document knowledge and ingestion tests

These verify that the document knowledge layer behaves correctly when it is implemented. These tests are not yet active because the ingestion pipeline does not yet exist. They are defined here so that implementation proceeds toward a testable target.

Required test themes:

- **Document retrieval relevance for paraphrased queries.** A query that is semantically equivalent to a document passage but uses different phrasing must still retrieve the relevant chunk. Lexical mismatch alone must not cause retrieval failure.
- **Multilingual retrieval alignment where supported.** A query in one language must retrieve relevant chunks from documents in the same or a compatible language. Retrieval must not silently degrade for non-dominant-language content.
- **Source-grounded chunk retrieval beats unrelated recent logs.** For a document knowledge query, a relevant and well-sourced document chunk must rank above an unrelated operational log entry.
- **Provenance and confidence metadata are present on retrieved document knowledge.** Every retrieved chunk must carry source file, extraction method, ingestion timestamp, file hash, modality annotation, and confidence. A chunk without provenance must not be returned.
- **File change causes clean supersession and reindex.** When a source file is modified, the prior chunk set must be marked stale and replaced by a fresh ingestion run. Old chunks must not remain active in retrieval after successful reindexing.
- **File removal and deletion propagation stop stale chunks from surfacing.** When a source file is deleted, all associated chunks and embeddings must be removed from active retrieval. Orphaned chunks must not surface.
- **OCR, VLM, and native text distinctions are preserved where relevant.** The extraction method recorded in a chunk's provenance must reflect whether the content came from native text extraction, OCR, or visual language model interpretation. These three sources must not be flattened into one undifferentiated record.
- **Dropped files are not treated as implicit training data.** Placing a file in the knowledge folder must trigger the ingestion pipeline, not a fine-tuning or adaptation run. The test must verify that ingestion produces retrievable chunks with provenance, not model weight changes.

### 11. Greek and mixed-language tests

These verify text-first Greek and mixed-language support contracts without implying voice support.

Required test themes:

- invocation matrix tests for `bond`, `Bond`, `Μπόντ`, and `μποντ`
- mixed-language examples such as `Τι κάνεις bond` and `Μπόντ can you tell me the weather?`
- normalization tests for casefold, tonos/accent matching, punctuation handling, and mixed scripts
- response-language policy tests across language switches and preference overrides
- memory retrieval tests across Greek and English queries/content
- GUI locale fallback tests once UI localization and message catalog support exist

## Test expectations

A correct test suite must:

- cover all categories above
- include both positive and negative cases
- include failure-mode validation
- reflect real observed failure patterns
- evolve based on real system behavior, not only planned behavior

Required future survivability tests:

- schema migration correctness and compatibility-reader behavior
- rollback correctness after failed migration or failed update validation
- degraded health-state detection and reporting correctness
- resource timeout/cancellation enforcement for bounded execution
- secrets no-logging checks across action, probe, and failure paths

Required future trust/extensibility tests:

- capability discovery answers do not overclaim and are grounded in capability registry + probes
- explanation output does not reveal hidden chain-of-thought
- action preview output includes side effects and confirmation status for mutating/high-risk actions
- plugin registration paths cannot bypass policy or capability registry validation
- context-aware answers do not fabricate context and declare context source
- mode changes do not bypass safety or capability-truth constraints

Real failure patterns that test expectations must cover include:

- **Stale archive leakage.** A stale or archived record surfacing as a current-state answer when a live probe or durable fact should have taken priority.
- **Lexical mismatch on document queries.** A document knowledge query failing to retrieve a relevant chunk because the query phrasing does not literally match the chunk text.
- **Document provenance loss.** A retrieved document chunk missing source file reference, extraction method, or confidence metadata, making its origin unverifiable.
- **Correction override failure.** A superseded fact being returned instead of the correction that explicitly replaced it.
- **Reflection contamination.** A reflection record being treated as a factual answer to a truth question, overriding a durable fact or live probe result.
- **Stale chunk resurfacing after file updates.** Prior-version document chunks remaining active in retrieval after the source file was updated and reindexed.

## Failure interpretation

When a test fails:

- the system is incorrect
- or the test is incorrectly defined

Both cases must be investigated.

Test failure must not be ignored or bypassed.

## Test expansion rule

New features must not be added without:

- corresponding tests
- or explicit acknowledgment that tests are missing

Test coverage must grow with capability.

## Regression rule

Previously fixed issues must be:

- turned into tests
- protected from reappearing

The system must not regress silently.

## Documentation sync checks

Meaningful changes must be checked for documentation impact.

At minimum, review must verify whether the change affects:

- behavior
- architecture
- path truth
- testing expectations
- installation/update/uninstall behavior
- repository planning assumptions

If it does, the corresponding repository document must be updated in the same change, or the change must explicitly justify why no documentation update is needed.

A change that materially alters the system while leaving authoritative documentation stale must be treated as incomplete.

As a lightweight local declaration gate, the repository may provide a `make reviewcheck` target backed by `scripts/bond-reviewcheck`.

Such a target does not automatically prove that documentation is correct, but it does force explicit declaration of whether documentation review was performed, whether required external planning context was supplied, and a short written note about the change and documentation impact.

## Behavioral priority

Behavioral correctness is more important than:

- passing subsystem checks
- performance improvements
- feature count

A fast, feature-rich assistant that behaves incorrectly is not acceptable.

## Enforcement direction

Testing must eventually integrate with:

- CI or local automated runs
- pre-change validation
- post-change validation
- change tracking

The test system must become a gate, not a suggestion.

## Summary

Testing must ensure that Bond:

- behaves correctly
- acts safely
- tells the truth
- respects policy boundaries
- uses real system data
- does not regress

If tests do not guarantee this, they are incomplete.
