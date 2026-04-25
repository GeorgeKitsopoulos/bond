# Change 006 - Assistant Config Target Resolution

> Historical note: this document is preserved for design rationale or implementation history. It is not the current source of truth. Use the current docs and code for present behavior, paths, and project status.

## Scope
- Edited files:
  - src/bond/ai_action_parse.py
  - src/bond/ai_action_catalog.py
  - src/bond/ai_facts.py
  - docs/reports/change-006-assistant-config-target.md
- No other files changed.

## Reason
- ai_core now resolves the active config path correctly.
- the known target `assistant config` still pointed to outdated path assumptions.
- this caused multiple selftest failures related to opening assistant config.

## Changes
- known target mapping
  - Before: `assistant config` in action catalog mapped to `state_root / "assistant_config.json"`.
  - After: `assistant config` maps to `ai_core.CONFIG_FILE` (active bootstrap-resolved config path).
- target/path resolver logic
  - Before: explicit legacy state-path requests were treated only as explicit paths.
  - After: explicit path requests matching `get_state_root() / "assistant_config.json"` are redirected to the known target `assistant config`, so they resolve through active config path logic.
- policy alignment for explicit config path access
  - Before: assistant-config path facts returned state-root-based assistant config path.
  - After: assistant-config path facts return `ai_core.CONFIG_FILE`, aligned with active config resolution.

## Unchanged On Purpose
- ai_core bootstrap logic
- ai_run.py
- ai_selftest.py
- unrelated known targets
- test semantics
- wrappers

## Expected Result
- `assistant config` now resolves to the active config file path from ai_core
- tests related to opening assistant config should no longer fail for outdated path reasons
- no unrelated target behavior was modified

## Validation Commands

```bash
cd <repo>

python3 -m py_compile src/bond/ai_action_parse.py src/bond/ai_action_catalog.py src/bond/ai_action_policy.py src/bond/ai_facts.py

BOND_ROOT=$PWD PYTHONPATH=src \
python3 src/bond/ai_selftest.py
```
