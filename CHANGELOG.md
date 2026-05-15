# Changelog

This file records meaningful repository-level changes to Bond.

It is intended to track project evolution in a form suitable for maintainers, future contributors, LLM-assisted development workflows, and later release/version discipline.

This changelog does not attempt to preserve every chat detail, temporary experiment, or live-system observation. Those belong in commit history, focused docs, issue tracking, testing artifacts, or archived transcript material as appropriate.

## Format and discipline

Until formal release tagging is established, this changelog should follow these rules:

- keep an `Unreleased` section at the top
- record only meaningful repository changes
- prefer concise entries tied to actual repo evolution
- avoid mixing future plans into completed change entries
- avoid logging speculative work as if it were done
- keep operational transcript detail out of this file unless it materially changed the repository
- treat git history as the lower-level ground truth and this file as the maintainers’ curated summary

## Unreleased

### Stage 2G-F-I disabled user-space install write-executor skeleton

- Adds `ai_user_install_write_executor.py`.
- Adds `user_install_write_executor` probe.
- Defines a deterministic disabled/default-deny user-space install write-executor skeleton.
- Composes the Stage 2G-F-H approval-validation output into `executor_disabled_packet` and `executor_json_preview` outputs.
- Does not collect approval, validate approval as true, authorize execution, authorize writes, create directories, write manifests, install packages, mutate services, move storage, generate commands, or execute commands.
- Adds 9 selftests.
- Final integrated selftest JSON summary: {"ok": true, "passed": 387, "failed": 0, "total": 387}.

### Stage 2G-F-H user-space install approval-validation contract

- Adds `ai_user_install_approval_validation.py`.
- Adds `user_install_approval_validation` probe.
- Defines a deterministic non-executing user-space install approval-validation contract and challenge.
- Composes the Stage 2G-F-G write-preflight packet into `approval_challenge` and `approval_challenge_json_preview` outputs.
- Does not collect approval, validate approval as true, authorize execution, authorize writes, create directories, write manifests, install packages, mutate services, move storage, generate commands, or execute commands.
- Adds 9 selftests.
- Final integrated selftest JSON summary: {"ok": true, "passed": 378, "failed": 0, "total": 378}.

### Stage 2G-F-G user-space install write-preflight contract

- Adds `ai_user_install_write_preflight.py`.
- Adds `user_install_write_preflight` probe.
- Defines a deterministic non-executing user-space install write-preflight packet.
- Composes the Stage 2G-F-F review/report packet into `write_preflight_packet` and `write_preflight_json_preview` outputs.
- Uses lexical path checks only and does not inspect the real filesystem.
- Does not validate approval, authorize execution, create directories, write manifests, install packages, mutate services, move storage, generate commands, or execute commands.
- Adds 9 selftests.
- Final integrated selftest JSON summary: {"ok": true, "passed": 369, "failed": 0, "total": 369}.

### Stage 2G-F-F user-space install review/report contract

- Adds `ai_user_install_review.py`.
- Adds `user_install_review_report` probe.
- Defines a deterministic non-executing human-facing user-space install review/report packet.
- Composes the Stage 2G-F-E execution gate into `human_review_packet` and `review_json_preview` outputs.
- Does not validate approval, authorize execution, create directories, write manifests, install packages, mutate services, move storage, generate commands, or execute commands.
- Adds 9 selftests.
- Final integrated selftest JSON summary: {"ok": true, "passed": 360, "failed": 0, "total": 360}.

### Stage 2G-F-E user-space install execution-gate/readiness decision

- Adds `ai_user_install_execution_gate.py`.
- Adds `user_install_execution_gate` probe.
- Defines `gate_decision` and `gate_json_preview` for future user-space install execution readiness review.
- Computes deterministic `approval_envelope_digest` from `approval_json_preview`.
- Validates manifest path and transaction digest consistency from approval-envelope inputs.
- `execution_allowed` remains False.
- `approval_validated` remains False.
- `future_approval_mechanism_available` remains False.
- All authorization fields remain False.
- No commands generated.
- No approval validated, approval granted, directory creation, manifest write, package operation, service mutation, storage move, or command execution.
- Adds 8 selftests.
- Final integrated selftest JSON summary: {"ok": true, "passed": 351, "failed": 0, "total": 351}.

### Stage 2G-F-D user-space install approval envelope contract

- Adds `ai_user_install_approval.py`.
- Adds `user_install_approval_plan` probe.
- Defines `approval_candidate` and `approval_json_preview` for future user-space install transaction review.
- Computes deterministic `transaction_digest` from `transaction_json_preview`.
- Defines approval requirements that must match transaction digest, manifest path, and operation count.
- `approval_granted` remains False.
- All authorization fields remain False.
- No commands generated.
- No approval granted, directory creation, manifest write, package operation, service mutation, storage move, or command execution.
- Adds 8 selftests.
- Final integrated selftest JSON summary: {"ok": true, "passed": 343, "failed": 0, "total": 343}.

### Stage 2G-F-C user-space install transaction/preflight plan

- Adds `ai_user_install_transaction.py`.
- Adds `user_install_transaction_plan` probe.
- Composes `user_install_plan` and `user_install_manifest_plan` into a deterministic `transaction_candidate` and `transaction_json_preview`.
- Defines ordered future operation candidates for preflight, directory candidates, manifest write candidate, and post-install verification.
- Validates manifest-path and write-set-summary consistency between upstream plans.
- All authorization fields remain False.
- No commands generated.
- No directory creation, manifest write, package operation, service mutation, storage move, or command execution.
- Adds 8 selftests.
- Final integrated selftest JSON summary: {"ok": true, "passed": 335, "failed": 0, "total": 335}.

### Stage 2G-F-B1 manifest package-manager fact preservation

