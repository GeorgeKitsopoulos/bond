# Planning Interface

This document defines the boundary between repository truth and external planning data.

It exists to prevent confusion between:

- what is stored in the repository
- what is stored in external project-management systems
- what may be supplied later through manual API fetches or issue exports

## Core rule

Repository documentation defines project truth for:

- current state
- architecture
- behavior constraints
- testing expectations
- current path truth
- installation/update/uninstall model
- long-term repository planning direction

External planning systems do not override repository truth automatically.

## Gitea boundary

Bond may use a Gitea project layer that contains:

- issues
- milestones
- labels
- planning breakdown
- execution sequencing

That layer is external to the repository unless its contents are explicitly imported or quoted.

This means:

- Gitea issues must not be assumed to exist locally
- Gitea milestone contents must not be hallucinated
- label meanings must not be invented
- task status must not be inferred without fetched data

## Repository versus Gitea roles

The repository is authoritative for:

- what Bond is
- how Bond is structured
- what Bond currently does
- what Bond must not do
- what constraints have been derived from prior failures

Gitea is authoritative only for externally managed planning metadata when that metadata has been explicitly fetched.

## Missing-context rule

If a task depends on issue, milestone, or label content that is not present in the repository, the correct behavior is:

1. state that the required external planning context is missing
2. request the specific issue text or API output
3. avoid inventing the missing content
4. avoid pretending the repository already contains that planning data

## Reference discipline

Repository docs may reference external planning items by identifier, but must not summarize or rely on their contents unless those contents have been explicitly brought into scope.

## Sync discipline

If repository work materially changes planning assumptions, that change should be reflected by:

- repository document updates where appropriate
- external planning updates in Gitea where appropriate

But the two layers must remain conceptually distinct.

## Summary

Bond must keep a clean boundary between:

- repository truth
- external planning metadata

If external planning context is missing, it must be requested rather than invented.
