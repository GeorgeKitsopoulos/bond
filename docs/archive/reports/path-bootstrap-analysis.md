# Path Bootstrap Analysis

> Historical note: this document is preserved for design rationale or implementation history. It is not the current source of truth. Use the current docs and code for present behavior, paths, and project status.

## Scope
- Verified: Inspection was limited to path resolution, runtime root detection, config bootstrap, wrappers, and selftest/runtime path assumptions.
- Verified: Primary inspected files:
  - `src/bond/ai_core.py`
  - `src/bond/ai_run.py`
  - `src/bond/ai_selftest.py`
  - `scripts/bond`
  - `scripts/ai`
  - `Makefile`
  - `config/bond/assistant_config.example.json`
- Verified: Additional inspected files (explicitly needed because they are directly imported and consume path/config helpers):
  - `src/bond/ai_facts.py`
  - `src/bond/ai_memory_query.py`

## Files Inspected
- Verified: `src/bond/ai_core.py`
- Verified: `src/bond/ai_run.py`
- Verified: `src/bond/ai_selftest.py`
- Verified: `scripts/bond`
- Verified: `scripts/ai`
- Verified: `Makefile`
- Verified: `config/bond/assistant_config.example.json`
- Verified: `src/bond/ai_facts.py` (additional, directly imported, path consumer)
- Verified: `src/bond/ai_memory_query.py` (additional, directly imported, path consumer)

## Findings
- Verified: Root/path logic is fragmented across runtime (`ai_core.py`, `ai_run.py`, `ai_facts.py`, `ai_memory_query.py`), selftest (`ai_selftest.py`), and wrappers (`scripts/bond`, `scripts/ai`).
- Verified: Hardcoded `HOME/AI` assumptions remain in multiple modules (`ai_core.py`, `ai_run.py`, `ai_facts.py`, `ai_memory_query.py`).
- Verified: Wrappers are hardcoded to `$HOME/bond`, not repository-relative or `BOND_ROOT`-aware.
- Verified: `ai_selftest.py` has independent root detection and path assembly incompatible with current repo layout.
- Verified: Config bootstrap starts from `CONFIG_FILE = STATE_ROOT / "assistant_config.json"` where `STATE_ROOT` is already fixed from hardcoded `HOME/AI` defaults.
- Inferred: There is no recursive call loop, but bootstrap is effectively locked to a fixed initial location and cannot self-relocate safely.
- Verified: `BOND_CONFIG_PATH` appears in docs/env example but is not implemented in inspected runtime code.
- Inferred: Fixing only `ai_core.py` will not fully resolve runtime because `ai_run.py` and consumers still build local hardcoded paths.

## Root Detection
- A1. Where runtime root is currently determined:
  - Verified: No single runtime-root function exists in `ai_core.py`; module-level constants are used instead:
    - `HOME = Path.home()`
    - `AI_ROOT = HOME / "AI"`
- A2. Files independently determine or assume root path:
  - Verified: `src/bond/ai_core.py` assumes `HOME/AI`.
  - Verified: `src/bond/ai_run.py` re-assumes `HOME/AI`.
  - Verified: `src/bond/ai_facts.py` re-assumes `HOME/AI`.
  - Verified: `src/bond/ai_memory_query.py` re-assumes `HOME/AI`.
  - Verified: `src/bond/ai_selftest.py` has its own `get_runtime_root()` with `BOND_ROOT` env fallback plus local file-based fallback.
  - Verified: `scripts/bond` assumes `$HOME/bond`.
  - Verified: `scripts/ai` assumes `$HOME/bond` indirectly via `scripts/bond`.
- A3. Files still assuming `HOME/AI` or equivalent hardcoded layout:
  - Verified: `src/bond/ai_core.py`
  - Verified: `src/bond/ai_run.py`
  - Verified: `src/bond/ai_facts.py`
  - Verified: `src/bond/ai_memory_query.py`
  - Verified: `scripts/bond` and `scripts/ai` assume `$HOME/bond` layout (different hardcoded layout).
- A4. Single source of truth candidate:
  - Inferred: `src/bond/ai_core.py` should become single source of truth for root detection because it already centralizes path/config helper functions used by runtime modules.

