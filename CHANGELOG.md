# Changelog

This file records meaningful repository-level changes to Bond.

It is intended to track project evolution in a form suitable for maintainers, future contributors, LLM-assisted development workflows, and later release/version discipline.

This changelog does not attempt to preserve every chat detail, temporary experiment, or live-system observation. Those belong in commit history, focused docs, issue tracking, testing artifacts, or archived transcript material as appropriate.

## Format and discipline

Until formal release tagging is established, this changelog should follow these rules:

- keep an `Unreleased` section at the top
- record only meaningful repository changes
- prefer concise entries tied to actual repo evolution
- avoid mixing future plans into completed change entries
- avoid logging speculative work as if it were done
- keep operational transcript detail out of this file unless it materially changed the repository
- treat git history as the lower-level ground truth and this file as the maintainers’ curated summary

## Unreleased
### Stage 2F-E-C classifier-boundary cleanup

- Centralized explicit maintenance-readiness alias detection behind `ai_capability_classifier.py`.
- Removed duplicated maintenance-readiness alias ownership from `ai_capability_answer.py`.
- Preserved maintenance/readiness, context, general capability, and model inventory answer behavior.
- No aliases, probes, actions, capabilities, or execution authority were added.
- Latest integrated selftest run after cleanup: 218 passed, 0 failed, total 218.

### Stage 2F-E-C read-only maintenance/readiness report

- Added `describe_maintenance_readiness` as a partial read-only capability.
- Added a bounded explicit maintenance/readiness report answer surface.
- The report uses existing read-only probes only.
- It does not fix anything, install packages, write files, delete files, restart services, or authorize execution.
- It does not inspect real package freshness, logs, or storage usage.
- Existing `inspect_package_update_status`, `inspect_storage_hygiene`, `inspect_boot_and_service_health`, `generate_periodic_health_report`, `present_maintenance_dashboard`, and `apply_privileged_system_updates` capabilities remain planned/unavailable.
- Latest integrated selftest run after Stage 2F-E-C: 216 passed, 0 failed, total 216.

### Stage 2F-E-B CI recovery

- Replaced the non-hermetic `/tmp` source snapshot selftest with a CI-safe contract-only guard.
- Preserved classifier and answer runtime behavior.
- No aliases, probes, actions, capabilities, or execution authority were added.
- Latest integrated selftest run after recovery: 208 passed, 0 failed, total 208.

### Stage 2F-E-B transitional linguistic intent normalization contract

- Added `src/bond/ai_linguistic_intent_contract.py` as a contract-only module.
- Documented deterministic aliases as transitional scaffolding behind the classifier boundary.
- Preserved classifier and answer behavior unchanged.
- Added tests proving the contract does not claim smart NLP, semantic classification, or model-based classification.
- No aliases, probes, actions, or execution authority were added.
- Latest integrated selftest run after Stage 2F-E-B: 208 passed, 0 failed, total 208.

### Stage 2F-E-A capability classifier boundary

- Moved capability-question detection/classification into `src/bond/ai_capability_classifier.py`.
- Kept capability answer generation in `src/bond/ai_capability_answer.py`.
- Preserved existing public helper behavior through compatibility imports in `ai_capability_answer.py`.
- Preserved existing context/general/specific capability answer behavior.
- No aliases, probes, actions, or execution authority were added.
- Latest integrated selftest run after Stage 2F-E-A: 200 passed, 0 failed, total 200.

### Stage 2F-D-D bounded context capability answers

- Moved `describe_context_capabilities` from planned to partial.
- Added bounded explicit context-capability answers for explicit context question surfaces using existing read-only probes only (`host_baseline`, `session_baseline`, `tool_inventory`, `model_truth`).
- Kept general capability answers non-probe-expanded (`what can you do?` remains registry summary only).
- Kept normal assistant answers not broadly dynamically probe-backed.
- No new probes, no new actions, and no execution authority were added.
- Latest integrated selftest run after Stage 2F-D-D: 192 passed, 0 failed, total 192.

### Stage 2F-D-C bounded model-truth fallback hardening

