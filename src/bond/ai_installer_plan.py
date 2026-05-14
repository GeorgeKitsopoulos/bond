#!/usr/bin/env python3
"""Pure deterministic installer/reconfigure planning contract.

Does not execute installs, updates, reconfiguration, service changes, manifest
writes, package operations, or storage mutations.
Accepts dictionaries/strings/lists as explicit inputs and returns dictionaries.
Does not call package managers, shell out, write files, or read live machine files.
"""

from typing import Any

INSTALLER_PLAN_SCHEMA_VERSION = 1
INSTALLER_PLAN_KIND = "bond_installer_plan"

# Allowed requested_mode values
_KNOWN_MODES = {
    "fresh_install_review",
    "reconfigure_review",
    "update_review",
    "doctor_review",
}

# Bounded plan step IDs
_PLAN_STEP_IDS = (
    "collect_host_profile",
    "collect_storage_profile",
    "review_install_manifest_drift",
    "review_dependency_plan",
    "review_storage_locations",
    "review_service_strategy",
    "final_human_approval",
)

# Identity/secret field names to exclude from input summaries
_SENSITIVE_FIELD_NAMES = frozenset({
    "hostname", "username", "email", "token", "password", "secret",
    "api_key", "apikey", "machine_id", "machineid", "machine-id",
    "user", "login", "credentials", "auth", "private_key", "privatekey",
})


def _is_sensitive_key(key: str) -> bool:
    """Return True if the field name looks like an identity or secret field."""
    k = key.lower().replace("-", "_").replace(" ", "_")
    for sensitive in _SENSITIVE_FIELD_NAMES:
        if k == sensitive or k.endswith(f"_{sensitive}") or k.startswith(f"{sensitive}_"):
            return True
    return False


def _safe_get(d: dict, key: str, default: Any = None) -> Any:
    """Get a value from a dict safely."""
    if not isinstance(d, dict):
        return default
    return d.get(key, default)


def _build_host_summary(host_profile: dict | None) -> dict:
    """Build a bounded host profile summary omitting sensitive fields."""
    if not isinstance(host_profile, dict):
        return {}
    summary = {}
    for key in ("architecture", "os_family", "package_manager", "immutable_hint", "steam_deck_hint"):
        val = host_profile.get(key)
        if val is not None:
            summary[key] = val
    return summary


def _build_storage_summary(storage_profile: dict | None) -> dict:
    """Build a bounded storage profile summary omitting sensitive fields."""
    if not isinstance(storage_profile, dict):
        return {}
    summary = {}
    for key in ("preferred_large_data_base", "requires_manual_review", "storage_pressure", "home_mount_point"):
        val = storage_profile.get(key)
        if val is not None:
            summary[key] = val
    return summary


def _build_drift_summary(install_drift_report: dict | None) -> dict:
    """Build a bounded drift report summary."""
    if not isinstance(install_drift_report, dict):
        return {}
    summary = {}
    for key in ("drift_severity", "recommended_next_step_kind", "requires_manual_review"):
        val = install_drift_report.get(key)
        if val is not None:
            summary[key] = val
    return summary


def _build_strategy_summary(package_strategy: dict | None) -> dict:
    """Build a bounded package strategy summary."""
    if not isinstance(package_strategy, dict):
        return {}
    summary = {}
    for key in ("strategy_kind", "preferred_install_surface", "requires_manual_review", "supported_package_manager"):
        val = package_strategy.get(key)
        if val is not None:
            summary[key] = val
    return summary


def _build_dependency_summary(dependency_plan: dict | None) -> dict:
    """Build a bounded dependency plan summary."""
    if not isinstance(dependency_plan, dict):
        return {}
    summary = {}
    for key in ("recommended_next_step_kind", "requires_manual_review"):
        val = dependency_plan.get(key)
        if val is not None:
            summary[key] = val
    # Add item status counts
    plan_items = dependency_plan.get("plan_items", [])
    if isinstance(plan_items, list):
        status_counts: dict[str, int] = {}
        for item in plan_items:
            if isinstance(item, dict):
                s = item.get("status", "unknown")
                status_counts[s] = status_counts.get(s, 0) + 1
        if status_counts:
            summary["item_status_counts"] = status_counts
    return summary


