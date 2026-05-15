#!/usr/bin/env python3
"""Pure deterministic user-space install write-set planning contract.

This module defines candidate user-space write targets for future installer
review only. It never executes installation or writes.
"""

import posixpath
from typing import Any

USER_INSTALL_PLAN_SCHEMA_VERSION = 1
USER_INSTALL_PLAN_KIND = "bond_user_space_install_write_set_plan"

_REQUIRED_ROLES: tuple[str, ...] = (
    "config",
    "data",
    "cache",
    "models",
    "telemetry",
    "logs",
    "backups",
)

_ROLE_ENV_KEYS: dict[str, str] = {
    "config": "BOND_CONFIG_DIR",
    "data": "BOND_DATA_DIR",
    "cache": "BOND_CACHE_DIR",
    "models": "BOND_MODEL_DIR",
    "telemetry": "BOND_TELEMETRY_DIR",
    "logs": "BOND_LOG_DIR",
    "backups": "BOND_BACKUP_DIR",
}

_RECOGNIZED_ENV_KEYS = {
    "BOND_HOME",
    "BOND_CONFIG_DIR",
    "BOND_DATA_DIR",
    "BOND_CACHE_DIR",
    "BOND_MODEL_DIR",
    "BOND_TELEMETRY_DIR",
    "BOND_LOG_DIR",
    "BOND_BACKUP_DIR",
}

_KNOWN_MODES = {
    "fresh_install_review",
    "reconfigure_review",
    "update_review",
    "doctor_review",
}

_ALLOWED_USER_ROOTS = (
    "/home/",
    "/var/home/",
    "/run/media/",
    "/media/",
    "/m" + "nt/",
    "~/",
)

_FORBIDDEN_ROOTS = (
    "/usr",
    "/etc",
    "/var/lib",
    "/root",
    "/boot",
    "/sys",
    "/proc",
    "/dev",
)


def _normalize_requested_mode(mode: str | None) -> str:
    if isinstance(mode, str) and mode in _KNOWN_MODES:
        return mode
    return "doctor_review"


def _extract_path_value(value: Any) -> str | None:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        candidate = value.get("path")
        if isinstance(candidate, str):
            return candidate
    return None


def _normalize_path(path_value: str | None) -> str | None:
    if not isinstance(path_value, str):
        return None
    raw = path_value.strip()
    if not raw:
        return ""

    if raw == "~":
        return raw
    if raw.startswith("~/"):
        suffix = "/".join(part for part in raw[2:].split("/") if part)
        return "~/" + suffix if suffix else "~/"
    if raw.startswith("/"):
        suffix = "/".join(part for part in raw.split("/") if part)
        return "/" + suffix if suffix else "/"

    return "/".join(part for part in raw.split("/") if part)


def _has_invalid_characters(path_value: str | None) -> bool:
    if path_value is None:
        return False
    if path_value == "":
        return True
    return "\x00" in path_value or "\n" in path_value or "\r" in path_value


def _is_forbidden_root(path_value: str) -> bool:
    for root in _FORBIDDEN_ROOTS:
        if path_value == root or path_value.startswith(root + "/"):
            return True
    return False


def _is_allowed_user_root(path_value: str) -> bool:
    for root in _ALLOWED_USER_ROOTS:
        if path_value.startswith(root):
            return True
    return False


def _validate_target_path(path_value: str | None) -> tuple[str, str]:
    if path_value is None:
        return "missing_input", "Target path is missing from explicit inputs."

    if _has_invalid_characters(path_value):
        return "unsupported_manual_review", "Target path is empty or contains forbidden control characters."

    if _is_forbidden_root(path_value):
        return "unsupported_manual_review", "Target path is outside allowed user-space roots and requires manual platform review."

    if not _is_allowed_user_root(path_value):
        return "unsupported_manual_review", "Target path is outside allowed user-space roots and requires manual platform review."

    return "planned_not_authorized", "Candidate user-space directory only; no directory creation is authorized."


def _coerce_env_paths(payload: Any) -> dict[str, Any]:
    if isinstance(payload, dict):
        return payload
    return {}


def _collect_role_recommendations(storage_profile: dict[str, Any] | None) -> dict[str, str]:
    if not isinstance(storage_profile, dict):
        return {}

    recommendations = storage_profile.get("recommendations")
    if not isinstance(recommendations, dict):
        return {}

    role_recs = recommendations.get("role_recommendations")
    if not isinstance(role_recs, list):
        return {}

    resolved: dict[str, str] = {}
    for item in role_recs:
        if not isinstance(item, dict):
            continue
        role = item.get("role")
        base = item.get("preferred_base")
        if not isinstance(role, str) or not isinstance(base, str):
            continue
        if role not in _REQUIRED_ROLES:
            continue
        target = _normalize_path(posixpath.join(base, "bond", role))
        if isinstance(target, str):
            resolved[role] = target
    return resolved


