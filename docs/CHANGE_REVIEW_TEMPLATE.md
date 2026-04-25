# Change Review Template

Use this template when proposing or reviewing a meaningful change.

## Change summary

- Target files:
- Intended effect:

## Documentation impact review

- Behavior impact:
- Architecture impact:
- Path-truth impact:
- Testing impact:
- Installation/lifecycle impact:

## Authoritative documents checked

- `STATE.md`:
- `ARCHITECTURE.md`:
- `BEHAVIOR_CONTRACT.md`:
- `CURRENT_PATHS.md`:
- `TESTING.md`:
- `INSTALLATION.md`:
- `BOND_PROJECT_MASTER_PLAN.md`:
- `PLANNING_INTERFACE.md`:
- `REVIEW_CHECKLIST.md`:

## Documentation updates required

- Files to update:
- If none, explicit justification:

## External planning context

- Required:
- If required, what is missing:
- Issue text/API output supplied:

## Completion check

A change is not complete if:

- implementation changed but authoritative docs were left stale
- external planning data was assumed rather than supplied
- behavioral implications were not reviewed

## Optional repository-local gate

If desired, run:

`DOCS_REVIEWED=yes|no DOCS_UPDATED=yes|no EXTERNAL_CONTEXT_NEEDED=yes|no EXTERNAL_CONTEXT_PROVIDED=yes|no CHANGE_SUMMARY="text" DOCS_IMPACT_NOTE="text" EXTERNAL_CONTEXT_NOTE="text" make reviewcheck`

This does not replace real review, but it requires explicit declaration plus short written notes through the repository-local gate.
