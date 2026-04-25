# Development

## Development principles

- small, reviewable changes
- keep behavior contracts intact
- update docs with behavior changes
- run validation before committing
- avoid local-path assumptions
- keep secrets and runtime data out of source control

## Repository boundaries

Repository-tracked content includes source code, examples, tests, and public documentation.

Repository-tracked content excludes local config files, memory/log/runtime state, virtual environments, databases, and private planning material.

## Change workflow

1. start from a clean working tree
2. understand current state
3. make bounded changes
4. run validation
5. review diff
6. update changelog and state docs when appropriate
7. commit with a clear message

## Validation commands

Run these checks before committing meaningful changes:

```bash
python3 -m compileall src/bond
python3 src/bond/ai_selftest.py
make reviewcheck
```

When documentation scope is significant, reviewcheck requires explicit environment declarations about documentation review and external context.

## Safety regression checks

Use these smoke checks when action/policy/parser behavior may have changed:

```bash
BOND_ACTION_DRY_RUN=1 python3 src/bond/ai_run.py "open downloads"
BOND_ACTION_DRY_RUN=1 python3 src/bond/ai_run.py "open downloads and then tell me what changed"; echo "MIXED_EXIT:$?"
BOND_ACTION_DRY_RUN=1 python3 src/bond/ai_run.py "notify me hello"; echo "NOTIFY_EXIT:$?"
python3 src/bond/ai_run.py "shutdown the computer"; echo "SHUTDOWN_EXIT:$?"
```

Expected behavior:

- dry-run succeeds without execution
- mixed chat/action request exits 4
- notification dry-run exits 0
- shutdown requires confirmation and exits 5

## Documentation updates

- README.md, ROADMAP.md, CHANGELOG.md, and docs/STATE.md should reflect current truth
- historical analysis should not override current docs
- planned features must be marked planned

## Public-safety checks

Run this scan when docs/source/deploy path behavior is touched:

```bash
grep -RInE '(/home/[^/]+|/m[n]t/|~/.+ai|AI[-]Archive|gk[-]pc|george[k])' \
  src/bond deploy README.md ROADMAP.md CHANGELOG.md docs \
  --exclude-dir=analysis \
  --exclude-dir=reports \
  2>/dev/null || true
```

Any hit must be reviewed and then removed, replaced with placeholders, or moved to private/historical material as appropriate.

## Commit discipline

- commit only intended files
- review staged diff before committing
- do not push until explicitly intended
- use clear, truthful commit messages
