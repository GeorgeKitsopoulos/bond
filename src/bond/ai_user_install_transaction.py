#!/usr/bin/env python3
"""Pure deterministic user-space install transaction/preflight planning contract."""

import json
from typing import Any

USER_INSTALL_TRANSACTION_PLAN_SCHEMA_VERSION = 1
USER_INSTALL_TRANSACTION_PLAN_KIND = "bond_user_install_transaction_plan"
USER_INSTALL_TRANSACTION_KIND = "bond_user_install_transaction"

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

_KNOWN_MODES = {
    "fresh_install_review",
    "reconfigure_review",
    "update_review",
    "doctor_review",
}


def _normalize_requested_mode(mode: str | None) -> str:
    if isinstance(mode, str) and mode in _KNOWN_MODES:
        return mode
    return "doctor_review"


def _append_unique(values: list[str], item: str) -> None:
    if item not in values:
        values.append(item)


def _top_level_authorization() -> dict[str, bool]:
    return {field: False for field in _TOP_LEVEL_AUTHORIZATION_FIELDS}


def _operation_status_for_plan_status(plan_status: str) -> str:
    if plan_status == "ready_for_user_review":
        return "planned_not_authorized"
    if plan_status == "manual_review_required":
        return "manual_review_needed"
    if plan_status == "blocked_missing_inputs":
        return "missing_input"
    return "unsupported_manual_review"


def _is_valid_user_install_plan(plan: dict[str, Any] | None) -> bool:
    return (
        isinstance(plan, dict)
        and plan.get("kind") == "bond_user_space_install_write_set_plan"
        and isinstance(plan.get("target_layout"), dict)
        and isinstance(plan.get("write_set"), list)
    )


def _is_valid_user_install_manifest_plan(plan: dict[str, Any] | None) -> bool:
    return (
        isinstance(plan, dict)
        and plan.get("kind") == "bond_user_install_manifest_payload_plan"
        and isinstance(plan.get("manifest_candidate"), dict)
        and isinstance(plan.get("manifest_json_preview"), str)
    )


def _classify_authorization_violation(field: str) -> str:
    if field == "commands_generated":
        return "command"
    if field in {"write_authorized", "write_manifest_authorized"}:
        return "write"
    return "execution"


def _collect_authorization_violations(
    user_install_plan: dict[str, Any],
    user_install_manifest_plan: dict[str, Any],
) -> tuple[bool, bool, bool]:
    execution_violation = False
    write_violation = False
    command_violation = False

    payloads = [
        user_install_plan,
        user_install_manifest_plan,
    ]

    manifest_candidate = user_install_manifest_plan.get("manifest_candidate")
    if isinstance(manifest_candidate, dict):
        authorization = manifest_candidate.get("authorization")
        if isinstance(authorization, dict):
            payloads.append(authorization)

    for payload in payloads:
        for field in _TOP_LEVEL_AUTHORIZATION_FIELDS:
            if payload.get(field) is not False:
                violation_kind = _classify_authorization_violation(field)
                if violation_kind == "execution":
                    execution_violation = True
                elif violation_kind == "write":
                    write_violation = True
                else:
                    command_violation = True

    write_set = user_install_plan.get("write_set")
    if isinstance(write_set, list):
        for item in write_set:
            if not isinstance(item, dict):
                continue
            if item.get("execution_authorized") is not False:
                execution_violation = True
            if item.get("write_authorized") is not False:
                write_violation = True
            if item.get("command") is not None:
                command_violation = True

    return (execution_violation, write_violation, command_violation)


def _write_set_summary_consistent(
    write_set: list[dict[str, Any]],
    write_set_summary: Any,
) -> bool:
    if not isinstance(write_set_summary, list):
        return False
    if len(write_set_summary) != len(write_set):
        return False

    for idx, item in enumerate(write_set):
        summary_item = write_set_summary[idx]
        if not isinstance(summary_item, dict):
            return False
        if summary_item.get("operation_kind") != item.get("operation_kind"):
            return False
        if summary_item.get("role") != item.get("role"):
            return False
        if summary_item.get("path") != item.get("path"):
            return False
        if summary_item.get("status") != item.get("status"):
            return False

    return True