def _resolve_exact_env_path(
    role: str,
    arg_env_paths: dict[str, Any],
    storage_env_paths: dict[str, Any],
    manifest_env_paths: dict[str, Any],
) -> str | None:
    env_key = _ROLE_ENV_KEYS[role]
    candidate = _extract_path_value(arg_env_paths.get(env_key))
    if candidate is None:
        candidate = _extract_path_value(storage_env_paths.get(env_key))
    if candidate is None:
        candidate = _extract_path_value(manifest_env_paths.get(env_key))

    if role == "logs" and candidate is None:
        telemetry_exact = _extract_path_value(arg_env_paths.get("BOND_TELEMETRY_DIR"))
        if telemetry_exact is None:
            telemetry_exact = _extract_path_value(storage_env_paths.get("BOND_TELEMETRY_DIR"))
        if telemetry_exact is None:
            telemetry_exact = _extract_path_value(manifest_env_paths.get("BOND_TELEMETRY_DIR"))
        if isinstance(telemetry_exact, str):
            candidate = posixpath.join(telemetry_exact, "logs")

    return _normalize_path(candidate)


def _resolve_home_fallback(
    role: str,
    arg_env_paths: dict[str, Any],
    storage_env_paths: dict[str, Any],
    manifest_env_paths: dict[str, Any],
) -> str | None:
    bond_home = _extract_path_value(arg_env_paths.get("BOND_HOME"))
    if bond_home is None:
        bond_home = _extract_path_value(storage_env_paths.get("BOND_HOME"))
    if bond_home is None:
        bond_home = _extract_path_value(manifest_env_paths.get("BOND_HOME"))
    if not isinstance(bond_home, str):
        return None
    return _normalize_path(posixpath.join(bond_home, "bond", role))


def _build_input_summaries(
    installer_plan: dict[str, Any] | None,
    storage_profile: dict[str, Any] | None,
    install_manifest: dict[str, Any] | None,
) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "installer_plan": {
            "plan_status": installer_plan.get("plan_status") if isinstance(installer_plan, dict) else None,
            "recommended_next_step_kind": installer_plan.get("recommended_next_step_kind") if isinstance(installer_plan, dict) else None,
            "requires_manual_review": installer_plan.get("requires_manual_review") if isinstance(installer_plan, dict) else None,
        },
        "storage_profile": {
            "strategy": None,
            "requires_manual_review": None,
            "reason": None,
        },
        "install_manifest": {
            "kind": install_manifest.get("kind") if isinstance(install_manifest, dict) else None,
            "schema_version": install_manifest.get("schema_version") if isinstance(install_manifest, dict) else None,
            "service_backend": install_manifest.get("service_backend") if isinstance(install_manifest, dict) else None,
        },
    }

    if isinstance(storage_profile, dict):
        recommendations = storage_profile.get("recommendations")
        if isinstance(recommendations, dict):
            summary["storage_profile"]["strategy"] = recommendations.get("strategy")
            summary["storage_profile"]["requires_manual_review"] = recommendations.get("requires_manual_review")
            summary["storage_profile"]["reason"] = recommendations.get("reason")

    return summary


