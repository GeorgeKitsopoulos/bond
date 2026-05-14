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

## Host portability profiling prerequisite (Stage 2G-A)

Future installer/updater work must start with read-only host profiling.

In Stage 2G-A, host profiling can classify Debian/Mint/Ubuntu-like, Fedora/Bazzite/Fedora Atomic-like, SteamOS/Arch-like, openSUSE-like, Alpine-like, Void-like, Nix-like, macOS-like, and unknown systems from safe signals.

Bazzite/Steam Deck/SteamOS-like systems must default to rootless/user-space/container-first planning and avoid blind host mutation.

This is not a working installer, updater, package installer, or satellite runtime.

Any future install/update flow must remain:

detect -> plan -> show -> explicitly authorize -> execute -> verify -> report

Execution is not added in this stage.

## Storage portability profiling prerequisite (Stage 2G-B)

Future installer/updater work must understand storage before creating directories, placing models, moving telemetry, or writing manifests.

Stage 2G-B can classify internal/home fallback, external media paths, Steam Deck SD-card-like paths, free-space pressure, and Bond role placement recommendations from safe signals.

Bazzite, Steam Deck, and SteamOS-like systems should prefer SD-card or external-storage recommendations for large Bond data, models, telemetry, logs, backups, and RAG/index data when detected, but must not hardcode a Deck path.

This is not a working installer, updater, cleanup tool, data mover, mount manager, or satellite runtime.

Any future storage-affecting flow must remain:

detect -> plan -> show -> explicitly authorize -> execute -> verify -> report

Execution is not added in this stage.

## Install manifest and drift detection prerequisite (Stage 2G-C)

Future installer/updater work must compare intended Bond placement facts against current read-only host/storage portability facts before any reconfiguration path exists.

Stage 2G-C adds a read-only, in-memory install manifest and drift detection contract.

It can build a bounded manifest from explicit inputs and existing read-only portability profiles, and it can compare a previous manifest dictionary to a current manifest dictionary for drift review.

This stage does not persist manifests, load manifests from disk, perform reconfiguration, install packages, update services, or mutate storage.

Any future manifest/reconfiguration flow must remain:

detect -> compare -> show -> explicitly authorize -> execute -> verify -> report

Execution is not added in this stage.

## Package-manager classification and dependency planning prerequisite (Stage 2G-D)

Future installer/updater work must classify package managers and plan dependencies before any package installation execution path exists.

Stage 2G-D adds deterministic, read-only package-manager classification and dependency planning contracts without authorizing installation or execution.

It can classify package managers into strategy categories (mutable, immutable user-space-preferred, unknown) based on host facts and distro signals.

It can map core and optional capabilities (Python runtime, git, build tools, containers, local LLM) to package-manager-specific package names.

It can classify capability status as: already observed, needs planning, requires manual review, or optional and not needed.

This stage does not call package managers, authorize installation, execute commands, install packages, or mutate hosts.

All authorization fields (execution_authorized, install_authorized, etc.) remain explicitly False.

Any future installer/dependency flow must remain:

classify -> plan -> show -> explicitly authorize -> execute -> verify -> report

Package manager execution is not added in this stage.

## Installer planning prerequisite (Stage 2G-E)

Future installer/updater work must compose bounded plans from Stage 2G read-only facts before any interactive or execution work begins.

Stage 2G-E adds a deterministic, read-only installer planning contract that composes host profiles, storage profiles, install manifest drift, and dependency plans into bounded installer plans without authorizing execution.

It can compose read-only Stage 2G facts into a plan structure with discrete steps (collect_host_profile, collect_storage_profile, review_install_manifest_drift, review_dependency_plan, review_storage_locations, review_service_strategy, final_human_approval).

It can classify plan readiness as: ready_for_human_review, manual_review_required, blocked_missing_inputs, or unsupported_manual_review.

It can recommend deterministic next steps: review_installer_plan, manual_installer_review, collect_missing_profile_facts, or manual_platform_review.

It omits sensitive fields (hostname, username, email, token, password, secret, api_key, machine_id) from plan output to prevent credential leakage.

This stage does not call package managers, perform reconfigurations, update services, write manifests, move storage, authorize execution, execute commands, or mutate hosts in any way.

All authorization fields (execution_authorized, install_authorized, reconfigure_authorized, service_authorized, write_plan_authorized, write_manifest_authorized, etc.) remain explicitly False.

The formatted plan output includes an explicit disclaimer: "No install, update, reconfigure, service, storage, or manifest write action was performed."

Any future installer/dependency flow must remain:

classify -> plan -> show -> explicitly authorize -> execute -> verify -> report

Installation, reconfiguration, and storage execution are not added in this stage.

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
