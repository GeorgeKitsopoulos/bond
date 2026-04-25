# Change 003 - Runtime Separation Plan

> Historical note: this document is preserved for design rationale or implementation history. It is not the current source of truth. Use the current docs and code for present behavior, paths, and project status.

## Scope
- Verified: This is inspection and planning only.
- Verified: No source/config/script/test changes are included in this step.
- Verified: Goal is controlled separation of repo source, venv, and mutable runtime data without destabilizing recent bootstrap/path fixes.

## Current Layout
- Verified:
  - Repo source paths:
    - `<repo>/src/bond/*.py`
    - `<repo>/scripts/*`
    - `<repo>/config/*`
    - `<repo>/docs/*`
    - `<repo>/tests/*`
  - Python environment path:
    - `<repo>/.venv/`
  - Mutable runtime paths (configured):
    - `memory_root`: `<repo>/memory`
    - `state_root`: `<repo>/state`
    - Config file: `<repo>/config/bond/assistant_config.json`
  - Generated/mutable artifacts in repo tree:
    - `<repo>/memory/facts/*`
    - `<repo>/memory/logs/*`
    - `<repo>/memory/state/*`
    - `<repo>/state/*`
    - `<repo>/dev/changelog/changelog.jsonl`
- Verified: Optional archive storage path is configured outside repo:
  - `archive_root`: `<archive-root>/memory`
- Inferred: Runtime mutable data is currently mixed into repo working tree by design/config, which conflicts with stricter source/runtime separation goals.

## Separation Target
- Recommended: Minimal target categories for next phase:
  - Repo source:
    - `<repo>` (tracked code, docs, configs, scripts, tests)
  - Venv:
    - `<repo>/.venv` (Python interpreter + packages only)
  - Runtime mutable data:
    - outside repo (state, memory facts/logs/state, runtime changelog artifacts)
  - Local config:
    - `~/.config/bond/assistant_config.json` (or env-selected equivalent)
  - Optional archive storage:
    - existing second-drive archive path remains optional and external
- Recommended: Do not store runtime mutable data under `.venv`.
- Recommended: Do not redesign packaging in this slice.

## Recommended Runtime Location
- Recommended (single strategy): **XDG-style locations**
  - Runtime mutable data: `~/.local/share/bond/`
    - `~/.local/share/bond/memory`
    - `~/.local/share/bond/state`
    - `~/.local/share/bond/dev/changelog`
  - Local config: `~/.config/bond/assistant_config.json`
- Why this is better for current stage:
  - Recommended: Keeps repo clean while preserving repo-first source ownership.
  - Recommended: Aligns with Linux conventions without requiring packaging redesign.
  - Recommended: Easier to document and validate than ad-hoc per-user repo-local runtime paths.

## Migration Impact
- Verified: Future patch areas impacted:
  - `ai_core` path helpers and config bootstrap precedence
  - active config values (`memory_root`, `state_root`, and config path source)
  - selftest expectations/path assumptions (`ai_selftest.py` currently has separate logic)
  - wrappers/launcher assumptions (`scripts/bond`, `scripts/ai` currently hardcoded to `$HOME/bond`)
  - install/update flow docs/scripts (currently manual/partial)
  ## Separation Target
- Recommended: Minimal target categories for next phase:
  - cleanup of repo-local runtime artifacts from `<repo>/memory`, `<repo>/state`, `<repo>/dev/changelog`
- Inferred: If only ai_core changes but selftest/wrappers are not aligned, path divergence will persist.

## Preconditions
- Recommended minimum preconditions before implementation:
  - Confirm canonical runtime location policy (XDG choice above) is approved.
  - Confirm canonical local config location policy (`~/.config/bond/assistant_config.json`) and env override precedence.
  - Confirm migration behavior for existing repo-local runtime data (copy vs move, and whether old dirs remain readable temporarily).
  - Confirm that this slice is path/config only (no assistant behavior/routing changes).

## Minimal Implementation Order
1. Target file(s): `src/bond/ai_core.py`
- Exact purpose: add/adjust defaults so runtime mutable paths default to XDG runtime, and config bootstrap can resolve local config path first while preserving env overrides.
- Must NOT change: memory/query/routing/action logic, JSON formats, bucket names.

2. Target file(s): `config/bond/assistant_config.example.json`
- Exact purpose: update example defaults to XDG runtime + local config conventions.
- Must NOT change: key set semantics, archive behavior semantics.

3. Target file(s): `src/bond/ai_selftest.py`
- Exact purpose: align test path resolution with ai_core single-source helpers and remove separate runtime-root hack assumptions.
- Must NOT change: test intent/assertion semantics beyond path source alignment.

4. Target file(s): `scripts/bond`, `scripts/ai`
- Exact purpose: remove hardcoded `$HOME/bond` assumptions; resolve through `BOND_ROOT` + deterministic fallback.
- Must NOT change: command behavior beyond path resolution.

5. Target file(s): `docs/INSTALLATION.md`, `docs/TESTING.md` (and install/update docs if present)
- Exact purpose: document runtime location and migration steps for existing users.
- Must NOT change: unrelated project roadmap or architecture content.

## Risks
- Verified: Breaking tests if selftest keeps separate root/path logic while runtime moves.
- Verified: Mixing repo and runtime paths during partial migration can cause split state.
- Verified: Accidental runtime writes into `.venv` if path defaults are misconfigured.
- Verified: Stale state left in old repo-local locations may continue to be read if precedence is unclear.
- Verified: Wrapper breakage if launchers are not aligned with new root/config/runtime assumptions.
- Inferred: Backward-compat read paths may mask misconfiguration unless explicit diagnostics are added later.

## Verification Plan
- Recommended commands to run **after future implementation** (not run in this step):
```bash
cd <repo>

python3 -m py_compile src/bond/ai_core.py src/bond/ai_run.py src/bond/ai_selftest.py

BOND_ROOT=$PWD PYTHONPATH=src \
python3 -c "from bond import ai_core; print('CONFIG_FILE=', ai_core.CONFIG_FILE); print('STATE_ROOT=', ai_core.get_state_root()); print('MEMORY_ROOT=', ai_core.get_memory_root()); print('ROUTER_CONFIG=', ai_core.get_router_config_path())"

BOND_ROOT=$PWD PYTHONPATH=src \
python3 src/bond/ai_selftest.py

rg 'HOME\s*/\s*"AI"|\$HOME/bond|<legacy-runtime-root>|<repo>/memory|<repo>/state' src/bond scripts config/bond

test -d ~/.local/share/bond && echo "runtime dir present"
test -d ~/.config/bond && echo "config dir present"
```

## Notes
- Verified: Current bootstrap/path fixes already moved ai_core and ai_run toward repo-aware behavior.
- Verified: Current active config still keeps mutable runtime data inside repo (`<repo>/memory`, `<repo>/state`).
- Recommended: Next separation patch should stay strictly path/config scoped and avoid assistant behavior changes.
