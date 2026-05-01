# Service Mode

Service mode is optional and future/planned.

## Purpose

Service mode exists to support:

- warm state for repeated requests
- faster repeated interaction
- applet integration
- shared session cache
- background ingestion when explicitly enabled

## IPC boundary

Preferred IPC boundary order:

1. local Unix socket first
2. localhost HTTP only if necessary
3. D-Bus only with a strong desktop integration reason

## Responsibilities

Service mode should:

- accept structured requests
- return structured responses
- expose health
- expose telemetry
- hold session cache
- provide last response summary for applet surfaces
- run explicitly enabled scheduled read-only maintenance checks
- produce structured monthly health report payloads
- expose latest maintenance report summary for applet/dashboard display

## Non-responsibilities

Service mode does not duplicate core logic and does not bypass control boundaries.

It must not:

- duplicate parsing, policy, memory, or capability logic outside core
- bypass policy gates
- imply privileged actions by daemon existence alone
- perform unattended privileged system updates
- delete files or empty Trash automatically
- restart or modify services automatically
- let scheduled tasks bypass parser, policy, capability, or confirmation contracts

## Runtime documentation to define later

Future implementation docs should define:

- socket path
- start/stop/status controls
- failure modes
- runtime files
- safe mode behavior
- maintenance report schedule configuration
- report artifact location
- report retention policy
- degraded report behavior when probes fail

## Current implementation status

Service mode is planned and not yet complete.

## Cross references

- `docs/ARCHITECTURE.md`
- `docs/PACKAGING_STRATEGY.md`
- `docs/APPLET.md`
- `docs/RELEASE_PROCESS.md`
- `docs/SURVIVABILITY.md`
