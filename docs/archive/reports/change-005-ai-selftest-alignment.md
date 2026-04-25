# Change 005 - ai_selftest Path Alignment

> Historical note: this document is preserved for design rationale or implementation history. It is not the current source of truth. Use the current docs and code for present behavior, paths, and project status.

## Scope
- Edited files:
  - src/bond/ai_selftest.py
  - docs/reports/change-005-ai-selftest-alignment.md
- No other files changed.

## Reason
- ai_core is now the single source of truth for runtime path resolution.
- ai_selftest.py still used separate local path/root logic.
- This caused selftest/runtime divergence.

## Changes
- removed selftest-local root assumptions
  - Before: ai_selftest defined its own `get_runtime_root()` and local `HOME`/`AI_ROOT` path tree.
  - After: ai_selftest no longer uses local root bootstrap logic.
- replaced local path construction with ai_core-derived values
  - Before: memory/state/tool paths were manually built from local assumptions.
  - After: paths are derived from `ai_core.BOND_ROOT`, `ai_core.get_memory_root()`, and `ai_core.get_state_root()`.
- aligned internal tool/module paths with repository-aware runtime paths
  - Before: internal tool paths referenced legacy `.../tools/ai/...` assumptions.
  - After: internal module paths resolve from `BOND_ROOT / "src" / "bond" / ...` and wrapper path from `BOND_ROOT / "scripts" / "ai"`.

## Unchanged On Purpose
- test intent
- test assertions
- subprocess strategy
- runtime behavior
- Makefile
- ai_core.py

## Expected Result
- selftest now resolves paths from ai_core
- test/runtime path divergence is reduced
- failing tests, if any remain, should be more likely to reflect real issues rather than path-bootstrap mismatch

## Validation Commands

```bash
cd <repo>

python3 -m py_compile src/bond/ai_selftest.py

BOND_ROOT=$PWD PYTHONPATH=src \
python3 src/bond/ai_selftest.py
```

## Test Results
- Command run:
  - `BOND_ROOT=$PWD PYTHONPATH=src python3 src/bond/ai_selftest.py`
- Exit code:
  - `1`
- Summary:
  - `passed: 15`
  - `failed: 3`
  - `total: 18`
- Failing tests:
  - `action_known_target_in_editor`
    - expected exit 0, got 3
    - missing stdout text: `"ok": true`
    - stdout: `{"ok": false, "error": "unknown_or_missing_target: assistant config", "intent": {"intent": "open_known_in_editor", "target": "assistant config"}}`
  - `action_explicit_allowed_path`
    - expected exit 0, got 3
    - missing stdout text: `"ok": true`
    - stdout: `{"ok": false, "error": "missing_path: <repo>/state/assistant_config.json", "intent": {"intent": "open_path_in_editor", "path": "<repo>/state/assistant_config.json"}}`
  - `chain_success`
    - expected exit 0, got 3
    - stdout includes failed step 2: `open assistant config in editor` with `unknown_or_missing_target: assistant config`
