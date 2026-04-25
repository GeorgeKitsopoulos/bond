# Change 002 - ai_run Path Resolution

> Historical note: this document is preserved for design rationale or implementation history. It is not the current source of truth. Use the current docs and code for present behavior, paths, and project status.

## Scope
- Edited files:
  - src/bond/ai_run.py
  - docs/reports/change-002-ai-run-paths.md
- No other files changed.

## Reason
- ai_core is now the single source of truth for root and config.
- ai_run.py still used local hardcoded paths.
- This caused inconsistency between runtime and bootstrap logic.

## Changes
- Removed HOME/AI assumptions
  - Before: ai_run.py defined local `HOME = Path.home()` and `AI_ROOT = HOME / "AI"`.
  - After: ai_run.py no longer defines local HOME/AI root assumptions.
- Replaced with ai_core helpers
  - Before: only part of path state used ai_core helpers while root-related paths remained local.
  - After: ai_run.py imports and uses `get_state_root()`, `get_memory_root()`, and `get_router_config_path()` for path resolution.
- Replaced hardcoded ai_exec path
  - Before: action execution used `AI_ROOT / "tools" / "ai_exec.py"`.
  - After: action execution path is derived from `BOND_ROOT / "src" / "bond" / "ai_exec.py"`.

## Unchanged On Purpose
- intent routing
- memory logic
- LLM behavior
- output structure

## Expected Result
- ai_run.py no longer depends on `<legacy-runtime-root>` paths
- All paths resolve consistently via ai_core
- Runtime behavior unchanged except path correctness

## Validation Commands

```bash
cd <repo>

make compile

BOND_ROOT=$PWD PYTHONPATH=src \
python3 src/bond/ai_run.py "hello"
```
