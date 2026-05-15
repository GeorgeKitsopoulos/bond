#!/usr/bin/env python3
import json
import posixpath
from typing import Any

USER_INSTALL_WRITE_PREFLIGHT_SCHEMA_VERSION = 1
USER_INSTALL_WRITE_PREFLIGHT_KIND = "bond_user_space_install_write_preflight"
USER_INSTALL_WRITE_PREFLIGHT_PACKET_KIND = "bond_user_space_install_write_preflight_packet"

AUTHORIZATION_FIELDS = (
    "execution_authorized",
    "execution_allowed",
    "install_authorized",
    "package_install_authorized",
    "upgrade_authorized",
    "reconfigure_authorized",
    "service_authorized",
    "storage_move_authorized",
    "write_authorized",
    "write_manifest_authorized",
    "filesystem_write_authorized",
    "commands_generated",
    "approval_granted",
    "approval_validated",
)

ALLOWED_REQUESTED_MODES = {
    "fresh_install_preflight",
    "reconfigure_preflight",
    "update_preflight",
    "doctor_preflight",
}

PATH_KEYS = (
    "path",
    "target_path",
    "directory_path",
    "parent_path",
    "manifest_path",
    "destination_path",
    "data_path",
    "config_path",
    "cache_path",
    "model_path",
    "telemetry_path",
)


def _base_authorization() -> dict[str, bool]:
    return {field: False for field in AUTHORIZATION_FIELDS}


def _append_unique(values: list[str], message: str) -> None:
    if message not in values:
        values.append(message)


def _normalize_requested_mode(requested_mode: str | None) -> str:
    if not isinstance(requested_mode, str):
        return "doctor_preflight"
    normalized = requested_mode.strip()
    if normalized in ALLOWED_REQUESTED_MODES:
        return normalized
    return "doctor_preflight"


