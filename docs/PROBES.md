# Probe Layer Specification

## Purpose

This document is the canonical probe-layer specification for deterministic system truth in Bond.

Probes gather real local facts. They do not perform model reasoning.
Probe truth feeds capability truth and live-truth answers.

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
- portals / D-Bus / user-session capability surfaces
- clipboard / notification / desktop interaction availability
- model and runtime truth
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

```
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

## Cross references

- [docs/ARCHITECTURE.md](ARCHITECTURE.md)
- [docs/CAPABILITIES.md](CAPABILITIES.md)
- [docs/STATE.md](STATE.md)
- [docs/TESTING.md](TESTING.md)
- [docs/CURRENT_PATHS.md](CURRENT_PATHS.md)