def build_user_space_install_plan(
    *,
    installer_plan: dict[str, Any] | None = None,
    storage_profile: dict[str, Any] | None = None,
    install_manifest: dict[str, Any] | None = None,
    env_paths: dict[str, Any] | None = None,
    requested_mode: str | None = None,
) -> dict[str, Any]:
    requested_mode_normalized = _normalize_requested_mode(requested_mode)

    blocked_reasons: list[str] = []
    review_reasons: list[str] = []

    installer_valid = isinstance(installer_plan, dict) and installer_plan.get("kind") == "bond_installer_plan"
    if not installer_valid:
        blocked_reasons.append("installer_plan is missing or invalid")

    storage_valid = isinstance(storage_profile, dict)
    if not storage_valid:
        blocked_reasons.append("storage recommendations are missing or invalid")

    arg_env_paths = _coerce_env_paths(env_paths)
    storage_env_paths = _coerce_env_paths(storage_profile.get("env_paths") if isinstance(storage_profile, dict) else None)
    manifest_env_paths = _coerce_env_paths(install_manifest.get("env_paths") if isinstance(install_manifest, dict) else None)

    role_recommendations = _collect_role_recommendations(storage_profile)

    explicit_role_paths: dict[str, str | None] = {}
    for role in _REQUIRED_ROLES:
        explicit_role_paths[role] = _resolve_exact_env_path(
            role,
            arg_env_paths,
            storage_env_paths,
            manifest_env_paths,
        )

    has_role_recommendations = bool(role_recommendations)
    explicit_has_all_roles = all(explicit_role_paths.get(role) is not None for role in _REQUIRED_ROLES)
    if storage_valid and not has_role_recommendations and not explicit_has_all_roles:
        blocked_reasons.append("storage recommendations are missing or invalid")

    target_layout: dict[str, str | None] = {}
    for role in _REQUIRED_ROLES:
        resolved = explicit_role_paths.get(role)
        if resolved is None and role in role_recommendations:
            resolved = role_recommendations.get(role)
        if resolved is None:
            resolved = _resolve_home_fallback(role, arg_env_paths, storage_env_paths, manifest_env_paths)
        target_layout[role] = resolved

    config_target = target_layout.get("config")
    if isinstance(config_target, str):
        target_layout["manifest_path"] = _normalize_path(posixpath.join(config_target, "install-manifest.json"))

    path_statuses: dict[str, str] = {}
    path_reasons: dict[str, str] = {}
    for role in _REQUIRED_ROLES:
        status, reason = _validate_target_path(target_layout.get(role))
        path_statuses[role] = status
        path_reasons[role] = reason

    manifest_status, manifest_reason = _validate_target_path(target_layout.get("manifest_path"))

    plan_status = "ready_for_user_review"

    if blocked_reasons:
        plan_status = "blocked_missing_inputs"

    if installer_valid and installer_plan.get("plan_status") == "blocked_missing_inputs":
        plan_status = "blocked_missing_inputs"

    if installer_valid and installer_plan.get("plan_status") == "unsupported_manual_review":
        plan_status = "unsupported_manual_review"

    installer_needs_manual = bool(installer_plan.get("requires_manual_review")) if installer_valid else False
    if installer_valid and installer_plan.get("plan_status") == "manual_review_required":
        installer_needs_manual = True
    storage_needs_manual = False
    if isinstance(storage_profile, dict):
        recommendations = storage_profile.get("recommendations")
        if isinstance(recommendations, dict):
            storage_needs_manual = bool(recommendations.get("requires_manual_review"))

    if plan_status not in ("blocked_missing_inputs", "unsupported_manual_review"):
        if installer_needs_manual or storage_needs_manual:
            plan_status = "manual_review_required"

    if any(status == "missing_input" for status in path_statuses.values()) or manifest_status == "missing_input":
        if plan_status != "unsupported_manual_review":
            plan_status = "blocked_missing_inputs"

    if any(status == "unsupported_manual_review" for status in path_statuses.values()) or manifest_status == "unsupported_manual_review":
        plan_status = "unsupported_manual_review"

    if installer_needs_manual:
        review_reasons.append("installer plan requires manual review")
    if storage_needs_manual:
        review_reasons.append("storage recommendations require manual review")

    recommended_map = {
        "ready_for_user_review": "review_user_install_write_set",
        "manual_review_required": "manual_user_install_review",
        "blocked_missing_inputs": "collect_missing_user_install_inputs",
        "unsupported_manual_review": "manual_platform_review",
    }
    recommended_next_step_kind = recommended_map[plan_status]

    write_set: list[dict[str, Any]] = []
    for role in _REQUIRED_ROLES:
        role_status = path_statuses[role]
        role_reason = path_reasons[role]
        if role_status == "planned_not_authorized" and plan_status == "manual_review_required":
            role_status = "manual_review_needed"
            role_reason = "Path is valid but manual review is required before any future install action."
        write_set.append(
            {
                "operation_kind": "create_directory_candidate",
                "role": role,
                "path": target_layout.get(role),
                "status": role_status,
                "execution_authorized": False,
                "write_authorized": False,
                "command": None,
                "reason": role_reason,
            }
        )

    manifest_item_status = manifest_status
    manifest_item_reason = "Future manifest write location only; no manifest write is authorized."
    if manifest_item_status == "planned_not_authorized" and plan_status == "manual_review_required":
        manifest_item_status = "manual_review_needed"

    write_set.append(
        {
            "operation_kind": "write_manifest_candidate",
            "role": "manifest",
            "path": target_layout.get("manifest_path"),
            "status": manifest_item_status,
            "execution_authorized": False,
            "write_authorized": False,
            "command": None,
            "reason": manifest_item_reason,
        }
    )

    requires_manual_review = plan_status in ("manual_review_required", "unsupported_manual_review")

    input_summaries = _build_input_summaries(installer_plan, storage_profile, install_manifest)

    return {
        "kind": USER_INSTALL_PLAN_KIND,
        "schema_version": USER_INSTALL_PLAN_SCHEMA_VERSION,
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
        "plan_status": plan_status,
        "recommended_next_step_kind": recommended_next_step_kind,
        "requires_manual_review": requires_manual_review,
        "blocked_reasons": blocked_reasons,
        "review_reasons": review_reasons,
        "target_layout": target_layout,
        "write_set": write_set,
        "input_summaries": input_summaries,
        "plan_notes": "Read-only user-space install write-set planning contract; no execution or writes are authorized.",
    }


def format_user_space_install_plan(plan: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("User-space install write-set report")
    lines.append("")
    lines.append(f"Plan status: {plan.get('plan_status', '(unknown)')}")
    lines.append(f"Recommended next step: {plan.get('recommended_next_step_kind', '(unknown)')}")
    lines.append("Execution authorized: false")
    lines.append("Write authorized: false")
    lines.append("")

    write_set = plan.get("write_set", [])
    if isinstance(write_set, list):
        for item in write_set:
            if not isinstance(item, dict):
                continue
            status = item.get("status", "?")
            operation_kind = item.get("operation_kind", "?")
            role = item.get("role", "?")
            path = item.get("path")
            lines.append(f"- [{status}] {operation_kind} {role} -> {path}")

    lines.append("")
    lines.append("No user-space install, directory creation, manifest write, package operation, service mutation, storage move, or command execution was performed.")
    return "\n".join(lines)
