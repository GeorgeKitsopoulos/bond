# Current Paths

## Purpose

This document describes Bond path resolution and runtime storage without assuming a specific machine layout.

## Repository root

The repository root is discovered by wrappers or set explicitly with BOND_ROOT.

Examples in this document use the placeholder <repo>.

## Configuration

- example config file: config/bond/assistant_config.example.json
- local configuration files are ignored and are not public source artifacts
- BOND_CONFIG_PATH may override the active config file location

## Runtime storage

Runtime roots follow a platform and XDG-style model for config, data, state, and cache locations.

Use these placeholders when documenting runtime paths:

- <config-home>
- <data-home>
- <state-home>
- <cache-home>

Environment overrides may redirect these roots. Memory, logs, state payloads, and other runtime artifacts are operational data and are not public source files.

## URI-style paths

Bond supports URI-style path references for portability:

- repo://
- config://
- data://
- state://
- cache://

These references should resolve to the active repository/runtime path model instead of hardcoded machine paths.

## Archive root

Archive root is optional.

- it may be set by environment or configuration
- it should not point to a hardcoded public path
- source code and public docs must not assume a fixed archive location

Use <archive-root> in documentation examples when archive behavior is relevant.

## Public release rule

Public documentation and deploy examples must use placeholders or environment variables.

Real local paths belong only in ignored local configuration and private runtime context.
