# Capability Registry

This document is the canonical capability truth source for Bond.
It defines what Bond can do, how it is classified, and what policy and adaptation rules apply.

See `docs/ARCHITECTURE.md` for the registry concept and schema definition.
See `docs/archive/analysis/Bond_Capability_Expansion_Plan.md` for the full expansion design authority.

## Capability doctrine

Bond should expose capabilities in this order of preference:

1. deterministic and read-only
2. deterministic and rootless with explicit user intent
3. rootless interactive handoff through standard platform APIs
4. rootless write actions with confirmation
5. privileged actions only in a distinct, explicit lane

Privilege escalation is never implicit. Rootless-first is both a safety posture and a portability posture.

## Capability classes

- **inspector**: read-only, rootless, deterministic fact-gathering. No side effects.
- **handoff**: rootless delegation to a platform handler (e.g. `xdg-open`, portal). Minimal Bond-owned side effects.
- **bounded_mutator**: rootless write action within a clearly scoped target, requires confirmation.
- **privileged_lane**: must route through the explicit privileged execution lane. Requires policy gate approval and confirmation.

## Registry schema

Each capability entry uses these fields:

- `name`: stable capability identifier.
- `class`: one of `inspector`, `handoff`, `bounded_mutator`, `privileged_lane`.
- `status`: one of `available`, `partial`, `planned`, `blocked`, `unsupported`.
- `execution_mode`: how the capability runs (`deterministic_probe`, `guarded_action`, `handoff`, `none`).
- `risk_level`: baseline risk classification (`low`, `medium`, `high`, `n/a`).
- `read_only`: whether the capability mutates any state.
- `rootless`: whether the capability can run without privilege escalation.
- `side_effects`: observable side effects outside the immediate operation scope.
- `requires_confirmation`: baseline confirmation requirement.
- `interactive`: whether the capability requires active user interaction during execution.
- `needs_gui_session`: whether a GUI/display session is required.
- `needs_network`: whether network access is required.
- `needs_elevated_lane`: whether the capability must route through the privileged execution lane.
- `backends`: platform-to-adapter map for this capability.
- `degraded_modes`: degraded but still usable paths when preferred backends are unavailable.
- `result_schema`: typed result schema returned on success.
- `error_schema`: typed error schema returned on failure.
- `audit_tag`: tag for audit/log hooks when executed.
- `required_tools`: deterministic tools/probes required for reliable operation.
- `notes`: free-form clarification.

## Capability entries

Existing entries use the legacy compact schema. New entries should use the full schema above.
All entries may be extended with full-schema fields incrementally without breaking existing policy logic.

Route names in `config/router/profiles.json` are dispatch targets, not capability assertions.

Current documented baseline roster for capability planning: qwen2.5:3b-instruct, gemma2:2b, qwen2.5:7b-instruct, and nomic-embed-text:latest. `qwen2.5:7b-instruct` is the highest-capability local baseline currently assumed. No current heavyweight local model tier is part of the default capability plan.

---

Initial capabilities:

- name: open_known_target
  status: partial
  execution_mode: guarded_action
  risk_level: low
  notes: Open actions for known targets only.

- name: open_explicit_path
  status: partial
  execution_mode: guarded_action
  risk_level: medium
  notes: Path-based open action with policy checks.

- name: query_shell
  status: partial
  execution_mode: deterministic_probe
  risk_level: medium
  notes: Query-only shell information through probe wrappers.

- name: query_directory
  status: partial
  execution_mode: deterministic_probe
  risk_level: low
  notes: Directory state query without arbitrary execution.

- name: query_model
  status: partial
  execution_mode: deterministic_probe
  risk_level: low
  required_tools: [route_config_probe, model_inventory_probe, model_runtime_probe]
  notes: Model/runtime identity query must distinguish configured route targets, installed local model inventory, and runtime reachability. Route names and configured model strings are not installation proof and not runtime-health proof. Current documented baseline roster is qwen2.5:3b-instruct, gemma2:2b, qwen2.5:7b-instruct, and nomic-embed-text:latest; qwen2.5:7b-instruct is the highest-capability local baseline currently assumed. No current heavyweight local model tier should be assumed; capability design should compensate through structure, decomposition, retrieval, validation, and tighter contracts rather than hidden model-size assumptions.

- name: timer
  status: unsupported
  execution_mode: none
  risk_level: n/a
  notes: Not implemented in current phase.

- name: clipboard
  status: unsupported
  execution_mode: none
  risk_level: n/a
  notes: Not implemented in current phase.

- name: describe_capabilities
  class: inspector
  status: planned
  execution_mode: deterministic_probe
  risk_level: low
  read_only: true
  notes: answers what Bond can do from capability registry, not model improvisation.