## Config Bootstrap
- B1. How config path is currently determined:
  - Verified: `ai_core.py` defines:
    - `STATE_ROOT = AI_ROOT / "state"`
    - `CONFIG_FILE = STATE_ROOT / "assistant_config.json"`
  - Verified: `load_assistant_config()` reads only `CONFIG_FILE`.
- B2. Circular dependency status:
  - Verified: No direct recursive circular call in code.
  - Inferred: Bootstrap lock exists: `CONFIG_FILE` depends on initial `STATE_ROOT`, while `get_state_root()` depends on config values from that same file. This is not recursion but constrains relocation.
- B3. Exact current bootstrap chain:
  - Verified:
    1. Import `ai_core.py`.
    2. Set `HOME`, `AI_ROOT`, `STATE_ROOT`, `MEMORY_ROOT`, `CONFIG_FILE` from hardcoded defaults.
    3. `FILES = get_files()` executes at import; `get_files()` calls `get_memory_root()`.
    4. `get_memory_root()` calls `config_value("memory_root")`.
    5. `config_value()` calls `load_assistant_config()`.
    6. `load_assistant_config()` reads `CONFIG_FILE` at hardcoded location.
    7. If file absent, defaults are used.
- B4. Smallest safe bootstrap order (for later patch):
  - Inferred:
    1. Resolve project/runtime root first (env var then deterministic fallback).
    2. Resolve base state/config location from that root.
    3. Load config file once from bootstrap path.
    4. Derive memory/state/router paths from loaded config with defaults.
  - Needs confirmation: Exact canonical config file location policy (`state/assistant_config.json` vs repo config path) for production behavior.

## Path Consumers
- C1. Modules consuming root/state/memory/config paths:
  - Verified: `ai_core.py` (all path primitives and file map).
  - Verified: `ai_run.py` (`STATE_ROOT`, `ROUTER_CONFIG`, `CHANGELOG_PATH`, `run_safe_action` path to `ai_exec.py`).
  - Verified: `ai_facts.py` (`STATE_ROOT`, `MEMORY_ROOT`, `ROUTER_CONFIG`, `SYSTEM_PROFILE`, `MAIN_WRAPPER`).
  - Verified: `ai_memory_query.py` (`CHANGELOG_PATH`, plus `FILES`/fact buckets from `ai_core`).
  - Verified: `ai_selftest.py` (all test executable and memory paths).
- C2. Modules computing local paths instead of shared helper:
  - Verified: `ai_run.py` local `HOME`, `AI_ROOT`, `CHANGELOG_PATH`, hardcoded `run_safe_action` executable path.
  - Verified: `ai_facts.py` local `HOME`, `AI_ROOT`, `MAIN_WRAPPER`.
  - Verified: `ai_memory_query.py` local `HOME`, `AI_ROOT`, `CHANGELOG_PATH`.
  - Verified: `ai_selftest.py` local root logic and independent path map.
  - Verified: `scripts/bond`, `scripts/ai` local hardcoded wrapper paths.
- C3. Likely breakpoints if `ai_core` is fixed but local logic remains:
  - Verified: `ai_run.py` can still call nonexistent `<legacy-runtime-root>/tools/ai_exec.py`.
  - Verified: `ai_run.py` changelog path can still point to nonexistent `<legacy-runtime-root>/dev/changelog/changelog.jsonl`.
  - Verified: `ai_selftest.py` can still resolve to `.../src/AI/...` and fail before meaningful test execution.
  - Inferred: `ai_facts.py`/`ai_memory_query.py` may read stale/nonexistent local-path constants even if shared helpers are corrected.

## Wrappers
- D1. `scripts/bond` and `scripts/ai` assumptions:
  - Verified: `scripts/bond` runs `python3 "$HOME/bond/src/bond/ai_run.py"`.
  - Verified: `scripts/ai` execs `"$HOME/bond/scripts/bond"`.
- D2. Hardcoded specific repo location:
  - Verified: Yes, hardcoded to `$HOME/bond`.
