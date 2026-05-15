#!/usr/bin/env python3
"""Pure deterministic user-space install manifest payload planning contract.

This module derives a sanitized manifest payload preview for future installer
review only. It never writes files, creates directories, or executes commands.
"""

import json
from typing import Any

USER_INSTALL_MANIFEST_PLAN_SCHEMA_VERSION = 1
USER_INSTALL_MANIFEST_PLAN_KIND = "bond_user_install_manifest_payload_plan"
USER_INSTALL_MANIFEST_SCHEMA_VERSION = 1
USER_INSTALL_MANIFEST_KIND = "bond_user_install_manifest"

_KNOWN_MODES = {
    "fresh_install_review",
    "reconfigure_review",
    "update_review",
    "doctor_review",
}

_TOP_LEVEL_AUTHORIZATION_FIELDS: tuple[str, ...] = (
    "execution_authorized",
    "install_authorized",
    "package_install_authorized",
    "upgrade_authorized",
    "reconfigure_authorized",
    "service_authorized",
    "storage_move_authorized",
    "write_authorized",
    "write_manifest_authorized",
    "commands_generated",
)

_ALLOWED_PATH_ROLES: tuple[str, ...] = (
    "config",
    "data",
    "cache",
    "models",
    "telemetry",
    "logs",
    "backups",
    "manifest_path",
)

_SENSITIVE_TOKENS: tuple[str, ...] = (
    "hostname",
    "username",
    "email",
    "token",
    "password",
    "secret",
    "api_key",
    "apikey",
    "private_key",
    "privatekey",
    "machine_id",
    "machineid",
    "machine-id",
    "credentials",
    "auth",
    "login",
    "user",
)


def _normalize_requested_mode(mode: str | None) -> str:
    if isinstance(mode, str) and mode in _KNOWN_MODES:
        return mode
    return "doctor_review"


