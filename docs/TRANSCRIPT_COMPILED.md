# Transcript Compiled Constraints

This document is a compiled mapping of:

- observed failures from live usage and transcript history
- enforced constraints derived from those failures

It is not a narrative log.
It is a constraint system.

Each section represents a real failure pattern and the rule that must prevent it from recurring.

## Core rule

If a failure has been observed, it must:

- be documented here
- be converted into a constraint
- be enforced through:
  - architecture
  - behavior contract
  - testing

## Failure category 1 — Capability fabrication

Observed failures:

- claiming to start timers without implementation
- claiming to access clipboard without implementation
- claiming to take screenshots without implementation
- implying system control without grounded execution

Constraint:

Bond must not claim capability without:

- actual implementation
- or explicit supported path

Enforcement direction:

- capability truth layer must exist
- unsupported capabilities must be clearly stated
- tests must verify refusal or limitation explanation

## Failure category 2 — Fake execution

Observed failures:

- describing actions as completed when no execution occurred
- providing “results” without running commands
- implying system changes that did not happen

Constraint:

Execution must only be reported if:

- it actually happened
- it returned a real result

Enforcement direction:

- execution layer must return structured results
- responses must be tied to execution outcome
- no execution → no success claim

## Failure category 3 — Wrong target resolution

Observed failures:

- "open internet" opening internal project directories
- vague inputs resolving to unrelated paths
- arbitrary default targets being chosen

Constraint:

Ambiguous targets must not be guessed.

Enforcement direction:

- parser must mark ambiguity
- policy must require clarification
- no default unsafe guesses

## Failure category 4 — Lexical hijacking

Observed failures:

- "test" triggering test logic
- "memory test" triggering memory routines
- "path test" triggering unrelated behavior

Constraint:

Keywords must not override intent understanding.

Enforcement direction:

- parsing must rely on structure, not keywords alone
- lexical triggers must not bypass intent classification
- tests must include hijack scenarios

## Failure category 5 — Mixed-intent confusion

Observed failures:

- combining unrelated actions and responses
- partial execution without clear separation
- invented workflows for multi-part input

Constraint:

Multiple intents must be:

- split explicitly
- or refused for clarification

Enforcement direction:

- policy must detect multiple intents
- execution must not proceed without clear structure
- tests must cover mixed-intent cases

## Failure category 6 — Unsafe action handling

Observed failures:

- deletion requests not being refused properly
- shutdown requests being treated casually
- dangerous actions being reframed incorrectly

Constraint:

Dangerous actions must be:

- classified as high risk
- gated strictly
- refused when appropriate

Enforcement direction:

- policy classification must include risk levels
- execution must not proceed without approval
- safety tests must exist

## Failure category 7 — System-state fabrication

Observed failures:

- incorrect current directory reporting
- incorrect environment variable reporting
- fabricated system responses

Constraint:

System answers must be grounded in real probes.

Enforcement direction:

- probe layer must be used
- no probe → no system claim
- fabricated state is forbidden

## Failure category 8 — Memory overreach

Observed failures:

- memory injected into unrelated prompts
- archive data overriding current truth
- irrelevant context being included

Constraint:

Memory must be:

- relevant
- scoped
- subordinate to current truth

Enforcement direction:

- retrieval gating must exist
- memory types must be separated
- tests must verify non-injection

## Failure category 9 — Over-centralized logic

Observed failures:

- too much logic inside orchestration layer
- mixed responsibilities in single modules
- difficult-to-reason behavior

Constraint:

Subsystem boundaries must be explicit.

Enforcement direction:

- parsing, policy, execution, memory must be separated
- orchestrator must be simplified
- architecture must enforce boundaries

## Failure category 10 — Misleading assistant behavior

Observed failures:

- generic assistant responses masking incorrect behavior
- confident tone hiding uncertainty
- verbose responses hiding lack of capability

Constraint:

Response style must not hide incorrect behavior.

Enforcement direction:

- behavior contract must enforce clarity
- responses must reflect actual capability and certainty
- tests must include sanity checks

## Failure category 11 — Path confusion

Observed failures:

- mixing repository paths with runtime paths
- incorrect assumptions about current directory
- hardcoded path usage

Constraint:

Paths must be:

- resolved
- explicit
- environment-aware

Enforcement direction:

- central path resolution must exist
- no direct hardcoded assumptions
- CURRENT_PATHS.md must reflect truth

## Failure category 12 — Test insufficiency

Observed failures:

- passing tests despite incorrect behavior
- missing coverage for real failure cases

Constraint:

Tests must reflect real usage failures.

Enforcement direction:

- failure cases must become tests
- behavioral testing must expand
- regression protection must be enforced

## Enforcement model

Each constraint in this document must be enforced through:

- architecture design
- behavior contract rules
- policy logic
- testing coverage

No constraint should remain documentation-only.

## Summary

This document exists to ensure:

- past failures are not forgotten
- rules are derived from real problems
- the system improves based on evidence

If a failure happens again and is not covered here:

- this document must be updated

This is a living constraint system.