def _resolve_operation_status(plan_status: str, item_status: Any) -> str:
    if item_status in {"missing_input", "unsupported_manual_review"}:
        return str(item_status)
    if plan_status == "ready_for_user_review":
        if isinstance(item_status, str) and item_status:
            return item_status
        return "planned_not_authorized"
    if plan_status == "manual_review_required":
        return "manual_review_needed"
    if plan_status == "blocked_missing_inputs":
        return "missing_input"
    return "unsupported_manual_review"


def build_user_install_transaction_plan(
    *,
    user_install_plan: dict[str, Any] | None = None,
    user_install_manifest_plan: dict[str, Any] | None = None,
    requested_mode: str | None = None,
) -> dict[str, Any]:
    requested_mode_normalized = _normalize_requested_mode(requested_mode)

    blocked_reasons: list[str] = []
    review_reasons: list[str] = []

    user_plan_valid = _is_valid_user_install_plan(user_install_plan)
    manifest_plan_valid = _is_valid_user_install_manifest_plan(user_install_manifest_plan)

    if not user_plan_valid:
        _append_unique(blocked_reasons, "user_install_plan is missing or invalid")
    if not manifest_plan_valid:
        _append_unique(blocked_reasons, "user_install_manifest_plan is missing or invalid")

    user_plan = user_install_plan if isinstance(user_install_plan, dict) else {}
    manifest_plan = user_install_manifest_plan if isinstance(user_install_manifest_plan, dict) else {}

    target_layout = user_plan.get("target_layout") if isinstance(user_plan.get("target_layout"), dict) else {}
    write_set = user_plan.get("write_set") if isinstance(user_plan.get("write_set"), list) else []
    write_set_items = [item for item in write_set if isinstance(item, dict)]

    manifest_candidate = (
        manifest_plan.get("manifest_candidate")
        if isinstance(manifest_plan.get("manifest_candidate"), dict)
        else {}
    )
    manifest_candidate_paths = (
        manifest_candidate.get("paths")
        if isinstance(manifest_candidate.get("paths"), dict)
        else {}
    )

    write_set_summary = manifest_candidate.get("write_set_summary")

    target_manifest_path = target_layout.get("manifest_path")
    plan_manifest_path = manifest_plan.get("manifest_path")
    candidate_manifest_path = manifest_candidate_paths.get("manifest_path")

    manifest_path_present = (
        isinstance(target_manifest_path, str)
        and bool(target_manifest_path)
        and isinstance(plan_manifest_path, str)
        and bool(plan_manifest_path)
        and isinstance(candidate_manifest_path, str)
        and bool(candidate_manifest_path)
    )
    if not manifest_path_present:
        _append_unique(blocked_reasons, "manifest path is missing")

    manifest_path_consistent = (
        manifest_path_present
        and target_manifest_path == plan_manifest_path
        and plan_manifest_path == candidate_manifest_path
    )
    if manifest_path_present and not manifest_path_consistent:
        _append_unique(
            review_reasons,
            "manifest path mismatch between write-set and manifest payload plans",
        )

    write_set_present = len(write_set_items) > 0
    if not write_set_present:
        _append_unique(blocked_reasons, "write-set is empty")

    write_set_summary_consistent = _write_set_summary_consistent(write_set_items, write_set_summary)
    if user_plan_valid and manifest_plan_valid and not write_set_summary_consistent:
        _append_unique(
            review_reasons,
            "manifest write-set summary does not match user install write-set",
        )

    no_upstream_execution_authorization = True
    no_upstream_write_authorization = True
    no_upstream_commands = True

    if user_plan_valid and manifest_plan_valid:
        (
            execution_violation,
            write_violation,
            command_violation,
        ) = _collect_authorization_violations(user_plan, manifest_plan)

        if execution_violation:
            no_upstream_execution_authorization = False
            _append_unique(review_reasons, "upstream plan attempted to authorize execution")
        if write_violation:
            no_upstream_write_authorization = False
            _append_unique(review_reasons, "upstream plan attempted to authorize writes")
        if command_violation:
            no_upstream_commands = False
            _append_unique(review_reasons, "upstream plan generated a command")

    upstream_user_status = user_plan.get("plan_status") if isinstance(user_plan.get("plan_status"), str) else ""
    upstream_manifest_status = (
        manifest_plan.get("plan_status") if isinstance(manifest_plan.get("plan_status"), str) else ""
    )
    upstream_user_requires_manual = user_plan.get("requires_manual_review") is True
    upstream_manifest_requires_manual = manifest_plan.get("requires_manual_review") is True

    unsupported_conditions = [
        upstream_user_status == "unsupported_manual_review",
        upstream_manifest_status == "unsupported_manual_review",
        manifest_path_present and not manifest_path_consistent,
        not no_upstream_execution_authorization,
        not no_upstream_write_authorization,
        not no_upstream_commands,
        user_plan_valid and manifest_plan_valid and (not write_set_summary_consistent),
    ]

    blocked_conditions = [
        not user_plan_valid,
        not manifest_plan_valid,
        not write_set_present,
        not manifest_path_present,
        upstream_user_status == "blocked_missing_inputs",
        upstream_manifest_status == "blocked_missing_inputs",
    ]

    manual_conditions = [
        upstream_user_status == "manual_review_required",
        upstream_manifest_status == "manual_review_required",
        upstream_user_requires_manual,
        upstream_manifest_requires_manual,
    ]

    if any(unsupported_conditions):
        plan_status = "unsupported_manual_review"
    elif any(blocked_conditions):
        plan_status = "blocked_missing_inputs"
    elif any(manual_conditions):
        plan_status = "manual_review_required"
    else:
        plan_status = "ready_for_user_review"

    requires_manual_review = plan_status in {
        "manual_review_required",
        "unsupported_manual_review",
    }

    if plan_status == "ready_for_user_review":
        recommended_next_step_kind = "review_user_install_transaction_plan"
    elif plan_status == "manual_review_required":
        recommended_next_step_kind = "manual_user_install_transaction_review"
    elif plan_status == "blocked_missing_inputs":
        recommended_next_step_kind = "collect_missing_user_install_transaction_inputs"
    else:
        recommended_next_step_kind = "manual_platform_review"

    manifest_path = None
    for candidate in (target_manifest_path, plan_manifest_path, candidate_manifest_path):
        if isinstance(candidate, str) and candidate:
            manifest_path = candidate
            break

    preflight_checks = {
        "user_install_plan_valid": user_plan_valid,
        "user_install_manifest_plan_valid": manifest_plan_valid,
        "manifest_path_present": manifest_path_present,
        "manifest_path_consistent": manifest_path_consistent,
        "write_set_present": write_set_present,
        "write_set_summary_consistent": write_set_summary_consistent,
        "no_upstream_execution_authorization": no_upstream_execution_authorization,
        "no_upstream_write_authorization": no_upstream_write_authorization,
        "no_upstream_commands": no_upstream_commands,
    }

    operation_status = _operation_status_for_plan_status(plan_status)

    operations: list[dict[str, Any]] = [
        {
            "operation_id": "000_preflight_review",
            "operation_kind": "preflight_review_candidate",
            "role": "preflight",
            "path": None,
            "status": operation_status,
            "source": "transaction_preflight",
            "execution_authorized": False,
            "write_authorized": False,
            "command": None,
            "requires_explicit_future_authorization": True,
            "verify_after_operation": True,
            "reason": "Review upstream plan consistency before any future install action.",
        }
    ]

    for idx, item in enumerate(write_set_items, start=1):
        role = item.get("role") if isinstance(item.get("role"), str) and item.get("role") else "unknown"
        op_kind = (
            item.get("operation_kind")
            if isinstance(item.get("operation_kind"), str) and item.get("operation_kind")
            else "unknown_operation"
        )
        reason = (
            item.get("reason")
            if isinstance(item.get("reason"), str)
            else "Candidate future install operation only; no execution is authorized."
        )
        operations.append(
            {
                "operation_id": f"{idx:03d}_{role}_{op_kind}",
                "operation_kind": op_kind,
                "role": role,
                "path": item.get("path"),
                "status": _resolve_operation_status(plan_status, item.get("status")),
                "source": "user_install_plan.write_set",
                "execution_authorized": False,
                "write_authorized": False,
                "command": None,
                "requires_explicit_future_authorization": True,
                "verify_after_operation": True,
                "reason": reason,
            }
        )

    operations.append(
        {
            "operation_id": "999_post_install_verification",
            "operation_kind": "post_install_verification_candidate",
            "role": "verification",
            "path": None,
            "status": operation_status,
            "source": "transaction_verification",
            "execution_authorized": False,
            "write_authorized": False,
            "command": None,
            "requires_explicit_future_authorization": True,
            "verify_after_operation": True,
            "reason": "Future verification checkpoint only; no verification command is generated.",
        }
    )

    source_summaries = {
        "user_install_plan": {
            "plan_status": user_plan.get("plan_status") if isinstance(user_plan.get("plan_status"), str) else None,
            "recommended_next_step_kind": (
                user_plan.get("recommended_next_step_kind")
                if isinstance(user_plan.get("recommended_next_step_kind"), str)
                else None
            ),
            "requires_manual_review": user_plan.get("requires_manual_review") is True,
            "write_set_count": len(write_set_items),
        },
        "user_install_manifest_plan": {
            "plan_status": (
                manifest_plan.get("plan_status")
                if isinstance(manifest_plan.get("plan_status"), str)
                else None
            ),
            "recommended_next_step_kind": (
                manifest_plan.get("recommended_next_step_kind")
                if isinstance(manifest_plan.get("recommended_next_step_kind"), str)
                else None
            ),
            "requires_manual_review": manifest_plan.get("requires_manual_review") is True,
            "manifest_path": manifest_path,
            "manifest_candidate_kind": (
                manifest_candidate.get("kind") if isinstance(manifest_candidate.get("kind"), str) else None
            ),
        },
    }

    transaction_candidate = {
        "kind": USER_INSTALL_TRANSACTION_KIND,
        "schema_version": USER_INSTALL_TRANSACTION_PLAN_SCHEMA_VERSION,
        "transaction_purpose": "user_space_install_review",
        "install_surface": "user_space",
        "requested_mode": requested_mode_normalized,
        "authorization": _top_level_authorization(),
        "manifest_path": manifest_path,
        "preflight_checks": preflight_checks,
        "operations": operations,
        "source_summaries": source_summaries,
        "notes": [
            "Transaction preview only; no install operation is authorized.",
        ],
    }

    transaction_json_preview = json.dumps(
        transaction_candidate,
        sort_keys=True,
        indent=2,
        ensure_ascii=False,
    )

    return {
        "kind": USER_INSTALL_TRANSACTION_PLAN_KIND,
        "schema_version": USER_INSTALL_TRANSACTION_PLAN_SCHEMA_VERSION,
        **_top_level_authorization(),
        "requested_mode": requested_mode_normalized,
        "plan_status": plan_status,
        "recommended_next_step_kind": recommended_next_step_kind,
        "requires_manual_review": requires_manual_review,
        "blocked_reasons": blocked_reasons,
        "review_reasons": review_reasons,
        "manifest_path": manifest_path,
        "transaction_candidate": transaction_candidate,
        "transaction_json_preview": transaction_json_preview,
        "input_summaries": source_summaries,
        "plan_notes": [
            "Transaction preview only; no install operation is authorized.",
            "No user-space install, directory creation, manifest write, package operation, service mutation, storage move, or command execution was performed.",
        ],
    }


