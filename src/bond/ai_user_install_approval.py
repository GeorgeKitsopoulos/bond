#!/usr/bin/env python3
import hashlib
import json
from typing import Any

USER_INSTALL_APPROVAL_PLAN_SCHEMA_VERSION = 1
USER_INSTALL_APPROVAL_PLAN_KIND = "bond_user_install_approval_plan"
USER_INSTALL_APPROVAL_CANDIDATE_KIND = "bond_user_install_approval_candidate"

AUTHORIZATION_FIELDS = (
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
    "approval_granted",
)

SENSITIVE_FIELD_NAMES = {
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
}

_ALLOWED_PLAN_STATUSES = {
    "ready_for_user_review",
    "manual_review_required",
    "blocked_missing_inputs",
    "unsupported_manual_review",
}

_ALLOWED_REQUESTED_MODES = {
    "fresh_install_review",
    "reconfigure_review",
    "update_review",
    "doctor_review",
}


def _base_authorization() -> dict[str, bool]:
    return {field: False for field in AUTHORIZATION_FIELDS}


def _normalize_requested_mode(requested_mode: str | None) -> str:
    if not isinstance(requested_mode, str):
        return "doctor_review"
    normalized = requested_mode.strip()
    if normalized in _ALLOWED_REQUESTED_MODES:
        return normalized
    return "doctor_review"


def _append_unique(values: list[str], message: str) -> None:
    if message not in values:
        values.append(message)


