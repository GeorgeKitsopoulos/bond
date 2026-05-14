# Probe Layer Specification

## Purpose

This document is the canonical probe-layer specification for deterministic system truth in Bond.

Probes gather real local facts. They do not perform model reasoning.
Probe truth feeds capability truth and live-truth answers.

## Implemented foundation: Stage 2F-D-A

Stage 2F-D-A implements the first read-only, rootless probe foundation.

Current implemented probe names:

- `host_baseline`
- `host_portability_profile`
- `storage_portability_profile`
- `install_manifest_drift`
- `session_baseline`
- `tool_inventory`
- `router_config_models`
- `ollama_model_inventory`
- `model_truth`
- `package_update_status`
- `storage_hygiene`
- `boot_service_health`

## Stage 2G-A host portability profile

- `host_portability_profile` is a read-only portability profile probe for future installer/updater/satellite planning.
- It consumes only OS release content, platform metadata, safe tool-path checks (`shutil.which`-style), and optional readable DMI/sysfs strings.
- It detects distro-family, package-manager/tool availability, atomic/image-based signals, Bazzite/SteamOS/Steam Deck-like signals, service backend hints, and a bounded dependency strategy.
- It does not run package-manager commands.
- It does not authorize package installation.
- It does not authorize host mutation.
- It is not part of the maintenance report contract.
- Maintenance report scope remains limited to `package_update_status`, `storage_hygiene`, and `boot_service_health`.

### Stage 2G-B storage portability profile

- `storage_portability_profile` is a read-only storage portability profile probe for future installer/updater/satellite planning.
- It consumes only `/proc/mounts`, platform metadata, `BOND_*` environment path observations, and safe disk-usage calls.
- It detects mount candidates, external media paths, Steam Deck SD-card-like paths, home fallback signals, free-space pressure, and bounded placement recommendations for Bond roles.
- It is not part of the maintenance report contract.
- `storage_hygiene` remains separate.
- Maintenance report scope remains limited to `package_update_status`, `storage_hygiene`, and `boot_service_health`.
- It does not create directories, move data, delete data, clean caches, mount, unmount, format, partition, or authorize storage mutation.
- It does not broaden normal assistant answers.

### Stage 2G-C install manifest drift detection

- `install_manifest_drift` is a read-only install manifest drift probe for future installer/updater/satellite planning.
- It can build a current in-memory manifest from the existing read-only host/storage portability profiles and compare it against a supplied manifest contract.
- Because manifest persistence is not implemented in this stage, the default probe output reports missing saved manifest and requires manual review with `recommended_next_step_kind=create_manifest_review`.
- It does not write manifests.
- It does not load manifests from disk.
- It does not perform reconfiguration.
- It does not authorize execution.
- It is not part of the maintenance report contract.
- Maintenance report scope remains limited to `package_update_status`, `storage_hygiene`, and `boot_service_health`.

## Stage 2F-F-A read-only maintenance probe foundation

- `package_update_status` inspects local apt upgradable-package cache only.
- `package_update_status` does not refresh package metadata and cannot prove cache freshness.
- `storage_hygiene` reports bounded disk-usage records only.
- `storage_hygiene` does not delete, clean caches, scan duplicates, or traverse large trees.
- `boot_service_health` reports bounded failed-unit and recent boot-warning signals only.
- `boot_service_health` does not restart, start, stop, enable, disable, mask, or repair services.
- The probes are rootless and read-only.
- These probe facts are not yet wired into normal assistant answers.
- These probe facts do not authorize actions.

## Stage 2F-F-B report integration

- The explicit maintenance/readiness report consumes `package_update_status`, `storage_hygiene`, and `boot_service_health`.
- This is report integration only.
- The probes remain read-only/rootless.
- The report does not authorize action.
- General capability answers are not broadly backed by these maintenance probes.
- Planning, privileged execution, repair/update/cleanup actions, service mutation, dashboards, and automation remain future work.

## Stage 2F-F-D maintenance report contract boundary

- `ai_maintenance_report.py` is the single owner of maintenance/readiness report assembly and formatting.
- Stage 2F-F-D is not a new probe layer.
- The report contract consumes only `package_update_status`, `storage_hygiene`, and `boot_service_health`.
- Context probes remain separate and are not pulled into this contract.
- The structured report dict carries `action_authorized=False` and `execution_supported=False`.
- The formatted report includes sections for all probe signals and all contract boundaries.
- Source purity is enforced: the module source must not contain shell execution or forbidden privileged-command substrings.
- `ai_capability_answer.py` delegates entirely to this module; it no longer assembles the report inline.

## Stage 2F-F-E maintenance report readiness metadata

