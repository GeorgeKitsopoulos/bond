# Contributing

Bond is an early local-assistant prototype. Contributions are welcome only when they preserve the project's safety, truthfulness, and documentation discipline.

## Current contribution boundary

Before the first stable release, the project prioritizes:

- current-truth documentation;
- deterministic routing and policy behavior;
- capability honesty;
- tests that prove behavior, not just code survival;
- public-repository hygiene;
- packaging and install discipline.

Do not submit changes that add broad assistant claims, privileged execution, voice-first behavior, plugin execution, or new automation surfaces unless the required capability, policy, test, and documentation boundaries are included.

## Required checks

Before proposing a change, run:

```bash
python3 -m compileall src/bond
python3 src/bond/ai_selftest.py
```

For documentation-impacting changes, also run the repository review check:

```bash
DOCS_REVIEWED="yes" \
DOCS_UPDATED="yes" \
EXTERNAL_CONTEXT_NEEDED="no" \
EXTERNAL_CONTEXT_PROVIDED="no" \
CHANGE_SUMMARY="<short change summary>" \
DOCS_IMPACT_NOTE="<docs reviewed/updated>" \
EXTERNAL_CONTEXT_NOTE="No external context required." \
make reviewcheck
```

## Documentation rule

A behavior-changing pull request is incomplete unless the relevant current documentation is updated in the same change.

Current truth belongs in:

- `README.md`
- `ROADMAP.md`
- `CHANGELOG.md`
- `docs/STATE.md`
- `docs/ARCHITECTURE.md`
- `docs/BEHAVIOR_CONTRACT.md`
- `docs/CAPABILITIES.md`
- `docs/TESTING.md`

Archived analysis under `docs/archive/` is historical context, not current project truth.