def _is_sensitive_value(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    lowered = value.lower()
    if "should_not_leak" in lowered:
        return True
    for token in _SENSITIVE_TOKENS:
        if token == "user":
            if lowered.strip() == token:
                return True
            continue
        if token in lowered:
            return True
    return False


def _safe_string(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    candidate = value.strip()
    if not candidate:
        return None
    if _is_sensitive_value(candidate):
        return None
    return candidate


def _safe_scalar(value: Any) -> Any:
    if isinstance(value, str):
        return _safe_string(value)
    if isinstance(value, (bool, int, float)) or value is None:
        return value
    return None


def _count_plan_item_statuses(plan_items: Any) -> dict[str, int]:
    counts: dict[str, int] = {}
    if not isinstance(plan_items, list):
        return counts
    for item in plan_items:
        if not isinstance(item, dict):
            continue
        status = _safe_string(item.get("status"))
        if not status:
            continue
        counts[status] = counts.get(status, 0) + 1
    return counts


def _build_source_summaries(
    host_profile: dict[str, Any] | None,
    storage_profile: dict[str, Any] | None,
    dependency_plan: dict[str, Any] | None,
    install_drift_report: dict[str, Any] | None,
) -> dict[str, Any]:
    host = host_profile if isinstance(host_profile, dict) else {}
    storage = storage_profile if isinstance(storage_profile, dict) else {}
    dependency = dependency_plan if isinstance(dependency_plan, dict) else {}
    drift = install_drift_report if isinstance(install_drift_report, dict) else {}

    storage_recommendations = (
        storage.get("recommendations")
        if isinstance(storage.get("recommendations"), dict)
        else {}
    )
    package_strategy = (
        dependency.get("package_strategy")
        if isinstance(dependency.get("package_strategy"), dict)
        else {}
    )
    package_manager = _safe_string(host.get("package_manager"))
    if isinstance(package_manager, str):
        package_manager = "_".join(package_manager.split("-"))

    return {
        "host_profile": {
            "architecture": _safe_scalar(host.get("architecture")),
            "os_family": _safe_scalar(host.get("os_family")),
            "distro_id": _safe_scalar(host.get("distro_id")),
            "distro_like": _safe_scalar(host.get("distro_like")),
            "package_manager": _safe_scalar(package_manager),
            "immutable_hint": _safe_scalar(host.get("immutable_hint")),
            "steam_deck_hint": _safe_scalar(host.get("steam_deck_hint")),
        },
        "storage_profile": {
            "profile_kind": _safe_scalar(storage.get("profile_kind")),
            "preferred_large_data_base": _safe_scalar(storage.get("preferred_large_data_base")),
            "preferred_config_base": _safe_scalar(storage.get("preferred_config_base")),
            "requires_manual_review": _safe_scalar(storage.get("requires_manual_review")),
            "storage_pressure": _safe_scalar(storage.get("storage_pressure")),
            "home_mount_point": _safe_scalar(storage.get("home_mount_point")),
            "recommendations": {
                "strategy": _safe_scalar(storage_recommendations.get("strategy")),
                "requires_manual_review": _safe_scalar(storage_recommendations.get("requires_manual_review")),
                "reason": _safe_scalar(storage_recommendations.get("reason")),
            },
        },
        "dependency_plan": {
            "kind": _safe_scalar(dependency.get("kind")),
            "schema_version": _safe_scalar(dependency.get("schema_version")),
            "recommended_next_step_kind": _safe_scalar(dependency.get("recommended_next_step_kind")),
            "requires_manual_review": _safe_scalar(dependency.get("requires_manual_review")),
            "package_strategy": {
                "strategy_kind": _safe_scalar(package_strategy.get("strategy_kind")),
                "preferred_install_surface": _safe_scalar(package_strategy.get("preferred_install_surface")),
                "requires_manual_review": _safe_scalar(package_strategy.get("requires_manual_review")),
                "supported_package_manager": _safe_scalar(package_strategy.get("supported_package_manager")),
            },
            "item_status_counts": _count_plan_item_statuses(dependency.get("plan_items")),
        },
        "install_drift_report": {
            "kind": _safe_scalar(drift.get("kind")),
            "schema_version": _safe_scalar(drift.get("schema_version")),
            "drift_severity": _safe_scalar(drift.get("drift_severity")),
            "recommended_next_step_kind": _safe_scalar(drift.get("recommended_next_step_kind")),
            "requires_manual_review": _safe_scalar(drift.get("requires_manual_review")),
        },
    }


def _build_write_set_summary(write_set: Any) -> list[dict[str, Any]]:
    if not isinstance(write_set, list):
        return []

    summary: list[dict[str, Any]] = []
    for item in write_set:
        if not isinstance(item, dict):
            continue
        summary.append(
            {
                "operation_kind": _safe_scalar(item.get("operation_kind")),
                "role": _safe_scalar(item.get("role")),
                "path": _safe_scalar(item.get("path")),
                "status": _safe_scalar(item.get("status")),
            }
        )
    return summary


def _build_manifest_paths(target_layout: Any, manifest_path: str | None) -> dict[str, Any]:
    layout = target_layout if isinstance(target_layout, dict) else {}
    paths: dict[str, Any] = {}
    for role in _ALLOWED_PATH_ROLES:
        if role == "manifest_path":
            paths[role] = _safe_scalar(manifest_path)
            continue
        paths[role] = _safe_scalar(layout.get(role))
    return paths


def _recommended_next_step(plan_status: str) -> str:
    if plan_status == "ready_for_user_review":
        return "review_user_install_manifest_payload"
    if plan_status == "manual_review_required":
        return "manual_user_install_manifest_review"
    if plan_status == "blocked_missing_inputs":
        return "collect_missing_user_install_manifest_inputs"
    return "manual_platform_review"


def build_user_install_manifest_payload_plan(
    *,
    user_install_plan: dict[str, Any] | None = None,
    host_profile: dict[str, Any] | None = None,
    storage_profile: dict[str, Any] | None = None,
    dependency_plan: dict[str, Any] | None = None,
    install_drift_report: dict[str, Any] | None = None,
    requested_mode: str | None = None,
) -> dict[str, Any]:
    requested_mode_normalized = _normalize_requested_mode(requested_mode)

    blocked_reasons: list[str] = []
    review_reasons: list[str] = []

    plan_valid = (
        isinstance(user_install_plan, dict)
        and user_install_plan.get("kind") == "bond_user_space_install_write_set_plan"
        and isinstance(user_install_plan.get("target_layout"), dict)
        and isinstance(user_install_plan.get("write_set"), list)
    )

    if not plan_valid:
        blocked_reasons.append("user_install_plan is missing or invalid")

    upstream = user_install_plan if isinstance(user_install_plan, dict) else {}
    target_layout = upstream.get("target_layout") if isinstance(upstream.get("target_layout"), dict) else {}
    write_set = upstream.get("write_set") if isinstance(upstream.get("write_set"), list) else []

    manifest_path = _safe_string(target_layout.get("manifest_path"))
    if not manifest_path:
        blocked_reasons.append("manifest path is missing")

    for item in write_set:
        if not isinstance(item, dict):
            continue
        if item.get("execution_authorized") is not False:
            review_reasons.append("upstream write-set attempted to authorize execution")
        if item.get("write_authorized") is not False:
            review_reasons.append("upstream write-set attempted to authorize writes")
        if item.get("command") is not None:
            review_reasons.append("upstream write-set generated a command")

    upstream_status = upstream.get("plan_status")
    upstream_requires_review = upstream.get("requires_manual_review") is True

    status = "ready_for_user_review"
    if review_reasons or upstream_status == "unsupported_manual_review":
        status = "unsupported_manual_review"
    elif blocked_reasons or upstream_status == "blocked_missing_inputs":
        status = "blocked_missing_inputs"
    elif upstream_status == "manual_review_required" or upstream_requires_review:
        status = "manual_review_required"

    if upstream_status == "blocked_missing_inputs" and "upstream user_install_plan is blocked_missing_inputs" not in blocked_reasons:
        blocked_reasons.append("upstream user_install_plan is blocked_missing_inputs")
    if upstream_status == "manual_review_required" and "upstream user_install_plan requires manual review" not in review_reasons:
        review_reasons.append("upstream user_install_plan requires manual review")

    write_set_summary = _build_write_set_summary(write_set)
    source_summaries = _build_source_summaries(
        host_profile=host_profile,
        storage_profile=storage_profile,
        dependency_plan=dependency_plan,
        install_drift_report=install_drift_report,
    )

    manifest_candidate = {
        "kind": USER_INSTALL_MANIFEST_KIND,
        "schema_version": USER_INSTALL_MANIFEST_SCHEMA_VERSION,
        "manifest_purpose": "user_space_install_review",
        "install_surface": "user_space",
        "requested_mode": requested_mode_normalized,
        "authorization": {field: False for field in _TOP_LEVEL_AUTHORIZATION_FIELDS},
        "paths": _build_manifest_paths(target_layout, manifest_path),
        "write_set_summary": write_set_summary,
        "source_summaries": source_summaries,
        "notes": ["Manifest payload preview only; no manifest write is authorized."],
    }

    manifest_json_preview = json.dumps(
        manifest_candidate,
        sort_keys=True,
        indent=2,
        ensure_ascii=False,
    )

    plan = {
        "kind": USER_INSTALL_MANIFEST_PLAN_KIND,
        "schema_version": USER_INSTALL_MANIFEST_PLAN_SCHEMA_VERSION,
        "execution_authorized": False,
        "install_authorized": False,
        "package_install_authorized": False,
        "upgrade_authorized": False,
        "reconfigure_authorized": False,
        "service_authorized": False,
        "storage_move_authorized": False,
        "write_authorized": False,
        "write_manifest_authorized": False,
        "commands_generated": False,
        "requested_mode": requested_mode_normalized,
        "plan_status": status,
        "recommended_next_step_kind": _recommended_next_step(status),
        "requires_manual_review": status in {"manual_review_required", "unsupported_manual_review"},
        "blocked_reasons": blocked_reasons,
        "review_reasons": review_reasons,
        "manifest_path": manifest_path,
        "manifest_candidate": manifest_candidate,
        "manifest_json_preview": manifest_json_preview,
        "input_summaries": {
            "upstream_user_install_plan": {
                "plan_status": _safe_scalar(upstream.get("plan_status")),
                "recommended_next_step_kind": _safe_scalar(upstream.get("recommended_next_step_kind")),
                "requires_manual_review": _safe_scalar(upstream.get("requires_manual_review")),
                "write_set_count": len(write_set),
            },
            "source_summaries": source_summaries,
        },
        "plan_notes": [
            "Deterministic manifest payload preview only.",
            "No user-space install, directory creation, manifest write, package operation, service mutation, storage move, or command execution was performed.",
        ],
    }

    return plan


def format_user_install_manifest_payload_plan(plan: dict[str, Any]) -> str:
    payload = plan if isinstance(plan, dict) else {}
    manifest_json_preview = payload.get("manifest_json_preview")
    if not isinstance(manifest_json_preview, str):
        manifest_json_preview = "{}"

    lines = [
        "User-space install manifest payload report",
        f"Plan status: {payload.get('plan_status')}",
        f"Recommended next step: {payload.get('recommended_next_step_kind')}",
        f"Manifest path: {payload.get('manifest_path')}",
        "Execution authorized: false",
        "Manifest write authorized: false",
        "Manifest JSON preview:",
        manifest_json_preview,
        "No user-space install, directory creation, manifest write, package operation, service mutation, storage move, or command execution was performed.",
    ]
    return "\n".join(lines)
