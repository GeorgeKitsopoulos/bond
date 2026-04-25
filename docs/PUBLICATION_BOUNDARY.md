# Publication Boundary

## Purpose

Bond is being prepared for a clean public release. This policy defines what belongs in a public repository and what must remain private/local so the project can be shared safely without losing important internal history.

## Public repository policy

The public repository should contain:

- portable source code
- portable examples and templates
- human-readable project documentation
- tests and CI configuration
- sanitized roadmap, state, and changelog records

The public repository must not contain:

- user-specific paths
- local runtime data
- private assistant memory
- private Gitea instance data
- secrets or credentials
- prompt or operator transcripts

## Private/local repository policy

The private/local repository may contain:

- local Gitea state
- private planning history
- machine-specific configuration
- runtime memory, logs, and state
- assistant/operator history
- temporary prompt drafts
- local-only archive material

## Git history policy

- The current private git history should not be pushed publicly as-is.
- The preferred public migration path is a fresh sanitized repository with a clean first public commit.
- If preserving history is ever required, a separate history scrub/rewrite review is mandatory.

## Documentation policy

- Public documentation must be written for human developers and users.
- Public documentation must not read like instructions to an assistant.
- Historical analysis should be preserved when useful, but marked as historical and prevented from overriding current documentation.
- Current truth must be maintained in a small, clearly-defined set of current documents.
- Internal prompt/operator workflow documents should remain private or be rewritten as normal contributor workflow documentation before publication.

## Configuration and runtime policy

- Actual local configuration files must remain ignored.
- Public configuration files must be examples/templates only.
- Runtime logs, memory, state, databases, caches, virtual environments, and generated outputs must not be published.
- Systemd and deploy examples must use portable placeholders or environment variables, not absolute user paths.

## Gitea and GitHub policy

- Local Gitea may remain private for planning and historical continuity.
- The public GitHub repository should be a clean public-facing project.
- Milestones and issues must be reconciled so repository documentation and tracker state do not contradict each other.

## Current known blockers before public release

- sanitize hardcoded paths in source/tests/deploy/docs
- consolidate public docs
- archive or merge historical analysis/reports safely
- remove public-facing Aider/Copilot/operator language
- reconcile Gitea milestones/issues with roadmap/state
- add or verify CI before public release