# Security Policy

Bond is an experimental local assistant prototype. It is not a stable release and must not be treated as safe for unattended automation, privileged execution, or safety-critical workflows.

## Supported versions

There are no supported stable releases yet.

Security fixes and hardening work apply to the active development branch until tagged release discipline exists.

## Security boundaries

Do not:

- run Bond as root;
- expose Bond as a public network service;
- give Bond unnecessary secrets;
- use Bond for unattended privileged/system changes;
- treat planned capabilities as implemented security guarantees.

Current safety work focuses on deterministic routing, parser preflight, policy gates, dry-run behavior, confirmation-required flow, and bounded rootless actions.

## Reporting a vulnerability

If GitHub private vulnerability reporting is enabled for this repository, use it.

If private vulnerability reporting is not available, open a minimal public issue asking for a secure reporting contact. Do not post exploit details, secrets, private paths, tokens, or sensitive logs publicly.

## Scope

Security reports are most useful when they involve:

- action execution bypass;
- policy gate bypass;
- confirmation bypass;
- unsafe parsing of action-looking requests;
- secret leakage through logs or diagnostics;
- public-repository leakage of private paths, credentials, memory, or local runtime data.
