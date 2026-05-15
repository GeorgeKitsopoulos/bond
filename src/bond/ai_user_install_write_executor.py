#!/usr/bin/env python3
import hashlib
import json
from typing import Any

USER_INSTALL_WRITE_EXECUTOR_SCHEMA_VERSION = 1
USER_INSTALL_WRITE_EXECUTOR_KIND = "bond_user_space_install_write_executor"
USER_INSTALL_WRITE_EXECUTOR_PACKET_KIND = "bond_user_space_install_write_executor_disabled_packet"

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
    "fresh_install_executor",
    "reconfigure_executor",
    "update_executor",
    "doctor_executor",
}


def _base_authorization() -> dict[str, bool]:
    return {field: False for field in AUTHORIZATION_FIELDS}


def _append_unique(values: list[str], message: str) -> None:
    if message not in values:
        values.append(message)


def _normalize_requested_mode(requested_mode: str | None) -> str:
    if not isinstance(requested_mode, str):
        return "doctor_executor"
    normalized = requested_mode.strip()
    if normalized in ALLOWED_REQUESTED_MODES:
        return normalized
    return "doctor_executor"


def _as_list_of_strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def _as_string_or_none(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value
    return None


def _as_nonnegative_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int) and value >= 0:
        return value
    return None


def _json_sha256_hex(value: Any) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _truthy_authorization_present(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    for field in AUTHORIZATION_FIELDS:
        if value.get(field):
            return True
    return False


def _normalize_operation_kind(value: Any, default: str) -> str:
    if isinstance(value, str) and value.strip():
        return value
    return default


def _normalize_target(value: Any) -> str:
    if isinstance(value, str) and value.strip():
        return value
    return "unknown_target"


def _append_refused_operation(refused_operations: list[dict[str, str]], operation_kind: str, target: str) -> None:
    entry = {
        "operation_kind": operation_kind,
        "target": target,
        "refusal_reason": "executor is disabled and execution remains locked",
    }
    if entry not in refused_operations:
        refused_operations.append(entry)


def _extract_from_candidate_write_set(value: Any, refused_operations: list[dict[str, str]]) -> None:
    if isinstance(value, list):
        for item in value:
            _extract_from_candidate_write_set(item, refused_operations)
        return

    if not isinstance(value, dict):
        return

    all_targets = value.get("all_candidate_targets")
    if isinstance(all_targets, list):
        for item in all_targets:
            if isinstance(item, dict):
                target = _normalize_target(item.get("path") or item.get("target"))
                operation_kind = _normalize_operation_kind(item.get("target_role"), "write_candidate")
            else:
                target = _normalize_target(item)
                operation_kind = "write_candidate"
            _append_refused_operation(refused_operations, operation_kind, target)
        return

    for key, item in value.items():
        if key == "all_candidate_targets":
            continue
        if isinstance(item, list):
            for sub_item in item:
                if isinstance(sub_item, dict):
                    target = _normalize_target(sub_item.get("path") or sub_item.get("target"))
                    operation_kind = _normalize_operation_kind(sub_item.get("target_role") or key, "write_candidate")
                else:
                    target = _normalize_target(sub_item)
                    operation_kind = _normalize_operation_kind(key, "write_candidate")
                _append_refused_operation(refused_operations, operation_kind, target)
            continue
        if isinstance(item, dict):
            target = _normalize_target(item.get("path") or item.get("target"))
            operation_kind = _normalize_operation_kind(item.get("target_role") or key, "write_candidate")
            _append_refused_operation(refused_operations, operation_kind, target)
            continue
        target = _normalize_target(item)
        operation_kind = _normalize_operation_kind(key, "write_candidate")
        _append_refused_operation(refused_operations, operation_kind, target)


def _extract_from_path_safety_checks(value: Any, refused_operations: list[dict[str, str]]) -> None:
    if not isinstance(value, list):
        return
    for item in value:
        if isinstance(item, dict):
            target = _normalize_target(
                item.get("path")
                or item.get("normalized_path")
                or item.get("target")
            )
            operation_kind = _normalize_operation_kind(
                item.get("target_role") or item.get("operation_kind") or item.get("path_status"),
                "path_safety_check",
            )
        else:
            target = _normalize_target(item)
            operation_kind = "path_safety_check"
        _append_refused_operation(refused_operations, operation_kind, target)


def _extract_refused_operations(
    approval_challenge: dict[str, Any],
    input_summaries: dict[str, Any],
    manifest_path: str | None,
) -> list[dict[str, str]]:
    refused_operations: list[dict[str, str]] = []

    expected_values = approval_challenge.get("expected_values")
    if isinstance(expected_values, dict):
        _extract_from_candidate_write_set(expected_values.get("candidate_write_set"), refused_operations)
        _extract_from_path_safety_checks(expected_values.get("path_safety_checks"), refused_operations)

    _extract_from_candidate_write_set(approval_challenge.get("candidate_write_set"), refused_operations)
    _extract_from_path_safety_checks(approval_challenge.get("path_safety_checks"), refused_operations)

    _extract_from_candidate_write_set(input_summaries.get("candidate_write_set"), refused_operations)
    _extract_from_path_safety_checks(input_summaries.get("path_safety_checks"), refused_operations)

    if not refused_operations and manifest_path:
        refused_operations.append(
            {
                "operation_kind": "manifest_or_install_write_candidate",
                "target": manifest_path,
                "refusal_reason": "executor is disabled and execution remains locked",
            }
        )

    return refused_operations


def _base_status(approval_validation_status: Any) -> str:
    if approval_validation_status == "approval_validation_ready_execution_locked":
        return "disabled_execution_locked"
    if approval_validation_status == "manual_review_required":
        return "disabled_manual_review_required"
    if approval_validation_status == "blocked_missing_inputs":
        return "blocked_missing_inputs"
    if approval_validation_status == "blocked_unsafe_write_targets":
        return "blocked_unsafe_write_targets"
    if approval_validation_status == "unsupported_manual_review":
        return "unsupported_manual_review"
    return "unsupported_manual_review"


def _recommended_next_step_kind(executor_status: str) -> str:
    if executor_status == "disabled_execution_locked":
        return "review_disabled_executor_packet"
    if executor_status == "disabled_manual_review_required":
        return "manual_executor_review_required"
    if executor_status == "blocked_missing_inputs":
        return "collect_missing_executor_inputs"
    if executor_status == "blocked_unsafe_write_targets":
        return "correct_or_reselect_write_targets"
    return "manual_platform_review"


def build_user_install_write_executor(
    *,
    user_install_approval_validation: dict[str, Any] | None = None,
    requested_mode: str | None = None,
) -> dict[str, Any]:
    normalized_mode = _normalize_requested_mode(requested_mode)
    blocked_reasons: list[str] = []
    review_reasons: list[str] = []
    denial_reasons: list[str] = []

    if (
        not isinstance(user_install_approval_validation, dict)
        or user_install_approval_validation.get("kind") != "bond_user_space_install_approval_validation"
    ):
        _append_unique(blocked_reasons, "user_install_approval_validation is missing or invalid")
        executor_status = "blocked_missing_inputs"
        refused_operations: list[dict[str, str]] = []
        approval_validation_digest = _json_sha256_hex(
            user_install_approval_validation if isinstance(user_install_approval_validation, dict) else {}
        )
        executor_disabled_packet = {
            "kind": USER_INSTALL_WRITE_EXECUTOR_PACKET_KIND,
            "schema_version": USER_INSTALL_WRITE_EXECUTOR_SCHEMA_VERSION,
            "requested_mode": normalized_mode,
            "executor_status": executor_status,
            "review_subject": "user_space_install_write_executor_disabled",
            "identifiers": {
                "manifest_path": None,
                "transaction_digest": None,
                "approval_envelope_digest": None,
                "write_preflight_digest": None,
                "approval_validation_digest": approval_validation_digest,
            },
            "executor_lock": {
                "executor_enabled": False,
                "dry_run_only": True,
                "would_write": False,
                "execution_allowed": False,
                "execution_authorized": False,
                "write_authorized": False,
                "write_manifest_authorized": False,
                "filesystem_write_authorized": False,
                "approval_granted": False,
                "approval_validated": False,
                "future_write_executor_required": True,
                "future_explicit_approval_validation_required": True,
            },
            "operation_summary": {
                "approved_operation_count": 0,
                "performed_operation_count": 0,
                "refused_operation_count": len(refused_operations),
            },
            "performed_operations": [],
            "refused_operations": refused_operations,
            "blockers": blocked_reasons,
            "manual_review_reasons": review_reasons,
            "denial_reasons": denial_reasons,
            "safety_boundary": [
                "Disabled executor skeleton only; execution remains locked.",
                "No approval was validated.",
                "No operations were performed.",
                "No user-space install, directory creation, manifest write, package operation, service mutation, storage move, command generation, or command execution was performed.",
            ],
        }
        executor_packet_digest = _json_sha256_hex(executor_disabled_packet)
        executor_json_preview = json.dumps(
            executor_disabled_packet,
            sort_keys=True,
            indent=2,
            ensure_ascii=False,
        )
        return {
            "kind": USER_INSTALL_WRITE_EXECUTOR_KIND,
            "schema_version": USER_INSTALL_WRITE_EXECUTOR_SCHEMA_VERSION,
            **_base_authorization(),
            "requested_mode": normalized_mode,
            "executor_status": executor_status,
            "executor_enabled": False,
            "dry_run_only": True,
            "would_write": False,
            "recommended_next_step_kind": "collect_missing_executor_inputs",
            "requires_manual_review": False,
            "blocked_reasons": blocked_reasons,
            "review_reasons": review_reasons,
            "denial_reasons": denial_reasons,
            "manifest_path": None,
            "transaction_digest": None,
            "approval_envelope_digest": None,
            "write_preflight_digest": None,
            "approval_validation_digest": approval_validation_digest,
            "approved_operation_count": 0,
            "performed_operations": [],
            "refused_operations": refused_operations,
            "executor_disabled_packet": executor_disabled_packet,
            "executor_packet_digest": executor_packet_digest,
            "executor_json_preview": executor_json_preview,
            "input_summaries": {},
            "plan_notes": [
                "Disabled executor skeleton only; execution remains locked.",
                "No approval was validated, and no user-space install, directory creation, manifest write, package operation, service mutation, storage move, command generation, or command execution was performed.",
            ],
        }

    approval_validation_status = user_install_approval_validation.get("approval_validation_status")
    if not isinstance(approval_validation_status, str):
        _append_unique(blocked_reasons, "approval_validation_status is missing or invalid")

    approval_record_status = user_install_approval_validation.get("approval_record_status")
    if approval_record_status is not None and not isinstance(approval_record_status, str):
        _append_unique(review_reasons, "approval_record_status is missing or invalid")

    upstream_next_step = user_install_approval_validation.get("recommended_next_step_kind")
    if upstream_next_step is not None and not isinstance(upstream_next_step, str):
        _append_unique(review_reasons, "recommended_next_step_kind is missing or invalid")

    upstream_requires_manual_review = user_install_approval_validation.get("requires_manual_review") is True

    for reason in _as_list_of_strings(user_install_approval_validation.get("blocked_reasons")):
        _append_unique(blocked_reasons, reason)
    if user_install_approval_validation.get("blocked_reasons") is not None and not isinstance(
        user_install_approval_validation.get("blocked_reasons"), list
    ):
        _append_unique(blocked_reasons, "blocked_reasons are missing or invalid")

    for reason in _as_list_of_strings(user_install_approval_validation.get("review_reasons")):
        _append_unique(review_reasons, reason)
    if user_install_approval_validation.get("review_reasons") is not None and not isinstance(
        user_install_approval_validation.get("review_reasons"), list
    ):
        _append_unique(review_reasons, "review_reasons are missing or invalid")

    for reason in _as_list_of_strings(user_install_approval_validation.get("denial_reasons")):
        _append_unique(denial_reasons, reason)
    if user_install_approval_validation.get("denial_reasons") is not None and not isinstance(
        user_install_approval_validation.get("denial_reasons"), list
    ):
        _append_unique(review_reasons, "denial_reasons are missing or invalid")

    manifest_path = _as_string_or_none(user_install_approval_validation.get("manifest_path"))
    if user_install_approval_validation.get("manifest_path") is not None and manifest_path is None:
        _append_unique(blocked_reasons, "manifest_path is missing or invalid")

    transaction_digest = _as_string_or_none(user_install_approval_validation.get("transaction_digest"))
    if user_install_approval_validation.get("transaction_digest") is not None and transaction_digest is None:
        _append_unique(blocked_reasons, "transaction_digest is missing or invalid")

    approval_envelope_digest = _as_string_or_none(user_install_approval_validation.get("approval_envelope_digest"))
    if user_install_approval_validation.get("approval_envelope_digest") is not None and approval_envelope_digest is None:
        _append_unique(blocked_reasons, "approval_envelope_digest is missing or invalid")

    write_preflight_digest = _as_string_or_none(user_install_approval_validation.get("write_preflight_digest"))
    if user_install_approval_validation.get("write_preflight_digest") is not None and write_preflight_digest is None:
        _append_unique(blocked_reasons, "write_preflight_digest is missing or invalid")

    approved_operation_count = _as_nonnegative_int(user_install_approval_validation.get("approved_operation_count"))
    if approved_operation_count is None:
        approved_operation_count = 0
        if user_install_approval_validation.get("approved_operation_count") is not None:
            _append_unique(review_reasons, "approved_operation_count is missing or invalid")

    approval_challenge = user_install_approval_validation.get("approval_challenge")
    if not isinstance(approval_challenge, dict):
        approval_challenge = {}
        if user_install_approval_validation.get("approval_challenge") is not None:
            _append_unique(review_reasons, "approval_challenge is missing or invalid")

    approval_challenge_json_preview = user_install_approval_validation.get("approval_challenge_json_preview")
    if approval_challenge_json_preview is not None and not isinstance(approval_challenge_json_preview, str):
        _append_unique(review_reasons, "approval_challenge_json_preview is missing or invalid")

    input_summaries = user_install_approval_validation.get("input_summaries")
    if not isinstance(input_summaries, dict):
        input_summaries = {}
        _append_unique(blocked_reasons, "input_summaries are missing or invalid")

    refused_operations = _extract_refused_operations(approval_challenge, input_summaries, manifest_path)

    status = _base_status(approval_validation_status)
    upstream_authorization_attempt = _truthy_authorization_present(user_install_approval_validation)
    if _truthy_authorization_present(approval_challenge):
        upstream_authorization_attempt = True
    challenge_lock = approval_challenge.get("execution_lock")
    if _truthy_authorization_present(challenge_lock):
        upstream_authorization_attempt = True

    if upstream_authorization_attempt:
        status = "unsupported_manual_review"
        _append_unique(
            denial_reasons,
            "upstream approval validation attempted to authorize execution, approval, commands, or writes",
        )

    if status == "disabled_execution_locked":
        status = "disabled_execution_locked"

    requires_manual_review = bool(
        upstream_requires_manual_review
        or review_reasons
        or denial_reasons
        or status in {"disabled_manual_review_required", "unsupported_manual_review"}
    )

    approval_validation_digest = _json_sha256_hex(user_install_approval_validation)

    executor_disabled_packet = {
        "kind": USER_INSTALL_WRITE_EXECUTOR_PACKET_KIND,
        "schema_version": USER_INSTALL_WRITE_EXECUTOR_SCHEMA_VERSION,
        "requested_mode": normalized_mode,
        "executor_status": status,
        "review_subject": "user_space_install_write_executor_disabled",
        "identifiers": {
            "manifest_path": manifest_path,
            "transaction_digest": transaction_digest,
            "approval_envelope_digest": approval_envelope_digest,
            "write_preflight_digest": write_preflight_digest,
            "approval_validation_digest": approval_validation_digest,
        },
        "executor_lock": {
            "executor_enabled": False,
            "dry_run_only": True,
            "would_write": False,
            "execution_allowed": False,
            "execution_authorized": False,
            "write_authorized": False,
            "write_manifest_authorized": False,
            "filesystem_write_authorized": False,
            "approval_granted": False,
            "approval_validated": False,
            "future_write_executor_required": True,
            "future_explicit_approval_validation_required": True,
        },
        "operation_summary": {
            "approved_operation_count": approved_operation_count,
            "performed_operation_count": 0,
            "refused_operation_count": len(refused_operations),
        },
        "performed_operations": [],
        "refused_operations": refused_operations,
        "blockers": blocked_reasons,
        "manual_review_reasons": review_reasons,
        "denial_reasons": denial_reasons,
        "safety_boundary": [
            "Disabled executor skeleton only; execution remains locked.",
            "No approval was validated.",
            "No operations were performed.",
            "No user-space install, directory creation, manifest write, package operation, service mutation, storage move, command generation, or command execution was performed.",
        ],
    }
    executor_packet_digest = _json_sha256_hex(executor_disabled_packet)
    executor_json_preview = json.dumps(
        executor_disabled_packet,
        sort_keys=True,
        indent=2,
        ensure_ascii=False,
    )

    return {
        "kind": USER_INSTALL_WRITE_EXECUTOR_KIND,
        "schema_version": USER_INSTALL_WRITE_EXECUTOR_SCHEMA_VERSION,
        **_base_authorization(),
        "requested_mode": normalized_mode,
        "executor_status": status,
        "executor_enabled": False,
        "dry_run_only": True,
        "would_write": False,
        "recommended_next_step_kind": _recommended_next_step_kind(status),
        "requires_manual_review": requires_manual_review,
        "blocked_reasons": blocked_reasons,
        "review_reasons": review_reasons,
        "denial_reasons": denial_reasons,
        "manifest_path": manifest_path,
        "transaction_digest": transaction_digest,
        "approval_envelope_digest": approval_envelope_digest,
        "write_preflight_digest": write_preflight_digest,
        "approval_validation_digest": approval_validation_digest,
        "approved_operation_count": approved_operation_count,
        "performed_operations": [],
        "refused_operations": refused_operations,
        "executor_disabled_packet": executor_disabled_packet,
        "executor_packet_digest": executor_packet_digest,
        "executor_json_preview": executor_json_preview,
        "input_summaries": input_summaries,
        "plan_notes": [
            "Disabled executor skeleton only; execution remains locked.",
            "No approval was validated, and no user-space install, directory creation, manifest write, package operation, service mutation, storage move, command generation, or command execution was performed.",
        ],
    }


def format_user_install_write_executor(report: dict[str, Any]) -> str:
    refused_operations = report.get("refused_operations") if isinstance(report.get("refused_operations"), list) else []
    lines = [
        "User-space install write executor",
        f"Executor status: {report.get('executor_status')}",
        "Executor enabled: false",
        "Dry run only: true",
        "Would write: false",
        f"Recommended next step: {report.get('recommended_next_step_kind')}",
        f"Manifest path: {report.get('manifest_path')}",
        f"Transaction digest: {report.get('transaction_digest')}",
        f"Approval envelope digest: {report.get('approval_envelope_digest')}",
        f"Write preflight digest: {report.get('write_preflight_digest')}",
        f"Approval validation digest: {report.get('approval_validation_digest')}",
        "Execution allowed: false",
        "Execution authorized: false",
        "Write authorized: false",
        "Write manifest authorized: false",
        "Filesystem write authorized: false",
        "Approval granted: false",
        "Approval validated: false",
        "Performed operations: 0",
        "Refused operations:",
    ]
    if refused_operations:
        for operation in refused_operations:
            if not isinstance(operation, dict):
                continue
            lines.append(
                "- "
                + f"{operation.get('operation_kind')} -> {operation.get('target')}"
                + f" ({operation.get('refusal_reason')})"
            )
    else:
        lines.append("- none")

    lines.append("Executor JSON preview:")
    lines.append(str(report.get("executor_json_preview")))
    lines.append(
        "No approval was validated, and no user-space install, directory creation, manifest write, package operation, service mutation, storage move, command generation, or command execution was performed."
    )
    return "\n".join(lines)