- name: describe_context_capabilities
  class: inspector
  status: planned
  execution_mode: deterministic_probe
  risk_level: low
  read_only: true
  notes: answers what Bond can do in the current environment/session using registry plus probes.

- name: preview_action
  class: inspector
  status: planned
  execution_mode: deterministic_probe
  risk_level: low
  read_only: true
  notes: previews target, side effects, reversibility, confirmation requirement, policy reason code.

- name: explain_decision
  class: inspector
  status: planned
  execution_mode: deterministic_probe
  risk_level: low
  read_only: true
  notes: exposes high-level path/source/reason metadata, not hidden chain-of-thought.

- name: register_plugin_capability
  class: privileged_lane
  status: planned
  execution_mode: guarded_action
  risk_level: high
  read_only: false
  notes: future extension registration path; must not bypass policy or registry validation.

- name: resolve_invocation_alias
  class: inspector
  status: partial
  execution_mode: deterministic_probe
  risk_level: low
  read_only: true
  notes: support capability for invocation alias matching across English/Greek/mixed forms; does not imply full Greek support today.

- name: detect_utterance_language
  class: inspector
  status: partial
  execution_mode: deterministic_probe
  risk_level: low
  read_only: true
  notes: support capability for utterance language classification (`el`/`en`/`mixed`/`unknown`); not user-facing magic and not full bilingual correctness yet.

- name: apply_response_language_policy
  class: inspector
  status: planned
  execution_mode: deterministic_probe
  risk_level: low
  read_only: true
  notes: support capability for response language continuity/policy; does not imply complete localization support today.

- name: localize_user_message
  class: inspector
  status: planned
  execution_mode: deterministic_probe
  risk_level: low
  read_only: true
  notes: support capability for future UI/user-message localization via message catalogs; must not imply full Greek/UI localization today.

---

## System maintenance and health capabilities

These entries define planned local system-maintenance capabilities. None are currently implemented. They exist so future work can be planned without letting the model claim unsupported power.

These capabilities must follow the same doctrine as every other Bond capability:

- read-only inspection first
- recommendation before mutation
- dry-run before execution
- no silent privileged action
- no automatic deletion
- no automatic system upgrade
- GUI surfaces may display or request actions, but may not bypass policy

- name: inspect_package_update_status
  class: inspector
  status: planned
  execution_mode: deterministic_probe
  risk_level: low
  read_only: true
  rootless: true
  side_effects: []
  requires_confirmation: false
  interactive: false
  needs_gui_session: false
  needs_network: true
  needs_elevated_lane: false
  backends:
    linux:
      - apt_update_probe
      - snap_refresh_probe
      - flatpak_update_probe
  degraded_modes:
    - report unavailable package surfaces explicitly
    - separate stale cache state from no-updates state
  result_schema: package_update_status_result
  error_schema: standard_error
  audit_tag: inspect_package_update_status
  required_tools:
    - apt
    - snap
    - flatpak
  notes: >
    Planned read-only inspection of available package updates. Must distinguish repository metadata
    freshness, available updates, held packages, security updates when safely knowable, and package
    manager errors. This is not permission to apply updates.

- name: plan_safe_system_update
  class: inspector
  status: planned
  execution_mode: deterministic_probe
  risk_level: medium
  read_only: true
  rootless: true
  side_effects: []
  requires_confirmation: false
  interactive: false
  needs_gui_session: false
  needs_network: true
  needs_elevated_lane: false
  backends:
    linux:
      - apt_simulation_probe
      - snap_refresh_plan_probe
      - flatpak_update_plan_probe
  degraded_modes:
    - provide partial plan per available package surface
    - mark unknown package-manager state as degraded rather than guessing
  result_schema: system_update_plan_result
  error_schema: standard_error
  audit_tag: plan_safe_system_update
  required_tools:
    - apt
    - snap
    - flatpak
  notes: >
    Planned dry-run style update planner. It should report what would change, what needs privilege,
    whether a reboot may be required, and what validation should run afterwards. It must not perform
    the update.

- name: apply_privileged_system_updates
  class: privileged_lane
  status: planned
  execution_mode: guarded_action
  risk_level: high
  read_only: false
  rootless: false
  side_effects:
    - modifies installed system packages
    - may restart services
    - may require reboot
    - may change package-manager state
  requires_confirmation: true
  interactive: true
  needs_gui_session: false
  needs_network: true
  needs_elevated_lane: true
  backends:
    linux:
      - privileged_update_adapter
  degraded_modes: []
  result_schema: privileged_update_result
  error_schema: standard_error
  audit_tag: apply_privileged_system_updates
  required_tools:
    - policy_gate
    - confirmation_token
    - privileged_lane
    - rollback_snapshot
    - post_update_validation
  notes: >
    Planned future privileged capability only. Must not exist until the privileged execution lane,
    confirmation flow, audit logging, snapshot/rollback expectations, and post-update validation are
    implemented. Bond must never silently run system upgrades.

