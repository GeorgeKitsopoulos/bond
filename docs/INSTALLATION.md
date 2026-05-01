# Installation, Update, and Uninstall

This document defines the current installation-state reality and the intended near-term operational lifecycle for Bond.

It is not a claim that Bond already has a finished packaging system.
It is a controlled description of how the project should be treated during the current repository-first phase.

## Core rule

Bond must not be treated as a loose pile of copied scripts.

The project direction is:

- repository as source of truth
- controlled local setup
- explicit update path
- explicit uninstall path
- no silent sprawl across the system

## Current reality

Bond is currently in a transitional state.

That means:

- the repository exists as the canonical source tree
- legacy runtime paths may still exist from earlier phases
- packaging is not yet mature
- install/update/uninstall behavior is not yet fully productized

So this document describes:

- what is true now
- what must be done in the near term
- what is deliberately not being overclaimed yet

## Repository-first operating model

During the current phase, Bond should be operated under this model:

1. the repository contains the maintained source of truth
2. runtime behavior should increasingly be derived from the repository structure
3. local installation should be controlled and deliberate
4. updates should come from repository changes, not manual drift
5. uninstall should be explicit rather than accidental neglect of old files

## Current installation assumptions

At present, the project may still involve a mixed state that includes:

- repository files under the repo root
- earlier runtime paths from transitional local layouts
- wrappers or aliases that still reflect older structure

This mixed state must be treated as migration debt, not finished architecture.

## Installation direction

The near-term installation direction is:

- install from the repository
- avoid copy-paste duplication
- move toward explicit entry points
- define runtime layout deliberately
- separate source from runtime/state concerns

Installation must eventually answer these questions clearly:

- where source code lives
- where configuration lives
- where runtime state lives
- where memory data lives
- where logs live
- how entry commands are exposed

## Install modes

Bond should be described through explicit install modes:

- developer editable install
- local user install through pipx or equivalent isolated environment
- future packaged install

Python packaging defines the application, while OS installers and adapters distribute that application on specific platforms.

See `docs/PACKAGING_STRATEGY.md` for layered packaging direction and `docs/RELEASE_PROCESS.md` for release/update governance.

## Stage 1 and Stage 2 packaging direction

Stage 1 direction:

- Python core first as canonical app definition
- local controlled install through `pipx` or equivalent isolation
- explicit entry point replacing ad hoc wrapper dependence
- role-based runtime path normalization

Stage 2 direction:

- keep Python core unchanged
- add platform adapters for Linux/Windows where useful
- treat Android as an optional separate product layer

Explicit Stage 1 rejections:

- Flatpak is not a core Stage 1 solution
- AppImage is not a core Stage 1 solution
- binary freezing is not a core Stage 1 solution

## Update direction

Updates must be repository-driven.

This section describes updating Bond itself. It is separate from future OS/package update advisory features.

That means updates should eventually follow a controlled path such as:

1. pull or otherwise receive repository changes
2. validate the repository state
3. apply the updated code/configuration in a controlled way
4. preserve or migrate runtime/state data intentionally
5. verify that the updated system still passes validation

Updates must not rely on:

- scattered manual edits
- undocumented local mutations
- hidden runtime drift

Update implications that must be explicit:

- preserve memory data by default unless a user requests destructive cleanup
- remove or refresh service entries where enabled
- clean obsolete wrappers and aliases that point to transitional paths
- validate after update using project checks

Update governance note:

- pre-update validation is required before applying meaningful updates
- migration checkpoints are required when schema or persisted-store contracts change
- rollback preservation must be defined before destructive or schema-affecting updates
- release/update governance requirements are defined in `docs/RELEASE_PROCESS.md`
- schema/version governance requirements are defined in `docs/SCHEMAS.md`
- survivability and recovery requirements are defined in `docs/SURVIVABILITY.md`

## Future OS/package update advisor boundary

Bond may later inspect and plan operating-system package updates as a user-facing maintenance capability. That future capability must not be confused with Bond's own repository update process.

Future OS/package update handling must follow this order:

1. read-only package/update inspection
2. dry-run or simulated update plan where supported
3. user-facing explanation of risk, privilege, reboot likelihood, and validation steps
4. explicit confirmation
5. privileged execution only through the future privileged lane
6. post-update validation and report
7. rollback/snapshot reference where applicable

Bond must not silently run `apt upgrade`, `snap refresh`, `flatpak update`, package removal, service restart, or cleanup commands from a scheduled report or GUI surface.

## Uninstall direction

Uninstall must eventually become explicit.

That means uninstall should define:

- what source/install locations are removed
- what runtime/state locations are removed
- what memory/archive locations are preserved or removed
- what wrappers, aliases, or service entries are removed
- what remains intentionally as user data, if anything

Uninstall implications must include removal of service entries (if enabled) and cleanup of obsolete wrappers/aliases while keeping default memory-preservation behavior explicit.

Uninstall must not mean:

- “delete random directories and hope”
- forgetting old runtime leftovers
- leaving undocumented system residue

## Transitional discipline

Until packaging is mature, the project should follow this discipline:

- keep repository and runtime roles distinct
- document transitional paths honestly
- avoid pretending a finished installer already exists
- avoid multiplying legacy deployment methods

## What this document does not claim yet

This document does not claim that Bond already has:

- a polished installer
- distribution-grade packaging
- finished service integration
- final runtime layout
- final entry-point exposure
- complete uninstall automation

Those are future implementation targets.

## Near-term documentation requirements

The repository must progressively define:

- installation prerequisites
- local setup steps
- validation steps after setup
- update procedure
- uninstall procedure
- migration notes from earlier runtime layouts

## Packaging relationship

Packaging work must eventually align with:

- `pyproject.toml`
- entry-point design
- path resolution design
- runtime layout decisions
- deployment documentation
- `docs/PACKAGING_STRATEGY.md`
- `docs/RELEASE_PROCESS.md`

But packaging must not outrun architectural clarity.

## Validation expectation

Any installation or update procedure must eventually require validation such as:

- environment check
- command availability check
- selftest or smoke validation
- confirmation that runtime paths resolve correctly

A setup that “runs once” but is not validated is not considered trustworthy.

## Documentation relationship

This file must stay aligned with:

- `README.md`
- `ROADMAP.md`
- `docs/STATE.md`
- `docs/CURRENT_PATHS.md`
- `docs/ARCHITECTURE.md`

If installation/update/uninstall reality changes materially, this file must be updated.

## Summary

Bond is not yet fully packaged.

But it must already be treated as a repository-first system with:

- deliberate installation thinking
- deliberate update discipline
- deliberate uninstall discipline
- reduced tolerance for script sprawl and path drift

This document defines that operational baseline.
