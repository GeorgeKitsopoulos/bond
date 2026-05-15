# Bond

Bond is a local-first assistant project for Linux systems. It is currently focused on safe request routing, policy gating, dry-run behavior, confirmation before risky actions, and portable runtime paths.

## Current status

- Bond is under active development.
- The current validated baseline is Stage 2G-F-F user-space install review/report contract.
- `src/bond/ai_user_install_approval.py` added: pure deterministic, non-executing user-space install approval-envelope planning contract that composes transaction/preflight planning inputs into deterministic `approval_candidate` and `approval_json_preview` outputs.
- `src/bond/ai_user_install_execution_gate.py` added: pure deterministic, non-executing user-space install execution-gate/readiness decision contract that consumes approval-envelope inputs into deterministic `gate_decision` and `gate_json_preview` outputs.
- `src/bond/ai_user_install_review.py` added: pure deterministic, non-executing user-space install review/report contract that composes execution-gate inputs into deterministic `human_review_packet` and `review_json_preview` outputs.
- `src/bond/ai_user_install_transaction.py` added: pure deterministic, non-executing user-space install transaction/preflight planning contract that composes upstream write-set and manifest payload plans into ordered `transaction_candidate` and `transaction_json_preview` outputs.
- `src/bond/ai_user_install_manifest.py` added: pure deterministic, non-executing user-space install manifest payload planning contract that derives sanitized `manifest_candidate` and deterministic `manifest_json_preview` from explicit planning inputs.
- `src/bond/ai_user_install_plan.py` remains integrated: pure deterministic, non-executing user-space install write-set planning contract composing explicit installer/storage/manifest path inputs.
- `src/bond/ai_installer_plan.py` added: pure deterministic, non-executing installer/reconfigure planning contract composing Stage 2G read-only facts.
- Current documented validation baseline: compile passes and integrated selftest currently reports {"ok": true, "passed": 360, "failed": 0, "total": 360} (see docs/TESTING.md for exact summary).
- Stage 2G-F-F adds a deterministic non-executing user-space install review/report packet; it does not validate approval, authorize execution, create directories, write manifests, install packages, mutate services, move storage, generate commands, or execute commands.
- Stage 2G-F-E defines a deterministic user-space install execution-gate/readiness decision only (`gate_decision` and `gate_json_preview`); it does not validate approval, grant approval, create directories, write manifests, install packages, mutate services, move storage, generate commands, or authorize execution.
- execution_allowed remains False in Stage 2G-F-E.
- approval_validated remains False in Stage 2G-F-E.
- future_approval_mechanism_available remains False in Stage 2G-F-E.
- Stage 2G-F-D defines a deterministic user-space install approval envelope preview only (`approval_candidate` and `approval_json_preview`); it does not grant approval, does not create directories, does not write manifests, does not install packages, does not mutate services, does not move storage, does not generate commands, and does not authorize execution.
- approval_granted remains False in Stage 2G-F-D.
- Stage 2G-F-C defines an ordered user-space install transaction/preflight preview only (`transaction_candidate` and `transaction_json_preview`); it does not create directories, does not write manifests, does not install packages, does not mutate services, does not move storage, does not generate commands, and does not authorize execution.
- Stage 2G-F-B1 preserves factual package-manager identity in manifest previews while keeping command generation and execution unauthorized.
- Stage 2G-F-B defines a deterministic sanitized user-space install manifest payload preview only (`manifest_candidate` and `manifest_json_preview`); it does not create directories, does not write manifests, does not install packages, does not mutate services, does not move storage, does not generate commands, and does not authorize execution.
- Stage 2G-F-A defines a non-executing user-space write-set only and remains intact beneath Stage 2G-F-B.
- Stage 2G-E adds a read-only installer planning layer without authorizing installation, reconfiguration, service changes, manifest writes, or storage mutation.
- Stage 2G-D adds a read-only package-manager classification and dependency planning layer without authorizing installation, execution, or host mutation.
- Stage 2G-C adds a read-only install manifest and drift detection layer on top of the existing portability profiles.
- Stage 2G-B continues the portable installer/updater/satellite track with a read-only storage portability profile.
- Stage 2G-A host portability profile remains integrated and current.
- Stage 2G-D does not implement a finished installer, updater, package installer, service mutation, Steam Deck deployment, or satellite runtime.
- Stage 2G-C does not implement a finished installer, updater, package installer, package layering, service mutation, Steam Deck deployment, or satellite runtime.
- Stage 2G-B does not implement a finished installer, updater, package installer, data mover, cleanup tool, mount manager, Steam Deck deployment, or satellite runtime.
- Stage 2F-F-E adds metadata-only maintenance report readiness fields for the explicit maintenance/readiness report; it does not schedule reports, start background work, add dashboards, authorize actions, or broaden probe-backed normal answers.
- Stage 2F-F-C adds a deterministic non-executing maintenance planning contract inside the explicit maintenance/readiness report.
- Stage 2F-F-C classifies observed maintenance signals only; it does not recommend commands, execute fixes, add actions, add privileged execution, or broaden normal answers.
- Stage 2F-C hardens deterministic guardrails from telemetry findings (assistant-prefix normalization, mixed-intent handling, high-risk command shaping, and capability alias coverage) while keeping telemetry opt-in and answers telemetry-free by default.
- Stage 2F-C2 follows with a small regression cleanup for model/language capability prompts, restart-laptop confirmation shaping, and deterministic social check-in handling.
- Stage 2F-C3 addresses remaining telemetry edge cases: bare capability noun phrases ("installed models", "local models") now deterministically answer as capability questions, and time/project-state queries return bounded deterministic answers instead of timing out.
- Stage 2F-C4 deterministic diagnostic cleanup adds centralized Greek/action normalization and capability alias hardening for adversarial high-risk phrasing, Greek polite high-risk commands, Greek destructive mixed-intent classification, unsupported-capability truthfulness prompts, Greek model-inventory wording, and exploratory capability questions.
- Stage 2F-C5 strict timeout and diagnostic-expectation cleanup hardens deterministic handling for Greek voice/memory capability questions, unsupported reminder/file/email request surfaces, high-risk capability-question wording, and social/name diagnostic expectation alignment.
- Stage 2F-C5 follow-up strict timeout cleanup closes the three remaining strict broad-regression timeout edges: Greek "can you answer in Greek?" language-policy wording, unsupported create-folder requests, and unsupported write-file requests.
- Stage 2F-C5 keeps `notify me to stretch` as a current bounded action dry-run path and does not reclassify it as unsupported.
- Stage 2F-C5 keeps `απάντα ελληνικά` as a registry-backed language-policy capability answer (`apply_response_language_policy`), not proof of complete Greek language-state architecture.
- Greek support remains transitional and centered on normalization/alias/intent handling; final language-state architecture is not complete.
- Stage 2F-D-A introduces the first read-only structured probe foundation through the explicit scan/probe CLI.
- Stage 2F-D-A2 cleanup/hardening updates CI to Node 24-compatible official GitHub Actions majors (`actions/checkout@v5`, `actions/setup-python@v6`) and adds hygiene/readiness selftests without changing assistant-answer behavior.
- Stage 2F-D-B wires the existing read-only `model_truth` probe into bounded capability answers only for `query_model` surfaces (model-inventory/model-identity questions).
- Stage 2F-D-B keeps general capability discovery and normal assistant answers non-probe-backed.
- Stage 2F-D-B preserves the distinction between configured route targets and installed local model inventory; inventory can be unavailable when Ollama is missing, down, or times out.
- Stage 2F-D-B bounded model truth does not prove which model is currently answering, runtime health, model quality, or privileged/system capability.
- Stage 2F-D-C narrowly hardens bounded `model_truth` answer fallback wording and tests for unavailable-inventory, validation-failure, and exception paths without broadening probe-backed answer scope or adding new probes.
- Stage 2F-D-D adds bounded explicit context-capability answers for "what can you do here/on this system" surfaces using existing read-only probes only.
- Stage 2F-D-D keeps plain general capability discovery (`what can you do?`) and normal assistant answers not broadly dynamically probe-backed.
- Stage 2F-E-A separates capability question detection/classification behind a deterministic classifier boundary before capability answer generation.
- Stage 2F-E-A is a structural seam for future smarter linguistic handling and does not add semantic NLP, model-based classification, new probes, new actions, or broader probe-backed normal answers.
- Stage 2F-E-B records a transitional linguistic intent normalization contract behind the classifier boundary.
- In Stage 2F-E-B, deterministic aliases are transitional scaffolding, not the final smart linguistic layer.
- Stage 2F-E-B does not implement smart linguistic support, semantic classification, model-based classification, new probes, new actions, or broader probe-backed normal answers.
- Stage 2F-E-C adds a bounded explicit read-only maintenance/readiness report.
- Stage 2F-E-C uses existing read-only probes only.
- Stage 2F-E-C does not fix anything, does not install packages, does not write files, does not delete files, does not restart services, and does not authorize execution.
- Stage 2F-E-C does not inspect real package freshness, real logs, or real storage usage yet.
- Stage 2F-E-E is a validation/accounting cleanup and does not add maintenance automation.
- A bounded read-only maintenance probe foundation and non-executing maintenance planning contract now exist; privileged execution, repair/update/cleanup actions, service mutation, dashboards, automation, and broad normal-answer probe backing remain future work.
- Stage 2F-D-C keeps unavailable inventory explicit: missing/extra installed-model sets are unknown for that run, not zero.
- Probe-backed capability discovery in normal assistant answers is still not implemented.
- Bond is not yet a general-purpose desktop assistant.
- Bond should not be used for unattended automation, privileged/system changes, or safety-critical workflows.