- Preserves factual host `package_manager` values such as `rpm-ostree` in `manifest_candidate` and `manifest_json_preview`.
- Narrows no-command tests so factual package-manager names are allowed as data but executable command phrases remain forbidden.
- Adds 2 selftests.
- Final integrated selftest JSON summary: {"ok": true, "passed": 327, "failed": 0, "total": 327}.
- No installer execution, directory creation, manifest write, package operation, service mutation, storage move, command generation, or command execution was added.

### Stage 2G-F-B user-space install manifest payload contract

- Adds `ai_user_install_manifest.py` as a pure deterministic, non-executing user-space install manifest payload planning contract.
- Adds `user_install_manifest_plan` as a read-only probe that composes user-space write-set and read-only profile facts into a bounded manifest payload review plan.
- Defines sanitized `manifest_candidate` and deterministic `manifest_json_preview` for future user-space installer review.
- All authorization fields remain explicitly False.
- No commands are generated.
- No directory creation, manifest write, package operation, service mutation, storage move, or command execution is performed.
- Adds 8 selftests for Stage 2G-F-B contract coverage.
- Final integrated selftest JSON summary: {"ok": true, "passed": 325, "failed": 0, "total": 325}.

### Stage 2G-F-A user-space install write-set contract

- Adds `ai_user_install_plan.py` as a pure deterministic, non-executing user-space install write-set planning contract.
- Adds `user_install_plan` as a read-only probe that composes installer/storage facts into a bounded user-space write-set review plan.
- Defines deterministic `target_layout` and `write_set` structures for future user-space installer review.
- All authorization fields remain explicitly False.
- No commands are generated.
- No directory creation, manifest write, package operation, service mutation, storage move, or command execution is performed.
- Adds 8 selftests for Stage 2G-F-A contract coverage.
- Final integrated selftest JSON summary: {"ok": true, "passed": 317, "failed": 0, "total": 317}.

### Stage 2G-E read-only installer planning contract

- Adds a read-only installer planning contract composing Stage 2G profile, drift, and dependency facts into a bounded installer plan.
- Adds `ai_installer_plan.py` as a pure deterministic builder that composes host profile, storage profile, install manifest drift, and dependency plan into a plan structure.
- Adds `installer_plan` as a read-only probe that generates bounded installer plans from Stage 2G read-only facts.
- Defines plan readiness statuses: ready_for_human_review (plan complete, no manual review needed); manual_review_required (plan complete but manual review required); blocked_missing_inputs (profile facts incomplete); unsupported_manual_review (unsupported configurations detected).
- Defines deterministic next-step recommendations: review_installer_plan (for ready status); manual_installer_review (for manual-review status); collect_missing_profile_facts (for blocked status); manual_platform_review (for unsupported status).
- Defines plan steps: collect_host_profile, collect_storage_profile, review_install_manifest_drift, review_dependency_plan, review_storage_locations, review_service_strategy, final_human_approval.
- Omits sensitive fields (hostname, username, email, token, password, secret, api_key, machine_id) from plan output to prevent credential leakage.
- All authorization fields (execution_authorized, install_authorized, upgrade_authorized, reconfigure_authorized, service_authorized, write_plan_authorized, write_manifest_authorized) are explicitly False; no commands are generated; no package managers, services, storage, or installers are called.
- Adds 7 selftests covering plan shape/boundaries, missing-inputs blocking, dependency-manual-review propagation, critical-drift-manual-review triggering, sensitive-field exclusion, non-executing format output, and probe read-only shape.
- Final integrated selftest JSON summary: {"ok": true, "passed": 309, "failed": 0, "total": 309}.

### Stage 2G-D package-manager classification and dependency planning contract

- Adds a read-only package-manager strategy classification and dependency planning contract for future installer/updater/satellite planning.
- Adds `ai_package_manager.py` as a pure deterministic classifier for package manager strategies (mutable, immutable, unknown) based on package manager, OS family, distro signals, and immutability hints.
- Adds `ai_dependency_plan.py` as a pure deterministic planner that maps requested capabilities to package manager-specific package names without authorizing installation or execution.
- Adds `dependency_plan` as a read-only probe that combines host portability facts and observed tools to generate deterministic dependency plans.
- Covers 8 package managers: apt, dnf, zypper, apk, xbps, nix, brew (mutable strategies); rpm-ostree (immutable user-space preferred); pacman (mutable or user-space depending on Steam Deck/immutable hints); and unknown (requires manual review).
- Supports 5 bounded capabilities: core_python_runtime, git_source_checkout, selftest_validation, local_llm_runtime_optional, container_user_space_optional.
- Classifies capability status as: observed_available (tool already present), plan_needed (unsupported package manager prevents automatic planning), manual_review_needed (unknown manager), optional_not_required (optional capability without tools).
- Classifies capability status as: observed_available (tool already present), plan_needed (supported mutable manager and capability absent), manual_review_needed (unsupported, unknown, immutable, Steam Deck-like, or otherwise manual-review-required manager), optional_not_required (optional capability without tools).
- All authorization fields (execution_authorized, install_authorized, etc.) are explicitly False; no commands are generated; no package managers are called.
- Adds 8 selftests covering package strategy classification for apt/mutable, rpm-ostree/immutable, pacman/Steam-Deck, unknown managers, dependency plan shape, observed-tools integration, optional-LLM non-claiming, and probe read-only boundaries.

### Stage 2G-D forward-fix: harden dependency planning classification