- Hardened bounded `model_truth` capability-answer fallback wording for unavailable inventory paths so installed inventory is explicitly unavailable-in-run and missing/extra installed-model sets are explicit unknowns for that run.
- Hardened validation-failure and probe-exception fallback wording to the same bounded unavailable envelope (`truth_status=unavailable`) without leaking probe exception details.
- Added Stage 2F-D-C integrated selftests for unavailable-inventory fallback behavior, validation-failure fallback behavior, exception fallback behavior, success-path continuity, and non-probe-expanded general capability answers.
- Kept scope narrow: no new probes, no broadened probe-backed answers, no model-roster changes.
- Latest integrated selftest run after Stage 2F-D-C hardening: 186 passed, 0 failed, total 186.
- This stage does not complete Stage 2F-D, does not implement maintenance advisor/package update planning, and does not complete M4.

### Stage 2F-D-B bounded model-truth capability answers

- Wired existing read-only `model_truth` probe output into bounded `query_model` capability answers for model-inventory/model-identity question surfaces only.
- Added deterministic `model_truth` answer formatting with validation and bounded fallback behavior; fallback explicitly keeps configured route targets and installed local model inventory distinct.
- Kept general capability discovery and normal assistant answers non-probe-backed.
- Reordered unknown/pure-question handling so precise fact queries run before capability answers, while guarding model-capability surfaces from assistant-name fact alias interception.
- Added Stage 2F-D-B integrated selftests for unit and CLI model-truth answer behavior, telemetry answer-path expectations (`capability_answer` vs `fact_answer`), non-probe-expanded general capability answers, and probe-shape compatibility.
- Latest integrated selftest run after Stage 2F-D-B integration: 181 passed, 0 failed, total 181.
- This stage does not complete Stage 2F-D, does not implement maintenance advisor/package update planning, and does not complete M4.

### Stage 2F-D-A2 cleanup and CI hardening

- updates CI to Node 24-compatible GitHub Actions majors
- adds hygiene tests for key Markdown/YAML formatting
- adds a model_truth future-answer-shape check
- preserves the boundary that normal assistant answers are not yet dynamically probe-backed

### Stage 2F-D-A dynamic probe foundation

- Added `src/bond/ai_probe_contract.py` with the deterministic structured probe-result contract for Layer 0/1/2 probe snapshots.
- Added `src/bond/ai_probes.py` with the first read-only probe set: `host_baseline`, `session_baseline`, `tool_inventory`, `router_config_models`, `ollama_model_inventory`, and `model_truth`.
- Replaced the legacy broad `src/bond/ai_scan_system.py` scanner with a thin structured probe CLI wrapper that preserves the compatibility state snapshot path.
- Added Stage 2F-D-A integrated selftests for probe contract validation, structured probe behavior, CLI JSON output, wrapper execution, and static `shell=True` absence checks.
- Updated README, STATE, TESTING, PROBES, CAPABILITIES, and ROADMAP docs to distinguish the new read-only probe foundation from future probe-backed capability discovery.
- This stage does not implement probe-backed normal answers, privileged actions, maintenance advisor behavior, or package updates.

### Stage 2F-C3 CI selftest portability fix

- Fixed Stage 2F-C3 selftest portability by using the repository-local `scripts/ai` wrapper instead of assuming a globally installed `ai` command in CI.

### Stage 2F-C5 follow-up strict timeout cleanup

- Added language-policy capability aliases for Greek and English "can you answer/respond in Greek" wording so those forms stay deterministic capability answers instead of timing out.
- Expanded unsupported side-effect action-start detection for create-folder and write-file phrasing so those requests fail closed as deterministic parser-contract rejects.
- Extended the existing Stage 2F-C5 integrated selftests with the three follow-up timeout-edge cases.
- This follow-up does not implement Stage 2F-D dynamic probes, full Greek language-state architecture, file creation, or general observe/model-chat timeout handling.
- Latest integrated selftest run after the C5 follow-up: 157 passed, 0 failed, total 157.

