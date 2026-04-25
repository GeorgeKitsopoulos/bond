# Commit Message Guide

Commit messages must reflect the real scope of the change.

They must not hide documentation updates, behavior changes, or planning-boundary changes behind vague wording.

## Core rules

A good commit message should make it possible to understand:

- what changed
- whether the change affected implementation, documentation, or both
- whether the change introduced or updated repository process controls

## Preferred structure

Use a short subject line in the form:

`type: summary`

Examples of types:

- `docs`
- `feat`
- `fix`
- `refactor`
- `test`
- `chore`

## Subject-line rules

The subject line should be:

- specific
- truthful
- narrow
- consistent with actual diff scope

Avoid vague subjects such as:

- `update files`
- `misc cleanup`
- `improve project`
- `fix stuff`

## Documentation-aware examples

Examples:

- `docs: define repository and Gitea planning boundary`
- `docs: add review checklist and change review template`
- `chore: add repository-local review declaration gate`
- `docs: add Copilot session starter and operator wrapper`
- `test: document documentation-sync review requirements`

## Multi-scope honesty

If a change affects both code and documentation, the message should not pretend it was documentation-only.

If a change mainly adds process controls, the message should say so.

## Summary

A commit message is part of repository truth.
It should describe the real change, not just provide a label.