def _determine_plan_status(
    host_profile: dict | None,
    storage_profile: dict | None,
    package_strategy: dict | None,
    dependency_plan: dict | None,
    install_drift_report: dict | None,
) -> tuple[str, list[str], list[str]]:
    """
    Determine plan_status, blocked_reasons, review_reasons.
    Returns (plan_status, blocked_reasons, review_reasons).
    """
    blocked_reasons: list[str] = []
    review_reasons: list[str] = []

    # Check for missing required inputs
    if not isinstance(host_profile, dict) or not host_profile:
        blocked_reasons.append("host_profile is missing or invalid")
    if not isinstance(storage_profile, dict) or not storage_profile:
        blocked_reasons.append("storage_profile is missing or invalid")

    # Check for missing package_strategy or dependency_plan
    if not isinstance(package_strategy, dict) or not package_strategy:
        blocked_reasons.append("package_strategy is missing or invalid")
    if not isinstance(dependency_plan, dict) or not dependency_plan:
        blocked_reasons.append("dependency_plan is missing or invalid")

    if blocked_reasons:
        return "blocked_missing_inputs", blocked_reasons, review_reasons

    # Check for unsupported/unknown strategy
    strategy_kind = _safe_get(package_strategy, "strategy_kind", "")
    supported = _safe_get(package_strategy, "supported_package_manager", True)
    if strategy_kind == "unknown_requires_manual_review" or not supported:
        review_reasons.append(f"package strategy is unsupported or unknown: {strategy_kind}")
        return "unsupported_manual_review", blocked_reasons, review_reasons

    # Check for manual review conditions
    if _safe_get(package_strategy, "requires_manual_review"):
        review_reasons.append("package strategy requires manual review")

    if _safe_get(dependency_plan, "requires_manual_review"):
        review_reasons.append("dependency plan requires manual review")
    if _safe_get(dependency_plan, "recommended_next_step_kind") == "manual_dependency_review":
        review_reasons.append("dependency plan recommends manual dependency review")

    if isinstance(install_drift_report, dict):
        if _safe_get(install_drift_report, "drift_severity") == "critical":
            review_reasons.append("install manifest drift severity is critical")
        if _safe_get(install_drift_report, "recommended_next_step_kind") == "review_before_reconfigure":
            review_reasons.append("install manifest drift requires review before reconfigure")
        if _safe_get(install_drift_report, "requires_manual_review"):
            review_reasons.append("install manifest drift requires manual review")

    if _safe_get(storage_profile, "requires_manual_review"):
        review_reasons.append("storage profile requires manual review")

    if review_reasons:
        return "manual_review_required", blocked_reasons, review_reasons

    return "ready_for_human_review", blocked_reasons, review_reasons


