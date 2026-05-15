#!/usr/bin/env python3
import json
from typing import Any

USER_INSTALL_REVIEW_SCHEMA_VERSION = 1
USER_INSTALL_REVIEW_KIND = "bond_user_space_install_review_report"

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
    "commands_generated",
    "approval_granted",
    "approval_validated",
)

ALLOWED_REQUESTED_MODES = {
    "fresh_install_review",
    "reconfigure_review",
    "update_review",
    "doctor_review",
}


def _base_authorization() -> dict[str, bool]:
    return {field: False for field in AUTHORIZATION_FIELDS}


def _append_unique(values: list[str], message: str) -> None:
    if message not in values:
        values.append(message)


def _normalize_requested_mode(requested_mode: str | None) -> str:
    if not isinstance(requested_mode, str):
        return "doctor_review"
    normalized = requested_mode.strip()
    if normalized in ALLOWED_REQUESTED_MODES:
        return normalized
    return "doctor_review"


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


def _as_reviewed_operations(value: Any) -> tuple[list[dict[str, Any]], bool]:
    if not isinstance(value, list):
        return [], False
    operations: list[dict[str, Any]] = []
    valid = True
    for item in value:
        if not isinstance(item, dict):
            valid = False
            continue
        operations.append(item)
    return operations, valid


def _recommended_next_step_kind(report_status: str) -> str:
    if report_status == "ready_for_human_review_execution_locked":
        return "human_review_execution_locked_packet"
    if report_status == "manual_review_required":
        return "manual_install_review_required"
    if report_status == "blocked_missing_inputs":
        return "collect_missing_install_review_inputs"
    return "manual_platform_review"


def _map_report_status(gate_status: Any) -> str:
    if gate_status == "execution_locked_pending_future_approval":
        return "ready_for_human_review_execution_locked"
    if gate_status == "manual_review_required":
        return "manual_review_required"
    if gate_status == "unsupported_manual_review":
        return "unsupported_manual_review"
    if gate_status == "blocked_missing_inputs":
        return "blocked_missing_inputs"
    return "unsupported_manual_review"


def _collect_authorization_issues(values: dict[str, Any], *, execution_reason: str) -> list[str]:
    issues: list[str] = []
    for field in AUTHORIZATION_FIELDS:
        if field not in values or values.get(field) is False:
            continue
        if field in {
            "execution_authorized",
            "execution_allowed",
            "install_authorized",
            "package_install_authorized",
            "upgrade_authorized",
            "reconfigure_authorized",
            "service_authorized",
            "storage_move_authorized",
        }:
            _append_unique(issues, execution_reason)
        elif field in {"write_authorized", "write_manifest_authorized"}:
            _append_unique(issues, "upstream execution gate attempted to authorize writes")
        elif field == "commands_generated":
            _append_unique(issues, "upstream execution gate generated commands")
        elif field == "approval_granted":
            _append_unique(issues, "upstream execution gate attempted to grant approval")
        elif field == "approval_validated":
            _append_unique(issues, "upstream execution gate attempted to validate approval")
    return issues


def _collect_operation_review_issues(reviewed_operations: list[dict[str, Any]]) -> list[str]:
    issues: list[str] = []
    for reviewed_operation in reviewed_operations:
        if reviewed_operation.get("command") is not None:
            _append_unique(issues, "upstream execution gate generated commands")
        if (
            "execution_authorized" in reviewed_operation
            and reviewed_operation.get("execution_authorized") is not False
        ):
            _append_unique(issues, "upstream execution gate attempted to authorize execution")
        if (
            "write_authorized" in reviewed_operation
            and reviewed_operation.get("write_authorized") is not False
        ):
            _append_unique(issues, "upstream execution gate attempted to authorize writes")
    return issues