def _as_string_or_none(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value
    return None


def _as_list_of_strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def _as_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    return {}


def _recommended_next_step_kind(write_preflight_status: str) -> str:
    if write_preflight_status == "write_preflight_ready_execution_locked":
        return "review_write_preflight_packet_execution_locked"
    if write_preflight_status == "manual_review_required":
        return "manual_write_preflight_review_required"
    if write_preflight_status == "blocked_missing_inputs":
        return "collect_missing_write_preflight_inputs"
    if write_preflight_status == "blocked_unsafe_write_targets":
        return "correct_or_reselect_write_targets"
    return "manual_platform_review"


def _map_status_from_review(report_status: Any) -> str:
    if report_status == "ready_for_human_review_execution_locked":
        return "write_preflight_ready_execution_locked"
    if report_status == "manual_review_required":
        return "manual_review_required"
    if report_status == "unsupported_manual_review":
        return "unsupported_manual_review"
    if report_status == "blocked_missing_inputs":
        return "blocked_missing_inputs"
    return "unsupported_manual_review"


def _has_upstream_authorization(report: dict[str, Any], human_review_packet: dict[str, Any]) -> bool:
    for field in AUTHORIZATION_FIELDS:
        if report.get(field):
            return True
        if human_review_packet.get(field):
            return True

    packet_lock = _as_dict(human_review_packet.get("execution_lock"))
    packet_auth = _as_dict(human_review_packet.get("authorization"))
    for field in AUTHORIZATION_FIELDS:
        if packet_lock.get(field):
            return True
        if packet_auth.get(field):
            return True
    return False


def _protected_root(path_value: str) -> str | None:
    protected_roots = (
        "/bin",
        "/boot",
        "/dev",
        "/etc",
        "/lib",
        "/lib64",
        "/proc",
        "/root",
        "/sbin",
        "/sys",
        "/usr",
    )
    for root in protected_roots:
        if path_value == root or path_value.startswith(root + "/"):
            return root
    return None


def _is_exact_or_child(path_value: str, root: str) -> bool:
    return path_value == root or path_value.startswith(root + "/")


def _contains_traversal(path_value: str) -> bool:
    return ".." in [component for component in path_value.split("/") if component]


def _check_path_safety(target_role: str, path_value: Any) -> dict[str, Any]:
    reasons: list[str] = []
    normalized_path: str | None = None

    if not isinstance(path_value, str):
        reasons.append("path is missing or not a string")
        return {
            "target_role": target_role,
            "path": path_value,
            "normalized_path": normalized_path,
            "path_status": "blocked",
            "reasons": reasons,
        }

    if not path_value:
        reasons.append("path is empty")
        return {
            "target_role": target_role,
            "path": path_value,
            "normalized_path": normalized_path,
            "path_status": "blocked",
            "reasons": reasons,
        }

    if not path_value.startswith("/"):
        reasons.append("path is not absolute")
        return {
            "target_role": target_role,
            "path": path_value,
            "normalized_path": normalized_path,
            "path_status": "blocked",
            "reasons": reasons,
        }

    if _contains_traversal(path_value):
        reasons.append("path contains traversal components")
        return {
            "target_role": target_role,
            "path": path_value,
            "normalized_path": normalized_path,
            "path_status": "blocked",
            "reasons": reasons,
        }

    normalized_path = posixpath.normpath(path_value)

    if normalized_path == "/":
        reasons.append("path targets filesystem root")
        return {
            "target_role": target_role,
            "path": path_value,
            "normalized_path": normalized_path,
            "path_status": "blocked",
            "reasons": reasons,
        }

    if normalized_path == "/run":
        reasons.append("path is under protected system root: /run")
        return {
            "target_role": target_role,
            "path": path_value,
            "normalized_path": normalized_path,
            "path_status": "blocked",
            "reasons": reasons,
        }

    if _is_exact_or_child(normalized_path, "/run/user"):
        reasons.append("runtime user path is not a persistent install target")
        return {
            "target_role": target_role,
            "path": path_value,
            "normalized_path": normalized_path,
            "path_status": "blocked",
            "reasons": reasons,
        }

    if _is_exact_or_child(normalized_path, "/run/media"):
        reasons.append("removable or externally mounted storage requires review")
        return {
            "target_role": target_role,
            "path": path_value,
            "normalized_path": normalized_path,
            "path_status": "manual_review_required",
            "reasons": reasons,
        }

    protected_root = _protected_root(normalized_path)
    if protected_root is not None:
        reasons.append(f"path is under protected system root: {protected_root}")
        return {
            "target_role": target_role,
            "path": path_value,
            "normalized_path": normalized_path,
            "path_status": "blocked",
            "reasons": reasons,
        }

    if _is_exact_or_child(normalized_path, "/tmp"):
        reasons.append("temporary path is not a persistent install target")
        return {
            "target_role": target_role,
            "path": path_value,
            "normalized_path": normalized_path,
            "path_status": "blocked",
            "reasons": reasons,
        }

    if _is_exact_or_child(normalized_path, "/mnt"):
        reasons.append("external storage path requires review")
        return {
            "target_role": target_role,
            "path": path_value,
            "normalized_path": normalized_path,
            "path_status": "manual_review_required",
            "reasons": reasons,
        }

    if _is_exact_or_child(normalized_path, "/media"):
        reasons.append("external storage path requires review")
        return {
            "target_role": target_role,
            "path": path_value,
            "normalized_path": normalized_path,
            "path_status": "manual_review_required",
            "reasons": reasons,
        }

    if _is_exact_or_child(normalized_path, "/home"):
        return {
            "target_role": target_role,
            "path": path_value,
            "normalized_path": normalized_path,
            "path_status": "safe_candidate",
            "reasons": reasons,
        }

    reasons.append("non-standard absolute path requires review")
    return {
        "target_role": target_role,
        "path": path_value,
        "normalized_path": normalized_path,
        "path_status": "manual_review_required",
        "reasons": reasons,
    }


def _collect_targets(
    *,
    manifest_path: str | None,
    reviewed_operations_sources: list[Any],
) -> tuple[dict[str, Any] | None, list[dict[str, str]], list[dict[str, str]], list[str]]:
    all_candidate_targets: list[dict[str, str]] = []
    directory_create_candidates: list[dict[str, str]] = []
    blocked_reasons: list[str] = []
    seen_pairs: set[tuple[str, str]] = set()

    manifest_target: dict[str, str] | None = None
    if manifest_path is not None:
        manifest_target = {
            "target_role": "manifest_write_candidate",
            "path": manifest_path,
        }
        pair = (manifest_target["target_role"], manifest_target["path"])
        seen_pairs.add(pair)
        all_candidate_targets.append(manifest_target)

    for source in reviewed_operations_sources:
        if not isinstance(source, list):
            continue
        for operation in source:
            if not isinstance(operation, dict):
                _append_unique(blocked_reasons, "reviewed operation is malformed")
                continue

            operation_role = _as_string_or_none(operation.get("role")) or "reviewed_operation"
            operation_kind = _as_string_or_none(operation.get("operation_kind"))

            for key in PATH_KEYS:
                path_value = operation.get(key)
                if not isinstance(path_value, str):
                    continue

                target_role = f"{operation_role}:{key}"
                pair = (target_role, path_value)
                if pair in seen_pairs:
                    continue

                target = {
                    "target_role": target_role,
                    "path": path_value,
                }
                seen_pairs.add(pair)
                all_candidate_targets.append(target)

                looks_like_directory_candidate = (
                    key in {"directory_path", "parent_path"}
                    or operation_kind == "create_directory_candidate"
                    or "directory" in target_role
                )
                if looks_like_directory_candidate:
                    directory_create_candidates.append(target)

    return manifest_target, directory_create_candidates, all_candidate_targets, blocked_reasons


def build_user_install_write_preflight(
    *,
    user_install_review_report: dict[str, Any] | None = None,
    requested_mode: str | None = None,
) -> dict[str, Any]:
    normalized_mode = _normalize_requested_mode(requested_mode)

    blocked_reasons: list[str] = []
    review_reasons: list[str] = []
    denial_reasons: list[str] = []

    manifest_path: str | None = None
    transaction_digest: str | None = None
    approval_envelope_digest: str | None = None
    report_status: Any = None
    input_summaries: dict[str, Any] = {}
    status = "blocked_missing_inputs"
    requires_manual_review = False

    candidate_write_set = {
        "manifest_write_candidate": None,
        "directory_create_candidates": [],
        "all_candidate_targets": [],
    }
    path_safety_checks: list[dict[str, Any]] = []

    review_report = user_install_review_report if isinstance(user_install_review_report, dict) else None
    human_review_packet: dict[str, Any] = {}

    if review_report is None or review_report.get("kind") != "bond_user_space_install_review_report":
        _append_unique(blocked_reasons, "user_install_review_report is missing or invalid")
    else:
        human_review_packet = _as_dict(review_report.get("human_review_packet"))

        report_status = review_report.get("report_status")
        status = _map_status_from_review(report_status)

        requires_manual_review = review_report.get("requires_manual_review") is True
        for reason in _as_list_of_strings(review_report.get("blocked_reasons")):
            _append_unique(blocked_reasons, reason)
        for reason in _as_list_of_strings(review_report.get("review_reasons")):
            _append_unique(review_reasons, reason)
        for reason in _as_list_of_strings(review_report.get("denial_reasons")):
            _append_unique(denial_reasons, reason)

        manifest_path = _as_string_or_none(review_report.get("manifest_path"))
        transaction_digest = _as_string_or_none(review_report.get("transaction_digest"))
        approval_envelope_digest = _as_string_or_none(review_report.get("approval_envelope_digest"))

        packet_identifiers = _as_dict(human_review_packet.get("identifiers"))
        if manifest_path is None:
            manifest_path = _as_string_or_none(packet_identifiers.get("manifest_path"))
        if transaction_digest is None:
            transaction_digest = _as_string_or_none(packet_identifiers.get("transaction_digest"))
        if approval_envelope_digest is None:
            approval_envelope_digest = _as_string_or_none(packet_identifiers.get("approval_envelope_digest"))

        input_summaries_value = review_report.get("input_summaries")
        if isinstance(input_summaries_value, dict):
            input_summaries = input_summaries_value
        else:
            _append_unique(blocked_reasons, "input summaries are missing or invalid")

        if _has_upstream_authorization(review_report, human_review_packet):
            _append_unique(
                denial_reasons,
                "upstream review report attempted to authorize execution, approval, commands, or writes",
            )
            status = "unsupported_manual_review"

        packet_operation_summary = _as_dict(human_review_packet.get("operation_summary"))
        packet_reviewed_operations = packet_operation_summary.get("reviewed_operations")

        local_packet = _as_dict(review_report.get("human_review_packet"))
        local_operation_summary = _as_dict(local_packet.get("operation_summary"))
        local_reviewed_operations = local_operation_summary.get("reviewed_operations")

        (
            manifest_target,
            directory_create_candidates,
            all_candidate_targets,
            target_collection_blockers,
        ) = _collect_targets(
            manifest_path=manifest_path,
            reviewed_operations_sources=[packet_reviewed_operations, local_reviewed_operations],
        )
        candidate_write_set = {
            "manifest_write_candidate": manifest_target,
            "directory_create_candidates": directory_create_candidates,
            "all_candidate_targets": all_candidate_targets,
        }
        for reason in target_collection_blockers:
            _append_unique(blocked_reasons, reason)

        for target in all_candidate_targets:
            path_safety_checks.append(
                _check_path_safety(target.get("target_role", "reviewed_operation"), target.get("path"))
            )

        if manifest_path is None:
            _append_unique(blocked_reasons, "manifest path is missing")
        if transaction_digest is None:
            _append_unique(blocked_reasons, "transaction digest is missing")
        if approval_envelope_digest is None:
            _append_unique(blocked_reasons, "approval envelope digest is missing")

        if status not in {"unsupported_manual_review", "blocked_unsafe_write_targets"} and blocked_reasons:
            status = "blocked_missing_inputs"

        blocked_target_found = any(item.get("path_status") == "blocked" for item in path_safety_checks)
        manual_target_found = any(item.get("path_status") == "manual_review_required" for item in path_safety_checks)

        if status not in {"unsupported_manual_review", "blocked_missing_inputs"} and blocked_target_found:
            status = "blocked_unsafe_write_targets"
            _append_unique(blocked_reasons, "candidate write targets include blocked paths")

        if (
            status not in {"unsupported_manual_review", "blocked_missing_inputs", "blocked_unsafe_write_targets"}
            and (manual_target_found or requires_manual_review)
        ):
            status = "manual_review_required"

    for reason in blocked_reasons:
        _append_unique(denial_reasons, reason)
    for reason in review_reasons:
        _append_unique(denial_reasons, reason)

    recommended_next_step_kind = _recommended_next_step_kind(status)
    requires_manual_review = bool(
        requires_manual_review
        or review_reasons
        or status in {"manual_review_required", "unsupported_manual_review"}
        or any(item.get("path_status") == "manual_review_required" for item in path_safety_checks)
    )

    write_preflight_packet = {
        "kind": USER_INSTALL_WRITE_PREFLIGHT_PACKET_KIND,
        "requested_mode": normalized_mode,
        "write_preflight_status": status,
        "review_subject": "user_space_install_write_preflight",
        "identifiers": {
            "manifest_path": manifest_path,
            "transaction_digest": transaction_digest,
            "approval_envelope_digest": approval_envelope_digest,
        },
        "execution_lock": {
            "execution_allowed": False,
            "execution_authorized": False,
            "write_authorized": False,
            "write_manifest_authorized": False,
            "filesystem_write_authorized": False,
            "approval_granted": False,
            "approval_validated": False,
            "future_write_executor_available": False,
            "explicit_future_approval_required": True,
        },
        "candidate_write_set": candidate_write_set,
        "path_safety_checks": path_safety_checks,
        "blockers": blocked_reasons,
        "manual_review_reasons": review_reasons,
        "denial_reasons": denial_reasons,
        "safety_boundary": [
            "Write preflight only; execution remains locked.",
            "No approval was validated.",
            "No user-space install, directory creation, manifest write, package operation, service mutation, storage move, command generation, or command execution was performed.",
        ],
    }

    write_preflight_json_preview = json.dumps(
        write_preflight_packet,
        sort_keys=True,
        indent=2,
        ensure_ascii=False,
    )

    return {
        "kind": USER_INSTALL_WRITE_PREFLIGHT_KIND,
        "schema_version": USER_INSTALL_WRITE_PREFLIGHT_SCHEMA_VERSION,
        **_base_authorization(),
        "requested_mode": normalized_mode,
        "write_preflight_status": status,
        "recommended_next_step_kind": recommended_next_step_kind,
        "requires_manual_review": requires_manual_review,
        "blocked_reasons": blocked_reasons,
        "review_reasons": review_reasons,
        "denial_reasons": denial_reasons,
        "manifest_path": manifest_path,
        "transaction_digest": transaction_digest,
        "approval_envelope_digest": approval_envelope_digest,
        "candidate_write_set": candidate_write_set,
        "path_safety_checks": path_safety_checks,
        "write_preflight_packet": write_preflight_packet,
        "write_preflight_json_preview": write_preflight_json_preview,
        "input_summaries": input_summaries,
        "plan_notes": [
            "Write preflight only; execution remains locked.",
            "No approval was validated, and no user-space install, directory creation, manifest write, package operation, service mutation, storage move, command generation, or command execution was performed.",
        ],
    }


def format_user_install_write_preflight(report: dict[str, Any]) -> str:
    candidate_write_set = report.get("candidate_write_set")
    if not isinstance(candidate_write_set, dict):
        candidate_write_set = {}

    all_candidate_targets = candidate_write_set.get("all_candidate_targets")
    if not isinstance(all_candidate_targets, list):
        all_candidate_targets = []

    path_safety_checks = report.get("path_safety_checks")
    if not isinstance(path_safety_checks, list):
        path_safety_checks = []

    lines = [
        "User-space install write preflight",
        f"Write preflight status: {report.get('write_preflight_status')}",
        f"Recommended next step: {report.get('recommended_next_step_kind')}",
        f"Manifest path: {report.get('manifest_path')}",
        f"Transaction digest: {report.get('transaction_digest')}",
        f"Approval envelope digest: {report.get('approval_envelope_digest')}",
        "Execution allowed: false",
        "Execution authorized: false",
        "Write authorized: false",
        "Write manifest authorized: false",
        "Filesystem write authorized: false",
        "Approval granted: false",
        "Approval validated: false",
        "Candidate write targets:",
    ]

    for target in all_candidate_targets:
        if not isinstance(target, dict):
            continue
        lines.append(f"- {target.get('target_role')}: {target.get('path')}")

    lines.append("Path safety checks:")
    for check in path_safety_checks:
        if not isinstance(check, dict):
            continue
        lines.append(
            f"- {check.get('target_role')} -> {check.get('normalized_path')} ({check.get('path_status')}): {', '.join(check.get('reasons', []))}"
        )

    lines.extend(
        [
            "Write preflight JSON preview:",
            str(report.get("write_preflight_json_preview", "")),
            "No approval was validated, and no user-space install, directory creation, manifest write, package operation, service mutation, storage move, command generation, or command execution was performed.",
        ]
    )
    return "\n".join(lines)