def _build_plan_items(
    host_profile: dict | None,
    storage_profile: dict | None,
    install_drift_report: dict | None,
    dependency_plan: dict | None,
    plan_status: str,
    requested_mode: str,
) -> list[dict]:
    """Build deterministic list of non-executable plan items."""
    items = []

    # Helper to check if an input exists
    has_host = isinstance(host_profile, dict) and bool(host_profile)
    has_storage = isinstance(storage_profile, dict) and bool(storage_profile)
    has_drift = isinstance(install_drift_report, dict) and bool(install_drift_report)
    has_dep = isinstance(dependency_plan, dict) and bool(dependency_plan)

    # 1. collect_host_profile
    if has_host:
        host_status = "satisfied"
        host_review = False
    else:
        host_status = "missing_input"
        host_review = False
    items.append({
        "step_id": "collect_host_profile",
        "title": "Collect host portability profile",
        "status": host_status,
        "requires_manual_review": host_review,
        "execution_authorized": False,
        "command": None,
        "note": "Read-only host portability facts are required before any installer planning.",
    })

    # 2. collect_storage_profile
    if has_storage:
        storage_status = "satisfied"
        storage_review = _safe_get(storage_profile, "requires_manual_review", False) is True
        if storage_review:
            storage_status = "manual_review_needed"
    else:
        storage_status = "missing_input"
        storage_review = False
    items.append({
        "step_id": "collect_storage_profile",
        "title": "Collect storage portability profile",
        "status": storage_status,
        "requires_manual_review": storage_review,
        "execution_authorized": False,
        "command": None,
        "note": "Read-only storage portability facts are required before any installer planning.",
    })

    # 3. review_install_manifest_drift
    if has_drift:
        drift_severity = _safe_get(install_drift_report, "drift_severity", "")
        drift_manual = _safe_get(install_drift_report, "requires_manual_review", False) is True
        drift_next = _safe_get(install_drift_report, "recommended_next_step_kind", "")
        if drift_severity == "critical" or drift_next == "review_before_reconfigure" or drift_manual:
            drift_status = "manual_review_needed"
            drift_review = True
        else:
            drift_status = "satisfied"
            drift_review = False
    else:
        drift_status = "missing_input"
        drift_review = False
    items.append({
        "step_id": "review_install_manifest_drift",
        "title": "Review install manifest drift",
        "status": drift_status,
        "requires_manual_review": drift_review,
        "execution_authorized": False,
        "command": None,
        "note": "Drift review is read-only; no manifest writes or reconfiguration are authorized.",
    })

    # 4. review_dependency_plan
    if has_dep:
        dep_manual = _safe_get(dependency_plan, "requires_manual_review", False) is True
        dep_next = _safe_get(dependency_plan, "recommended_next_step_kind", "")
        if dep_manual or dep_next == "manual_dependency_review":
            dep_status = "manual_review_needed"
            dep_review = True
        else:
            dep_status = "satisfied"
            dep_review = False
    else:
        dep_status = "missing_input"
        dep_review = False
    items.append({
        "step_id": "review_dependency_plan",
        "title": "Review dependency plan",
        "status": dep_status,
        "requires_manual_review": dep_review,
        "execution_authorized": False,
        "command": None,
        "note": "Dependency plan review is read-only; no package installation or execution is authorized.",
    })

    # 5. review_storage_locations
    if has_storage:
        loc_review = _safe_get(storage_profile, "requires_manual_review", False) is True
        loc_status = "manual_review_needed" if loc_review else "satisfied"
    else:
        loc_status = "missing_input"
        loc_review = False
    items.append({
        "step_id": "review_storage_locations",
        "title": "Review storage locations",
        "status": loc_status,
        "requires_manual_review": loc_review,
        "execution_authorized": False,
        "command": None,
        "note": "Storage location review is read-only; no directories are created or data moved.",
    })

    # 6. review_service_strategy
    # Not applicable for fresh install in early stages; otherwise satisfied if host known
    if requested_mode == "fresh_install_review" and not has_host:
        svc_status = "missing_input"
        svc_review = False
    elif requested_mode in ("update_review", "doctor_review") and has_host:
        svc_status = "satisfied"
        svc_review = False
    elif has_host:
        svc_status = "satisfied"
        svc_review = False
    else:
        svc_status = "missing_input"
        svc_review = False
    items.append({
        "step_id": "review_service_strategy",
        "title": "Review service strategy",
        "status": svc_status,
        "requires_manual_review": svc_review,
        "execution_authorized": False,
        "command": None,
        "note": "Service strategy review is read-only; no service mutation is authorized.",
    })

    # 7. final_human_approval
    # Only satisfied when all prior items are satisfied/not missing
    prior_ok = all(
        item["status"] in ("satisfied", "not_applicable")
        for item in items
    )
    approval_status = "satisfied" if prior_ok else "manual_review_needed"
    items.append({
        "step_id": "final_human_approval",
        "title": "Final human approval gate",
        "status": approval_status,
        "requires_manual_review": True,
        "execution_authorized": False,
        "command": None,
        "note": "Human approval is always required before any future installer/updater execution stage.",
    })

    return items


