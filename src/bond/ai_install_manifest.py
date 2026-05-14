#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from typing import Any

INSTALL_MANIFEST_SCHEMA_VERSION = 1
INSTALL_DRIFT_SCHEMA_VERSION = 1
INSTALL_MANIFEST_KIND = "bond_install_manifest"
INSTALL_DRIFT_KIND = "bond_install_drift_report"

_ENV_PATH_KEYS = (
    "BOND_HOME",
    "BOND_CONFIG_DIR",
    "BOND_DATA_DIR",
    "BOND_CACHE_DIR",
    "BOND_MODEL_DIR",
    "BOND_TELEMETRY_DIR",
    "BOND_BACKUP_DIR",
)


def _text(value: Any) -> str | None:
    if isinstance(value, str):
        return value
    if value is None:
        return None
    return str(value)


def _mapping(value: Any) -> Mapping[str, object]:
    if isinstance(value, Mapping):
        return value
    return {}


def _clean_scalar(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return _text(value)


def _first_present(*values: Any) -> Any:
    for value in values:
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        return value
    return None


def _normalize_env_paths(env_paths: Mapping[str, object] | None) -> dict[str, object]:
    source = _mapping(env_paths)
    normalized: dict[str, object] = {}
    for name in _ENV_PATH_KEYS:
        raw_value = source.get(name)
        if isinstance(raw_value, Mapping):
            normalized[name] = _text(raw_value.get("path"))
        else:
            normalized[name] = _text(raw_value)
    return normalized


def _normalize_host_summary(host_profile: Mapping[str, object] | None) -> dict[str, object]:
    profile = _mapping(host_profile)
    os_release = _mapping(profile.get("os_release"))
    dependency_strategy = _mapping(profile.get("dependency_strategy"))
    platform_signals = _mapping(profile.get("platform_signals"))
    service_backends = _mapping(profile.get("service_backends"))

    return {
        "architecture": _clean_scalar(
            _first_present(
                profile.get("architecture"),
                profile.get("platform_machine"),
                profile.get("machine"),
            )
        ),
        "machine": _clean_scalar(_first_present(profile.get("machine"), profile.get("platform_machine"))),
        "system": _clean_scalar(_first_present(profile.get("system"), profile.get("platform_system"))),
        "os_id": _clean_scalar(_first_present(profile.get("os_id"), os_release.get("ID"))),
        "os_family": _clean_scalar(_first_present(profile.get("os_family"), profile.get("distro_family"))),
        "distro_id": _clean_scalar(_first_present(profile.get("distro_id"), os_release.get("ID"))),
        "distro_like": _clean_scalar(_first_present(profile.get("distro_like"), os_release.get("ID_LIKE"))),
        "package_manager": _clean_scalar(
            _first_present(profile.get("package_manager"), dependency_strategy.get("native_package_manager"))
        ),
        "service_manager": _clean_scalar(
            _first_present(
                profile.get("service_manager"),
                "systemd" if service_backends.get("systemd_user_possible") is True else None,
            )
        ),
        "init_system": _clean_scalar(
            _first_present(
                profile.get("init_system"),
                "systemd" if service_backends.get("systemd_user_possible") is True else None,
            )
        ),
        "immutable_hint": _clean_scalar(
            _first_present(
                profile.get("immutable_hint"),
                profile.get("immutable_host"),
                platform_signals.get("is_atomic_or_image_based_like"),
            )
        ),
        "steam_deck_hint": _clean_scalar(
            _first_present(
                profile.get("steam_deck_hint"),
                profile.get("steam_deck_like"),
                platform_signals.get("is_steam_deck_like"),
            )
        ),
    }


def _space_pressure(storage_profile: Mapping[str, object]) -> str:
    candidate_summary = _mapping(storage_profile.get("candidate_summary"))
    summary = _mapping(candidate_summary.get("space_pressure_summary"))
    if not summary:
        return "unknown"
    if int(summary.get("critical", 0) or 0) > 0:
        return "critical"
    if int(summary.get("low", 0) or 0) > 0:
        return "low"
    if int(summary.get("large_data_friendly", 0) or 0) > 0:
        return "large_data_friendly"
    if int(summary.get("adequate", 0) or 0) > 0:
        return "adequate"
    return "unknown"


def _normalize_storage_summary(storage_profile: Mapping[str, object] | None) -> dict[str, object]:
    profile = _mapping(storage_profile)
    candidate_summary = _mapping(profile.get("candidate_summary"))
    recommendations = _mapping(profile.get("recommendations"))
    home_mount_record = _mapping(candidate_summary.get("home_mount"))

    first_large_data_candidate = None
    for key in ("large_data_candidates", "steam_deck_sd_candidates", "external_candidates"):
        candidates = candidate_summary.get(key)
        if not isinstance(candidates, list):
            continue
        for candidate in candidates:
            if isinstance(candidate, Mapping):
                mount_point = _text(candidate.get("mount_point"))
                if mount_point:
                    first_large_data_candidate = mount_point
                    break
        if first_large_data_candidate:
            break

    role_paths: dict[str, object] = {}
    role_recommendations = recommendations.get("role_recommendations")
    if isinstance(role_recommendations, list):
        for recommendation in role_recommendations:
            if not isinstance(recommendation, Mapping):
                continue
            role = _text(recommendation.get("role"))
            preferred_base = _text(recommendation.get("preferred_base"))
            if role:
                role_paths[role] = preferred_base

    return {
        "home_mount_point": _clean_scalar(home_mount_record.get("mount_point")),
        "home_device": _clean_scalar(home_mount_record.get("device")),
        "preferred_large_data_base": _clean_scalar(recommendations.get("preferred_large_data_base")),
        "external_large_data_candidate": _clean_scalar(first_large_data_candidate),
        "requires_manual_review": bool(recommendations.get("requires_manual_review") is True),
        "storage_pressure": _space_pressure(profile),
        "role_paths": role_paths,
    }


def _fingerprint_source(host_summary: Mapping[str, object]) -> dict[str, object]:
    return {
        "architecture": host_summary.get("architecture"),
        "system": host_summary.get("system"),
        "os_id": host_summary.get("os_id"),
        "os_family": host_summary.get("os_family"),
        "distro_id": host_summary.get("distro_id"),
        "distro_like": host_summary.get("distro_like"),
        "package_manager": host_summary.get("package_manager"),
        "service_manager": host_summary.get("service_manager"),
        "init_system": host_summary.get("init_system"),
        "immutable_hint": host_summary.get("immutable_hint"),
        "steam_deck_hint": host_summary.get("steam_deck_hint"),
    }


def _host_fingerprint(host_summary: Mapping[str, object]) -> str:
    payload = json.dumps(_fingerprint_source(host_summary), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_install_manifest(
    *,
    host_profile=None,
    storage_profile=None,
    bond_root=None,
    repo_commit=None,
    python_version=None,
    env_paths=None,
    service_backend=None,
    created_at=None,
) -> dict:
    host_summary = _normalize_host_summary(_mapping(host_profile))
    storage_summary = _normalize_storage_summary(_mapping(storage_profile))
    env_summary = _normalize_env_paths(_mapping(env_paths))

    resolved_python_version = _clean_scalar(
        _first_present(python_version, _mapping(host_profile).get("python_version"))
    )
    resolved_service_backend = _clean_scalar(
        _first_present(
            service_backend,
            _mapping(host_profile).get("service_backend"),
            _mapping(_mapping(host_profile).get("service_backends")).get("preferred_initial_backend"),
        )
    )

    return {
        "kind": INSTALL_MANIFEST_KIND,
        "schema_version": INSTALL_MANIFEST_SCHEMA_VERSION,
        "created_at": _clean_scalar(created_at),
        "execution_authorized": False,
        "install_authorized": False,
        "reconfigure_authorized": False,
        "write_manifest_authorized": False,
        "bond_root": _clean_scalar(bond_root),
        "repo_commit": _clean_scalar(repo_commit),
        "python_version": resolved_python_version,
        "service_backend": resolved_service_backend,
        "host_fingerprint": _host_fingerprint(host_summary),
        "host": host_summary,
        "storage": storage_summary,
        "env_paths": env_summary,
        "manifest_notes": [
            "read-only install manifest only",
            "built from supplied bounded facts only",
            "no manifest persistence",
            "no install or reconfigure authorization",
        ],
    }


def _invalid_manifest_report(reason: str, next_step: str, note: str) -> dict:
    return {
        "kind": INSTALL_DRIFT_KIND,
        "schema_version": INSTALL_DRIFT_SCHEMA_VERSION,
        "execution_authorized": False,
        "install_authorized": False,
        "reconfigure_authorized": False,
        "drift_detected": False,
        "drift_count": 0,
        "drift_severity": "warning",
        "drift_items": [],
        "recommended_next_step_kind": next_step,
        "requires_manual_review": True,
        "report_notes": [reason, note, "no install, reconfigure, or manifest-write action was performed or authorized"],
    }


def _is_supported_manifest(manifest: Any) -> bool:
    if not isinstance(manifest, Mapping):
        return False
    if manifest.get("kind") != INSTALL_MANIFEST_KIND:
        return False
    if manifest.get("schema_version") != INSTALL_MANIFEST_SCHEMA_VERSION:
        return False
    return True


def _manifest_value(manifest: Mapping[str, object], field: str) -> Any:
    if field == "host.immutable_hint":
        host = _mapping(manifest.get("host"))
        return _first_present(host.get("immutable_hint"), host.get("immutable_host"))

    current: Any = manifest
    for part in field.split("."):
        if not isinstance(current, Mapping):
            return None
        current = current.get(part)
    return current


def _drift_category(field: str) -> str:
    if field.startswith("env_paths."):
        return "env_path_drift"
    if field.startswith("storage."):
        return "storage_drift"
    if field.startswith("host.") or field == "host_fingerprint":
        return "host_drift"
    if field in {"repo_commit", "bond_root"}:
        return "repo_drift"
    return "runtime_drift"


def _drift_severity(field: str) -> str:
    if field in {
        "host.architecture",
        "host.os_family",
        "host.package_manager",
        "bond_root",
        "env_paths.BOND_HOME",
        "storage.preferred_large_data_base",
    }:
        return "critical"
    if field in {
        "python_version",
        "service_backend",
        "host.service_manager",
        "host.immutable_hint",
        "repo_commit",
        "env_paths.BOND_CONFIG_DIR",
        "env_paths.BOND_DATA_DIR",
        "env_paths.BOND_CACHE_DIR",
        "env_paths.BOND_MODEL_DIR",
        "env_paths.BOND_TELEMETRY_DIR",
        "env_paths.BOND_BACKUP_DIR",
    }:
        return "warning"
    return "info"


def _drift_note(field: str) -> str:
    if field.startswith("env_paths."):
        return "Explicit Bond path drift requires review before any future reconfiguration."
    if field == "storage.preferred_large_data_base":
        return "Preferred large-data base changed; review storage placement before any future reconfiguration."
    if field in {"host.architecture", "host.os_family", "host.package_manager"}:
        return "Host portability baseline changed; review compatibility before any future reconfiguration."
    return "Read-only drift observation only; no install, reconfigure, or write action was performed."


def compare_install_manifest(saved_manifest, current_manifest) -> dict:
    if not _is_supported_manifest(saved_manifest):
        return _invalid_manifest_report(
            "saved_manifest_missing_or_invalid",
            "create_manifest_review",
            "A saved install manifest was not supplied or did not match the supported manifest contract.",
        )
    if not _is_supported_manifest(current_manifest):
        return _invalid_manifest_report(
            "current_manifest_missing_or_invalid",
            "inspect_current_profile",
            "The current install manifest input was not supplied or did not match the supported manifest contract.",
        )

    saved_node = _mapping(saved_manifest)
    current_node = _mapping(current_manifest)
    fields = [
        "repo_commit",
        "bond_root",
        "python_version",
        "service_backend",
        "host_fingerprint",
        "host.architecture",
        "host.os_family",
        "host.os_id",
        "host.package_manager",
        "host.service_manager",
        "host.immutable_hint",
        "storage.preferred_large_data_base",
        "storage.home_mount_point",
        "env_paths.BOND_HOME",
        "env_paths.BOND_CONFIG_DIR",
        "env_paths.BOND_DATA_DIR",
        "env_paths.BOND_CACHE_DIR",
        "env_paths.BOND_MODEL_DIR",
        "env_paths.BOND_TELEMETRY_DIR",
        "env_paths.BOND_BACKUP_DIR",
    ]

    drift_items: list[dict[str, object]] = []
    for field in fields:
        previous = _manifest_value(saved_node, field)
        current = _manifest_value(current_node, field)
        if previous == current:
            continue
        severity = _drift_severity(field)
        drift_items.append(
            {
                "field": field,
                "previous": previous,
                "current": current,
                "severity": severity,
                "category": _drift_category(field),
                "note": _drift_note(field),
            }
        )

    severity_order = {"none": 0, "info": 1, "warning": 2, "critical": 3}
    overall_severity = "none"
    for item in drift_items:
        item_severity = _text(item.get("severity")) or "info"
        if severity_order.get(item_severity, 0) > severity_order[overall_severity]:
            overall_severity = item_severity

    drift_detected = bool(drift_items)
    if not drift_detected:
        recommended_next_step_kind = "none"
        requires_manual_review = False
    elif overall_severity == "critical":
        recommended_next_step_kind = "review_before_reconfigure"
        requires_manual_review = True
    else:
        recommended_next_step_kind = "review_manifest"
        requires_manual_review = False

    return {
        "kind": INSTALL_DRIFT_KIND,
        "schema_version": INSTALL_DRIFT_SCHEMA_VERSION,
        "execution_authorized": False,
        "install_authorized": False,
        "reconfigure_authorized": False,
        "drift_detected": drift_detected,
        "drift_count": len(drift_items),
        "drift_severity": overall_severity,
        "drift_items": drift_items,
        "recommended_next_step_kind": recommended_next_step_kind,
        "requires_manual_review": requires_manual_review,
        "report_notes": [
            "read-only drift comparison only",
            "no manifest persistence",
            "no install, reconfigure, or manifest-write action was performed or authorized",
        ],
    }


def format_install_drift_report(report) -> str:
    node = _mapping(report)
    lines = [
        "Install manifest drift report",
        f"Drift detected: {'yes' if node.get('drift_detected') else 'no'}",
        f"Severity: {_text(node.get('drift_severity')) or 'unknown'}",
        f"Recommended next step: {_text(node.get('recommended_next_step_kind')) or 'unknown'}",
    ]
    drift_items = node.get("drift_items")
    if isinstance(drift_items, list) and drift_items:
        lines.append("Drift items:")
        for item in drift_items:
            if not isinstance(item, Mapping):
                continue
            field = _text(item.get("field")) or "unknown"
            severity = _text(item.get("severity")) or "unknown"
            previous = item.get("previous")
            current = item.get("current")
            lines.append(f"- {field}: {severity} ({previous!r} -> {current!r})")
    lines.append("Boundary: no install, reconfigure, or manifest-write action was performed or authorized.")
    return "\n".join(lines)