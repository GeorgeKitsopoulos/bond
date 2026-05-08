# Bond

Bond is a local-first assistant project for Linux systems. It is currently focused on safe request routing, policy gating, dry-run behavior, confirmation before risky actions, and portable runtime paths.

## Current status

- Bond is under active development.
- The current validated baseline is Stage 2E plus P0 cleanup work.
- Current documented validation baseline: compile passes and integrated selftest currently reports 169/169 after Stage 2F-D-A probe foundation validation (see docs/TESTING.md for exact summary).
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

- no dynamic probe-backed capability discovery yet in normal assistant answers; the registry-backed capability answer path remains read-only and does not authorize execution, and the new probe foundation is exposed only through the explicit scan/probe CLI
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