def build_installer_plan(
    *,
    host_profile: dict[str, Any] | None = None,
    storage_profile: dict[str, Any] | None = None,
    install_manifest: dict[str, Any] | None = None,
    install_drift_report: dict[str, Any] | None = None,
    package_strategy: dict[str, Any] | None = None,
    dependency_plan: dict[str, Any] | None = None,
    requested_mode: str | None = None,
    bond_root: str | None = None,
) -> dict[str, Any]:
    """
    Build a deterministic, read-only installer/reconfigure planning dict.

    Does not execute installation, reconfiguration, service changes, manifest
    writes, package operations, or storage mutations.
    Does not inspect live system state.
    Does not call package managers or generate executable commands.

    Args:
        host_profile: Host portability profile dict (explicit input).
        storage_profile: Storage portability profile dict (explicit input).
        install_manifest: Install manifest dict (informational; not used for writes).
        install_drift_report: Drift report dict (explicit input).
        package_strategy: Package manager strategy dict (explicit input).
        dependency_plan: Dependency plan dict (explicit input).
        requested_mode: One of fresh_install_review, reconfigure_review,
            update_review, doctor_review. Defaults to doctor_review.
        bond_root: Bond root path (informational only).

    Returns:
        Dictionary with installer plan and all authorization fields set to False.
    """
    # Normalize requested_mode
    if requested_mode not in _KNOWN_MODES:
        requested_mode = "doctor_review"

    # Determine plan status
    plan_status, blocked_reasons, review_reasons = _determine_plan_status(
        host_profile=host_profile,
        storage_profile=storage_profile,
        package_strategy=package_strategy,
        dependency_plan=dependency_plan,
        install_drift_report=install_drift_report,
    )

    # Determine recommended next step
    _next_step_map = {
        "ready_for_human_review": "review_installer_plan",
        "manual_review_required": "manual_installer_review",
        "blocked_missing_inputs": "collect_missing_profile_facts",
        "unsupported_manual_review": "manual_platform_review",
    }
    recommended_next = _next_step_map.get(plan_status, "manual_installer_review")

    # Top-level requires_manual_review
    requires_manual_review = plan_status in (
        "manual_review_required",
        "unsupported_manual_review",
        "blocked_missing_inputs",
    )

    # Build plan items
    plan_items = _build_plan_items(
        host_profile=host_profile,
        storage_profile=storage_profile,
        install_drift_report=install_drift_report,
        dependency_plan=dependency_plan,
        plan_status=plan_status,
        requested_mode=requested_mode,
    )

    # Build bounded input summaries (omit sensitive fields)
    input_summaries: dict[str, Any] = {}
    host_summary = _build_host_summary(host_profile)
    if host_summary:
        input_summaries["host_profile"] = host_summary
    storage_summary = _build_storage_summary(storage_profile)
    if storage_summary:
        input_summaries["storage_profile"] = storage_summary
    drift_summary = _build_drift_summary(install_drift_report)
    if drift_summary:
        input_summaries["install_drift_report"] = drift_summary
    strategy_summary = _build_strategy_summary(package_strategy)
    if strategy_summary:
        input_summaries["package_strategy"] = strategy_summary
    dep_summary = _build_dependency_summary(dependency_plan)
    if dep_summary:
        input_summaries["dependency_plan"] = dep_summary
    if bond_root is not None:
        input_summaries["bond_root"] = bond_root

    return {
        "kind": INSTALLER_PLAN_KIND,
        "schema_version": INSTALLER_PLAN_SCHEMA_VERSION,
        "execution_authorized": False,
        "install_authorized": False,
        "upgrade_authorized": False,
        "reconfigure_authorized": False,
        "service_authorized": False,
        "write_plan_authorized": False,
        "write_manifest_authorized": False,
        "commands_generated": False,
        "requested_mode": requested_mode,
        "plan_status": plan_status,
        "recommended_next_step_kind": recommended_next,
        "requires_manual_review": requires_manual_review,
        "blocked_reasons": blocked_reasons,
        "review_reasons": review_reasons,
        "plan_items": plan_items,
        "input_summaries": input_summaries,
        "plan_notes": (
            "Read-only installer planning contract; does not authorize installation, "
            "reconfiguration, service changes, manifest writes, package operations, "
            "or storage mutations."
        ),
    }


def format_installer_plan(plan: dict[str, Any]) -> str:
    """
    Return a short deterministic human-readable installer planning report.

    Does not print directly. Does not include ANSI colors.
    Does not authorize execution.
    """
    lines = ["Installer planning report", ""]
    plan_status = plan.get("plan_status", "(unknown)")
    lines.append(f"Plan status: {plan_status}")
    next_step = plan.get("recommended_next_step_kind", "(unknown)")
    lines.append(f"Recommended next step: {next_step}")
    mode = plan.get("requested_mode", "(unknown)")
    lines.append(f"Requested mode: {mode}")
    lines.append("Execution authorized: false")
    lines.append("")

    blocked = plan.get("blocked_reasons", [])
    if blocked:
        lines.append("Blocked reasons:")
        for r in blocked:
            lines.append(f"  - {r}")
        lines.append("")

    review = plan.get("review_reasons", [])
    if review:
        lines.append("Review reasons:")
        for r in review:
            lines.append(f"  - {r}")
        lines.append("")

    plan_items = plan.get("plan_items", [])
    if plan_items:
        lines.append("Plan items:")
        for item in plan_items:
            step_id = item.get("step_id", "?")
            status = item.get("status", "?")
            lines.append(f"  [{status}] {step_id}")
        lines.append("")

    lines.append("No install, update, reconfigure, service, storage, or manifest write action was performed.")
    return "\n".join(lines)