def _is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _top_level_authorization_issues(plan: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    for field in AUTHORIZATION_FIELDS:
        if field == "approval_granted":
            continue
        if field not in plan:
            continue
        value = plan.get(field)
        if value is False:
            continue
        if field in {
            "execution_authorized",
            "install_authorized",
            "package_install_authorized",
            "upgrade_authorized",
            "reconfigure_authorized",
            "service_authorized",
            "storage_move_authorized",
        }:
            _append_unique(issues, "upstream transaction attempted to authorize execution")
        elif field in {"write_authorized", "write_manifest_authorized"}:
            _append_unique(issues, "upstream transaction attempted to authorize writes")
        elif field == "commands_generated":
            _append_unique(issues, "upstream transaction generated a command")
    return issues


def _candidate_authorization_issues(candidate: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    authorization = candidate.get("authorization")
    if not isinstance(authorization, dict):
        return issues

    for field in AUTHORIZATION_FIELDS:
        if field == "approval_granted":
            continue
        if field not in authorization:
            continue
        value = authorization.get(field)
        if value is False:
            continue
        if field in {
            "execution_authorized",
            "install_authorized",
            "package_install_authorized",
            "upgrade_authorized",
            "reconfigure_authorized",
            "service_authorized",
            "storage_move_authorized",
        }:
            _append_unique(issues, "upstream transaction attempted to authorize execution")
        elif field in {"write_authorized", "write_manifest_authorized"}:
            _append_unique(issues, "upstream transaction attempted to authorize writes")
        elif field == "commands_generated":
            _append_unique(issues, "upstream transaction generated a command")
    return issues


def _operation_authorization_issues(operations: list[dict[str, Any]]) -> list[str]:
    issues: list[str] = []
    for op in operations:
        if op.get("execution_authorized") is not False:
            _append_unique(issues, "upstream transaction attempted to authorize execution")
        if op.get("write_authorized") is not False:
            _append_unique(issues, "upstream transaction attempted to authorize writes")
        if op.get("command") is not None:
            _append_unique(issues, "upstream transaction generated a command")
    return issues


def _reviewed_operation(op: dict[str, Any]) -> dict[str, Any]:
    reviewed: dict[str, Any] = {
        "operation_id": op.get("operation_id"),
        "operation_kind": op.get("operation_kind"),
        "role": op.get("role"),
        "path": op.get("path"),
        "status": op.get("status"),
        "source": op.get("source"),
        "requires_explicit_future_authorization": op.get("requires_explicit_future_authorization"),
        "verify_after_operation": op.get("verify_after_operation"),
    }
    return reviewed


def _status_next_step(status: str) -> str:
    if status == "ready_for_user_review":
        return "review_user_install_approval_envelope"
    if status == "manual_review_required":
        return "manual_user_install_approval_review"
    if status == "blocked_missing_inputs":
        return "collect_missing_user_install_approval_inputs"
    return "manual_platform_review"


def _final_status(
    *,
    unsupported: bool,
    blocked: bool,
    upstream_status: str,
    upstream_requires_manual: bool,
) -> str:
    if unsupported:
        return "unsupported_manual_review"
    if blocked:
        return "blocked_missing_inputs"
    if upstream_status == "unsupported_manual_review":
        return "unsupported_manual_review"
    if upstream_status == "blocked_missing_inputs":
        return "blocked_missing_inputs"
    if upstream_status == "manual_review_required" or upstream_requires_manual:
        return "manual_review_required"
    return "ready_for_user_review"


def build_user_install_approval_plan(
    *,
    user_install_transaction_plan: dict[str, Any] | None = None,
    requested_mode: str | None = None,
) -> dict[str, Any]:
    normalized_mode = _normalize_requested_mode(requested_mode)

    blocked_reasons: list[str] = []
    review_reasons: list[str] = []

    transaction_plan = (
        user_install_transaction_plan
        if isinstance(user_install_transaction_plan, dict)
        else None
    )

    transaction_candidate: dict[str, Any] = {}
    operations: list[dict[str, Any]] = []
    transaction_json_preview: str | None = None
    manifest_path: str | None = None
    transaction_digest: str | None = None
    upstream_status = "blocked_missing_inputs"
    upstream_requires_manual = False

    invalid_transaction = False

    if transaction_plan is None:
        invalid_transaction = True
    else:
        if transaction_plan.get("kind") != "bond_user_install_transaction_plan":
            invalid_transaction = True
        candidate = transaction_plan.get("transaction_candidate")
        if not isinstance(candidate, dict):
            invalid_transaction = True
            candidate = {}
        transaction_candidate = candidate
        if transaction_candidate.get("kind") != "bond_user_install_transaction":
            invalid_transaction = True
        operations_value = transaction_candidate.get("operations")
        if not isinstance(operations_value, list):
            invalid_transaction = True
        else:
            operations = [item for item in operations_value if isinstance(item, dict)]
            if len(operations) != len(operations_value):
                operations = operations_value

        preview_value = transaction_plan.get("transaction_json_preview")
        if isinstance(preview_value, str):
            transaction_json_preview = preview_value
        else:
            transaction_json_preview = None

        upstream_plan_status = transaction_plan.get("plan_status")
        if isinstance(upstream_plan_status, str) and upstream_plan_status in _ALLOWED_PLAN_STATUSES:
            upstream_status = upstream_plan_status
        upstream_requires_manual = transaction_plan.get("requires_manual_review") is True

    if invalid_transaction:
        _append_unique(
            blocked_reasons,
            "user_install_transaction_plan is missing or invalid",
        )

    top_manifest_path = None
    candidate_manifest_path = None
    if isinstance(transaction_plan, dict):
        value = transaction_plan.get("manifest_path")
        if _is_non_empty_string(value):
            top_manifest_path = value.strip()
    if isinstance(transaction_candidate, dict):
        value = transaction_candidate.get("manifest_path")
        if _is_non_empty_string(value):
            candidate_manifest_path = value.strip()

    if top_manifest_path and candidate_manifest_path and top_manifest_path != candidate_manifest_path:
        _append_unique(review_reasons, "manifest path mismatch in transaction plan")

    if top_manifest_path:
        manifest_path = top_manifest_path
    elif candidate_manifest_path:
        manifest_path = candidate_manifest_path

    if not manifest_path:
        _append_unique(blocked_reasons, "manifest path is missing")

    if transaction_json_preview is None:
        _append_unique(blocked_reasons, "transaction JSON preview is missing")
    else:
        transaction_digest = hashlib.sha256(transaction_json_preview.encode("utf-8")).hexdigest()

    malformed_operations = False
    if isinstance(transaction_candidate, dict):
        operations_value = transaction_candidate.get("operations")
        if isinstance(operations_value, list):
            if len(operations_value) == 0:
                _append_unique(blocked_reasons, "transaction operations are missing")
            for op in operations_value:
                if not isinstance(op, dict):
                    malformed_operations = True
                    break
                for key in ("operation_id", "operation_kind", "role", "status"):
                    if key not in op:
                        malformed_operations = True
                        break
                if malformed_operations:
                    break
            if not malformed_operations:
                operations = [op for op in operations_value if isinstance(op, dict)]
        elif transaction_plan is not None:
            malformed_operations = True

    if malformed_operations:
        _append_unique(review_reasons, "transaction operation is malformed")

    if isinstance(transaction_plan, dict):
        for reason in _top_level_authorization_issues(transaction_plan):
            _append_unique(review_reasons, reason)
    if isinstance(transaction_candidate, dict):
        for reason in _candidate_authorization_issues(transaction_candidate):
            _append_unique(review_reasons, reason)
    if operations:
        for reason in _operation_authorization_issues(operations):
            _append_unique(review_reasons, reason)

    unsupported = bool(review_reasons)
    blocked = bool(blocked_reasons)

    final_status = _final_status(
        unsupported=unsupported,
        blocked=blocked,
        upstream_status=upstream_status,
        upstream_requires_manual=upstream_requires_manual,
    )

    requires_manual_review = final_status in {
        "manual_review_required",
        "unsupported_manual_review",
    }

    reviewed_operations = [_reviewed_operation(op) for op in operations if isinstance(op, dict)]

    source_summary = {
        "plan_status": upstream_status,
        "recommended_next_step_kind": (
            transaction_plan.get("recommended_next_step_kind")
            if isinstance(transaction_plan, dict)
            else None
        ),
        "requires_manual_review": upstream_requires_manual,
        "manifest_path": manifest_path,
        "transaction_candidate_kind": transaction_candidate.get("kind") if isinstance(transaction_candidate, dict) else None,
        "operation_count": len(reviewed_operations),
        "transaction_digest": transaction_digest,
    }

    approval_candidate = {
        "kind": USER_INSTALL_APPROVAL_CANDIDATE_KIND,
        "schema_version": USER_INSTALL_APPROVAL_PLAN_SCHEMA_VERSION,
        "approval_purpose": "user_space_install_transaction_review",
        "install_surface": "user_space",
        "requested_mode": normalized_mode,
        "authorization": _base_authorization(),
        "manifest_path": manifest_path,
        "transaction_digest": transaction_digest,
        "approval_requirements": {
            "explicit_future_approval_required": True,
            "approval_granted": False,
            "approval_must_match_transaction_digest": transaction_digest,
            "approval_must_match_manifest_path": manifest_path,
            "approval_must_match_operation_count": len(reviewed_operations),
            "approval_must_be_collected_after_review": True,
            "approval_is_not_collected_in_this_stage": True,
            "approval_does_not_authorize_execution_in_this_stage": True,
        },
        "reviewed_operations": reviewed_operations,
        "source_summaries": {
            "user_install_transaction_plan": source_summary,
        },
        "notes": [
            "Approval envelope preview only; no approval is granted.",
            "No user-space install, directory creation, manifest write, package operation, service mutation, storage move, or command execution was performed.",
        ],
    }

    approval_json_preview = json.dumps(
        approval_candidate,
        sort_keys=True,
        indent=2,
        ensure_ascii=False,
    )

    plan: dict[str, Any] = {
        "kind": USER_INSTALL_APPROVAL_PLAN_KIND,
        "schema_version": USER_INSTALL_APPROVAL_PLAN_SCHEMA_VERSION,
        **_base_authorization(),
        "requested_mode": normalized_mode,
        "plan_status": final_status,
        "recommended_next_step_kind": _status_next_step(final_status),
        "requires_manual_review": requires_manual_review,
        "blocked_reasons": blocked_reasons,
        "review_reasons": review_reasons,
        "manifest_path": manifest_path,
        "transaction_digest": transaction_digest,
        "approval_candidate": approval_candidate,
        "approval_json_preview": approval_json_preview,
        "input_summaries": {
            "user_install_transaction_plan": source_summary,
        },
        "plan_notes": [
            "Approval envelope preview only; no approval is granted.",
            "No user-space install, directory creation, manifest write, package operation, service mutation, storage move, or command execution was performed.",
        ],
    }

    return plan


def format_user_install_approval_plan(plan: dict[str, Any]) -> str:
    candidate = plan.get("approval_candidate")
    if not isinstance(candidate, dict):
        candidate = {}

    reviewed_operations = candidate.get("reviewed_operations")
    if not isinstance(reviewed_operations, list):
        reviewed_operations = []

    lines = [
        "User-space install approval envelope report",
        f"Plan status: {plan.get('plan_status')}",
        f"Recommended next step: {plan.get('recommended_next_step_kind')}",
        f"Manifest path: {plan.get('manifest_path')}",
        f"Transaction digest: {plan.get('transaction_digest')}",
        "Execution authorized: false",
        "Write authorized: false",
        "Approval granted: false",
        "Reviewed operations:",
    ]

    for op in reviewed_operations:
        if not isinstance(op, dict):
            continue
        status = op.get("status")
        operation_id = op.get("operation_id")
        operation_kind = op.get("operation_kind")
        role = op.get("role")
        path = op.get("path")
        lines.append(f"[{status}] {operation_id} {operation_kind} {role} -> {path}")

    lines.extend(
        [
            "Approval JSON preview:",
            str(plan.get("approval_json_preview", "")),
            "No approval was granted, and no user-space install, directory creation, manifest write, package operation, service mutation, storage move, or command execution was performed.",
        ]
    )

    return "\n".join(lines)
