# Packaging Strategy

This document defines Bond's packaging direction. It separates Python application definition from OS distribution mechanisms.

## Core rule

Bond needs a layered packaging strategy, not one universal package format.

## Current reality

Bond is currently repository-first and transitional. `pyproject.toml` exists but packaging is not complete. Wrapper scripts and legacy paths must be treated as migration debt, not final installation design.

## Layered model

### Layer A — Canonical Python core

- `pyproject.toml`
- package metadata
- dependencies
- entry points
- `src/bond/` modules

This layer defines the application.

### Layer B — Platform adapters

- Linux: wheel first, optional `.deb`/`.rpm` later.
- Windows: bundled executable plus `.exe`/`.msi`/MSIX-style installer later.
- Android: APK/AAB only as a separate product layer because Android sandboxing changes the execution model.

These adapters distribute the application; they do not redefine the core architecture.

### Layer C — Integration surfaces

- Cinnamon applet
- systemd user services
- desktop files
- icons
- OS-specific hooks

Integration surfaces must stay decoupled from the core.

## Stage 1 — Local controlled install

Stage 1 target:

- Python package as canonical app definition;
- local installation through `pipx` or an equivalent isolated local environment;
- explicit entry point replacing ad hoc wrapper dependence;
- runtime paths normalized through config/path logic;
- no direct repo execution as final user path.

Explicit Stage 1 rejections:

- no Flatpak for core;
- no AppImage for core;
- no binary freezing;
- no `.deb`/`.rpm` as the first solution.

## Stage 2 — Stable distribution adapters

Stage 2 keeps the Python core unchanged and adds native adapters where useful:

- Linux wheel and optional native packages;
- Windows installer/bundle;
- Android only as an optional separate architecture.

## Misconceptions to avoid

- One package does not fit all operating systems.
- Flatpak/AppImage solve distribution shape, not architecture.
- Android is not equivalent to desktop Linux.
- A wrapper around current path chaos is not packaging.

## Relationship to current model roster

Packaging must not assume a hidden heavyweight model tier. The current planning baseline remains the lean local roster documented in `README.md` and `docs/STATE.md`.

## Current implementation status

Packaging is partial/transitional. This document defines direction, not completion.

## Cross references

- `docs/INSTALLATION.md`
- `docs/CURRENT_PATHS.md`
- `docs/RELEASE_PROCESS.md`
- `docs/SERVICE.md`
- `docs/APPLET.md`
- `docs/BOND_PROJECT_MASTER_PLAN.md`
