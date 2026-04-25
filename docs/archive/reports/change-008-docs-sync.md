# Change 008 - Documentation Sync

> Historical note: this document is preserved for design rationale or implementation history. It is not the current source of truth. Use the current docs and code for present behavior, paths, and project status.

## Scope
- Edited files:
  - docs/TESTING.md
  - docs/INSTALLATION.md
  - docs/ARCHITECTURE.md
  - docs/DEVELOPMENT.md
  - project transcript.md
  - docs/reports/change-008-docs-sync.md
- No other files changed.

## Reason
- Documentation referenced outdated path/bootstrap issues and failing tests.
- System has reached a stable checkpoint with all selftests passing.
- Docs must reflect current state without hiding remaining weaknesses.

## Changes
- testing status updated
- installation expectations corrected
- architecture weaknesses split into current vs historical
- development workflow updated
- transcript checkpoint added

## Unchanged On Purpose
- runtime separation not implemented
- wrappers/install flow not fixed
- assistant behavior still imperfect
- memory ranking issues still present

## Expected Result
- docs reflect current system state accurately
- no misleading references to resolved issues
- future chats and contributors start from correct baseline

## Notes
- This is a sync step, not a redesign
- Historical issues preserved but marked as resolved