- Hardens `ai_package_manager.py` to correctly resolve `distro_like` from `host_profile` when no direct `distro_like` argument is passed; previously the host_profile-provided value was silently ignored during normalization.
- Hardens `ai_dependency_plan.py` so that rpm-ostree, immutable, Steam Deck-like, and unknown package manager strategies do not present rpm-ostree host package names as a normal package install path; `package_names_by_manager` is empty for unobserved items under those strategies.
- Required core capabilities (core_python_runtime, git_source_checkout, selftest_validation) now produce `manual_review_needed` status for immutable/rpm-ostree/unknown strategies unless the tool is explicitly observed available.
- Fixes `recommended_next_step_kind` aggregation: if any plan item is `manual_review_needed` the top-level result is `manual_dependency_review`; else if any item is `plan_needed` the result is `review_dependency_plan`; else `none`. The previous logic allowed "all core tools observed" to suppress manual-review items.
- No execution behavior added. No package managers called. No commands generated. All authorization fields remain False.
- Adds 4 regression selftests for the above corrections; selftest baseline at this checkpoint advanced to 300 passing tests (superseded by Stage 2G-D second forward-fix below).

### Stage 2G-D forward-fix: align dependency plan manual-review status aggregation

- Aligns `ai_dependency_plan.py` so that item-level manual review cannot be hidden behind a `plan_needed` status: if a plan item requires manual review, its status is now `manual_review_needed`, not `plan_needed`.
- Specifically, `container_user_space_optional` on rpm-ostree, immutable, and Steam Deck-like strategies now returns `manual_review_needed` rather than `plan_needed`.
- Hardens top-level `recommended_next_step_kind` aggregation to consult item-level `requires_manual_review` in addition to item status, ensuring `manual_dependency_review` is returned whenever any item carries `requires_manual_review: true`.
- `package_names_by_manager` remains empty for manual-review items. No command strings generated. No execution behavior added. All authorization fields remain False.
- Adds 2 regression selftests (`stage2g_d_dependency_plan_manual_review_items_not_plan_needed`, `stage2g_d_dependency_plan_item_requires_review_drives_top_level_review`); selftest baseline is now 302 tests passing (superseded by Stage 2G-E baseline of 309 passing tests).

### Stage 2G-C install manifest drift detection

- Adds a read-only install manifest and drift detection contract for future installer/updater/satellite planning.
- Adds `ai_install_manifest.py` as a pure in-memory manifest builder, bounded drift comparator, and formatter.
- Adds `install_manifest_drift` as a read-only probe that defaults to missing-saved-manifest/manual-review output because persistence is not implemented in this stage.
- Does not write manifests, perform reconfiguration, install packages, update services, or mutate storage.
- Final integrated selftest JSON summary: {"ok": true, "passed": 288, "failed": 0, "total": 288}.

### Stage 2G-B storage portability profile

- Continues the portable installer/updater/satellite track with a read-only storage portability profile.
- Detects mount candidates, external media paths, Steam Deck SD-card-like paths, home fallback, disk free-space pressure, Bond environment path observations, and bounded storage placement recommendations.
- Adds `storage_portability_profile` as a read-only probe for future installer/updater/satellite planning.
- Adds Stage 2G-B selftests for mount parsing, SD/external candidate detection, home fallback, environment-path observation, contract boundaries, and probe registration/scope checks.
- Hardens Stage 2G-B storage classification with conservative SD/external detection, clean `/proc/mounts` option parsing, explicit Bond env-path precedence by role, read-only derivation from mount options, deepest home-mount selection, and low-space external manual-review behavior.
- Does not create directories, move data, delete data, clean caches, mount or unmount, format or partition, authorize execution, start automation, write manifests, run an updater, or broaden normal assistant answers.
- The original Stage 2G-B-only checkpoint is preserved in commit history; current unreleased validation is represented by the newer Stage 2G-C baseline above.

### Stage 2G-A host portability profile

- Starts the portable installer/updater/satellite track with a read-only host portability profile.
- Adds conservative host portability detection for distro-family, package-manager/tool availability, atomic/image-based signals, Bazzite/SteamOS/Steam Deck-like signals, service-backend hints, and bounded dependency strategy.
- Adds `host_portability_profile` as a read-only probe for future installer/updater/satellite planning.
- Adds Stage 2G-A selftests for parser behavior, host signal detection, strategy boundaries, contract boundaries, and probe registration/scope checks.
- This stage does not install packages, update the system, layer packages, mutate services, authorize execution, start automation, write manifests, run an updater, or broaden normal assistant answers.
- Final integrated selftest JSON summary: {"ok": true, "passed": 268, "failed": 0, "total": 268}.

### Stage 2F-F-E maintenance report readiness metadata

- Added metadata-only readiness fields to the explicit maintenance/readiness report contract.
- The metadata is derived from existing probe validation and the existing non-executing maintenance plan.
- The maintenance probe scope remains limited to `package_update_status`, `storage_hygiene`, and `boot_service_health`.
- Added selftest coverage for readiness metadata shape, limited-signal behavior, formatter markers, and source/documentation boundaries.
- No probes, aliases, routes, actions, execution authority, service mutation, dashboards, scheduling, automation, privileged execution, or broad normal-answer probe backing were added.
- Final integrated selftest JSON summary: {"ok": true, "passed": 262, "failed": 0, "total": 262}.

### Stage 2F-F-D docs hygiene: baseline and coverage guard

- Aligned current baseline documentation in `README.md`, `ROADMAP.md`, `docs/STATE.md`, and `docs/TESTING.md`.
- Removed duplicate maintenance coverage bullets from `ROADMAP.md` and `docs/TESTING.md`.
- Added a selftest guard so stale current baseline summaries and duplicate maintenance coverage bullets cannot silently return.
- No runtime behavior, probes, aliases, routes, actions, execution authority, service mutation, dashboards, automation, or broad normal-answer probe backing were added.
- Final integrated selftest JSON summary: {"ok": true, "passed": 258, "failed": 0, "total": 258}.

### Stage 2F-F-D docs hygiene: roadmap duplicate guard