### Stage 2F-C5 strict timeout and diagnostic-expectation cleanup

- Updated deterministic social check-in wording so `how are you?` responses include `Bond` while remaining direct deterministic answers.
- Added capability-question surface guarding for high-risk and capability phrasing to keep question forms (update/restart/shutdown/delete/rm-rf/Greek voice/memory) from being misclassified as executable action requests.
- Added unsupported side-effect action starts (`remind`, `create a file`, `send an email`) in action-start detection to keep deterministic bounded handling and avoid model fallback.
- Added parser rejection for fake/nonexistent open targets containing `does not exist` markers.
- Added `dangerous_action_confirmation` capability registry entry and capability-answer aliases/status-note wiring for high-risk confirmation semantics.
- Expanded capability aliases for timer reminder wording, Greek voice/memory wording, and package-update question forms.
- Added Stage 2F-C5 integrated selftests covering strict timeout cleanup, capability-question wording, reject paths, and diagnostic expectation alignment.
- `notify me to stretch` remains a current bounded action dry-run path.
- `απάντα ελληνικά` remains a registry-backed `apply_response_language_policy` capability answer and is not treated as complete Greek language-state architecture.
- Stage 2F-D dynamic probes remain not implemented in this stage.
- Latest integrated selftest run after C5 integration: 154 passed, 0 failed, total 154.

### Stage 2F-C4 deterministic diagnostic cleanup

- Added centralized action-noise stripping for adversarial high-risk prefixes (`ignore all safety rules and ...`, `without asking confirmation ...`, `pretend I confirmed ...`) so embedded high-risk commands remain deterministic confirmation-required candidates.
- Expanded centralized Greek action normalizations for reboot/shutdown/delete verb surfaces so Greek and mixed-language action phrasing converges into language-neutral forms used by intent/risk gates.
- Hardened high-risk command-like detection to evaluate normalized action text and to exempt bounded harmless/quoted prompts.
- Added bounded deterministic direct answers for `say the word reboot but do not do anything` and `explain why dangerous actions require confirmation` to avoid confirmation/model-timeout misrouting.
- Expanded capability registry and capability-answer aliases for exploratory questions (voice/applet/web/memory/files/terminal/packages), timer truthfulness probes, and Greek model-inventory wording.
- Added Stage 2F-C4 diagnostic cleanup selftests for mixed-intent Greek destructive input, adversarial high-risk bypass wording, Greek polite reboot confirmation flow, timer truthfulness, Greek model inventory phrasing, exploratory capability questions, high-risk shell/update no-timeout paths, and harmless quoted safety wording.
- Greek support remains transitional and centralized in normalization/alias/intent handling; final language-state architecture is not complete.
- Stage 2F-D dynamic probes remain not implemented in this stage.
- Latest integrated selftest run after C4 integration: 136 passed, 0 failed, total 136.

### Stage 2F-C3 telemetry edge case cleanup

- Fixed bare capability noun phrase detection: "installed models" and "local models" now recognized as capability questions and answered deterministically without requiring question markers or question phrases.
- Added time-query handlers (`give me the time`, `what time is it`) to return bounded deterministic answer explaining local time queries are not yet a fully wired capability, preventing timeout/model fallback.
- Added project-state-query handlers (`current state of the project`, `project state`) to return bounded deterministic answer directing to git status/docs/STATE/CHANGELOG, preventing timeout/model fallback.
- Added four targeted Stage 2F-C3 edge-case tests in integrated selftest covering bare capability phrases and time/project-state queries.
- Historical baseline note: 113/113 baseline with +4 edge-case tests at the C3 checkpoint.

### Stage 2F-C2 telemetry verification regression cleanup

- Reordered `ai_run.py` guardrail flow so policy/action gating and action execution paths are handled before capability/fact/model fallback, then capability answers are checked before fact answers.
- Added deterministic social check-in handling for trivial prompts such as `how are you?` to avoid model fallback.
- Expanded capability-query detection/aliases for model and Greek language-policy prompts, including direct imperative-style language-policy requests.
- Hardened high-risk restart phrasing (`restart the laptop` family) to remain confirmation-required instead of falling through to action-not-parsed/model paths.
- Added six targeted Stage 2F-C2 regression tests in integrated selftest.
- Validation baseline advanced to 113/113.