def build_user_install_review_report(
    *,
    user_install_execution_gate: dict[str, Any] | None = None,
    requested_mode: str | None = None,
) -> dict[str, Any]:
    normalized_mode = _normalize_requested_mode(requested_mode)
    blocked_reasons: list[str] = []
    review_reasons: list[str] = []
    denial_reasons: list[str] = []

    manifest_path: str | None = None
    transaction_digest: str | None = None
    approval_envelope_digest: str | None = None
    reviewed_operations_summary: list[dict[str, Any]] = []
    source_summaries: dict[str, Any] = {}
    gate_decision: dict[str, Any] = {}
    report_status = "blocked_missing_inputs"

    if (
        not isinstance(user_install_execution_gate, dict)
        or user_install_execution_gate.get("kind") != "bond_user_install_execution_gate"
    ):
        _append_unique(blocked_reasons, "user_install_execution_gate is missing or invalid")
    else:
        gate = user_install_execution_gate
        gate_decision = _as_dict(gate.get("gate_decision"))
        execution_gate = _as_dict(gate_decision.get("execution_gate"))

        manifest_path = _as_string_or_none(gate.get("manifest_path"))
        if manifest_path is None:
            manifest_path = _as_string_or_none(gate_decision.get("manifest_path"))
        if manifest_path is None:
            manifest_path = _as_string_or_none(execution_gate.get("manifest_path"))

        transaction_digest = _as_string_or_none(gate.get("transaction_digest"))
        if transaction_digest is None:
            transaction_digest = _as_string_or_none(gate_decision.get("transaction_digest"))
        if transaction_digest is None:
            transaction_digest = _as_string_or_none(execution_gate.get("transaction_digest"))

        approval_envelope_digest = _as_string_or_none(gate.get("approval_envelope_digest"))
        if approval_envelope_digest is None:
            approval_envelope_digest = _as_string_or_none(gate_decision.get("approval_envelope_digest"))
        if approval_envelope_digest is None:
            approval_envelope_digest = _as_string_or_none(execution_gate.get("approval_envelope_digest"))

        source_value = gate.get("input_summaries")
        if not isinstance(source_value, dict):
            source_value = gate.get("source_summaries")
        if not isinstance(source_value, dict):
            source_value = gate_decision.get("source_summaries")
        if isinstance(source_value, dict):
            source_summaries = source_value
        else:
            _append_unique(blocked_reasons, "execution gate source summaries are missing or invalid")

        reviewed_value = gate.get("reviewed_operations_summary")
        if reviewed_value is None:
            reviewed_value = gate_decision.get("reviewed_operations_summary")
        reviewed_operations_summary, reviewed_valid = _as_reviewed_operations(reviewed_value)
        if reviewed_value is None:
            _append_unique(blocked_reasons, "reviewed operations summary is missing or invalid")
        elif not reviewed_valid:
            _append_unique(review_reasons, "reviewed operations summary is malformed")

        if manifest_path is None:
            _append_unique(blocked_reasons, "manifest path is missing")
        if transaction_digest is None:
            _append_unique(blocked_reasons, "transaction digest is missing")
        if approval_envelope_digest is None:
            _append_unique(blocked_reasons, "approval envelope digest is missing")

        denial_reasons = _as_list_of_strings(gate.get("denial_reasons"))
        if not denial_reasons:
            denial_reasons = _as_list_of_strings(execution_gate.get("denial_reasons"))

        for issue in _collect_authorization_issues(
            gate,
            execution_reason="upstream execution gate attempted to authorize execution",
        ):
            _append_unique(review_reasons, issue)
        for issue in _collect_authorization_issues(
            _as_dict(gate_decision.get("authorization")),
            execution_reason="upstream execution gate attempted to authorize execution",
        ):
            _append_unique(review_reasons, issue)
        for issue in _collect_authorization_issues(
            execution_gate,
            execution_reason="upstream execution gate attempted to authorize execution",
        ):
            _append_unique(review_reasons, issue)
        for issue in _collect_operation_review_issues(reviewed_operations_summary):
            _append_unique(review_reasons, issue)

        gate_status = gate.get("gate_status")
        if gate_status is None:
            gate_status = execution_gate.get("gate_status")
        if gate_status not in {
            "execution_locked_pending_future_approval",
            "manual_review_required",
            "unsupported_manual_review",
            "blocked_missing_inputs",
        }:
            _append_unique(review_reasons, "execution gate status is unsupported or missing")
        report_status = _map_report_status(gate_status)

        if review_reasons:
            report_status = "unsupported_manual_review"
        elif blocked_reasons:
            report_status = "blocked_missing_inputs"

    recommended_next_step_kind = _recommended_next_step_kind(report_status)
    requires_manual_review = bool(
        review_reasons
        or report_status in {"manual_review_required", "unsupported_manual_review"}
        or (
            isinstance(user_install_execution_gate, dict)
            and user_install_execution_gate.get("requires_manual_review") is True
        )
    )

    for reason in blocked_reasons:
        _append_unique(denial_reasons, reason)
    for reason in review_reasons:
        _append_unique(denial_reasons, reason)

    human_review_packet = {
        "kind": "bond_user_space_install_human_review_packet",
        "requested_mode": normalized_mode,
        "report_status": report_status,
        "review_subject": "user_space_install",
        "identifiers": {
            "manifest_path": manifest_path,
            "transaction_digest": transaction_digest,
            "approval_envelope_digest": approval_envelope_digest,
        },
        "execution_lock": {
            "execution_allowed": False,
            "execution_authorized": False,
            "approval_granted": False,
            "approval_validated": False,
            "future_approval_mechanism_available": False,
            "explicit_future_approval_required": True,
        },
        "operation_summary": {
            "reviewed_operation_count": len(reviewed_operations_summary),
            "reviewed_operations": reviewed_operations_summary,
        },
        "blockers": list(blocked_reasons),
        "manual_review_reasons": list(review_reasons),
        "denial_reasons": list(denial_reasons),
        "source_summaries": source_summaries,
        "safety_boundary": [
            "Review packet only; execution remains locked.",
            "No approval was validated.",
            "No user-space install, directory creation, manifest write, package operation, service mutation, storage move, command generation, or command execution was performed.",
        ],
    }
    review_json_preview = json.dumps(
        human_review_packet,
        sort_keys=True,
        indent=2,
        ensure_ascii=False,
    )

    return {
        "kind": USER_INSTALL_REVIEW_KIND,
        "schema_version": USER_INSTALL_REVIEW_SCHEMA_VERSION,
        **_base_authorization(),
        "requested_mode": normalized_mode,
        "report_status": report_status,
        "recommended_next_step_kind": recommended_next_step_kind,
        "requires_manual_review": requires_manual_review,
        "blocked_reasons": blocked_reasons,
        "review_reasons": review_reasons,
        "denial_reasons": denial_reasons,
        "manifest_path": manifest_path,
        "transaction_digest": transaction_digest,
        "approval_envelope_digest": approval_envelope_digest,
        "reviewed_operation_count": len(reviewed_operations_summary),
        "human_review_packet": human_review_packet,
        "review_json_preview": review_json_preview,
        "input_summaries": source_summaries,
        "plan_notes": [
            "Review packet only; execution remains locked.",
            "No approval was validated, and no user-space install, directory creation, manifest write, package operation, service mutation, storage move, command generation, or command execution was performed.",
        ],
    }