- The explicit maintenance/readiness report now carries metadata-only readiness fields.
- The metadata is derived from existing probe validation and the existing non-executing maintenance plan.
- This is not a new probe layer.
- The maintenance probe list remains limited to `package_update_status`, `storage_hygiene`, and `boot_service_health`.
- The metadata does not schedule reports, start background jobs, create dashboards, authorize actions, mutate services, or add privileged execution.

## Stage 2F-F-C non-executing planning contract

- The explicit maintenance/readiness report includes a non-executing maintenance planning summary.
- The planning summary consumes existing read-only probe facts only.
- The planning summary classifies observed signals into bounded statuses such as no immediate signal, manual review, future privileged lane required, and unavailable.
- The planning summary does not recommend shell commands.
- The planning summary does not authorize action.
- Probes remain read-only/rootless.
- Privileged execution, repair/update/cleanup actions, service mutation, dashboards, automation, and broad normal-answer probe backing remain future work.

Current implementation boundaries:

- probes are read-only and rootless
- `model_truth` explicitly separates configured route targets from installed local model inventory
- installed inventory is not proof of runtime health or route reachability
- probe results are not yet used to authorize actions
- probe results are not broadly used in normal assistant capability answers

## Stage 2F-D-B bounded answer integration

Stage 2F-D-B wires existing read-only `model_truth` probe output into bounded `query_model` capability answers only.

Boundaries for this step:

- integration scope is model-inventory/model-identity capability-answer surfaces only
- general `what can you do` capability discovery is not dynamically probe-backed
- normal assistant answers are not broadly dynamically probe-backed
- configured route targets remain separate from installed local model inventory
- installed local model inventory may be unavailable in a run when Ollama is missing, down, or times out
- this bounded answer detail does not prove which model is currently answering, runtime health, model quality, or privileged/system capability

## Stage 2F-D-C bounded fallback hardening

Stage 2F-D-C narrows and hardens fallback wording in bounded `model_truth` capability answers only.

Boundaries for this step:

- no new probes are added
- no probe categories are broadened
- general `what can you do` capability discovery remains not dynamically probe-backed
- normal assistant answers remain not broadly dynamically probe-backed
- unavailable installed inventory means missing/extra installed-model sets are unknown for that run, not zero
- validation-failure and probe-exception paths use the same bounded unavailable fallback envelope
- this hardening does not prove currently answering model identity, runtime health, model quality, or privileged/system capability

## Stage 2F-D-D bounded context capability answers

Stage 2F-D-D adds bounded explicit context-capability answers for explicit context question surfaces.

Boundaries for this step:

- existing probes are used only for explicit context-capability questions
- no new probes were added
- raw probe dumps are not exposed to users
- tool paths and local paths are not exposed in context answers
- this does not authorize execution
- general `what can you do?` remains registry summary only
- normal assistant answers remain not broadly dynamically probe-backed

## Stage 2F-E-C read-only maintenance/readiness report

Stage 2F-E-C adds a bounded explicit read-only maintenance/readiness report.

Boundaries for this step:

- no new probes are added
- the report uses existing read-only probes only
- it summarizes readiness boundaries from `host_baseline`, `session_baseline`, `tool_inventory`, and `model_truth`
- it does not inspect real package freshness
- it does not inspect real logs
- it does not inspect real storage usage
- it does not expose raw probe payloads, raw local paths, executable paths, or exception text
- it does not authorize execution

## Core principles

- deterministic probes, not LLM guessing
- rootless-first by default
- no raw shell use without a wrapper or typed probe interface
- probe failure must never be turned into fabricated truth
- probing and interpretation are separate stages
- the assistant reasons from derived assistant-usable facts, not from raw scan dumps

## Probe hierarchy

Bond uses a three-layer fact hierarchy.

### Layer 0 — authoritative OS facts

What belongs here:

- host identity, OS release, kernel, architecture, session type, desktop environment
- baseline path facts such as XDG directories and executable path resolution
- portal and session-bus presence facts as raw inspectable state

Refresh expectations:

- low-churn refresh class; collect at startup and re-probe on explicit invalidation or environment change events

Authority level:

- highest authority for machine/environment baseline truth

Model consumption rules:

- the model may not consume raw Layer 0 dumps directly
- Layer 0 facts must be normalized into Layer 2 assistant-usable facts first

### Layer 1 — user-environment facts

What belongs here:

- default app/handler resolution state
- app inventory and package-surface visibility
- clipboard, notification, and desktop interaction availability
- user-session capability surfaces (portals, D-Bus, session integrations)

Refresh expectations:

- medium-churn refresh class; periodic refresh and on-demand re-probe for action planning

Authority level:

- authoritative for user/session environment, but lower than Layer 0 for host identity baseline

Model consumption rules:

- the model may not consume raw Layer 1 dumps directly
- Layer 1 facts must be interpreted into Layer 2 statements before policy/model reasoning

### Layer 2 — derived assistant-usable facts

What belongs here:

