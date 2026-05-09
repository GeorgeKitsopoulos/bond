"""Pure deterministic maintenance planning contract that does not authorize execution."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

PLAN_KIND = "non_executing_maintenance_plan"
PLAN_STATUS_NO_IMMEDIATE_SIGNAL = "no_immediate_signal"
PLAN_STATUS_MANUAL_REVIEW = "manual_review"
PLAN_STATUS_FUTURE_PRIVILEGED_LANE_REQUIRED = "future_privileged_lane_required"
PLAN_STATUS_UNAVAILABLE = "unavailable"
SEVERITY_INFO = "info"
SEVERITY_LOW = "low"
SEVERITY_MEDIUM = "medium"
SEVERITY_UNKNOWN = "unknown"


@dataclass(frozen=True)
class MaintenancePlanItem:
    area: str
    signal: str
    severity: str
    status: str
    user_impact: str
    next_check: str
    requires_future_privileged_lane: bool
    action_authorized: bool = False


def maintenance_plan_item_to_dict(item: MaintenancePlanItem) -> dict[str, object]:
    return {
        "area": item.area,
        "signal": item.signal,
        "severity": item.severity,
        "status": item.status,
        "user_impact": item.user_impact,
        "next_check": item.next_check,
        "requires_future_privileged_lane": item.requires_future_privileged_lane,
        "action_authorized": item.action_authorized,
    }


def _result_ok(result: Any | None) -> bool:
    return getattr(result, "ok", False) is True


def _result_data(result: Any | None) -> dict[str, Any]:
    if result is None:
        return {}
    data = getattr(result, "data", None)
    return data if isinstance(data, dict) else {}


def _as_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    return None


def _as_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int) or isinstance(value, float):
        return float(value)
    return None


def _safe_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    return []


def _failed_or_unavailable_status(result: Any | None) -> bool:
    return result is None or _result_ok(result) is not True


def _build_package_plan_item(package_result: Any | None) -> MaintenancePlanItem:
    if _failed_or_unavailable_status(package_result):
        return MaintenancePlanItem(
            area="package_update_status",
            signal="package update signal unavailable or degraded",
            severity=SEVERITY_UNKNOWN,
            status=PLAN_STATUS_UNAVAILABLE,
            user_impact="Bond cannot classify package update pressure from this run.",
            next_check="Repeat the read-only maintenance readiness report later or inspect package state outside Bond.",
            requires_future_privileged_lane=False,
        )

    data = _result_data(package_result)
    count = _as_int(data.get("upgradable_count"))
    cache_known = data.get("cache_freshness_known") is True

    if count is None:
        return MaintenancePlanItem(
            area="package_update_status",
            signal="package update count unknown",
            severity=SEVERITY_UNKNOWN,
            status=PLAN_STATUS_MANUAL_REVIEW,
            user_impact="Package update pressure is unclear because the read-only signal did not produce a count.",
            next_check="Keep this as an observation only; do not infer update urgency from this run.",
            requires_future_privileged_lane=False,
        )

    if count == 0:
        user_impact = "No package update pressure was observed from the local apt cache."
        if not cache_known:
            user_impact += " Cache freshness is unknown because Bond did not refresh package metadata."
        return MaintenancePlanItem(
            area="package_update_status",
            signal="no upgradable packages observed from local cache",
            severity=SEVERITY_INFO,
            status=PLAN_STATUS_NO_IMMEDIATE_SIGNAL,
            user_impact=user_impact,
            next_check="No update action is planned by Bond; cache freshness remains unproven.",
            requires_future_privileged_lane=False,
        )

    user_impact = "The local apt cache suggests updates may exist, but freshness and safety are not proven."
    if not cache_known:
        user_impact += " Cache freshness is unknown because Bond did not refresh package metadata."
    return MaintenancePlanItem(
        area="package_update_status",
        signal=f"{count} upgradable package(s) observed from local cache",
        severity=SEVERITY_LOW if count <= 5 else SEVERITY_MEDIUM,
        status=PLAN_STATUS_FUTURE_PRIVILEGED_LANE_REQUIRED,
        user_impact=user_impact,
        next_check="Classify update intent in a future policy-gated planning stage; this stage does not run updates.",
        requires_future_privileged_lane=True,
    )


def _build_storage_plan_items(storage_result: Any | None) -> list[MaintenancePlanItem]:
    if _failed_or_unavailable_status(storage_result):
        return [
            MaintenancePlanItem(
                area="storage_hygiene",
                signal="storage signal unavailable or degraded",
                severity=SEVERITY_UNKNOWN,
                status=PLAN_STATUS_UNAVAILABLE,
                user_impact="Bond cannot classify storage pressure from this run.",
                next_check="Repeat the read-only maintenance readiness report later or inspect disk usage outside Bond.",
                requires_future_privileged_lane=False,
            )
        ]

    data = _result_data(storage_result)
    items: list[MaintenancePlanItem] = []
    for record in _safe_list(data.get("paths")):
        if not isinstance(record, dict):
            continue
        label = record.get("label") if isinstance(record.get("label"), str) else "unknown"
        exists = record.get("exists")
        free_percent = _as_float(record.get("free_percent"))
        if exists is not True or free_percent is None:
            continue
        if free_percent < 10:
            items.append(
                MaintenancePlanItem(
                    area="storage_hygiene",
                    signal=f"{label} free space below 10%",
                    severity=SEVERITY_MEDIUM,
                    status=PLAN_STATUS_MANUAL_REVIEW,
                    user_impact="Low free space may affect system reliability or future updates.",
                    next_check="Review storage pressure manually; this stage does not delete files or clean caches.",
                    requires_future_privileged_lane=False,
                )
            )
        elif free_percent < 20:
            items.append(
                MaintenancePlanItem(
                    area="storage_hygiene",
                    signal=f"{label} free space below 20%",
                    severity=SEVERITY_LOW,
                    status=PLAN_STATUS_MANUAL_REVIEW,
                    user_impact="Free space is getting low enough to watch.",
                    next_check="Review storage pressure manually; this stage does not delete files or clean caches.",
                    requires_future_privileged_lane=False,
                )
            )

    if not items:
        return [
            MaintenancePlanItem(
                area="storage_hygiene",
                signal="no low-free-space signal observed in bounded records",
                severity=SEVERITY_INFO,
                status=PLAN_STATUS_NO_IMMEDIATE_SIGNAL,
                user_impact="Bounded disk-usage records did not show immediate storage pressure.",
                next_check="No cleanup action is planned by Bond.",
                requires_future_privileged_lane=False,
            )
        ]

    return items


def _build_boot_service_plan_item(boot_result: Any | None) -> MaintenancePlanItem:
    if _failed_or_unavailable_status(boot_result):
        return MaintenancePlanItem(
            area="boot_service_health",
            signal="boot/service signal unavailable or degraded",
            severity=SEVERITY_UNKNOWN,
            status=PLAN_STATUS_UNAVAILABLE,
            user_impact="Bond cannot classify failed-unit or boot-warning pressure from this run.",
            next_check="Repeat the read-only maintenance readiness report later or inspect service health outside Bond.",
            requires_future_privileged_lane=False,
        )

    data = _result_data(boot_result)
    failed_count = _as_int(data.get("failed_units_count"))
    warning_count = _as_int(data.get("journal_warning_sample_count"))

    if failed_count is not None and failed_count > 0:
        return MaintenancePlanItem(
            area="boot_service_health",
            signal=f"{failed_count} failed unit(s) observed",
            severity=SEVERITY_MEDIUM,
            status=PLAN_STATUS_MANUAL_REVIEW,
            user_impact="Failed units may indicate degraded boot or service health.",
            next_check="Inspect failed-unit context in a future diagnostic stage; this stage does not restart or repair services.",
            requires_future_privileged_lane=False,
        )

    if warning_count is not None and warning_count > 0:
        return MaintenancePlanItem(
            area="boot_service_health",
            signal=f"{warning_count} recent boot warning line(s) sampled",
            severity=SEVERITY_LOW,
            status=PLAN_STATUS_MANUAL_REVIEW,
            user_impact="Recent warning signals may deserve review but are not proof of failure.",
            next_check="Review warning context in a future diagnostic stage; this stage does not mutate services.",
            requires_future_privileged_lane=False,
        )

    return MaintenancePlanItem(
        area="boot_service_health",
        signal="no failed-unit or boot-warning pressure observed in bounded sample",
        severity=SEVERITY_INFO,
        status=PLAN_STATUS_NO_IMMEDIATE_SIGNAL,
        user_impact="Bounded boot/service signals did not show immediate pressure.",
        next_check="No service action is planned by Bond.",
        requires_future_privileged_lane=False,
    )


def build_maintenance_plan(probe_results: Mapping[str, Any | None]) -> dict[str, object]:
    package_result = probe_results.get("package_update_status")
    storage_result = probe_results.get("storage_hygiene")
    boot_result = probe_results.get("boot_service_health")

    items = [
        _build_package_plan_item(package_result),
        *_build_storage_plan_items(storage_result),
        _build_boot_service_plan_item(boot_result),
    ]

    return {
        "plan_kind": PLAN_KIND,
        "action_authorized": False,
        "execution_supported": False,
        "items": [maintenance_plan_item_to_dict(item) for item in items],
        "boundaries": [
            "classification only",
            "no commands recommended",
            "no package updates",
            "no cleanup",
            "no service mutation",
            "no privileged execution",
            "does not authorize execution",
        ],
    }