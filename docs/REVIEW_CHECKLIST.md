# Review Checklist

This checklist exists to prevent repository drift during LLM-assisted changes.

## Core rule

A meaningful change is not complete until both implementation impact and documentation impact have been reviewed.

## Required review questions

For every meaningful change, review must ask:

1. Does this change alter behavior?
2. Does this change alter architectural boundaries or module responsibilities?
3. Does this change alter current path truth?
4. Does this change alter testing expectations or regression coverage?
5. Does this change alter install, update, uninstall, packaging, or lifecycle behavior?
6. Does this change rely on external planning context that is not currently present in the repository?

## Documentation sync requirement

If the answer to any of questions 1 through 5 is yes, the corresponding authoritative document must be updated in the same change, or the change must explicitly justify why no documentation update is required.

## External-context requirement

If the answer to question 6 is yes, the change must not invent the missing external context.

Instead, it must:

- state what external context is missing
- request the specific issue text, milestone content, or API output
- avoid pretending that external planning data is already available locally

## Minimum review output

A Copilot-produced change should not be accepted if the originating prompt failed to define:

- exact edit scope
- exact task
- reviewed documentation scope
- external-context status
- verification commands

A compliant review should explicitly state:

- what changed
- which authoritative documents were checked
- which authoritative documents were updated
- whether any external planning context was required
- whether any required context was missing

For quick operator reference, `scripts/bond-dev-help` may be used to print the current developer prompt-wrapper and declaration-gate entry points.

For consistent session setup, operators should use:

- `docs/DEVELOPMENT.md`
- `docs/LLM_OPERATING_GUIDE.md`

These are setup aids for bounded Copilot work and do not replace actual review.

When a meaningful change needs a written review record, use `REPOSITORY_REVIEW_NOTE_TEMPLATE.md` instead of vague free-form notes.

## Summary

The review process must protect:

- repository truth
- documentation sync
- behavioral honesty
- external-context honesty
