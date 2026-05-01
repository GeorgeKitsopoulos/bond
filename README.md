# Bond

Bond is a local-first assistant project for Linux systems. It is currently focused on safe request routing, policy gating, dry-run behavior, confirmation before risky actions, and portable runtime paths.

## Current status

- Bond is under active development.
- The current validated baseline is Stage 2E plus P0 cleanup work.
- Current documented validation baseline: compile passes and integrated selftest passes 61/61.
- Stage 2F has resumed with the code-level capability registry foundation; public-release hardening remains ongoing.
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
- code-level capability registry foundation
- portable path/config foundations
- memory/logging foundations
- selftest suite

## What does not work yet

- no dynamic probe-backed capability discovery yet; the code-level registry foundation is present but not yet wired into normal assistant answers or execution decisions
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
