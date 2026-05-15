#!/usr/bin/env python3
import hashlib
import json
from typing import Any

USER_INSTALL_EXECUTION_GATE_SCHEMA_VERSION = 1
USER_INSTALL_EXECUTION_GATE_KIND = "bond_user_install_execution_gate"

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


def _is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _normalize_requested_mode(requested_mode: str | None) -> str:
    if not isinstance(requested_mode, str):
        return "doctor_review"
    normalized = requested_mode.strip()
    if normalized in ALLOWED_REQUESTED_MODES:
        return normalized
    return "doctor_review"


def _read_matching_value(*values: Any) -> tuple[str | None, bool]:
    present_values = [value for value in values if _is_non_empty_string(value)]
    if not present_values:
        return None, False
    reference = present_values[0]
    return reference, len(set(present_values)) > 1


def _summarize_source_plan(
    user_install_approval_plan: dict[str, Any],
    approval_envelope_digest: str | None,
) -> dict[str, Any]:
    approval_candidate = user_install_approval_plan.get("approval_candidate")
    if not isinstance(approval_candidate, dict):
        approval_candidate = {}

    reviewed_operations = approval_candidate.get("reviewed_operations")
    if not isinstance(reviewed_operations, list):
        reviewed_operations = []

    return {
        "plan_status": user_install_approval_plan.get("plan_status"),
        "recommended_next_step_kind": user_install_approval_plan.get("recommended_next_step_kind"),
        "requires_manual_review": user_install_approval_plan.get("requires_manual_review"),
        "manifest_path": user_install_approval_plan.get("manifest_path"),
        "transaction_digest": user_install_approval_plan.get("transaction_digest"),
        "approval_candidate_kind": approval_candidate.get("kind"),
        "reviewed_operation_count": len(reviewed_operations),
        "approval_envelope_digest": approval_envelope_digest,
    }


def _collect_authorization_issues(values: dict[str, Any], *, execution_reason: str) -> list[str]:
    issues: list[str] = []
    if not isinstance(values, dict):
        return issues

    for field in AUTHORIZATION_FIELDS:
        if field not in values:
            continue
        if values.get(field) is False:
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
            _append_unique(issues, "upstream approval plan attempted to authorize writes")
        elif field == "commands_generated":
            _append_unique(issues, "upstream approval plan generated a command")
        elif field == "approval_granted":
            _append_unique(issues, "upstream approval plan attempted to grant approval")
        elif field == "approval_validated":
            _append_unique(issues, "upstream approval plan did not preserve non-collection boundary")
    return issues


def _collect_reviewed_operation_issues(reviewed_operations: list[dict[str, Any]]) -> list[str]:
    issues: list[str] = []
    for reviewed_operation in reviewed_operations:
        if not isinstance(reviewed_operation, dict):
            _append_unique(issues, "reviewed operation is malformed")
            continue
        if reviewed_operation.get("command") is not None:
            _append_unique(issues, "upstream approval plan generated a command")
        if "execution_authorized" in reviewed_operation and reviewed_operation.get("execution_authorized") is not False:
            _append_unique(issues, "upstream approval plan attempted to authorize execution")
        if "write_authorized" in reviewed_operation and reviewed_operation.get("write_authorized") is not False:
            _append_unique(issues, "upstream approval plan attempted to authorize writes")
        for field in ("operation_id", "operation_kind", "role", "status"):
            if field not in reviewed_operation:
                _append_unique(issues, "reviewed operation is malformed")
                break
    return issues