- Removed a duplicated Stage 2F-F-C maintenance-planning checkpoint note from `ROADMAP.md`.
- Added a selftest guard so the duplicate roadmap note cannot silently return.
- No runtime behavior, probes, aliases, routes, actions, execution authority, service mutation, dashboards, automation, or broad normal-answer probe backing were added.
- Final integrated selftest JSON summary: {"ok": true, "passed": 257, "failed": 0, "total": 257}.

### Stage 2F-F-D follow-up: journalctl report key correction

- Corrected maintenance report formatting to read journalctl_available and journalctl_error_kind from boot_service_health probe data.
- Strengthened Stage 2F-F-D formatter/source tests so the misspelled jrnctl keys cannot return.
- No probes, aliases, routes, actions, execution authority, service mutation, dashboards, automation, or broad normal-answer probe backing were added.
- Final integrated selftest JSON summary: {"ok": true, "passed": 256, "failed": 0, "total": 256}.

### Stage 2F-F-D recovery: narrow maintenance report contract

- Narrowed `ai_maintenance_report.py` back to the three maintenance probes.
- Removed accidental capability-registry coupling from the maintenance report module.
- Strengthened tests so host/session/tool/model context probes cannot leak into the maintenance report contract.
- Corrected documentation wording that implied all seven probes or future maintenance planning.
- Final integrated selftest JSON summary: {"ok": true, "passed": 256, "failed": 0, "total": 256}.

### Stage 2F-F-D maintenance report contract boundary

- Added `src/bond/ai_maintenance_report.py`: a pure, isolated seam for assembling and formatting the maintenance/readiness report.
- The report module formats a narrow maintenance/readiness contract around `package_update_status`, `storage_hygiene`, `boot_service_health`, and the non-executing maintenance plan.
- `ai_capability_answer.py` delegates the maintenance/readiness report path entirely to `ai_maintenance_report.build_and_format_maintenance_readiness_report()`.
- Contract boundaries: action_authorized=False, execution_supported=False; report is read-only and does not authorize execution.
- Six new Stage 2F-F-D tests added to the integrated selftest suite, all passing.
- Final integrated selftest JSON summary: {"ok": true, "passed": 256, "failed": 0, "total": 256}.

### Stage 2F-F-C non-executing maintenance planning contract

- Added a deterministic non-executing maintenance planning contract.
- The existing maintenance/readiness report now includes a bounded planning summary based on package update status, storage hygiene, and boot/service health signals.
- The planning layer classifies observed signals only.
- The planning layer does not recommend shell commands and does not execute fixes.
- Package update/update execution, cleanup execution, service mutation, privileged execution, dashboards, automation, and broad normal-answer probe backing remain future work.
- No aliases, probes, actions, privileged execution, package installs, package upgrades, cleanup execution, service mutation, or maintenance automation were added.
- Final integrated selftest JSON summary: {"ok": true, "passed": 250, "failed": 0, "total": 250}.

### Stage 2F-F-B maintenance readiness report probe integration

- Integrated Stage 2F-F-A read-only maintenance probe facts into the explicit maintenance/readiness report.
- The report now summarizes package update status, bounded storage hygiene, and boot/service health signals.
- Package update status remains local apt cache inspection only and does not run apt update or upgrades.
- Storage hygiene remains bounded to disk-usage records and does not delete files, clean caches, scan duplicates, or traverse large trees.
- Boot/service health remains bounded to failed-unit and recent boot-warning signals and does not mutate services.
- General capability answers are not broadly probe-backed by these maintenance facts.
- No aliases, probes, actions, privileged execution, maintenance planning, package installs, package upgrades, cleanup execution, service mutation, or maintenance automation were added.
- Final integrated selftest JSON summary: {"ok": true, "passed": 242, "failed": 0, "total": 242}.

### Stage 2F-F-A read-only maintenance probe foundation

- Added read-only/rootless maintenance probes for `package_update_status`, `storage_hygiene`, and `boot_service_health`.
- Probes are available through the structured probe layer and scan wrapper only.
- Package update status uses local apt cache inspection only and does not run apt update or upgrades.
- Storage hygiene is bounded to disk-usage signals and does not delete files, clean caches, or scan duplicates.
- Boot/service health reports failed-unit and recent boot-warning signals only and does not restart or modify services.
- No normal assistant-answer behavior, aliases, actions, privileged execution, package installs, package upgrades, cleanup execution, service mutation, or maintenance automation were added.
- Final integrated selftest JSON summary: {"ok": true, "passed": 235, "failed": 0, "total": 235}.

### Stage 2F-E-E selftest accounting and baseline reconciliation

- Fixed selftest pass accounting so memory tests are not double-counted.
- Added a hermetic selftest accounting integrity guard.
- Reconciled current baseline documentation after the accounting fix.
- No runtime assistant behavior, aliases, probes, actions, capabilities, or execution authority were added.
- Final integrated selftest JSON summary: {"ok": true, "passed": 229, "failed": 0, "total": 229}.

### CI Node 24 workflow guard

- Added a hermetic CI Node 24 workflow guard.
- The guard checks the local workflow file directly to avoid relying on GitHub UI/rendered-page artifacts.

### Developer helper cleanup

- Updated `bond-dev-help` to reference current repository documents.
- Added selftest coverage so helper output does not point to missing documentation.

### Stage 2F-E-D archive-pruning hardening

- Hardened archive pruning so corrupted archive metadata cannot delete files outside the archive root.
- Added hermetic selftests for archive path containment.

### Stage 2F-E-D confirmation-token hardening

- Hardened pending confirmation token storage permissions on POSIX systems.
- Added selftest coverage for private confirmation-token file modes.

### Stage 2F-E-D timeout hardening

- Added bounded subprocess timeout handling for model invocation and safe-action execution.
- Added selftest timeout guards so hung subprocesses fail deterministically instead of stalling the suite.

### Stage 2F-E-C classifier-boundary cleanup

