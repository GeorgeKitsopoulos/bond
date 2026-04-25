# Bond Conventions

## Core rules

- source code lives in the repository
- mutable runtime state does not
- backups and archives do not go into git
- changes must be validated before commit
- routing must have one canonical config source
- live paths must not be hardcoded into tracked template files unless explicitly intended

## Change discipline

Before meaningful changes:
- inspect affected files
- prefer modifying existing structure over duplication

After meaningful changes:
- run compile validation
- run selftests
- record changelog entry if appropriate