def _build_reviewed_operations_summary(reviewed_operations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summary: list[dict[str, Any]] = []
    for reviewed_operation in reviewed_operations:
        if not isinstance(reviewed_operation, dict):
            continue
        summary.append(
            {
                "operation_id": reviewed_operation.get("operation_id"),
                "operation_kind": reviewed_operation.get("operation_kind"),
                "role": reviewed_operation.get("role"),
                "path": reviewed_operation.get("path"),
                "status": reviewed_operation.get("status"),
                "source": reviewed_operation.get("source"),
                "requires_explicit_future_authorization": reviewed_operation.get("requires_explicit_future_authorization"),
                "verify_after_operation": reviewed_operation.get("verify_after_operation"),
            }
        )
    return summary


def _recommended_next_step_kind(gate_status: str) -> str:
    if gate_status == "manual_review_required":
        return "manual_execution_gate_review"
    if gate_status == "blocked_missing_inputs":
        return "collect_missing_execution_gate_inputs"
    if gate_status == "unsupported_manual_review":
        return "manual_platform_review"
    return "review_execution_gate_denial"


def build_user_install_execution_gate(
    *,
    user_install_approval_plan: dict[str, Any] | None = None,
    requested_mode: str | None = None,
) -> dict[str, Any]:
    normalized_mode = _normalize_requested_mode(requested_mode)

    blocked_reasons: list[str] = []
    review_reasons: list[str] = []
    denial_reasons: list[str] = []

    approval_plan = user_install_approval_plan if isinstance(user_install_approval_plan, dict) else None
    approval_candidate: dict[str, Any] = {}
    approval_requirements: dict[str, Any] = {}
    reviewed_operations: list[dict[str, Any]] = []
    approval_json_preview: str | None = None
    approval_envelope_digest: str | None = None
    manifest_path: str | None = None
    transaction_digest: str | None = None

    if approval_plan is None:
        _append_unique(blocked_reasons, "user_install_approval_plan is missing or invalid")
    else:
        if approval_plan.get("kind") != "bond_user_install_approval_plan":
            _append_unique(blocked_reasons, "user_install_approval_plan is missing or invalid")
        candidate_value = approval_plan.get("approval_candidate")
        if not isinstance(candidate_value, dict):
            _append_unique(blocked_reasons, "user_install_approval_plan is missing or invalid")
            candidate_value = {}
        approval_candidate = candidate_value
        if approval_candidate.get("kind") != "bond_user_install_approval_candidate":
            _append_unique(blocked_reasons, "user_install_approval_plan is missing or invalid")

        requirements_value = approval_candidate.get("approval_requirements")
        if not isinstance(requirements_value, dict):
            _append_unique(blocked_reasons, "user_install_approval_plan is missing or invalid")
            requirements_value = {}
        approval_requirements = requirements_value

        reviewed_operations_value = approval_candidate.get("reviewed_operations")
        if not isinstance(reviewed_operations_value, list):
            _append_unique(blocked_reasons, "user_install_approval_plan is missing or invalid")
            reviewed_operations_value = []
        reviewed_operations = reviewed_operations_value

        preview_value = approval_plan.get("approval_json_preview")
        if isinstance(preview_value, str):
            approval_json_preview = preview_value
        else:
            _append_unique(blocked_reasons, "approval JSON preview is missing")

        top_manifest_path = approval_plan.get("manifest_path")
        candidate_manifest_path = approval_candidate.get("manifest_path")
        requirement_manifest_path = approval_requirements.get("approval_must_match_manifest_path")
        manifest_path, manifest_mismatched = _read_matching_value(
            top_manifest_path,
            candidate_manifest_path,
            requirement_manifest_path,
        )
        if manifest_path is None:
            _append_unique(blocked_reasons, "manifest path is missing")
        elif manifest_mismatched:
            _append_unique(review_reasons, "manifest path mismatch in approval plan")

        top_transaction_digest = approval_plan.get("transaction_digest")
        candidate_transaction_digest = approval_candidate.get("transaction_digest")
        requirement_transaction_digest = approval_requirements.get("approval_must_match_transaction_digest")
        transaction_digest, transaction_mismatched = _read_matching_value(
            top_transaction_digest,
            candidate_transaction_digest,
            requirement_transaction_digest,
        )
        if transaction_digest is None:
            _append_unique(blocked_reasons, "transaction digest is missing")
        elif transaction_mismatched:
            _append_unique(review_reasons, "transaction digest mismatch in approval plan")

        if approval_json_preview is not None:
            approval_envelope_digest = hashlib.sha256(approval_json_preview.encode("utf-8")).hexdigest()

        if approval_requirements.get("approval_granted") is True:
            _append_unique(review_reasons, "upstream approval plan attempted to grant approval")
        if (
            approval_requirements.get("approval_is_not_collected_in_this_stage") is not True
            or approval_requirements.get("approval_does_not_authorize_execution_in_this_stage") is not True
        ):
            _append_unique(review_reasons, "upstream approval plan did not preserve non-collection boundary")

        approval_candidate_authorization = approval_candidate.get("authorization")
        if isinstance(approval_candidate_authorization, dict):
            for issue in _collect_authorization_issues(
                approval_candidate_authorization,
                execution_reason="upstream approval plan attempted to authorize execution",
            ):
                _append_unique(review_reasons, issue)

        for issue in _collect_authorization_issues(
            approval_plan,
            execution_reason="upstream approval plan attempted to authorize execution",
        ):
            _append_unique(review_reasons, issue)

        if not reviewed_operations:
            _append_unique(blocked_reasons, "reviewed operations are missing")
        else:
            if any(not isinstance(reviewed_operation, dict) for reviewed_operation in reviewed_operations):
                _append_unique(review_reasons, "reviewed operation is malformed")
            else:
                for reviewed_operation in reviewed_operations:
                    for required_field in ("operation_id", "operation_kind", "role", "status"):
                        if required_field not in reviewed_operation:
                            _append_unique(review_reasons, "reviewed operation is malformed")
                            break
                    if "reviewed operation is malformed" in review_reasons:
                        break

            operation_count_requirement = approval_requirements.get("approval_must_match_operation_count")
            if operation_count_requirement is not None and operation_count_requirement != len(reviewed_operations):
                _append_unique(review_reasons, "reviewed operation count mismatch in approval plan")

            for issue in _collect_reviewed_operation_issues(reviewed_operations):
                _append_unique(review_reasons, issue)

    if review_reasons:
        gate_status = "unsupported_manual_review"
    elif blocked_reasons:
        gate_status = "blocked_missing_inputs"
    else:
        upstream_status = approval_plan.get("plan_status") if isinstance(approval_plan, dict) else None
        upstream_requires_manual = approval_plan.get("requires_manual_review") is True if isinstance(approval_plan, dict) else False
        if upstream_status == "unsupported_manual_review":
            gate_status = "unsupported_manual_review"
        elif upstream_status == "blocked_missing_inputs":
            gate_status = "blocked_missing_inputs"
        elif upstream_status == "manual_review_required" or upstream_requires_manual:
            gate_status = "manual_review_required"
        else:
            gate_status = "execution_locked_pending_future_approval"

    requires_manual_review = gate_status in {"manual_review_required", "unsupported_manual_review"}
    reviewed_operations_summary = _build_reviewed_operations_summary(reviewed_operations)
    source_summaries = {
        "user_install_approval_plan": _summarize_source_plan(
            approval_plan if isinstance(approval_plan, dict) else {},
            approval_envelope_digest,
        )
    }

    denial_reasons.extend(
        [
            "future approval validation mechanism is not implemented",
            "execution is locked in Stage 2G-F-E",
        ]
    )
    for reason in blocked_reasons:
        _append_unique(denial_reasons, reason)
    for reason in review_reasons:
        _append_unique(denial_reasons, reason)

    gate_decision: dict[str, Any] = {
        "kind": USER_INSTALL_EXECUTION_GATE_KIND,
        "schema_version": USER_INSTALL_EXECUTION_GATE_SCHEMA_VERSION,
        "gate_purpose": "user_space_install_execution_readiness_review",
        "install_surface": "user_space",
        "requested_mode": normalized_mode,
        "authorization": _base_authorization(),
        "manifest_path": manifest_path,
        "transaction_digest": transaction_digest,
        "approval_envelope_digest": approval_envelope_digest,
        "execution_gate": {
            "gate_status": gate_status,
            "execution_allowed": False,
            "execution_authorized": False,
            "approval_granted": False,
            "approval_validated": False,
            "future_approval_mechanism_available": False,
            "explicit_future_approval_required": True,
            "approval_envelope_digest": approval_envelope_digest,
            "transaction_digest": transaction_digest,
            "manifest_path": manifest_path,
            "denial_reasons": list(denial_reasons),
        },
        "reviewed_operations_summary": reviewed_operations_summary,
        "source_summaries": source_summaries,
        "notes": [
            "Execution gate preview only; execution remains locked.",
            "No approval was validated, and no user-space install, directory creation, manifest write, package operation, service mutation, storage move, or command execution was performed.",
        ],
    }

    gate_json_preview = json.dumps(gate_decision, sort_keys=True, indent=2, ensure_ascii=False)

    gate = {
        "kind": USER_INSTALL_EXECUTION_GATE_KIND,
        "schema_version": USER_INSTALL_EXECUTION_GATE_SCHEMA_VERSION,
        **_base_authorization(),
        "requested_mode": normalized_mode,
        "gate_status": gate_status,
        "recommended_next_step_kind": _recommended_next_step_kind(gate_status),
        "requires_manual_review": requires_manual_review,
        "blocked_reasons": blocked_reasons,
        "review_reasons": review_reasons,
        "denial_reasons": denial_reasons,
        "manifest_path": manifest_path,
        "transaction_digest": transaction_digest,
        "approval_envelope_digest": approval_envelope_digest,
        "gate_decision": gate_decision,
        "gate_json_preview": gate_json_preview,
        "input_summaries": source_summaries,
        "plan_notes": [
            "Execution gate preview only; execution remains locked.",
            "No approval was validated, and no user-space install, directory creation, manifest write, package operation, service mutation, storage move, or command execution was performed.",
        ],
        "future_approval_mechanism_available": False,
    }

    return gate


def format_user_install_execution_gate(gate: dict[str, Any]) -> str:
    gate_decision = gate.get("gate_decision")
    if not isinstance(gate_decision, dict):
        gate_decision = {}

    reviewed_operations = gate_decision.get("reviewed_operations_summary")
    if not isinstance(reviewed_operations, list):
        reviewed_operations = []

    denial_reasons = gate.get("denial_reasons")
    if not isinstance(denial_reasons, list):
        denial_reasons = []

    lines = [
        "User-space install execution-gate report",
        f"Gate status: {gate.get('gate_status')}",
        f"Recommended next step: {gate.get('recommended_next_step_kind')}",
        f"Manifest path: {gate.get('manifest_path')}",
        f"Transaction digest: {gate.get('transaction_digest')}",
        f"Approval envelope digest: {gate.get('approval_envelope_digest')}",
        "Execution allowed: false",
        "Execution authorized: false",
        "Approval granted: false",
        "Approval validated: false",
        "Future approval mechanism available: false",
        "Denial reasons:",
    ]

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
            "Gate JSON preview:",
            str(gate.get("gate_json_preview", "")),
            "No approval was validated, and no user-space install, directory creation, manifest write, package operation, service mutation, storage move, or command execution was performed.",
        ]
    )

    return "\n".join(lines)