- Centralized explicit maintenance-readiness alias detection behind `ai_capability_classifier.py`.
- Removed duplicated maintenance-readiness alias ownership from `ai_capability_answer.py`.
- Preserved maintenance/readiness, context, general capability, and model inventory answer behavior.
- No aliases, probes, actions, capabilities, or execution authority were added.
- Latest integrated selftest run after cleanup: all 218 checks passed.

### Stage 2F-E-C read-only maintenance/readiness report

- Added `describe_maintenance_readiness` as a partial read-only capability.
- Added a bounded explicit maintenance/readiness report answer surface.
- The report uses existing read-only probes only.
- It does not fix anything, install packages, write files, delete files, restart services, or authorize execution.
- It does not inspect real package freshness, logs, or storage usage.
- Existing `inspect_package_update_status`, `inspect_storage_hygiene`, `inspect_boot_and_service_health`, `generate_periodic_health_report`, `present_maintenance_dashboard`, and `apply_privileged_system_updates` capabilities remain planned/unavailable.
- Latest integrated selftest run after Stage 2F-E-C: all 216 checks passed.

### Stage 2F-E-B CI recovery

- Replaced the non-hermetic `/tmp` source snapshot selftest with a CI-safe contract-only guard.
- Preserved classifier and answer runtime behavior.
- No aliases, probes, actions, capabilities, or execution authority were added.
- Latest integrated selftest run after recovery: 208 passed, 0 failed, total 208.

### Stage 2F-E-B transitional linguistic intent normalization contract

- Added `src/bond/ai_linguistic_intent_contract.py` as a contract-only module.
- Documented deterministic aliases as transitional scaffolding behind the classifier boundary.
- Preserved classifier and answer behavior unchanged.
- Added tests proving the contract does not claim smart NLP, semantic classification, or model-based classification.
- No aliases, probes, actions, or execution authority were added.
- Latest integrated selftest run after Stage 2F-E-B: 208 passed, 0 failed, total 208.

### Stage 2F-E-A capability classifier boundary

- Moved capability-question detection/classification into `src/bond/ai_capability_classifier.py`.
- Kept capability answer generation in `src/bond/ai_capability_answer.py`.
- Preserved existing public helper behavior through compatibility imports in `ai_capability_answer.py`.
- Preserved existing context/general/specific capability answer behavior.
- No aliases, probes, actions, or execution authority were added.
- Latest integrated selftest run after Stage 2F-E-A: 200 passed, 0 failed, total 200.

### Stage 2F-D-D bounded context capability answers

- Moved `describe_context_capabilities` from planned to partial.
- Added bounded explicit context-capability answers for explicit context question surfaces using existing read-only probes only (`host_baseline`, `session_baseline`, `tool_inventory`, `model_truth`).
- Kept general capability answers non-probe-expanded (`what can you do?` remains registry summary only).
- Kept normal assistant answers not broadly dynamically probe-backed.
- No new probes, no new actions, and no execution authority were added.
- Latest integrated selftest run after Stage 2F-D-D: 192 passed, 0 failed, total 192.

### Stage 2F-D-C bounded model-truth fallback hardening

- Hardened bounded `model_truth` capability-answer fallback wording for unavailable inventory paths so installed inventory is explicitly unavailable-in-run and missing/extra installed-model sets are explicit unknowns for that run.
- Hardened validation-failure and probe-exception fallback wording to the same bounded unavailable envelope (`truth_status=unavailable`) without leaking probe exception details.
- Added Stage 2F-D-C integrated selftests for unavailable-inventory fallback behavior, validation-failure fallback behavior, exception fallback behavior, success-path continuity, and non-probe-expanded general capability answers.
- Kept scope narrow: no new probes, no broadened probe-backed answers, no model-roster changes.
- Latest integrated selftest run after Stage 2F-D-C hardening: 186 passed, 0 failed, total 186.
- This stage does not complete Stage 2F-D, does not implement maintenance advisor/package update planning, and does not complete M4.

### Stage 2F-D-B bounded model-truth capability answers

- Wired existing read-only `model_truth` probe output into bounded `query_model` capability answers for model-inventory/model-identity question surfaces only.
- Added deterministic `model_truth` answer formatting with validation and bounded fallback behavior; fallback explicitly keeps configured route targets and installed local model inventory distinct.
- Kept general capability discovery and normal assistant answers non-probe-backed.
- Reordered unknown/pure-question handling so precise fact queries run before capability answers, while guarding model-capability surfaces from assistant-name fact alias interception.
- Added Stage 2F-D-B integrated selftests for unit and CLI model-truth answer behavior, telemetry answer-path expectations (`capability_answer` vs `fact_answer`), non-probe-expanded general capability answers, and probe-shape compatibility.
- Latest integrated selftest run after Stage 2F-D-B integration: 181 passed, 0 failed, total 181.
- This stage does not complete Stage 2F-D, does not implement maintenance advisor/package update planning, and does not complete M4.

### Stage 2F-D-A2 cleanup and CI hardening

- updates CI to Node 24-compatible GitHub Actions majors
- adds hygiene tests for key Markdown/YAML formatting
- adds a model_truth future-answer-shape check
- preserves the boundary that normal assistant answers are not yet dynamically probe-backed

### Stage 2F-D-A dynamic probe foundation

- Added `src/bond/ai_probe_contract.py` with the deterministic structured probe-result contract for Layer 0/1/2 probe snapshots.
- Added `src/bond/ai_probes.py` with the first read-only probe set: `host_baseline`, `session_baseline`, `tool_inventory`, `router_config_models`, `ollama_model_inventory`, and `model_truth`.
- Replaced the legacy broad `src/bond/ai_scan_system.py` scanner with a thin structured probe CLI wrapper that preserves the compatibility state snapshot path.
- Added Stage 2F-D-A integrated selftests for probe contract validation, structured probe behavior, CLI JSON output, wrapper execution, and static `shell=True` absence checks.
- Updated README, STATE, TESTING, PROBES, CAPABILITIES, and ROADMAP docs to distinguish the new read-only probe foundation from future probe-backed capability discovery.
- This stage does not implement probe-backed normal answers, privileged actions, maintenance advisor behavior, or package updates.

