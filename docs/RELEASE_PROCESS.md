# Release, Update, and Version Governance

Bond has no real releases yet and must not create decorative fake releases.

## Current status

Bond is still in a repository-first development phase. Packaging and operational contracts are improving, but release governance is not yet being exercised through meaningful tagged releases.

## Versioning rule

semantic versioning starts when meaningful release tags begin;

Until then, repository checkpoints, changelog entries, and validation evidence are the governance baseline.

## Development versus stable channels

Development and stable channels must be treated as distinct lanes once release discipline starts.

- Development channel: active iteration, transitional behavior, and explicit migration risk.
- Stable channel: release-tagged checkpoints with documented validation and rollback guidance.

No stable claim is valid without the required release evidence in this file.

## Version pinning and recording

Release records must pin or record versions for:

- core repository version/tag
- schema versions and migration set
- adapter/capability contract versions when applicable
- capability registry checkpoint
- model roster planning baseline

model roster in release notes records the planning baseline, not live runtime health.

## Pre-update validation

Before an update is accepted, validation evidence must be recorded for the target checkpoint.

Minimum expected evidence includes:

- changelog coverage for the update scope
- required validation command results for the repository phase
- schema/migration impact declaration
- rollback path declaration

## Migration checkpoint

A migration checkpoint is required when schemas, persisted stores, or compatibility readers change.

The checkpoint must include:

- source and target schema versions
- migration path reference
- validation result reference
- rollback snapshot reference
- compatibility-reader status

## Post-update validation

After update completion, post-update checks must confirm that:

- core commands still run as expected
- required validation commands still pass
- schema-dependent read/write paths behave correctly
- known degraded modes are explicitly reported, not hidden

## Rollback rule

Rollback must be possible for any meaningful update that changes persistent state, schema versions, or operational contracts.

Rollback documentation must state:

- what can be rolled back
- what data compatibility caveats exist
- what validation proves rollback success

## Gitea release rule

Gitea releases are used only for meaningful checkpoints;

A meaningful release requires evidence, not presentation. At minimum, releases require a changelog entry, known validation command results, schema/migration notes, model roster assumption, and rollback notes;

## Cross references

- [CHANGELOG.md](../CHANGELOG.md)
- [ROADMAP.md](../ROADMAP.md)
- [docs/INSTALLATION.md](INSTALLATION.md)
- [docs/SURVIVABILITY.md](SURVIVABILITY.md)
- [docs/SCHEMAS.md](SCHEMAS.md)
- [docs/STATE.md](STATE.md)
- [docs/TESTING.md](TESTING.md)
