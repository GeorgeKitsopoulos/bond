#!/usr/bin/env python3
import hashlib
import json
from typing import Any

USER_INSTALL_APPROVAL_VALIDATION_SCHEMA_VERSION = 1
USER_INSTALL_APPROVAL_VALIDATION_KIND = "bond_user_space_install_approval_validation"
USER_INSTALL_APPROVAL_CHALLENGE_KIND = "bond_user_space_install_approval_challenge"
USER_INSTALL_APPROVAL_RECORD_KIND = "bond_user_space_install_approval_record"

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
    "fresh_install_approval_validation",
    "reconfigure_approval_validation",
    "update_approval_validation",
    "doctor_approval_validation",
}


def _base_authorization() -> dict[str, bool]:
    return {field: False for field in AUTHORIZATION_FIELDS}


def _append_unique(values: list[str], message: str) -> None:
    if message not in values:
        values.append(message)


def _normalize_requested_mode(requested_mode: str | None) -> str:
    if not isinstance(requested_mode, str):
        return "doctor_approval_validation"
    normalized = requested_mode.strip()
    if normalized in ALLOWED_REQUESTED_MODES:
        return normalized
    return "doctor_approval_validation"


def _as_list_of_strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def _as_string_or_none(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
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


def _write_preflight_digest(write_preflight_packet: Any, write_preflight_json_preview: Any) -> str | None:
    if isinstance(write_preflight_packet, dict):
        return _json_sha256_hex(write_preflight_packet)
    if isinstance(write_preflight_json_preview, str) and write_preflight_json_preview:
        return _json_sha256_hex(write_preflight_json_preview)
    return None


def _approved_operation_count(candidate_write_set: Any, path_safety_checks: Any) -> int:
    if isinstance(candidate_write_set, dict):
        all_candidate_targets = candidate_write_set.get("all_candidate_targets")
        if isinstance(all_candidate_targets, list):
            return len(all_candidate_targets)
    if isinstance(path_safety_checks, list):
        return len(path_safety_checks)
    return 0


def _base_status(write_preflight_status: Any) -> str:
    if write_preflight_status == "write_preflight_ready_execution_locked":
        return "approval_validation_ready_execution_locked"
    if write_preflight_status == "manual_review_required":
        return "manual_review_required"
    if write_preflight_status == "blocked_missing_inputs":
        return "blocked_missing_inputs"
    if write_preflight_status == "blocked_unsafe_write_targets":
        return "blocked_unsafe_write_targets"
    if write_preflight_status == "unsupported_manual_review":
        return "unsupported_manual_review"
    return "unsupported_manual_review"


def _recommended_next_step_kind(status: str) -> str:
    if status == "approval_validation_ready_execution_locked":
        return "review_approval_challenge_execution_locked"
    if status == "manual_review_required":
        return "manual_approval_review_required"
    if status == "blocked_missing_inputs":
        return "collect_missing_approval_validation_inputs"
    if status == "blocked_unsafe_write_targets":
        return "correct_or_reselect_write_targets"
    return "manual_platform_review"


def _status_is_blocked_or_manual(status: str) -> bool:
    return status in {
        "blocked_missing_inputs",
        "blocked_unsafe_write_targets",
        "manual_review_required",
        "unsupported_manual_review",
    }


def _build_approval_challenge(
    *,
    normalized_mode: str,
    transaction_digest: str | None,
    write_preflight_digest: str | None,
    approval_envelope_digest: str | None,
    approved_operation_count: int,
) -> dict[str, Any]:
    return {
        "kind": USER_INSTALL_APPROVAL_CHALLENGE_KIND,
        "schema_version": USER_INSTALL_APPROVAL_VALIDATION_SCHEMA_VERSION,
        "requested_mode": normalized_mode,
        "review_subject": "user_space_install_approval_validation",
        "required_approval_record_kind": USER_INSTALL_APPROVAL_RECORD_KIND,
        "required_approval_record_schema_version": 1,
        "required_fields": [
            "kind",
            "schema_version",
            "approval_scope",
            "approval_statement",
            "transaction_digest",
            "write_preflight_digest",
            "approved_operation_count",
            "approval_envelope_digest",
        ],
        "expected_values": {
            "transaction_digest": transaction_digest,
            "write_preflight_digest": write_preflight_digest,
            "approval_envelope_digest": approval_envelope_digest,
            "approved_operation_count": approved_operation_count,
        },
        "approval_scope": {
            "allowed_scopes": [
                "user_space_install",
                "user_space_reconfigure",
                "user_space_update",
                "user_space_doctor",
            ],
            "requested_mode": normalized_mode,
        },
        "expiry_policy": {
            "expiry_validation_available": False,
            "future_expiry_required": True,
            "accepted_without_expiry": False,
        },
        "identity_policy": {
            "identity_validation_available": False,
            "future_local_identity_binding_required": True,
            "accepted_without_identity_binding": False,
        },
        "execution_lock": {
            "approval_validation_available": False,
            "approval_granted": False,
            "approval_validated": False,
            "execution_allowed": False,
            "execution_authorized": False,
            "write_authorized": False,
            "filesystem_write_authorized": False,
            "future_approval_mechanism_required": True,
        },
        "safety_boundary": [
            "Approval challenge only; execution remains locked.",
            "No approval was validated.",
            "No user-space install, directory creation, manifest write, package operation, service mutation, storage move, command generation, or command execution was performed.",
        ],
    }


def _evaluate_approval_record(
    approval_record: dict[str, Any] | None,
    *,
    expected_values: dict[str, Any],
    review_reasons: list[str],
    denial_reasons: list[str],
) -> str:
    if approval_record is None:
        _append_unique(
            review_reasons,
            "approval record is missing because approval validation is not implemented yet",
        )
        return "missing"
    if not isinstance(approval_record, dict):
        _append_unique(denial_reasons, "approval record is not a dict")
        return "invalid_shape"
    if approval_record.get("kind") != USER_INSTALL_APPROVAL_RECORD_KIND:
        _append_unique(denial_reasons, "approval record kind is invalid")
        return "invalid_kind"
    for field in AUTHORIZATION_FIELDS:
        if approval_record.get(field):
            _append_unique(
                denial_reasons,
                "approval record attempted to authorize execution, approval, commands, or writes",
            )
            return "rejected_authorization_attempt"

    mismatched_fields: list[str] = []
    for field_name in (
        "schema_version",
        "transaction_digest",
        "write_preflight_digest",
        "approved_operation_count",
        "approval_envelope_digest",
    ):
        if approval_record.get(field_name) != expected_values.get(field_name):
            mismatched_fields.append(field_name)

    if mismatched_fields:
        _append_unique(
            denial_reasons,
            "approval record mismatched fields: " + ", ".join(mismatched_fields),
        )
        return "mismatch"

    _append_unique(
        review_reasons,
        "approval record shape matches the future contract, but approval validation is not implemented and remains locked",
    )
    return "shape_matches_future_contract_but_validation_unavailable"


def build_user_install_approval_validation(
    *,
    user_install_write_preflight: dict[str, Any] | None = None,
    approval_record: dict[str, Any] | None = None,
    requested_mode: str | None = None,
) -> dict[str, Any]:
    normalized_mode = _normalize_requested_mode(requested_mode)
    blocked_reasons: list[str] = []
    review_reasons: list[str] = []
    denial_reasons: list[str] = []

    if (
        not isinstance(user_install_write_preflight, dict)
        or user_install_write_preflight.get("kind") != "bond_user_space_install_write_preflight"
    ):
        _append_unique(blocked_reasons, "user_install_write_preflight is missing or invalid")
        approval_record_status = _evaluate_approval_record(
            approval_record,
            expected_values={
                "schema_version": 1,
                "transaction_digest": None,
                "write_preflight_digest": None,
                "approved_operation_count": 0,
                "approval_envelope_digest": None,
            },
            review_reasons=review_reasons,
            denial_reasons=denial_reasons,
        )
        approval_challenge = _build_approval_challenge(
            normalized_mode=normalized_mode,
            transaction_digest=None,
            write_preflight_digest=None,
            approval_envelope_digest=None,
            approved_operation_count=0,
        )
        approval_challenge_json_preview = json.dumps(
            approval_challenge,
            sort_keys=True,
            indent=2,
            ensure_ascii=False,
        )
        return {
            "kind": USER_INSTALL_APPROVAL_VALIDATION_KIND,
            "schema_version": USER_INSTALL_APPROVAL_VALIDATION_SCHEMA_VERSION,
            **_base_authorization(),
            "requested_mode": normalized_mode,
            "approval_validation_status": "blocked_missing_inputs",
            "approval_record_status": approval_record_status,
            "recommended_next_step_kind": "collect_missing_approval_validation_inputs",
            "requires_manual_review": bool(review_reasons or denial_reasons),
            "blocked_reasons": blocked_reasons,
            "review_reasons": review_reasons,
            "denial_reasons": denial_reasons,
            "manifest_path": None,
            "transaction_digest": None,
            "approval_envelope_digest": None,
            "write_preflight_digest": None,
            "approved_operation_count": 0,
            "approval_challenge": approval_challenge,
            "approval_challenge_json_preview": approval_challenge_json_preview,
            "input_summaries": {},
            "plan_notes": [
                "Approval validation contract only; execution remains locked.",
                "No approval was validated, and no user-space install, directory creation, manifest write, package operation, service mutation, storage move, command generation, or command execution was performed.",
            ],
        }

    write_preflight_status = user_install_write_preflight.get("write_preflight_status")
    upstream_next_step_kind = user_install_write_preflight.get("recommended_next_step_kind")
    requires_manual_review = user_install_write_preflight.get("requires_manual_review") is True

    for reason in _as_list_of_strings(user_install_write_preflight.get("blocked_reasons")):
        _append_unique(blocked_reasons, reason)
    if user_install_write_preflight.get("blocked_reasons") is not None and not isinstance(
        user_install_write_preflight.get("blocked_reasons"), list
    ):
        _append_unique(blocked_reasons, "blocked_reasons are missing or invalid")

    for reason in _as_list_of_strings(user_install_write_preflight.get("review_reasons")):
        _append_unique(review_reasons, reason)
    if user_install_write_preflight.get("review_reasons") is not None and not isinstance(
        user_install_write_preflight.get("review_reasons"), list
    ):
        _append_unique(review_reasons, "review_reasons are missing or invalid")

    for reason in _as_list_of_strings(user_install_write_preflight.get("denial_reasons")):
        _append_unique(denial_reasons, reason)
    if user_install_write_preflight.get("denial_reasons") is not None and not isinstance(
        user_install_write_preflight.get("denial_reasons"), list
    ):
        _append_unique(denial_reasons, "denial_reasons are missing or invalid")

    manifest_path = _as_string_or_none(user_install_write_preflight.get("manifest_path"))
    if user_install_write_preflight.get("manifest_path") is not None and manifest_path is None:
        _append_unique(blocked_reasons, "manifest_path is missing or invalid")

    transaction_digest = _as_string_or_none(user_install_write_preflight.get("transaction_digest"))
    if user_install_write_preflight.get("transaction_digest") is not None and transaction_digest is None:
        _append_unique(blocked_reasons, "transaction_digest is missing or invalid")

    approval_envelope_digest = _as_string_or_none(user_install_write_preflight.get("approval_envelope_digest"))
    if user_install_write_preflight.get("approval_envelope_digest") is not None and approval_envelope_digest is None:
        _append_unique(blocked_reasons, "approval_envelope_digest is missing or invalid")

    candidate_write_set = user_install_write_preflight.get("candidate_write_set")
    if not isinstance(candidate_write_set, dict):
        candidate_write_set = {}
        _append_unique(blocked_reasons, "candidate_write_set is missing or invalid")

    path_safety_checks = user_install_write_preflight.get("path_safety_checks")
    if not isinstance(path_safety_checks, list):
        path_safety_checks = []
        _append_unique(review_reasons, "path_safety_checks are missing or invalid")

    write_preflight_packet = user_install_write_preflight.get("write_preflight_packet")
    if write_preflight_packet is not None and not isinstance(write_preflight_packet, dict):
        _append_unique(review_reasons, "write_preflight_packet is missing or invalid")
        write_preflight_packet = None

    write_preflight_json_preview = user_install_write_preflight.get("write_preflight_json_preview")
    if write_preflight_json_preview is not None and not isinstance(write_preflight_json_preview, str):
        _append_unique(review_reasons, "write_preflight_json_preview is missing or invalid")
        write_preflight_json_preview = None

    input_summaries = user_install_write_preflight.get("input_summaries")
    if not isinstance(input_summaries, dict):
        input_summaries = {}
        _append_unique(blocked_reasons, "input_summaries are missing or invalid")

    if not isinstance(write_preflight_status, str):
        _append_unique(blocked_reasons, "write_preflight_status is missing or invalid")
        write_preflight_status = None
    if upstream_next_step_kind is not None and not isinstance(upstream_next_step_kind, str):
        _append_unique(review_reasons, "recommended_next_step_kind is missing or invalid")

    write_preflight_digest = _write_preflight_digest(write_preflight_packet, write_preflight_json_preview)
    approved_operation_count = _approved_operation_count(candidate_write_set, path_safety_checks)
    approval_challenge = _build_approval_challenge(
        normalized_mode=normalized_mode,
        transaction_digest=transaction_digest,
        write_preflight_digest=write_preflight_digest,
        approval_envelope_digest=approval_envelope_digest,
        approved_operation_count=approved_operation_count,
    )
    expected_record_values = {
        "schema_version": 1,
        "transaction_digest": transaction_digest,
        "write_preflight_digest": write_preflight_digest,
        "approved_operation_count": approved_operation_count,
        "approval_envelope_digest": approval_envelope_digest,
    }
    approval_record_status = _evaluate_approval_record(
        approval_record,
        expected_values=expected_record_values,
        review_reasons=review_reasons,
        denial_reasons=denial_reasons,
    )

    status = _base_status(write_preflight_status)
    if approval_record_status in {"invalid_shape", "invalid_kind", "rejected_authorization_attempt", "mismatch"}:
        status = "unsupported_manual_review"
    elif approval_record_status in {"missing", "shape_matches_future_contract_but_validation_unavailable"}:
        if not _status_is_blocked_or_manual(status):
            status = "approval_validation_ready_execution_locked"

    approval_challenge_json_preview = json.dumps(
        approval_challenge,
        sort_keys=True,
        indent=2,
        ensure_ascii=False,
    )

    return {
        "kind": USER_INSTALL_APPROVAL_VALIDATION_KIND,
        "schema_version": USER_INSTALL_APPROVAL_VALIDATION_SCHEMA_VERSION,
        **_base_authorization(),
        "requested_mode": normalized_mode,
        "approval_validation_status": status,
        "approval_record_status": approval_record_status,
        "recommended_next_step_kind": _recommended_next_step_kind(status),
        "requires_manual_review": bool(
            requires_manual_review
            or review_reasons
            or denial_reasons
            or status in {"manual_review_required", "unsupported_manual_review"}
        ),
        "blocked_reasons": blocked_reasons,
        "review_reasons": review_reasons,
        "denial_reasons": denial_reasons,
        "manifest_path": manifest_path,
        "transaction_digest": transaction_digest,
        "approval_envelope_digest": approval_envelope_digest,
        "write_preflight_digest": write_preflight_digest,
        "approved_operation_count": approved_operation_count,
        "approval_challenge": approval_challenge,
        "approval_challenge_json_preview": approval_challenge_json_preview,
        "input_summaries": input_summaries,
        "plan_notes": [
            "Approval validation contract only; execution remains locked.",
            "No approval was validated, and no user-space install, directory creation, manifest write, package operation, service mutation, storage move, command generation, or command execution was performed.",
        ],
    }


def format_user_install_approval_validation(report: dict[str, Any]) -> str:
    lines = [
        "User-space install approval validation",
        f"Approval validation status: {report.get('approval_validation_status')}",
        f"Approval record status: {report.get('approval_record_status')}",
        f"Recommended next step: {report.get('recommended_next_step_kind')}",
        f"Manifest path: {report.get('manifest_path')}",
        f"Transaction digest: {report.get('transaction_digest')}",
        f"Approval envelope digest: {report.get('approval_envelope_digest')}",
        f"Write preflight digest: {report.get('write_preflight_digest')}",
        f"Approved operation count: {report.get('approved_operation_count')}",
        "Execution allowed: false",
        "Execution authorized: false",
        "Write authorized: false",
        "Write manifest authorized: false",
        "Filesystem write authorized: false",
        "Approval granted: false",
        "Approval validated: false",
        "Approval challenge JSON preview:",
        str(report.get("approval_challenge_json_preview", "")),
        "No approval was validated, and no user-space install, directory creation, manifest write, package operation, service mutation, storage move, command generation, or command execution was performed.",
    ]
    return "\n".join(lines)