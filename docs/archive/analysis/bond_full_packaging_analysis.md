# Bond Packaging Strategy – Full Analysis (Revised)

> Historical note: this document is preserved for design rationale or implementation history. It is not the current source of truth. Use the current docs and code for present behavior, paths, and project status.

## Executive Summary

Bond requires a **layered packaging strategy**, not a single universal packaging format.

The correct approach is:

- **Canonical core:** Python package (`pyproject.toml`)
- **Stage 1:** Local installation via `pipx`
- **Stage 2:** Platform-specific adapters (Linux, Windows, optional Android)
- **Integration layers:** Cinnamon applet, services, UI components (separate)

This ensures:
- Clean architecture
- No path pollution
- Future scalability across OSes
- No premature constraints

---

## Key Insight

There is a critical distinction:

- Python packaging = **application definition**
- OS installers = **distribution mechanism**

Trying to merge them early leads to architectural rigidity.

---

## Current Project Reality (Critical Observations)

The snapshot shows:

- Mixed modern + legacy structure
- `pyproject.toml` exists but is incomplete
- Hardcoded paths still present (`<legacy-runtime-root>/...`)
- Shell wrappers tied to repo layout
- systemd units pointing to absolute user paths
- No finalized UI or applet layer

### Implication

Packaging must **enforce structure cleanup**, not wrap existing chaos.

---

## Core Packaging Model

### Layer A — Canonical Core

Single source of truth:

- `pyproject.toml`
- dependencies
- metadata
- entry points
- internal modules (`src/bond/`)

This is:
- portable
- OS-agnostic (in logic, not installation)
- future-proof

---

### Layer B — Platform Adapters

Each OS requires its own delivery format.

| OS | Output |
|----|--------|
| Linux | wheel, optional `.deb` / `.rpm` |
| Windows | `.exe`, `.msi`, `MSIX` |
| Android | `.apk`, `.aab` |

Important:
- These wrap the core
- They are not interchangeable
- They impose runtime constraints

---

### Layer C — Integration

Separate modules:

- Cinnamon applet
- systemd user services
- desktop files
- icons
- OS-specific hooks

Must remain decoupled from core.

---

## Stage 1 — Temporary Packaging

### Objective

Stop:
- scattered execution
- path inconsistencies
- dependency leakage

### Solution

- Package as Python application
- Install via `pipx`

### Why pipx

- Isolated environments
- Clean uninstall/update
- Designed for CLI apps
- Minimal overhead

### Structural Impact

- Entry points replace shell scripts
- No direct repo execution
- Runtime paths normalized
- systemd units stop referencing dev paths

### Explicit Rejections

- No Flatpak
- No AppImage
- No binary freezing
- No `.deb`/`.rpm` yet

---

## Stage 2 — Stable Packaging

### Objective

- Multi-OS support
- Desktop integration
- Distribution readiness

### Critical Rule

Do NOT replace Python packaging. Build on top of it.

---

## Platform Analysis

## Linux

### Strengths

- Native Python support
- system-level access
- integration flexibility
- aligns with Bond design

### Strategy

- Core: Python package
- Optional:
  - `.deb` / `.rpm`
  - Cinnamon applet (separate)
  - systemd services

### Verdict

Primary target platform.

---

## Windows

### Constraints

- Users expect installers
- Python environment hidden
- different service model

### Strategy

- Bundle into executable
- Package as `.exe` / `.msi`

### Limitation

- Must build on Windows
- Integration differs from Linux

### Verdict

Supported via adapter, not equal architecture.

---

## Android

### Reality Check

This is NOT just another OS target.

### Constraints

- sandboxed environment
- limited system access
- strict lifecycle
- different execution model

### Requirements

- Gradle-based build
- APK/AAB packaging
- UI-driven interaction

### Architectural Conflict

Bond relies on:
- host inspection
- system-level awareness
- background execution

Android restricts all of these.

### Verdict

Separate product layer, not extension.

---

## Evaluation of Technologies

## Python Packaging

✔ Mandatory  
✔ Core definition  
✔ Cross-platform base  

---

## pipx

✔ Best Stage 1 solution  
✔ Clean and isolated  

---

## Flatpak

✔ Good for GUI apps  
✖ Breaks host interaction  

Not suitable for core.

---

## AppImage

✔ Portable  
✖ Weak integration  

Optional for future UI only.

---

## Native Linux Packages

✔ Good integration  
✖ Not cross-distro  

Optional convenience layer.

---

## Windows Installers

✔ Required for usability  

---

## Android Packaging

✔ Enables mobile version  
✖ Requires redesign  

---

## Critical Corrections

### Misconception: One package fits all OS

False.

You can share:
- code
- metadata

You cannot share:
- installer format
- runtime behavior
- permissions

---

### Misconception: Flatpak/AppImage solve portability

They solve distribution, not architecture.

---

### Misconception: Android is equivalent target

It is fundamentally different.

---

## Final Strategy

### Stage 1

- Python package
- pipx install
- fix structure

---

### Stage 2

Keep core unchanged.

Add adapters:

#### Linux
- wheel + optional `.deb` / `.rpm`
- Cinnamon applet (separate)

#### Windows
- bundled executable + installer

#### Android
- optional, separate architecture

---

## Decision Statement

Bond must:

- Use Python packaging as core
- Use pipx early
- Use native formats as adapters
- Separate integration layers
- Treat Android independently

---

## Bottom Line

This is not about packaging tools.

It is about enforcing a clean architecture:

Core → Adapters → Integration

If respected:
- scalable
- maintainable
- portable

If ignored:
- fragile
- inconsistent
- hard to evolve