- D3. Minimal later fix needed:
  - Inferred: Make wrappers resolve root from `BOND_ROOT` first, then deterministic script-relative fallback; avoid user-specific absolute paths.
  - Needs confirmation: Preferred wrapper fallback policy when invoked via symlink.

## Tests
- E1. How `ai_selftest.py` determines runtime root:
  - Verified: `get_runtime_root()`:
    - uses `BOND_ROOT` if set
    - else returns `current_file_path.parent.parent / "AI"`
- E2. Runtime path logic duplication:
  - Verified: Yes, it duplicates path logic and builds independent paths (`AI_ROOT`, `AI_RUN`, `AI_EXEC`, `AI_MEMORY`, etc.).
- E3. What should later change:
  - Inferred: Selftests should consume the same root/path bootstrap as runtime (central helper import or a single shared resolver), not maintain a separate fallback tree.

## Minimal Patch Order
- F1. First file to patch: `src/bond/ai_core.py`
  - Exact reason:
    - Verified: It already owns path/config helpers and `FILES` generation.
    - Inferred: Making this authoritative is the smallest path to consistency.
  - Exact kind of change:
    - Inferred: Add deterministic root bootstrap (env var + fallback), then derive config/state/memory/router defaults from it.
    - Inferred: Ensure config bootstrap order is non-circular and uses one initial config location.
  - Must NOT change yet:
    - Verified: Do not refactor unrelated logic (memory ranking, intent, action policy).
- F2. Second file to patch: `src/bond/ai_run.py`
  - Exact reason:
    - Verified: It contains local hardcoded executable and changelog paths that bypass core helpers.
  - Exact kind of change:
    - Inferred: Replace local hardcoded path construction with shared helpers from `ai_core.py` for action-exec and changelog path.
  - Must NOT change yet:
    - Verified: Do not alter routing behavior or model-selection logic.
- F3. Third file to patch (absolutely necessary): `src/bond/ai_selftest.py`
  - Exact reason:
    - Verified: Selftest root/path map is currently divergent and known-broken in fallback path.
  - Exact kind of change:
    - Inferred: Remove independent root hack in favor of shared runtime bootstrap logic.
  - Must NOT change yet:
    - Verified: Do not change test semantics/assertions beyond path resolution wiring.
- Needs confirmation: Whether wrapper script patch should be included in the same first slice or immediate follow-up.

## Risks
- Verified: Hidden hardcoded paths remain in non-patched consumers (`ai_facts.py`, `ai_memory_query.py`, wrappers) and can silently keep failures alive.
- Verified: If config bootstrap order is altered incorrectly, config file may never be found or may point to wrong state root.
- Verified: Test/runtime divergence can persist if selftest keeps separate root logic.
- Verified: Wrapper breakage risk remains if scripts keep `$HOME/bond` assumptions.
- Verified: Broad refactor risk is high because path constants are scattered; minimal slice discipline is required.
- Inferred: Module-level constants initialized at import can freeze stale paths before env/config adjustments if bootstrap is not ordered carefully.

## Verification Plan
- Verified (post-patch checks):
  - `rg 'HOME\s*/\s*"AI"|\$HOME/bond' src/bond scripts`
  - `make compile`
  - `make smoke`
  - `BOND_ROOT=$PWD python3 src/bond/ai_selftest.py | head -40`
  - `BOND_ROOT=$PWD python3 -c 'import ai_core; print(ai_core.get_state_root()); print(ai_core.get_memory_root()); print(ai_core.get_router_config_path())'`
- Needs confirmation:
  - Whether `PYTHONPATH=src/bond` is required in the targeted one-liner in this environment.

## Open Questions
- Needs confirmation: Canonical config file location policy for bootstrap (`state/assistant_config.json` vs repo config path with local override).
- Needs confirmation: Should wrapper scripts be included in the first minimal patch slice or immediately after runtime/selftest stabilization.
- Needs confirmation: Desired fallback behavior when `BOND_ROOT` is unset and code is executed from different working directories or via symlinks.
- Needs confirmation: Whether `BOND_CONFIG_PATH` is intentionally planned but not implemented, or should be removed from docs/examples until implemented.