- name: inspect_storage_hygiene
  class: inspector
  status: planned
  execution_mode: deterministic_probe
  risk_level: low
  read_only: true
  rootless: true
  side_effects: []
  requires_confirmation: false
  interactive: false
  needs_gui_session: false
  needs_network: false
  needs_elevated_lane: false
  backends:
    linux:
      - trash_size_probe
      - cache_size_probe
      - large_file_probe
      - duplicate_candidate_probe
  degraded_modes:
    - skip unreadable paths and report them
    - report duplicate candidates by evidence level rather than deleting anything
  result_schema: storage_hygiene_result
  error_schema: standard_error
  audit_tag: inspect_storage_hygiene
  required_tools:
    - filesystem_probe
  notes: >
    Planned read-only report for Trash size, cache growth, large files, and duplicate-file candidates.
    Duplicate detection must be conservative: size/name/path similarity may produce candidates, while
    hash-confirmed matches may produce stronger evidence. No deletion is allowed by this capability.

- name: inspect_boot_and_service_health
  class: inspector
  status: planned
  execution_mode: deterministic_probe
  risk_level: low
  read_only: true
  rootless: true
  side_effects: []
  requires_confirmation: false
  interactive: false
  needs_gui_session: false
  needs_network: false
  needs_elevated_lane: false
  backends:
    linux:
      - systemd_failed_units_probe
      - systemd_analyze_blame_probe
      - journal_warning_summary_probe
  degraded_modes:
    - report missing systemd tools explicitly
    - summarize inaccessible journal data as permission-limited
  result_schema: boot_service_health_result
  error_schema: standard_error
  audit_tag: inspect_boot_and_service_health
  required_tools:
    - systemctl
    - systemd-analyze
    - journalctl
  notes: >
    Planned read-only service and boot health inspection. The assistant may summarize failed units,
    slow boot contributors, and warning patterns, but must not restart, disable, enable, mask, or edit
    services from this capability.

- name: generate_periodic_health_report
  class: inspector
  status: planned
  execution_mode: deterministic_probe
  risk_level: low
  read_only: true
  rootless: true
  side_effects:
    - writes a local report artifact when enabled
  requires_confirmation: false
  interactive: false
  needs_gui_session: false
  needs_network: false
  needs_elevated_lane: false
  backends:
    linux:
      - maintenance_report_builder
  degraded_modes:
    - generate partial report when one probe family fails
    - mark missing probe sections as degraded
  result_schema: periodic_health_report_result
  error_schema: standard_error
  audit_tag: generate_periodic_health_report
  required_tools:
    - inspect_package_update_status
    - inspect_storage_hygiene
    - inspect_boot_and_service_health
  notes: >
    Planned monthly or user-requested local report that recommends actions. It should separate facts,
    recommendations, risk, required permission level, and suggested validation. It must not perform
    cleanup or updates by itself.

- name: present_maintenance_dashboard
  class: handoff
  status: planned
  execution_mode: handoff
  risk_level: low
  read_only: true
  rootless: true
  side_effects:
    - displays local report state
    - may submit explicit user requests back to core
  requires_confirmation: false
  interactive: true
  needs_gui_session: true
  needs_network: false
  needs_elevated_lane: false
  backends:
    linux:
      - cinnamon_applet_dashboard
      - local_gui_dashboard
  degraded_modes:
    - CLI report output when GUI session is unavailable
  result_schema: maintenance_dashboard_result
  error_schema: standard_error
  audit_tag: present_maintenance_dashboard
  required_tools:
    - service_health_endpoint
    - report_store
  notes: >
    Planned GUI-facing presentation capability. The dashboard may display update plans, storage
    warnings, duplicate candidates, Trash size, failed services, boot-delay contributors, and monthly
    recommendations. It must not duplicate parser, policy, memory, probes, or execution logic.

---

## Document knowledge capabilities

These entries cover the planned document knowledge ingestion and retrieval layer. None are currently implemented. They are defined here so that policy routing, capability truth, and testing can reference stable names when implementation begins.

These are document-knowledge capabilities. They are not voice or UI multimodal features. Multimodal here refers specifically to document modalities such as PDFs, scanned images, and screenshots handled during ingestion.

