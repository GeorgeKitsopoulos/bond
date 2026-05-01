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
- New validation baseline expected: 73/73.

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