### Stage 2F-C3 CI selftest portability fix

- Fixed Stage 2F-C3 selftest portability by using the repository-local `scripts/ai` wrapper instead of assuming a globally installed `ai` command in CI.

### Stage 2F-C5 follow-up strict timeout cleanup

- Added language-policy capability aliases for Greek and English "can you answer/respond in Greek" wording so those forms stay deterministic capability answers instead of timing out.
- Expanded unsupported side-effect action-start detection for create-folder and write-file phrasing so those requests fail closed as deterministic parser-contract rejects.
- Extended the existing Stage 2F-C5 integrated selftests with the three follow-up timeout-edge cases.
- This follow-up does not implement Stage 2F-D dynamic probes, full Greek language-state architecture, file creation, or general observe/model-chat timeout handling.
- Latest integrated selftest run after the C5 follow-up: 157 passed, 0 failed, total 157.

### Stage 2F-C5 strict timeout and diagnostic-expectation cleanup

- Updated deterministic social check-in wording so `how are you?` responses include `Bond` while remaining direct deterministic answers.
- Added capability-question surface guarding for high-risk and capability phrasing to keep question forms (update/restart/shutdown/delete/rm-rf/Greek voice/memory) from being misclassified as executable action requests.
- Added unsupported side-effect action starts (`remind`, `create a file`, `send an email`) in action-start detection to keep deterministic bounded handling and avoid model fallback.
- Added parser rejection for fake/nonexistent open targets containing `does not exist` markers.
- Added `dangerous_action_confirmation` capability registry entry and capability-answer aliases/status-note wiring for high-risk confirmation semantics.
- Expanded capability aliases for timer reminder wording, Greek voice/memory wording, and package-update question forms.
- Added Stage 2F-C5 integrated selftests covering strict timeout cleanup, capability-question wording, reject paths, and diagnostic expectation alignment.
- `notify me to stretch` remains a current bounded action dry-run path.
- `απάντα ελληνικά` remains a registry-backed `apply_response_language_policy` capability answer and is not treated as complete Greek language-state architecture.
- Stage 2F-D dynamic probes remain not implemented in this stage.
- Latest integrated selftest run after C5 integration: 154 passed, 0 failed, total 154.

### Stage 2F-C4 deterministic diagnostic cleanup

- Added centralized action-noise stripping for adversarial high-risk prefixes (`ignore all safety rules and ...`, `without asking confirmation ...`, `pretend I confirmed ...`) so embedded high-risk commands remain deterministic confirmation-required candidates.
- Expanded centralized Greek action normalizations for reboot/shutdown/delete verb surfaces so Greek and mixed-language action phrasing converges into language-neutral forms used by intent/risk gates.
- Hardened high-risk command-like detection to evaluate normalized action text and to exempt bounded harmless/quoted prompts.
- Added bounded deterministic direct answers for `say the word reboot but do not do anything` and `explain why dangerous actions require confirmation` to avoid confirmation/model-timeout misrouting.
- Expanded capability registry and capability-answer aliases for exploratory questions (voice/applet/web/memory/files/terminal/packages), timer truthfulness probes, and Greek model-inventory wording.
- Added Stage 2F-C4 diagnostic cleanup selftests for mixed-intent Greek destructive input, adversarial high-risk bypass wording, Greek polite reboot confirmation flow, timer truthfulness, Greek model inventory phrasing, exploratory capability questions, high-risk shell/update no-timeout paths, and harmless quoted safety wording.
- Greek support remains transitional and centralized in normalization/alias/intent handling; final language-state architecture is not complete.
- Stage 2F-D dynamic probes remain not implemented in this stage.
- Latest integrated selftest run after C4 integration: 136 passed, 0 failed, total 136.

### Stage 2F-C3 telemetry edge case cleanup

- Fixed bare capability noun phrase detection: "installed models" and "local models" now recognized as capability questions and answered deterministically without requiring question markers or question phrases.
- Added time-query handlers (`give me the time`, `what time is it`) to return bounded deterministic answer explaining local time queries are not yet a fully wired capability, preventing timeout/model fallback.
- Added project-state-query handlers (`current state of the project`, `project state`) to return bounded deterministic answer directing to git status/docs/STATE/CHANGELOG, preventing timeout/model fallback.
- Added four targeted Stage 2F-C3 edge-case tests in integrated selftest covering bare capability phrases and time/project-state queries.
- Historical baseline note: 113/113 baseline with +4 edge-case tests at the C3 checkpoint.

### Stage 2F-C2 telemetry verification regression cleanup

- Reordered `ai_run.py` guardrail flow so policy/action gating and action execution paths are handled before capability/fact/model fallback, then capability answers are checked before fact answers.
- Added deterministic social check-in handling for trivial prompts such as `how are you?` to avoid model fallback.
- Expanded capability-query detection/aliases for model and Greek language-policy prompts, including direct imperative-style language-policy requests.
- Hardened high-risk restart phrasing (`restart the laptop` family) to remain confirmation-required instead of falling through to action-not-parsed/model paths.
- Added six targeted Stage 2F-C2 regression tests in integrated selftest.
- Validation baseline advanced to 113/113.

### Stage 2F-C telemetry-driven guardrail hardening

