# Schema and Data Contract Registry

This file is the canonical index for data contracts and schema evolution.

## Core rule

Data contracts must be explicit, versioned, and reviewable so Bond can evolve without corrupting memory, policy decisions, retrieval behavior, or operational trust.

## Current status

Schema discipline is improving, but a complete versioned registry is not yet fully implemented across all stores. This file defines the canonical registry requirement and the minimum contract expected for forward work.

## Global schema registry requirement

Bond must maintain a single canonical schema registry that tracks store-level and object-level schema versions, migration paths, validation coverage, and compatibility-reader status.

The registry must make it possible to answer, for every active store and object contract:
- what schema version is current,
- what changed between versions,
- which migration path is valid,
- which compatibility reader exists,
- and which validation command proves the contract.

## Stores that require schema versions

- durable facts
- correction records
- episodic logs
- reflection records
- document manifests
- parsed document chunks
- embedding/vector indexes
- assistant config
- router profiles
- capability registry
- probe cache/state
- telemetry records

## Canonical object schemas

Do not duplicate full object fields here; use this file as the canonical index and route authoritative details to subsystem docs:

- [docs/ARCHITECTURE.md](ARCHITECTURE.md): parse result schema, policy decision schema, execution result schema, and capability registry concepts.
- [docs/MEMORY.md](MEMORY.md): durable fact, correction, episodic, archive, and reflection schemas.
- [docs/KNOWLEDGE_INGESTION.md](KNOWLEDGE_INGESTION.md): document manifest, chunk, extraction, provenance, and ingestion status schemas.
- [docs/PROBES.md](PROBES.md): probe output schema.

## ParseContract schema

Implemented in `src/bond/ai_parse_contract.py`.

Purpose: record what Bond understood before policy or execution. The parser contract is not permission and does not execute anything. It only says whether an input was parsed into a supported action shape.

Fields:

- `status`: one of `chat_or_question`, `mixed`, `unknown`, `parsed_action`, `parsed_action_chain`, `unparsed_action`, `partial_action_chain`
- `executable`: boolean; true only when the request parsed into a supported executable action shape
- `ambiguous`: boolean; true when the request should not be guessed into execution
- `reason`: stable reason string explaining the parse result
- `raw_text`: request text passed into the parse-contract layer
- `normalized_text`: normalized action text used for parsing
- `gatekeeper_result`: intent classifier result from `ai_intent.py`
- `chain_steps`: normalized action-chain steps when detected
- `parsed_intents`: parser outputs from `ai_action_parse.py`
- `unparsed_steps`: action-looking steps that did not parse
- `metadata`: bounded diagnostic metadata

Layer boundary:

- Parser contract says what was understood.
- Policy decides whether the understood request is allowed.
- Action contract decides dry-run, confirmation, rejection, or execution mode.
- Executor performs only bounded supported actions.
- A parsed action is not permission.
- An unparsed action must fail closed before executor.

## Minimal schema registry entry block

```yaml
store_name: stable store identifier
schema_name: stable schema identifier
schema_version: semver-like schema version
introduced_in: Bond version or repository checkpoint
current: true/false
migration_from: list of older versions
migration_to: list of newer versions
compatibility_reader: module or function name when implemented
validation_command: command or test id
notes: free-form notes
```

## Migration rules

migrations are explicit, logged, validated, snapshot-backed, and never silently destructive.

Each migration path must:
- declare source and target schema versions,
- include a deterministic validation step,
- record migration results in logs or change records,
- support rollback via snapshot when validation fails,
- and block completion when required checks fail.

## Compatibility rules

Compatibility readers are required when old data may remain in active environments during staged upgrades.

Compatibility behavior must:
- be explicitly scoped by schema version,
- fail closed on unknown or malformed versions,
- avoid silently rewriting data during read paths,
- and be removable only after migration coverage and validation prove old versions are no longer required.

## Cross references

- [docs/SURVIVABILITY.md](SURVIVABILITY.md)
- [docs/ARCHITECTURE.md](ARCHITECTURE.md)
- [docs/MEMORY.md](MEMORY.md)
- [docs/KNOWLEDGE_INGESTION.md](KNOWLEDGE_INGESTION.md)
- [docs/PROBES.md](PROBES.md)
- [docs/TESTING.md](TESTING.md)
- [docs/STATE.md](STATE.md)
