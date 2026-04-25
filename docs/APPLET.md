# Cinnamon Applet Integration

Applet integration is future/planned and must not outrun core behavior.

## Scope

The applet scope is:

- status display
- short text submission
- recent response/result display
- safe quick actions
- notifications and errors

## Non-scope

The applet does not duplicate core assistant internals.

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

## Packaging and deployment notes

The applet is an integration layer, not core packaging.

## Data caching rule

Applet caching should keep only UI state or recent summaries.
It does not store independent assistant memory.

## Current implementation status

Applet integration is planned and not yet complete.

## Cross references

- `docs/ARCHITECTURE.md`
- `docs/SERVICE.md`
- `docs/PACKAGING_STRATEGY.md`
- `docs/RELEASE_PROCESS.md`