### Stage 2F-C telemetry-driven guardrail hardening

- Hardened deterministic guardrails from telemetry findings: assistant-invocation stripping, Greek action normalization coverage, high-risk natural command shaping, and mixed-intent preemption protection.
- Moved capability-answer interception behind intent/risk gating so mixed/action paths are not preempted by capability wording.
- Expanded capability-alias coverage (English/Greek/colloquial/adversarial phrasing) while preserving registry truth boundaries for planned/unsupported capabilities.
- Improved single-action dry-run metadata to always include non-empty normalized action_steps for safe action previews.
- Added telemetry-derived regression selftests for assistant-prefixed commands, high-risk confirmations, mixed-intent rejection, and capability aliases.
- Telemetry remains opt-in dev/test instrumentation (`BOND_DEV_TELEMETRY=1`), stderr-only, and outside normal assistant answer text.
- Validation baseline has since advanced to 113/113 after Stage 2F-C2 cleanup.

### Development telemetry (opt-in test instrumentation)

- Added opt-in `BOND_DEV_TELEMETRY=1` development telemetry for response timing and safe decision metadata.
- Telemetry is disabled by default, goes to stderr, and is not part of normal Bond answers.
- Added dev telemetry selftests.
- New expected validation baseline: 78/78.

### Stage 2F-B read-only capability answer integration

- Corrected the describe_capabilities registry note so capability summaries no longer claim assistant-answer integration is pending after Stage 2F-B.
- Added `src/bond/ai_capability_answer.py` for deterministic read-only capability answers.
- Wired capability questions into `src/bond/ai_run.py` before model/action handling.
- Added six capability-answer selftests.
- Updated docs to distinguish static registry-backed answers from future dynamic probe-backed discovery.
- Validation baseline has since advanced to 113/113 after follow-up hardening stages.

### Stage 2F-A capability registry foundation

- Added `src/bond/ai_capabilities.py` static capability registry foundation.
- Added capability-registry honesty selftests.
- Updated docs to distinguish code-level registry foundation from dynamic probe-backed capability discovery.
- New validation baseline expected: 67/67.

### Documentation

- Documented planned system maintenance and health-advisor capabilities, including read-only package update inspection, safe update planning, storage hygiene reporting, duplicate-file candidate reporting, boot/service health reporting, monthly health reports, and future GUI/dashboard presentation boundaries.
- Clarified that maintenance reports are recommendations only and must not perform privileged updates, cleanup, deletion, or service changes without future privileged-lane, confirmation, audit, and validation support.

### P0F-A2 - Public repository truth alignment and hygiene
- Aligned current validation baseline references on 61/61.
- Added public security, contribution, and license files.
- Moved the root checkpoint transcript into the historical archive.
- Clarified public-use safety boundaries in the README.
- Preserved current behavior; no product capabilities were added.

### P0F-A1 - Current documentation reference cleanup
- Replaced stale current-doc references to pre-archive analysis/report paths with archive paths.
- Removed or redirected references to obsolete tool-specific workflow documents.
- Preserved current behavior; no product capabilities were added.

### P0E - Gitea and roadmap reconciliation
- Reconciled local Gitea milestones with the repository roadmap model.
- Created/opened roadmap-aligned tracker milestones for P0, M1-M6, and backlog work.
- Closed legacy Phase 1-6 milestones as historical tracker structure without deleting them.
- Closed the completed policy-classification issue and moved remaining open issues to current milestones.
- Updated repository planning docs to reflect the reconciled tracker state.
- Preserved Stage 2E behavior; no product capabilities were added.

### P0D - Historical documentation archival
- Moved historical design analysis and implementation reports under `docs/archive/`.
- Preserved historical reasoning while preventing archived material from acting as current project truth.
- Added archive guidance for using historical documents safely.
- Sanitized local/private path references in archived documentation.
- Preserved Stage 2E behavior; no product capabilities were added.