## What works today

- deterministic routing
- intent classification
- parser contract preflight
- policy/action separation
- dry-run support
- confirmation-required flow for high-risk actions
- safe bounded action execution for current supported actions
- read-only capability answers grounded in the code-level capability registry
- portable path/config foundations
- memory/logging foundations
- selftest suite

## What does not work yet

- no dynamic probe-backed capability discovery yet in normal assistant answers; the registry-backed capability answer path remains read-only and does not authorize execution, Stage 2F-D-B/2F-D-C keep bounded `model_truth` detail only for `query_model` capability answers, and Stage 2F-D-D adds bounded explicit context-capability detail only for explicit context questions
- no privileged execution lane
- no service/app/applet layer
- no system maintenance advisor, monthly health report, or GUI maintenance dashboard yet
- no voice interface
- no document ingestion/RAG pipeline
- no plugin marketplace/system
- no public release package yet
- no cross-platform installer yet

## Safety model

- chat and actions are separated
- mixed intent is rejected
- risky actions require confirmation
- dry-run can preview supported actions
- parser failures fail closed

## Repository status and publication boundary

The current private development history is not intended to be published as-is. The project is being prepared for a clean public release.

See [docs/PUBLICATION_BOUNDARY.md](docs/PUBLICATION_BOUNDARY.md) and [docs/CLEANUP_PLAN.md](docs/CLEANUP_PLAN.md).

Public project governance files:

- [SECURITY.md](SECURITY.md)
- [CONTRIBUTING.md](CONTRIBUTING.md)
- [LICENSE](LICENSE)

## Documentation

- [ROADMAP.md](ROADMAP.md)
- [CHANGELOG.md](CHANGELOG.md)
- [docs/STATE.md](docs/STATE.md)
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- [docs/BEHAVIOR_CONTRACT.md](docs/BEHAVIOR_CONTRACT.md)
- [docs/CAPABILITIES.md](docs/CAPABILITIES.md)
- [docs/TESTING.md](docs/TESTING.md)
- [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)
- [docs/PUBLICATION_BOUNDARY.md](docs/PUBLICATION_BOUNDARY.md)
- [docs/CLEANUP_PLAN.md](docs/CLEANUP_PLAN.md)

## Development

Bond uses Python 3. Install requirements as needed for your environment, then run compile and selftest checks before commits. See [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) for the contributor workflow.

```bash
python3 -m compileall src/bond
python3 src/bond/ai_selftest.py
```
