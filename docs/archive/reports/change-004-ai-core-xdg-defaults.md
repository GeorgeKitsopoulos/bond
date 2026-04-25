# Change 004 - ai_core XDG Transitional Defaults

> Historical note: this document is preserved for design rationale or implementation history. It is not the current source of truth. Use the current docs and code for present behavior, paths, and project status.

## Scope
- Edited files:
  - src/bond/ai_core.py
  - config/bond/assistant_config.example.json
  - docs/reports/change-004-ai-core-xdg-defaults.md
- No other files changed.

## Reason
- Runtime/config separation is planned.
- This step adds XDG-aware defaults without forcing migration.
- Explicit config values still take priority.

## Changes
- config bootstrap precedence
  - Before: `BOND_CONFIG_PATH` -> repo config -> legacy `<legacy-runtime-root>/state/assistant_config.json` -> repo path fallback.
  - After: `BOND_CONFIG_PATH` -> `~/.config/bond/assistant_config.json` -> repo config -> legacy `<legacy-runtime-root>/state/assistant_config.json` -> XDG config path fallback.
- default memory_root behavior
  - Before: when config key missing, default memory root was repo-local (`BOND_ROOT/memory`).
  - After: when config key missing, default memory root is XDG data path (`~/.local/share/bond/memory`).
- default state_root behavior
  - Before: when config key missing, default state root was repo-local (`BOND_ROOT/state`).
  - After: when config key missing, default state root is XDG data path (`~/.local/share/bond/state`).
- example config defaults
  - Before: example `memory_root` and `state_root` pointed to `<repo>/*`.
  - After: example `memory_root` and `state_root` point to `~/.local/share/bond/*`.

## Unchanged On Purpose
- active user config
- ai_run.py
- selftests
- wrappers
- runtime file migration
- assistant behavior

## Expected Result
- explicit config values still win
- XDG paths are now the default when config is absent
- repo router config default remains repo-relative
- no full migration happens in this step

## Validation Commands

```bash
cd <repo>

python3 -m py_compile src/bond/ai_core.py

BOND_ROOT=$PWD PYTHONPATH=src \
python3 -c "from bond import ai_core; print('CONFIG_FILE=', ai_core.CONFIG_FILE)"

BOND_ROOT=$PWD PYTHONPATH=src \
python3 -c "from bond import ai_core; print('STATE_ROOT=', ai_core.get_state_root()); print('MEMORY_ROOT=', ai_core.get_memory_root()); print('ROUTER_CONFIG=', ai_core.get_router_config_path())"

rg 'HOME\\s*/\\s*"AI"|<legacy-runtime-root>/memory|<repo>/memory|<repo>/state' src/bond/ai_core.py config/bond/assistant_config.example.json
```