- interpreted capability-relevant facts derived from Layer 0/1
- explicit assistant-usable truths such as safe-open availability, guarded-action constraints, and runtime reachability state

Refresh expectations:

- derived on refresh of Layer 0/1 inputs and recomputed when source facts change

Authority level:

- authoritative model-facing operational truth, traceable to Layer 0/1 evidence

Model consumption rules:

- the model reasons from Layer 2 only
- Layer 2 derivations must preserve provenance links back to source probe records

## Probe domains

Canonical probe domains include:

- host identity / OS / kernel / architecture
- session / desktop / GUI state
- XDG user dirs and path truth
- default app and handler resolution
- app inventory / package surfaces
- package update and package-manager state
- portals / D-Bus / user-session capability surfaces
- clipboard / notification / desktop interaction availability
- model and runtime truth
- storage hygiene state: Trash size, cache size, large-file candidates, duplicate-file candidates
- boot and service health: failed units, boot timing, `systemd-analyze blame`, journal warning summaries
- report-readiness state for periodic maintenance reports
- knowledge corpus / ingestion status only as probeable state, not as inferred knowledge
- health and diagnostic probes (planned): startup integrity checks, degraded-mode detection, and subsystem health summaries
- locale probes (planned): host locale, user dirs locale, UI/session locale where available, and keyboard/input locale when safely probeable
- conversation-language signals (planned): explicit distinction between locale fact and active conversation language

## Evidence ranking for app/backend resolution

Default app or backend resolution must rank evidence in this order:

1. explicit default handler
2. desktop/session API fact
3. desktop entry match
4. installed binary presence
5. heuristic fallback

"binary exists" is not equivalent to "this is the default app".
Guesses must be labeled as guesses.
Heuristics are last-resort only.

## Model/runtime truth separation

Probe documentation and probe outputs must distinguish three different truths:

- configured route targets from `config/router/profiles.json`
- installed local model inventory
- runtime availability / reachability / health of those models

Configured route targets are not proof that a model is installed.
Installed local model inventory is not proof that routing actually uses that model correctly.
Runtime availability is a separate fact from both configuration and inventory.
Documentation must not hardcode a roster unless the roster is sourced from a live probe or an explicitly maintained canonical state record.
The current documented baseline roster is qwen2.5:3b-instruct, gemma2:2b, qwen2.5:7b-instruct, and nomic-embed-text:latest; this baseline must not be confused with instantaneous runtime health, but it is the canonical planning baseline until intentionally changed.

## Probe output schema

Canonical structured probe result schema:

```text
ok:                  boolean
probe_name:          stable probe identifier
source_type:         "os_api" | "desktop_api" | "wrapped_command" | "config" | "runtime_probe"
certainty_class:     "authoritative" | "derived" | "heuristic" | "unknown"
collected_at:        ISO 8601 timestamp
data:                structured probe payload
warnings:            list of non-fatal warnings
error:               structured error object or null
refresh_class:       "low_churn" | "medium_churn" | "high_churn"
supports_live_truth: boolean
notes:               free-form probe notes
```

## Refresh policy

- low-churn facts: host baseline and near-static OS/session facts; re-probe on startup and explicit invalidation
- medium-churn facts: defaults, app surfaces, and session capabilities; re-probe periodically and before capability-critical actions
- high-churn facts: runtime reachability and volatile session state; re-probe at answer/action time when live-truth confidence is required

Re-probe is required whenever cached fact age exceeds its refresh class threshold or when an action depends on a volatile precondition.

## Safety and execution boundaries

Probes are inspectors, not arbitrary execution backdoors.
Probes may call deterministic tools/APIs but must remain bounded.
Side effects must be avoided unless a probe is explicitly documented as interactive or exceptional.

## Maintenance probe boundaries

Maintenance probes are inspectors.

They may collect package, storage, boot, service, and report-readiness facts, but they must not:

- apply updates
- remove packages
- empty Trash
- delete duplicate candidates
- restart, enable, disable, mask, or edit services
- treat journal or boot warnings as proof of root cause without evidence

Maintenance probe outputs must separate:

- observed fact
- confidence level
- source command or API
- user-impact summary
- recommended next action
- whether the next action requires confirmation
- whether the next action requires the future privileged lane

Package update probes must distinguish:

- stale metadata
- available updates
- security-relevant updates when safely knowable
- held or broken packages
- unavailable package surfaces
- permission-limited results

Duplicate-file probes must report candidates, not deletion decisions.

## Cross references

- [docs/ARCHITECTURE.md](ARCHITECTURE.md)
- [docs/CAPABILITIES.md](CAPABILITIES.md)
- [docs/STATE.md](STATE.md)
- [docs/TESTING.md](TESTING.md)
- [docs/CURRENT_PATHS.md](CURRENT_PATHS.md)
