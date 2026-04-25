# Change 007 - Clean Commit Checkpoint Record

> Historical note: this document is preserved for design rationale or implementation history. It is not the current source of truth. Use the current docs and code for present behavior, paths, and project status.

## Scope
- Record of actions performed for controlled cleanup and checkpoint commit preparation.
- No new implementation logic in this report.

## What Was Done

1. Updated ignore rules in .gitignore to protect runtime and local-only artifacts.
- Added runtime ignore entries:
  - memory/
  - state/
- Added local config ignore entry:
  - config/bond/assistant_config.json
- Added virtual env ignore entry:
  - .venv/
- Added explicit python bytecode ignore entry:
  - *.pyc

2. Cleaned staging area before selective staging.
- Command executed:
  - git restore --staged .

3. Inspected and classified working tree changes.
- Runtime/local config paths were excluded from commit scope.
- Expected code/report files were selected.
- Suspicious README diff was inspected.

4. Reverted README.md noise.
- README diff was large and outside the checkpoint scope, so it was reverted.
- Command executed:
  - git restore README.md

5. Staged only approved files.
- Staged source files:
  - src/bond/ai_core.py
  - src/bond/ai_run.py
  - src/bond/ai_selftest.py
  - src/bond/ai_action_parse.py
  - src/bond/ai_action_catalog.py
  - src/bond/ai_facts.py
- Staged config template:
  - config/bond/assistant_config.example.json
- Staged reports:
  - docs/reports/change-001-config-paths.md
  - docs/reports/change-002-ai-run-paths.md
  - docs/reports/change-003-runtime-separation-plan.md
  - docs/reports/change-004-ai-core-xdg-defaults.md
  - docs/reports/change-005-ai-selftest-alignment.md
  - docs/reports/change-006-assistant-config-target.md
  - docs/reports/path-bootstrap-analysis.md

6. Verified staged content before commit.
- Checked with:
  - git diff --cached --stat
- Confirmed no memory/, no state/, and no config/bond/assistant_config.json in staged set.

7. Created checkpoint commit.
- Command executed:
  - git commit -m "stabilize: bootstrap, path alignment, selftest alignment, assistant config target fix"
- Commit created:
  - c35f3056c310199ba2e05821a04182e85c9a43e6
- Commit summary:
  - 14 files changed, 680 insertions, 46 deletions
  - 7 new files under docs/reports/

8. Verified post-commit working tree.
- Remaining unstaged items were outside the commit scope:
  - .gitignore
  - src/bond/ai_action_policy.py
  - src/bond/ai_intent.py
  - src/bond/ai_linguistics.py
  - src/bond/ai_memory_query.py
  - docs/ARCHITECTURE.md
  - docs/DEVELOPMENT.md
  - docs/INSTALLATION.md
  - docs/TESTING.md

## Commit Captured
- Commit: c35f3056c310199ba2e05821a04182e85c9a43e6
- Message: stabilize: bootstrap, path alignment, selftest alignment, assistant config target fix
- Branch at time of commit: main

## Notes
- Runtime data and local config were intentionally excluded from the commit.
- No push was performed.