- Hardened deterministic guardrails from telemetry findings: assistant-invocation stripping, Greek action normalization coverage, high-risk natural command shaping, and mixed-intent preemption protection.
- Moved capability-answer interception behind intent/risk gating so mixed/action paths are not preempted by capability wording.
- Expanded capability-alias coverage (English/Greek/colloquial/adversarial phrasing) while preserving registry truth boundaries for planned/unsupported capabilities.
- Improved single-action dry-run metadata to always include non-empty normalized action_steps for safe action previews.
- Added telemetry-derived regression selftests for assistant-prefixed commands, high-risk confirmations, mixed-intent rejection, and capability aliases.
- Telemetry remains opt-in dev/test instrumentation (`BOND_DEV_TELEMETRY=1`), stderr-only, and outside normal assistant answer text.
- Validation baseline has since advanced to 113/113 after Stage 2F-C2 cleanup.

### Development telemetry (opt-in test instrumentation)

- Added opt-in `BOND_DEV_TELEMETRY=1` development telemetry for response timing and safe decision metadata.
- Telemetry is disabled by default, goes to stderr, and is not part of normal Bond answers.
- Added dev telemetry selftests.
- New expected validation baseline: 78/78.

### Stage 2F-B read-only capability answer integration

- Corrected the describe_capabilities registry note so capability summaries no longer claim assistant-answer integration is pending after Stage 2F-B.
- Added `src/bond/ai_capability_answer.py` for deterministic read-only capability answers.
- Wired capability questions into `src/bond/ai_run.py` before model/action handling.
- Added six capability-answer selftests.
- Updated docs to distinguish static registry-backed answers from future dynamic probe-backed discovery.
- Validation baseline has since advanced to 113/113 after follow-up hardening stages.

### Stage 2F-A capability registry foundation

- Added `src/bond/ai_capabilities.py` static capability registry foundation.
- Added capability-registry honesty selftests.
- Updated docs to distinguish code-level registry foundation from dynamic probe-backed capability discovery.
- New validation baseline expected: 67/67.

### Documentation

- Documented planned system maintenance and health-advisor capabilities, including read-only package update inspection, safe update planning, storage hygiene reporting, duplicate-file candidate reporting, boot/service health reporting, monthly health reports, and future GUI/dashboard presentation boundaries.
- Clarified that maintenance reports are recommendations only and must not perform privileged updates, cleanup, deletion, or service changes without future privileged-lane, confirmation, audit, and validation support.

### P0F-A2 - Public repository truth alignment and hygiene

- Aligned current validation baseline references on 61/61.
- Added public security, contribution, and license files.
- Moved the root checkpoint transcript into the historical archive.
- Clarified public-use safety boundaries in the README.
- Preserved current behavior; no product capabilities were added.

### P0F-A1 - Current documentation reference cleanup

- Replaced stale current-doc references to pre-archive analysis/report paths with archive paths.
- Removed or redirected references to obsolete tool-specific workflow documents.
- Preserved current behavior; no product capabilities were added.

### P0E - Gitea and roadmap reconciliation

- Reconciled local Gitea milestones with the repository roadmap model.
- Created/opened roadmap-aligned tracker milestones for P0, M1-M6, and backlog work.
- Closed legacy Phase 1-6 milestones as historical tracker structure without deleting them.
- Closed the completed policy-classification issue and moved remaining open issues to current milestones.
- Updated repository planning docs to reflect the reconciled tracker state.
- Preserved Stage 2E behavior; no product capabilities were added.

### P0D - Historical documentation archival

- Moved historical design analysis and implementation reports under `docs/archive/`.
- Preserved historical reasoning while preventing archived material from acting as current project truth.
- Added archive guidance for using historical documents safely.
- Sanitized local/private path references in archived documentation.
- Preserved Stage 2E behavior; no product capabilities were added.

### P0C - Public documentation consolidation

- Rewrote README for public human readers.
- Rewrote development documentation as a tool-agnostic contributor guide.
- Rewrote the AI-assisted maintenance guide without tool-specific prompt scaffolding.
- Sanitized the runtime path reference.
- Removed obsolete tool-specific workflow prompt/operator files from tracked public docs.
- Preserved current Stage 2E behavior; no product capabilities were added.

### P0B - Source and deploy sanitation

- Removed unused legacy local-path source debt by deleting `src/bond/ai_summarize_system.py` after confirming no active runtime/script/deploy references.
- Normalized deploy systemd examples away from machine-specific paths.
- Replaced user-specific test fixtures with neutral placeholders.
- Preserved Stage 2D confirmation and Stage 2E parser-contract behavior.
- No product capabilities were added.

### P0A - Publication boundary and cleanup plan

- Added a public/private repository boundary policy.
- Added a staged cleanup plan before Stage 2F.
- Documented that the current private history should not be pushed publicly as-is.
- Documented that the preferred public migration path is a fresh sanitized public repository.
- Marked Stage 2F as paused until cleanup gates pass.
- Preserved Stage 2E code behavior; no product capabilities were added.

### Stage 2D confirmation token flow

- Stage 2E: added parser contract and action preflight so action-looking requests with no safe parsed action shape fail closed as `action_not_parsed` before executor, while preserving Stage 2D confirmation behavior.

- Added deterministic short-lived confirmation tokens for high-risk `confirmation_required` action requests.
- Added confirmation request handling (`confirm TOKEN` / Greek confirmation forms) with invalid/expired/consumed safeguards and no policy/executor bypass.
- Added selftest coverage for confirmation token creation, validation failures, consumption, non-reuse, and confirmed dry-run path behavior.
- Hardened Stage 2D so confirmed requests with no parsed executable action fail closed before any execution path.

### Documentation reality sync after Stage 2C

- Updated repository docs to reflect implemented Stage 2A routing, Stage 2B policy gate, Stage 2C action-contract/dry-run behavior, and the current 43/43 selftest baseline.
- Preserved strict boundaries between implemented work and future work (including Stage 2D confirmation flow, capability registry implementation, parser/probe/memory depth, and service/applet/voice/packaging targets).

