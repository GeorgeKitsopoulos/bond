# Change 001 - Config Paths

> Historical note: this document is preserved for design rationale or implementation history. It is not the current source of truth. Use the current docs and code for present behavior, paths, and project status.

## Scope
- Edited files:
  - config/bond/assistant_config.json
  - docs/reports/change-001-config-paths.md
- No other files changed.

## Reason
- ai_core bootstrap now resolves the repo config correctly.
- The config still pointed runtime state/memory to legacy `<legacy-runtime-root>` paths.
- This change aligns active config with the repo-native layout.

## Changes
- memory_root
  - previous value: `<legacy-runtime-root>/memory`
  - new value: `<repo>/memory`
- state_root
  - previous value: `<legacy-runtime-root>/state`
  - new value: `<repo>/state`

## Unchanged On Purpose
- ollama_url
- router_config
- second_drive
- archive_root
- These were left unchanged intentionally except for verification.

## Expected Result
- After this change, ai_core should resolve:
  - config file from repo config path
  - state_root to `<repo>/state`
  - memory_root to `<repo>/memory`
  - router_config to `<repo>/config/router/profiles.json`

## Validation Commands
```bash
cd <repo>

BOND_ROOT=$PWD PYTHONPATH=src \
python3 -c "from bond import ai_core; print(ai_core.CONFIG_FILE)"

BOND_ROOT=$PWD PYTHONPATH=src \
python3 -c "from bond import ai_core; print(ai_core.get_state_root()); print(ai_core.get_memory_root()); print(ai_core.get_router_config_path())"
```