- name: inspect_document_corpus_status
  class: inspector
  status: planned
  execution_mode: deterministic_probe
  risk_level: low
  read_only: true
  rootless: true
  side_effects: []
  requires_confirmation: false
  interactive: false
  needs_gui_session: false
  needs_network: false
  needs_elevated_lane: false
  backends: {}
  degraded_modes: []
  result_schema: document_corpus_status_result
  error_schema: standard_error
  audit_tag: inspect_document_corpus_status
  required_tools: []
  notes: >
    Reports the current state of the local document knowledge corpus: number of indexed documents,
    index freshness, any quarantined files, and overall retrieval readiness. Read-only probe.
    Not implemented in current phase.

- name: retrieve_document_knowledge
  class: inspector
  status: planned
  execution_mode: deterministic_probe
  risk_level: low
  read_only: true
  rootless: true
  side_effects: []
  requires_confirmation: false
  interactive: false
  needs_gui_session: false
  needs_network: false
  needs_elevated_lane: false
  backends: {}
  degraded_modes: []
  result_schema: document_retrieval_result
  error_schema: standard_error
  audit_tag: retrieve_document_knowledge
  required_tools: []
  notes: >
    Semantic or hybrid retrieval over ingested document knowledge. Returns ranked, source-grounded
    chunks with provenance metadata including source file, extraction method, ingestion timestamp,
    file hash, modality, and confidence. This is retrieval and search over Bond's own ingested
    document knowledge store — it is not generic shell memory lookup, not a web search, and not a
    durable fact query. Not implemented in current phase.

- name: ingest_knowledge_sources
  class: bounded_mutator
  status: planned
  execution_mode: guarded_action
  risk_level: low
  read_only: false
  rootless: true
  side_effects:
    - writes parsed content and chunk embeddings to local knowledge store
    - updates metadata index and embedding index
  requires_confirmation: false
  interactive: false
  needs_gui_session: false
  needs_network: false
  needs_elevated_lane: false
  backends: {}
  degraded_modes: []
  result_schema: ingestion_result
  error_schema: standard_error
  audit_tag: ingest_knowledge_sources
  required_tools: []
  notes: >
    Controlled ingestion of local files into Bond's own document knowledge structures: file
    classification, parsing by modality, normalization, chunking, embedding, and indexing with
    provenance. This means ingestion into Bond's local knowledge store for later retrieval — it is
    not arbitrary model training, not fine-tuning, and not adapter modification. Dropped files
    default to ingestion and retrieval with provenance, not automatic model training. Not
    implemented in current phase.

- name: reindex_document_corpus
  class: bounded_mutator
  status: planned
  execution_mode: guarded_action
  risk_level: low
  read_only: false
  rootless: true
  side_effects:
    - updates or replaces stale chunk embeddings and metadata records for changed source files
    - removes orphaned chunks when source files are deleted
  requires_confirmation: false
  interactive: false
  needs_gui_session: false
  needs_network: false
  needs_elevated_lane: false
  backends: {}
  degraded_modes: []
  result_schema: reindex_result
  error_schema: standard_error
  audit_tag: reindex_document_corpus
  required_tools: []
  notes: >
    Hash-based change detection over the local knowledge folder, incremental reindexing of modified
    source files, supersession of prior chunk sets, deletion propagation when source files are
    removed, and stale-chunk prevention. Prior chunk set versions are retained in metadata for
    provenance history. Active retrieval serves only the current chunk set after a successful
    reindex. Not implemented in current phase.

---

## Result and error schema

Capabilities that return structured results should conform to the `Execution Result Schema` defined in `docs/ARCHITECTURE.md`.

Capabilities classified as `inspector` return read-only structured data with no `artifact_paths` entries.
Capabilities classified as `handoff` may return empty `stdout`/`stderr` when delegation is fire-and-forget.
Capabilities classified as `privileged_lane` must populate `audit_tag` in every result.

## Analysis references

- Routing and dispatch design: `docs/archive/analysis/Bond_Router_Agent_Redesign_Updated.md`
- Capability expansion design: `docs/archive/analysis/Bond_Capability_Expansion_Plan.md`
- Architecture registry concept: `docs/ARCHITECTURE.md` — `## Capability Registry Concept`
- Master plan capability direction: `docs/BOND_PROJECT_MASTER_PLAN.md` — `## Workstream F`
- Document knowledge ingestion design: `docs/KNOWLEDGE_INGESTION.md`
- Memory system specification: `docs/MEMORY.md`

---

Rule:

Assistant must NEVER claim unsupported capability.
Route names in `config/router/profiles.json` are dispatch targets, not capability assertions.