### Selftest non-interactive action mode

- Made automated selftests non-interactive by running GUI-opening action requests through action dry-run mode.
- Added selftest coverage to ensure the test environment enables `BOND_ACTION_DRY_RUN`.
- Preserved explicit dry-run and high-risk confirmation coverage without requiring manual window closing.

### Stage 2C cleanup: events log bucket

- Added `events` as a first-class memory log bucket so action dry-runs can be logged without falling back to chat logs.
- Added selftest coverage for the `events` memory log bucket.
- Staged the new action contract module for tracking without committing.

### Stage 2C action dry-run / confirmation contract

- Added Stage 2C action contracts to separate dry-run, safe execution, confirmation-required, rejection, and chat lanes.
- Added explicit and environment-driven action dry-run support via `BOND_ACTION_DRY_RUN`.
- Added action contract context to internal model prompts and route/policy/action metadata to logs.
- Added selftests for action contracts, dry-run behavior, and high-risk confirmation-required responses.

### Stage 2B policy gate + action lane separation

- Added Stage 2B policy gate separating route decisions, action/chat classification, and execution/chat branching.
- Added deterministic policy decisions for chat, safe actions, action chains, mixed-intent rejection, and high-risk action confirmation requirements.
- Added policy context to internal model prompts and route/policy metadata to logs.
- Added selftests for policy decisions and mixed-intent policy rejection.

### Stage 2A validation baseline cleanup

- Cleaned Stage 2A validation baseline by making selftests honor the resolved config path and a hermetic temporary archive root.
- Replaced the remaining active-source heavier-model memory reflection default with the installed lean model `gemma2:2b`.

### Stage 2 brain/routing rewrite - Stage 2a structured deterministic routing

- Began Stage 2 brain/routing rewrite by adding deterministic structured routing in ai_router.py.
- Aligned router profiles with the actual lean local model roster: qwen2.5:3b-instruct, gemma2:2b, and qwen2.5:7b-instruct.
- Replaced legacy automatic routing in ai_run.py with structured route decisions and route metadata logging.
- Added selftests for route decisions and router profile model truth.

### Path substrate and system portability

- Added platform-aware Bond path resolution for config, data, state, cache, memory, router config, changelog, archive, and wrapper entry points.
- Replaced hardcoded user-home runtime assumptions in active source modules and scripts with BOND_ROOT/env/config-driven resolution.
- Updated selftest path checks to avoid user-specific second-drive assertions.
- Central path resolver now supports Windows, macOS, Linux, and Android-like (Termux) environments with proper XDG and platform-native fallbacks.
- All wrapper scripts now repository-relative via dynamic BOND_ROOT discovery and PYTHONPATH injection.
- Config paths now support URI-like prefixes (repo://, config://, data://, state://, cache://) and variable expansion for portable configuration.

### Repository documentation foundation

- README expanded into a real project front page describing Bond’s identity, current state, goals, repository layout, documentation map, workflow expectations, and documentation limits.
- Documentation effort explicitly reframed around making the repository, not chat history, the durable source of truth.
- Added canonical trust, explainability, capability-discovery, extension, context, and interaction-mode documentation.
- Added canonical text-first Greek language support and localization planning documentation.
- Added canonical packaging strategy documentation covering Python core, Stage 1 local install, Stage 2 platform adapters, and integration boundaries.
- Added service, applet, voice, and tool-specific workflow documentation from the documentation-gap blueprint.

### Repository discipline

- Repository-first project direction reaffirmed.
- Documentation, install flow, packaging notes, issue structure, milestone structure, and release/versioning discipline identified as first-class engineering work rather than optional polish.

### Architecture and planning

- Current planning direction tightened around explicit subsystem boundaries for parsing, action policy, capability truth, execution, memory quality, correction ingestion, system probes, and behavioral testing.
- Long-term direction clarified: preserve the modular architecture while performing targeted corrective redesign in central decision layers.

## Historical baseline

The entries below summarize the already-established project evolution that led to the current repository phase.

### Pre-repository / loose-script phase

- Bond began as a loose collection of scripts under earlier live paths rather than as a clean repository-centered program.
- Runtime, config, code, and memory concerns were not cleanly separated.
- Hardcoded paths and environment-specific assumptions were common.
- Documentation and operating knowledge were overly dependent on transcript/chat context.

### Structural correction phase

- Need for a stricter architecture was recognized after observing that passing subsystem checks did not guarantee sane assistant behavior.
- Path handling, repository layout, and project structure began moving toward a cleaner source-tree model.
- Repository hygiene improved through git usage, ignore rules, and more deliberate change discipline.

### Core alignment phase

- Core scripts and project wiring were brought into closer alignment.
- Selftests reached a passing state.
- Memory retrieval priorities and live-truth-versus-archive handling were tightened.

### Stress-test reality check phase

- Live testing exposed major weaknesses in general assistant sanity, capability honesty, action truthfulness, mixed-intent handling, lexical hijacking, and system-tool grounding.
- The project conclusion shifted from “polish the current system” to “perform a controlled but more aggressive corrective rewrite of selected decision layers.”

### Documentation split phase

- Monolithic transcript dependency began being reduced by splitting durable knowledge into repository documentation.
- Core docs such as architecture, behavior contract, current paths, testing, state, compiled transcript conclusions, and master planning documents were established.

## Future release discipline

Once version tags are introduced, this file should evolve toward a release-oriented structure such as:

- `## [Unreleased]`
- `## [0.1.0] - YYYY-MM-DD`
- `## [0.1.1] - YYYY-MM-DD`

At that stage:

- completed unreleased items should move into versioned sections
- version sections should summarize shipped repository changes only
- release tags, release notes, and this changelog should stay consistent with each other