def format_user_install_transaction_plan(plan: dict[str, Any]) -> str:
    payload = plan if isinstance(plan, dict) else {}

    transaction_candidate = (
        payload.get("transaction_candidate")
        if isinstance(payload.get("transaction_candidate"), dict)
        else {}
    )
    operations = (
        transaction_candidate.get("operations")
        if isinstance(transaction_candidate.get("operations"), list)
        else []
    )
    transaction_json_preview = payload.get("transaction_json_preview")
    if not isinstance(transaction_json_preview, str):
        transaction_json_preview = json.dumps(
            transaction_candidate,
            sort_keys=True,
            indent=2,
            ensure_ascii=False,
        )

    lines = [
        "User-space install transaction/preflight report",
        f"Plan status: {payload.get('plan_status')}",
        f"Recommended next step: {payload.get('recommended_next_step_kind')}",
        f"Manifest path: {payload.get('manifest_path')}",
        "Execution authorized: false",
        "Write authorized: false",
        "Transaction operations:",
    ]

    for operation in operations:
        if not isinstance(operation, dict):
            continue
        status = operation.get("status")
        operation_id = operation.get("operation_id")
        operation_kind = operation.get("operation_kind")
        role = operation.get("role")
        path = operation.get("path")
        lines.append(f"[{status}] {operation_id} {operation_kind} {role} -> {path}")

    lines.extend(
        [
            "Transaction JSON preview:",
            transaction_json_preview,
            "No user-space install, directory creation, manifest write, package operation, service mutation, storage move, or command execution was performed.",
        ]
    )

    return "\n".join(lines)
