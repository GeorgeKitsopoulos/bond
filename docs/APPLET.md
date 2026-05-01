# Cinnamon Applet Integration

Applet integration is future/planned and must not outrun core behavior.

## Scope

The applet scope is:

- status display
- short text submission
- recent response/result display
- safe quick actions
- notifications and errors
- monthly maintenance report display
- update-plan summary display
- storage hygiene warnings
- boot/service health warnings
- explicit user request handoff for approved follow-up actions

## Non-scope

The applet does not duplicate core assistant internals.

The applet must not independently apply updates, delete files, empty Trash, restart services, or make package-manager changes. It only displays core-generated maintenance facts and submits explicit user requests back to the core.

It must not contain a duplicate:

- parser
- policy layer
- memory system
- capability registry
- execution engine

## Transport

Transport order:

1. CLI first for simple mode
2. service Unix socket later if daemon mode exists

## Applet states

Required state vocabulary:

- idle
- processing
- success
- action completed
- blocked/rejected
- degraded/offline
- report available
- report degraded
- action requires confirmation
- privileged lane unavailable

## Packaging and deployment notes

The applet is an integration layer, not core packaging.

## Data caching rule

Applet caching should keep only UI state or recent summaries.
It does not store independent assistant memory.

Maintenance report caching is display-only. The applet may cache the latest report summary, but the core remains the source of truth for probes, policy, recommendations, and action state.

## Current implementation status

Applet integration is planned and not yet complete.

## Cross references

- `docs/ARCHITECTURE.md`
- `docs/SERVICE.md`
- `docs/PACKAGING_STRATEGY.md`
- `docs/RELEASE_PROCESS.md`