### P0C - Public documentation consolidation

- Rewrote README for public human readers.
- Rewrote development documentation as a tool-agnostic contributor guide.
- Rewrote the AI-assisted maintenance guide without tool-specific prompt scaffolding.
- Sanitized the runtime path reference.
- Removed obsolete tool-specific workflow prompt/operator files from tracked public docs.
- Preserved current Stage 2E behavior; no product capabilities were added.

### P0B - Source and deploy sanitation

- Removed unused legacy local-path source debt by deleting `src/bond/ai_summarize_system.py` after confirming no active runtime/script/deploy references.
- Normalized deploy systemd examples away from machine-specific paths.
- Replaced user-specific test fixtures with neutral placeholders.
- Preserved Stage 2D confirmation and Stage 2E parser-contract behavior.
- No product capabilities were added.

### P0A - Publication boundary and cleanup plan

- Added a public/private repository boundary policy.
- Added a staged cleanup plan before Stage 2F.
- Documented that the current private history should not be pushed publicly as-is.
- Documented that the preferred public migration path is a fresh sanitized public repository.
- Marked Stage 2F as paused until cleanup gates pass.
- Preserved Stage 2E code behavior; no product capabilities were added.

### Stage 2D confirmation token flow

- Stage 2E: added parser contract and action preflight so action-looking requests with no safe parsed action shape fail closed as `action_not_parsed` before executor, while preserving Stage 2D confirmation behavior.

- Added deterministic short-lived confirmation tokens for high-risk `confirmation_required` action requests.
- Added confirmation request handling (`confirm TOKEN` / Greek confirmation forms) with invalid/expired/consumed safeguards and no policy/executor bypass.
- Added selftest coverage for confirmation token creation, validation failures, consumption, non-reuse, and confirmed dry-run path behavior.
- Hardened Stage 2D so confirmed requests with no parsed executable action fail closed before any execution path.

### Documentation reality sync after Stage 2C

- Updated repository docs to reflect implemented Stage 2A routing, Stage 2B policy gate, Stage 2C action-contract/dry-run behavior, and the current 43/43 selftest baseline.
- Preserved strict boundaries between implemented work and future work (including Stage 2D confirmation flow, capability registry implementation, parser/probe/memory depth, and service/applet/voice/packaging targets).

### Selftest non-interactive action mode

- Made automated selftests non-interactive by running GUI-opening action requests through action dry-run mode.
- Added selftest coverage to ensure the test environment enables `BOND_ACTION_DRY_RUN`.
- Preserved explicit dry-run and high-risk confirmation coverage without requiring manual window closing.

### Stage 2C cleanup: events log bucket

- Added `events` as a first-class memory log bucket so action dry-runs can be logged without falling back to chat logs.
- Added selftest coverage for the `events` memory log bucket.
- Staged the new action contract module for tracking without committing.

### Stage 2C action dry-run / confirmation contract

- Added Stage 2C action contracts to separate dry-run, safe execution, confirmation-required, rejection, and chat lanes.
- Added explicit and environment-driven action dry-run support via `BOND_ACTION_DRY_RUN`.
- Added action contract context to internal model prompts and route/policy/action metadata to logs.
- Added selftests for action contracts, dry-run behavior, and high-risk confirmation-required responses.

### Stage 2B policy gate + action lane separation

- Added Stage 2B policy gate separating route decisions, action/chat classification, and execution/chat branching.
- Added deterministic policy decisions for chat, safe actions, action chains, mixed-intent rejection, and high-risk action confirmation requirements.
- Added policy context to internal model prompts and route/policy metadata to logs.
- Added selftests for policy decisions and mixed-intent policy rejection.

### Stage 2A validation baseline cleanup

- Cleaned Stage 2A validation baseline by making selftests honor the resolved config path and a hermetic temporary archive root.
- Replaced the remaining active-source heavier-model memory reflection default with the installed lean model `gemma2:2b`.

### Stage 2 brain/routing rewrite - Stage 2a structured deterministic routing