def format_user_install_review_report(report: dict[str, Any]) -> str:
    packet = report.get("human_review_packet")
    if not isinstance(packet, dict):
        packet = {}

    operation_summary = packet.get("operation_summary")
    if not isinstance(operation_summary, dict):
        operation_summary = {}

    reviewed_operations = operation_summary.get("reviewed_operations")
    if not isinstance(reviewed_operations, list):
        reviewed_operations = []

    lines = [
        "User-space install review report",
        f"Report status: {report.get('report_status')}",
        f"Recommended next step: {report.get('recommended_next_step_kind')}",
        f"Manifest path: {report.get('manifest_path')}",
        f"Transaction digest: {report.get('transaction_digest')}",
        f"Approval envelope digest: {report.get('approval_envelope_digest')}",
        "Execution allowed: false",
        "Execution authorized: false",
        "Approval granted: false",
        "Approval validated: false",
    ]

    blockers = report.get("blocked_reasons")
    if isinstance(blockers, list) and blockers:
        lines.append("Blocked reasons:")
        for reason in blockers:
            lines.append(f"- {reason}")

    review_reasons = report.get("review_reasons")
    if isinstance(review_reasons, list) and review_reasons:
        lines.append("Review reasons:")
        for reason in review_reasons:
            lines.append(f"- {reason}")

    denial_reasons = report.get("denial_reasons")
    if isinstance(denial_reasons, list) and denial_reasons:
        lines.append("Denial reasons:")
        for reason in denial_reasons:
            lines.append(f"- {reason}")

    lines.append("Reviewed operations:")
    for reviewed_operation in reviewed_operations:
        if not isinstance(reviewed_operation, dict):
            continue
        lines.append(
            f"[{reviewed_operation.get('status')}] {reviewed_operation.get('operation_id')} {reviewed_operation.get('operation_kind')} {reviewed_operation.get('role')} -> {reviewed_operation.get('path')}"
        )

    lines.extend(
        [
            "Review JSON preview:",
            str(report.get("review_json_preview", "")),
            "No approval was validated, and no user-space install, directory creation, manifest write, package operation, service mutation, storage move, command generation, or command execution was performed.",
        ]
    )
    return "\n".join(lines)