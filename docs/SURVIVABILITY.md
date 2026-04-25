# System Integrity and Survivability

This document defines Bond's operational resilience requirements. It is not a feature wishlist. It exists to prevent memory corruption, update breakage, schema drift, resource runaway, secret leakage, and silent degradation.

## Current diagnosis

Bond is architecturally improving but operationally fragile. Current docs and code acknowledge memory, probes, packaging, and runtime separation, but the repository does not yet define a full survivability model.

## Core rule

Bond must be able to evolve, fail, recover, and explain degraded state without silently corrupting memory, configuration, runtime state, or user trust.

## Required layers

### 1. Schema versioning and migration
- Define a global schema registry.
- Track per-store schema versions for facts, corrections, logs, documents, chunks, vectors, config, and runtime state.
- Require migration checkpoints before update completion.
- Preserve compatibility readers for old data where reasonable.
- Never allow old data to fail silently inside retrieval or policy.

### 2. Snapshot, rollback, and safe mode
- Create versioned snapshots for state, memory, config, and indexes before risky updates or migrations.
- Use atomic write discipline for mutable state.
- Maintain a rollback index.
- Define a safe mode that can start without optional adapters, stale indexes, or risky plugins.
- Support partial recovery where possible: memory-only, config-only, index-only, or runtime-state-only.

### 3. Update and release governance
- Use semantic versioning for core once release discipline begins.
- Distinguish development state from stable release state.
- Pin or record versions for core, schemas, adapters, capability registry, and model roster assumptions.
- Require pre-update validation and post-update validation.
- Make updates migration-aware and rollback-aware.

### 4. Resource governance and execution budgeting
- Enforce task timeouts.
- Define CPU/RAM/concurrency budgets per task class.
- Keep model escalation bounded by current local roster reality.
- Support cancellation for long or runaway work.
- Prefer decomposition, retrieval, validation, and narrower contracts over assuming a larger local model.

### 5. Secrets and credential handling
- Keep secrets separate from config, memory, logs, and docs.
- Do not log secrets.
- Inject credentials only at runtime when a capability requires them.
- Scope credentials by adapter/capability.
- Treat external-service credentials as privileged data even when stored locally.

### 6. Health and diagnostics
- Define a health status surface for core, memory, probes, models, ingestion, adapters, and runtime state.
- Classify degraded modes explicitly.
- Expose debug traces for failures without exposing hidden chain-of-thought or secrets.
- Make startup checks detect corrupt or stale state before normal operation.

## Priority order

1. Schema versioning
2. Snapshot and rollback
3. Resource governance
4. Secrets handling
5. Release/update governance
6. Health monitoring

## Current implementation status

These requirements are mostly planned. Existing archive/rotation and logging pieces are useful but do not yet equal a full survivability system.

## Cross references

- `docs/SCHEMAS.md`
- `docs/RELEASE_PROCESS.md`
- `docs/MEMORY.md`
- `docs/KNOWLEDGE_INGESTION.md`
- `docs/PROBES.md`
- `docs/INSTALLATION.md`
- `docs/TESTING.md`
- `docs/STATE.md`