- Began Stage 2 brain/routing rewrite by adding deterministic structured routing in ai_router.py.
- Aligned router profiles with the actual lean local model roster: qwen2.5:3b-instruct, gemma2:2b, and qwen2.5:7b-instruct.
- Replaced legacy automatic routing in ai_run.py with structured route decisions and route metadata logging.
- Added selftests for route decisions and router profile model truth.

### Path substrate and system portability

- Added platform-aware Bond path resolution for config, data, state, cache, memory, router config, changelog, archive, and wrapper entry points.
- Replaced hardcoded user-home runtime assumptions in active source modules and scripts with BOND_ROOT/env/config-driven resolution.
- Updated selftest path checks to avoid user-specific second-drive assertions.
- Central path resolver now supports Windows, macOS, Linux, and Android-like (Termux) environments with proper XDG and platform-native fallbacks.
- All wrapper scripts now repository-relative via dynamic BOND_ROOT discovery and PYTHONPATH injection.
- Config paths now support URI-like prefixes (repo://, config://, data://, state://, cache://) and variable expansion for portable configuration.
### Documentation

- README expanded into a real project front page describing Bond’s identity, current state, goals, repository layout, documentation map, workflow expectations, and documentation limits.
- Documentation effort explicitly reframed around making the repository, not chat history, the durable source of truth.
- Added canonical trust, explainability, capability-discovery, extension, context, and interaction-mode documentation.
- Added canonical text-first Greek language support and localization planning documentation.
- Added canonical packaging strategy documentation covering Python core, Stage 1 local install, Stage 2 platform adapters, and integration boundaries.
- Added service, applet, voice, and tool-specific workflow documentation from the documentation-gap blueprint.

### Repository discipline

- Repository-first project direction reaffirmed.
- Documentation, install flow, packaging notes, issue structure, milestone structure, and release/versioning discipline identified as first-class engineering work rather than optional polish.

### Architecture and planning

- Current planning direction tightened around explicit subsystem boundaries for parsing, action policy, capability truth, execution, memory quality, correction ingestion, system probes, and behavioral testing.
- Long-term direction clarified: preserve the modular architecture while performing targeted corrective redesign in central decision layers.

## Historical baseline

The entries below summarize the already-established project evolution that led to the current repository phase.

### Pre-repository / loose-script phase

- Bond began as a loose collection of scripts under earlier live paths rather than as a clean repository-centered program.
- Runtime, config, code, and memory concerns were not cleanly separated.
- Hardcoded paths and environment-specific assumptions were common.
- Documentation and operating knowledge were overly dependent on transcript/chat context.

### Structural correction phase

- Need for a stricter architecture was recognized after observing that passing subsystem checks did not guarantee sane assistant behavior.
- Path handling, repository layout, and project structure began moving toward a cleaner source-tree model.
- Repository hygiene improved through git usage, ignore rules, and more deliberate change discipline.

### Core alignment phase

- Core scripts and project wiring were brought into closer alignment.
- Selftests reached a passing state.
- Memory retrieval priorities and live-truth-versus-archive handling were tightened.

### Stress-test reality check phase

- Live testing exposed major weaknesses in general assistant sanity, capability honesty, action truthfulness, mixed-intent handling, lexical hijacking, and system-tool grounding.
- The project conclusion shifted from “polish the current system” to “perform a controlled but more aggressive corrective rewrite of selected decision layers.”

### Documentation split phase

- Monolithic transcript dependency began being reduced by splitting durable knowledge into repository documentation.
- Core docs such as architecture, behavior contract, current paths, testing, state, compiled transcript conclusions, and master planning documents were established.

## Future release discipline

Once version tags are introduced, this file should evolve toward a release-oriented structure such as:

- `## [Unreleased]`
- `## [0.1.0] - YYYY-MM-DD`
- `## [0.1.1] - YYYY-MM-DD`

At that stage:

- completed unreleased items should move into versioned sections
- version sections should summarize shipped repository changes only
- release tags, release notes, and this changelog should stay consistent with each other
