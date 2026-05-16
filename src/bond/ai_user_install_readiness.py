#!/usr/bin/env python3
import hashlib
import json
from typing import Any

USER_INSTALL_READINESS_SCHEMA_VERSION = 1
USER_INSTALL_READINESS_KIND = "bond_user_space_install_readiness_report"
USER_INSTALL_READINESS_PACKET_KIND = "bond_user_space_install_readiness_packet"

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
    "fresh_install_readiness",
    "reconfigure_readiness",
    "update_readiness",
    "doctor_readiness",
}


def _base_authorization() -> dict[str, bool]:
    return {field: False for field in AUTHORIZATION_FIELDS}


def _append_unique(values: list[str], message: str) -> None:
    if message not in values:
        values.append(message)


def _normalize_requested_mode(requested_mode: str | None) -> str:
    if not isinstance(requested_mode, str):
        return "doctor_readiness"
    normalized = requested_mode.strip()
    if normalized in ALLOWED_REQUESTED_MODES:
        return normalized
    return "doctor_readiness"


def _json_sha256_hex(value: Any) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _as_string_or_none(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value
    return None


def _as_nonnegative_int(value: Any) -> int:
    if isinstance(value, bool):
        return 0
    if isinstance(value, int) and value >= 0:
        return value
    return 0


def _as_list_of_strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def _as_list_of_dicts(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _truthy_authorization_present(value: Any) -> bool:
    if isinstance(value, dict):
        for key, nested_value in value.items():
            if key in AUTHORIZATION_FIELDS and nested_value:
                return True
            if _truthy_authorization_present(nested_value):
                return True
        return False
    if isinstance(value, (list, tuple)):
        for item in value:
            if _truthy_authorization_present(item):
                return True
    return False


def _sanitize_refused_operations(value: Any, review_reasons: list[str]) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        _append_unique(review_reasons, "refused_operations was not a list and was ignored")
        return []

    sanitized_operations: list[dict[str, Any]] = []
    was_sanitized = False
    fixed_refusal_reason = "operation remains refused by the disabled readiness boundary"
    allowed_operation_kind_characters = set("-_./: ")
    forbidden_target_characters = "\n\r;&|`$><"

    for item in value[:50]:
        if not isinstance(item, dict):
            sanitized_operations.append(
                {
                    "operation_kind": "refused_operation_candidate",
                    "target": "<redacted_non_path_target>",
                    "refusal_reason": fixed_refusal_reason,
                }
            )
            was_sanitized = True
            continue

        operation_kind = item.get("operation_kind")
        if (
            isinstance(operation_kind, str)
            and 1 <= len(operation_kind) <= 80
            and all(character.isalnum() or character in allowed_operation_kind_characters for character in operation_kind)
        ):
            sanitized_operation_kind = operation_kind
        else:
            sanitized_operation_kind = "refused_operation_candidate"
            was_sanitized = True

        target = item.get("target")
        if (
            isinstance(target, str)
            and 1 <= len(target) <= 240
            and target.startswith("/")
            and not any(character in target for character in forbidden_target_characters)
        ):
            sanitized_target = target
        else:
            sanitized_target = "<redacted_non_path_target>"
            was_sanitized = True

        if item.get("refusal_reason") != fixed_refusal_reason:
            was_sanitized = True

        if set(item) != {"operation_kind", "target", "refusal_reason"}:
            was_sanitized = True

        sanitized_operations.append(
            {
                "operation_kind": sanitized_operation_kind,
                "target": sanitized_target,
                "refusal_reason": fixed_refusal_reason,
            }
        )

    if len(value) > 50:
        was_sanitized = True

    if was_sanitized:
        _append_unique(review_reasons, "refused_operations were sanitized by the readiness report boundary")

    return sanitized_operations


def _base_status_from_executor(executor_status: Any) -> str:
    if executor_status == "disabled_execution_locked":
        return "ready_for_final_human_review_execution_locked"
    if executor_status == "disabled_manual_review_required":
        return "manual_review_required"
    if executor_status == "blocked_missing_inputs":
        return "blocked_missing_inputs"
    if executor_status == "blocked_unsafe_write_targets":
        return "blocked_unsafe_write_targets"
    if executor_status == "unsupported_manual_review":
        return "unsupported_manual_review"
    return "unsupported_manual_review"


def _recommended_next_step_kind(readiness_status: str) -> str:
    if readiness_status == "ready_for_final_human_review_execution_locked":
        return "review_final_user_install_readiness_report"
    if readiness_status == "manual_review_required":
        return "manual_user_install_readiness_review_required"
    if readiness_status == "blocked_missing_inputs":
        return "collect_missing_readiness_inputs"
    if readiness_status == "blocked_unsafe_write_targets":
        return "correct_or_reselect_write_targets"
    return "manual_platform_review"


def _readiness_summary(readiness_status: str) -> str:
    if readiness_status == "ready_for_final_human_review_execution_locked":
        return "User-space install planning chain is complete for human review, but execution remains locked and no writes are authorized."
    if readiness_status == "manual_review_required":
        return "User-space install planning chain reached the final readiness layer, but manual review is required before any future approval or write-capable work."
    if readiness_status == "blocked_missing_inputs":
        return "User-space install readiness is blocked because required upstream inputs are missing."
    if readiness_status == "blocked_unsafe_write_targets":
        return "User-space install readiness is blocked because one or more future write targets are unsafe."
    return "User-space install readiness requires manual platform review because an unsupported or unsafe condition was detected."


def _build_report(
    *,
    normalized_mode: str,
    readiness_status: str,
    readiness_summary: str,
    blocked_reasons: list[str],
    review_reasons: list[str],
    denial_reasons: list[str],
    manifest_path: str | None,
    transaction_digest: str | None,
    approval_envelope_digest: str | None,
    write_preflight_digest: str | None,
    approval_validation_digest: str | None,
    executor_report_digest: str,
    executor_packet_digest: str | None,
    approved_operation_count: int,
    refused_operations: list[dict[str, Any]],
    input_summaries: dict[str, Any],
) -> dict[str, Any]:
    readiness_packet = {
        "kind": USER_INSTALL_READINESS_PACKET_KIND,
        "schema_version": USER_INSTALL_READINESS_SCHEMA_VERSION,
        "requested_mode": normalized_mode,
        "readiness_status": readiness_status,
        "readiness_summary": readiness_summary,
        "review_subject": "user_space_install_final_readiness",
        "identifiers": {
            "manifest_path": manifest_path,
            "transaction_digest": transaction_digest,
            "approval_envelope_digest": approval_envelope_digest,
            "write_preflight_digest": write_preflight_digest,
            "approval_validation_digest": approval_validation_digest,
            "executor_packet_digest": executor_packet_digest,
            "executor_report_digest": executor_report_digest,
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
            "Final readiness report only; execution remains locked.",
            "The user-space install chain is still non-executing.",
            "No approval was validated.",
            "No operations were performed.",
            "No user-space install, directory creation, manifest write, package operation, service mutation, storage move, command generation, or command execution was performed.",
        ],
    }

    readiness_packet_digest = _json_sha256_hex(readiness_packet)
    readiness_json_preview = json.dumps(
        readiness_packet,
        sort_keys=True,
        indent=2,
        ensure_ascii=False,
    )

    requires_manual_review = bool(
        review_reasons
        or denial_reasons
        or readiness_status in {"manual_review_required", "unsupported_manual_review"}
    )

    return {
        "kind": USER_INSTALL_READINESS_KIND,
        "schema_version": USER_INSTALL_READINESS_SCHEMA_VERSION,
        **_base_authorization(),
        "requested_mode": normalized_mode,
        "readiness_status": readiness_status,
        "readiness_summary": readiness_summary,
        "recommended_next_step_kind": _recommended_next_step_kind(readiness_status),
        "requires_manual_review": requires_manual_review,
        "blocked_reasons": blocked_reasons,
        "review_reasons": review_reasons,
        "denial_reasons": denial_reasons,
        "manifest_path": manifest_path,
        "transaction_digest": transaction_digest,
        "approval_envelope_digest": approval_envelope_digest,
        "write_preflight_digest": write_preflight_digest,
        "approval_validation_digest": approval_validation_digest,
        "executor_report_digest": executor_report_digest,
        "executor_packet_digest": executor_packet_digest,
        "readiness_packet_digest": readiness_packet_digest,
        "approved_operation_count": approved_operation_count,
        "performed_operations": [],
        "refused_operations": refused_operations,
        "readiness_packet": readiness_packet,
        "readiness_json_preview": readiness_json_preview,
        "input_summaries": input_summaries,
        "chain_closure": {
            "chain_name": "user_space_install_detect_plan_show",
            "closed_for_non_executing_human_review": True,
            "write_capable_installer_available": False,
            "approval_validation_available": False,
            "cli_surface_available": False,
            "real_execution_available": False,
        },
        "plan_notes": [
            "Final readiness report only; execution remains locked.",
            "No approval was validated, and no user-space install, directory creation, manifest write, package operation, service mutation, storage move, command generation, or command execution was performed.",
        ],
    }


def build_user_install_readiness_report(
    *,
    user_install_write_executor: dict[str, Any] | None = None,
    requested_mode: str | None = None,
) -> dict[str, Any]:
    normalized_mode = _normalize_requested_mode(requested_mode)
    blocked_reasons: list[str] = []
    review_reasons: list[str] = []
    denial_reasons: list[str] = []

    if (
        not isinstance(user_install_write_executor, dict)
        or user_install_write_executor.get("kind") != "bond_user_space_install_write_executor"
    ):
        _append_unique(blocked_reasons, "user_install_write_executor is missing or invalid")
        executor_report_digest = _json_sha256_hex(
            user_install_write_executor if isinstance(user_install_write_executor, dict) else {}
        )
        return _build_report(
            normalized_mode=normalized_mode,
            readiness_status="blocked_missing_inputs",
            readiness_summary="User-space install readiness cannot be evaluated because the disabled write-executor report is missing or invalid.",
            blocked_reasons=blocked_reasons,
            review_reasons=review_reasons,
            denial_reasons=denial_reasons,
            manifest_path=None,
            transaction_digest=None,
            approval_envelope_digest=None,
            write_preflight_digest=None,
            approval_validation_digest=None,
            executor_report_digest=executor_report_digest,
            executor_packet_digest=None,
            approved_operation_count=0,
            refused_operations=[],
            input_summaries={},
        )

    executor_status = user_install_write_executor.get("executor_status")
    if executor_status is None or not isinstance(executor_status, str):
        _append_unique(blocked_reasons, "executor_status is missing or invalid")

    executor_enabled = user_install_write_executor.get("executor_enabled")
    dry_run_only = user_install_write_executor.get("dry_run_only")
    would_write = user_install_write_executor.get("would_write")

    if user_install_write_executor.get("recommended_next_step_kind") is not None and not isinstance(
        user_install_write_executor.get("recommended_next_step_kind"), str
    ):
        _append_unique(review_reasons, "recommended_next_step_kind is missing or invalid")

    if user_install_write_executor.get("requires_manual_review") is not None and not isinstance(
        user_install_write_executor.get("requires_manual_review"), bool
    ):
        _append_unique(review_reasons, "requires_manual_review is missing or invalid")

    for reason in _as_list_of_strings(user_install_write_executor.get("blocked_reasons")):
        _append_unique(blocked_reasons, reason)
    if user_install_write_executor.get("blocked_reasons") is not None and not isinstance(
        user_install_write_executor.get("blocked_reasons"), list
    ):
        _append_unique(blocked_reasons, "blocked_reasons are missing or invalid")

    for reason in _as_list_of_strings(user_install_write_executor.get("review_reasons")):
        _append_unique(review_reasons, reason)
    if user_install_write_executor.get("review_reasons") is not None and not isinstance(
        user_install_write_executor.get("review_reasons"), list
    ):
        _append_unique(review_reasons, "review_reasons are missing or invalid")

    for reason in _as_list_of_strings(user_install_write_executor.get("denial_reasons")):
        _append_unique(denial_reasons, reason)
    if user_install_write_executor.get("denial_reasons") is not None and not isinstance(
        user_install_write_executor.get("denial_reasons"), list
    ):
        _append_unique(review_reasons, "denial_reasons are missing or invalid")

    manifest_path = _as_string_or_none(user_install_write_executor.get("manifest_path"))
    if user_install_write_executor.get("manifest_path") is not None and manifest_path is None:
        _append_unique(review_reasons, "manifest_path is missing or invalid")

    transaction_digest = _as_string_or_none(user_install_write_executor.get("transaction_digest"))
    if user_install_write_executor.get("transaction_digest") is not None and transaction_digest is None:
        _append_unique(review_reasons, "transaction_digest is missing or invalid")

    approval_envelope_digest = _as_string_or_none(user_install_write_executor.get("approval_envelope_digest"))
    if user_install_write_executor.get("approval_envelope_digest") is not None and approval_envelope_digest is None:
        _append_unique(review_reasons, "approval_envelope_digest is missing or invalid")

    write_preflight_digest = _as_string_or_none(user_install_write_executor.get("write_preflight_digest"))
    if user_install_write_executor.get("write_preflight_digest") is not None and write_preflight_digest is None:
        _append_unique(review_reasons, "write_preflight_digest is missing or invalid")

    approval_validation_digest = _as_string_or_none(user_install_write_executor.get("approval_validation_digest"))
    if user_install_write_executor.get("approval_validation_digest") is not None and approval_validation_digest is None:
        _append_unique(review_reasons, "approval_validation_digest is missing or invalid")

    approved_operation_count = _as_nonnegative_int(user_install_write_executor.get("approved_operation_count"))
    if user_install_write_executor.get("approved_operation_count") is not None and not isinstance(
        user_install_write_executor.get("approved_operation_count"), int
    ):
        _append_unique(review_reasons, "approved_operation_count is missing or invalid")

    refused_operations = _sanitize_refused_operations(user_install_write_executor.get("refused_operations"), review_reasons)

    raw_performed_operations = user_install_write_executor.get("performed_operations")
    if not isinstance(raw_performed_operations, list):
        _append_unique(review_reasons, "performed_operations are missing or invalid")

    executor_disabled_packet = user_install_write_executor.get("executor_disabled_packet")
    if executor_disabled_packet is not None and not isinstance(executor_disabled_packet, dict):
        _append_unique(review_reasons, "executor_disabled_packet is missing or invalid")
        executor_disabled_packet = {}
    if executor_disabled_packet is None:
        executor_disabled_packet = {}

    executor_packet_digest = _as_string_or_none(user_install_write_executor.get("executor_packet_digest"))
    if user_install_write_executor.get("executor_packet_digest") is not None and executor_packet_digest is None:
        _append_unique(review_reasons, "executor_packet_digest is missing or invalid")

    if user_install_write_executor.get("executor_json_preview") is not None and not isinstance(
        user_install_write_executor.get("executor_json_preview"), str
    ):
        _append_unique(review_reasons, "executor_json_preview is missing or invalid")

    input_summaries = user_install_write_executor.get("input_summaries")
    if not isinstance(input_summaries, dict):
        _append_unique(blocked_reasons, "input_summaries are missing or invalid")
        input_summaries = {}

    readiness_status = _base_status_from_executor(executor_status)

    upstream_authorization_attempt = _truthy_authorization_present(user_install_write_executor)
    if _truthy_authorization_present(executor_disabled_packet):
        upstream_authorization_attempt = True

    if upstream_authorization_attempt:
        readiness_status = "unsupported_manual_review"
        _append_unique(
            denial_reasons,
            "upstream write executor attempted to authorize execution, approval, commands, or writes",
        )

    if executor_enabled is not False:
        readiness_status = "unsupported_manual_review"
        _append_unique(
            denial_reasons,
            "disabled executor invariant failed: executor_enabled must be false",
        )

    if dry_run_only is not True:
        readiness_status = "unsupported_manual_review"
        _append_unique(
            denial_reasons,
            "disabled executor invariant failed: dry_run_only must be true",
        )

    if would_write is not False:
        readiness_status = "unsupported_manual_review"
        _append_unique(
            denial_reasons,
            "disabled executor invariant failed: would_write must be false",
        )

    if not isinstance(raw_performed_operations, list):
        readiness_status = "unsupported_manual_review"
        _append_unique(
            denial_reasons,
            "disabled executor invariant failed: performed_operations must be a list",
        )
    elif raw_performed_operations != []:
        readiness_status = "unsupported_manual_review"
        _append_unique(
            denial_reasons,
            "disabled executor invariant failed: upstream performed_operations must be empty",
        )

    if blocked_reasons and readiness_status == "ready_for_final_human_review_execution_locked":
        readiness_status = "blocked_missing_inputs"

    readiness_summary = _readiness_summary(readiness_status)
    executor_report_digest = _json_sha256_hex(user_install_write_executor)

    return _build_report(
        normalized_mode=normalized_mode,
        readiness_status=readiness_status,
        readiness_summary=readiness_summary,
        blocked_reasons=blocked_reasons,
        review_reasons=review_reasons,
        denial_reasons=denial_reasons,
        manifest_path=manifest_path,
        transaction_digest=transaction_digest,
        approval_envelope_digest=approval_envelope_digest,
        write_preflight_digest=write_preflight_digest,
        approval_validation_digest=approval_validation_digest,
        executor_report_digest=executor_report_digest,
        executor_packet_digest=executor_packet_digest,
        approved_operation_count=approved_operation_count,
        refused_operations=refused_operations,
        input_summaries=input_summaries,
    )


def format_user_install_readiness_report(report: dict[str, Any]) -> str:
    refused_operations = report.get("refused_operations") if isinstance(report.get("refused_operations"), list) else []
    chain_closure = report.get("chain_closure") if isinstance(report.get("chain_closure"), dict) else {}

    lines = [
        "User-space install readiness report",
        f"Readiness status: {report.get('readiness_status')}",
        f"Readiness summary: {report.get('readiness_summary')}",
        f"Recommended next step: {report.get('recommended_next_step_kind')}",
        f"Manifest path: {report.get('manifest_path')}",
        f"Transaction digest: {report.get('transaction_digest')}",
        f"Approval envelope digest: {report.get('approval_envelope_digest')}",
        f"Write preflight digest: {report.get('write_preflight_digest')}",
        f"Approval validation digest: {report.get('approval_validation_digest')}",
        f"Executor report digest: {report.get('executor_report_digest')}",
        f"Executor packet digest: {report.get('executor_packet_digest')}",
        f"Readiness packet digest: {report.get('readiness_packet_digest')}",
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

    lines.extend(
        [
            "Chain closed for non-executing human review: true",
            "Write-capable installer available: false",
            "CLI surface available: false",
            "Real execution available: false",
            "Readiness JSON preview:",
            str(report.get("readiness_json_preview")),
            "No approval was validated, and no user-space install, directory creation, manifest write, package operation, service mutation, storage move, command generation, or command execution was performed.",
        ]
    )

    if chain_closure.get("closed_for_non_executing_human_review") is not True:
        lines.append("(note: chain closure flag mismatch in source report)")

    return "\n".join(lines)
