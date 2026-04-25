# Control, Trust, and Extensibility

This document defines user-visible trust, explainability, capability discovery, plugin boundaries, multi-profile groundwork, context awareness, policy feedback, and interaction modes for Bond.

## Current diagnosis

Bond has internal logic and strong safety direction, but user-visible transparency and extension boundaries are not yet formalized.

## Core rule

Bond must make its capabilities, decisions, sources, actions, and extension boundaries visible enough that the user can understand what is happening without exposing hidden chain-of-thought or unsafe internals.

## Explainability layer

Bond should support high-level decision explanations such as:
- which mode/path was used;
- which source class was used: memory, document knowledge, live system probe, config, or unsupported/future capability;
- why an action was approved, blocked, rejected, or sent to clarification;
- what uncertainty remains.

Explanation must not expose hidden chain-of-thought. It should expose truthful operational metadata and concise rationale.

## Action transparency and confirmation

Before future supported mutating or risky actions, Bond should be able to preview:
- intended action;
- target;
- side effects;
- reversibility or rollback status;
- confirmation requirement;
- capability and policy reason codes.

## Capability discovery

Bond must eventually answer:
- `what can you do?`
- `what can you do here?`
- `what is available on this system?`

These answers must be generated from the capability registry and relevant probes, not from improvised model claims.

## Plugin and extension architecture

Plugins/extensions are planned, not implemented. The required contract is:
- plugin metadata;
- declared capabilities;
- required permissions/tools;
- lifecycle hooks;
- health check;
- isolation boundary;
- failure behavior;
- uninstall/disable behavior;
- audit tags.

Plugins must not mutate the core silently, bypass policy, own user memory without boundaries, or register capabilities without status and risk classification.

## Multi-profile and multi-user groundwork

Bond is currently single-user by reality. Future multi-profile support requires:
- explicit user/profile identity;
- per-profile memory;
- shared versus private data boundaries;
- permission boundaries;
- profile-aware capability and context settings.

Do not retrofit server/multi-user assumptions into current code until the single-user core is stable.

## Context awareness layer

Context awareness is planned and must be consent-aware. Candidate context includes:
- current app/window;
- selected file or target;
- current directory/session;
- screen context only when explicitly supported;
- recent assistant mode/session state.

Screen or app context must not be implied when it is not probed or permitted.

## Policy feedback loop

User corrections should inform policy and behavior only through structured correction memory and reviewable rules. Corrections must not blindly rewrite safety policy.

## Interaction modes

Bond should model modes explicitly:
- casual chat;
- command mode;
- system control;
- troubleshooting;
- development mode.

Mode affects routing, expected evidence, confirmation behavior, and answer style. Mode must not bypass safety.

## Current implementation status

These are planned or partial design layers. Current Bond must not claim complete plugin, multi-user, context-screen, or dynamic capability discovery support until implemented and tested.

## Cross references

- `docs/ARCHITECTURE.md`
- `docs/BEHAVIOR_CONTRACT.md`
- `docs/CAPABILITIES.md`
- `docs/MEMORY.md`
- `docs/PROBES.md`
- `docs/TESTING.md`
