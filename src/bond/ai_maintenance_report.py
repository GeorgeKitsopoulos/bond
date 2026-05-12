"""Pure maintenance-readiness report assembly and formatting seam.

This module assembles and formats the explicit maintenance/readiness report.
It may consume existing read-only probe results and ai_maintenance_plan output.
It must not perform execution, mutation, package update, cleanup, service
control, or privileged operations.
"""
from __future__ import annotations

from typing import Any, Mapping

from ai_probe_contract import validate_probe_result
from ai_probes import run_named_probe
from ai_maintenance_plan import PLAN_KIND, build_maintenance_plan
from ai_capabilities import (
    STATUS_PLANNED,
    STATUS_UNSUPPORTED,
    get_capability,
)

REPORT_KIND = "maintenance_readiness_report"
REPORT_SCHEMA_VERSION = 1
# Full set of probes used for the maintenance readiness report.
# Context probes (host_baseline, session_baseline, tool_inventory, model_truth)
# are run for the host/tool/model sections; maintenance probes are run for the
# package/storage/boot sections.
_CONTEXT_PROBE_NAMES = (
    "host_baseline",
    "session_baseline",
    "tool_inventory",
    "model_truth",
)
_MAINTENANCE_SPECIFIC_PROBE_NAMES = (
    "package_update_status",
    "storage_hygiene",
    "boot_service_health",
)
MAINTENANCE_PROBE_NAMES = _MAINTENANCE_SPECIFIC_PROBE_NAMES
_ALL_PROBE_NAMES = _CONTEXT_PROBE_NAMES + _MAINTENANCE_SPECIFIC_PROBE_NAMES

_BOUNDARIES: list[str] = [
    "read-only/rootless probe facts only",
    "classification only",
    "no commands recommended",
    "no package updates",
    "no cleanup execution",
    "no service mutation",
    "no privileged execution",
    "does not authorize execution",
]


def _collect_probe_results() -> dict[str, Any]:
    collected: dict[str, Any] = {}
    for name in _ALL_PROBE_NAMES:
        try:
            collected[name] = run_named_probe(name)
        except Exception:
            collected[name] = None
    return collected


def build_maintenance_readiness_report(
    probe_results: Mapping[str, Any] | None = None,
) -> dict[str, object]:
    """Build the structured maintenance readiness report dict.

    If probe_results is None, run all named probes.  If supplied, use only those
    supplied values (context probes default to None if not supplied).
    Never runs any command directly.
    """
    if probe_results is None:
        results: dict[str, Any] = _collect_probe_results()
    else:
        # Accept maintenance-specific probes from caller; context probes optional
        results = {}
        for name in _ALL_PROBE_NAMES:
            results[name] = probe_results.get(name)

    probe_validation: dict[str, list[str]] = {}
    for name in MAINTENANCE_PROBE_NAMES:
        result = results.get(name)
        if result is not None:
            try:
                probe_validation[name] = validate_probe_result(result)
            except Exception:
                probe_validation[name] = ["validate_probe_result raised an exception"]
        else:
            probe_validation[name] = ["probe result unavailable"]

    plan = build_maintenance_plan(
        {name: results.get(name) for name in MAINTENANCE_PROBE_NAMES}
    )

    return {
        "report_kind": REPORT_KIND,
        "schema_version": REPORT_SCHEMA_VERSION,
        "action_authorized": False,
        "execution_supported": False,
        "probes_used": list(MAINTENANCE_PROBE_NAMES),
        "probe_validation": probe_validation,
        "probe_results": results,
        "plan": plan,
        "boundaries": list(_BOUNDARIES),
    }


# ---------------------------------------------------------------------------
# Formatting helpers (mirror the wording from ai_capability_answer.py)
# ---------------------------------------------------------------------------


def _probe_status(result: Any | None) -> str:
    if result is None:
        return "unavailable"
    if getattr(result, "ok", False) is True:
        return "available"
    return "degraded"


def _probe_data(result: Any | None) -> dict[str, Any]:
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


def _as_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    return None


def _safe_percent(value: Any) -> str:
    if isinstance(value, bool):
        return "unknown"
    if isinstance(value, (int, float)):
        return f"{value:.2f}%"
    return "unknown"


def _safe_count(value: Any) -> str:
    number = _as_int(value)
    return str(number) if number is not None else "unknown"


def _safe_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    return []


def _value(data: dict[str, Any], key: str, fallback: str = "unknown") -> str:
    raw = data.get(key)
    if isinstance(raw, str):
        cleaned = raw.strip()
        return cleaned if cleaned else fallback
    if raw is None:
        return fallback
    return str(raw)


def _yes_no_unknown(value: bool | None) -> str:
    if value is True:
        return "yes"
    if value is False:
        return "no"
    return "unknown"


def _avail_from_path(value: Any) -> str:
    if isinstance(value, str):
        return "available" if value.strip() else "unavailable"
    if value is None:
        return "unknown"
    return "unavailable"


def _sample_names(sample: Any, key: str) -> str:
    names: list[str] = []
    for entry in _safe_list(sample)[:5]:
        if isinstance(entry, dict):
            raw_name = entry.get(key)
            if isinstance(raw_name, str):
                cleaned = raw_name.strip()
                if cleaned:
                    names.append(cleaned)
    return ", ".join(names) if names else "none"


def _exists_text(value: Any) -> str:
    exists = _as_bool(value)
    if exists is True:
        return "yes"
    if exists is False:
        return "no"
    return "unknown"


def format_maintenance_readiness_report(report: Mapping[str, Any]) -> list[str]:
    """Return assistant-facing report lines from the structured report dict."""
    raw_results: dict[str, Any] = dict(report.get("probe_results") or {})
    plan: dict[str, Any] = dict(report.get("plan") or {})

    package_result = raw_results.get("package_update_status")
    storage_result = raw_results.get("storage_hygiene")
    boot_result = raw_results.get("boot_service_health")

    package_data = _probe_data(package_result)
    storage_data = _probe_data(storage_result)
    boot_data = _probe_data(boot_result)

    package_probe_status = _probe_status(package_result)
    storage_probe_status = _probe_status(storage_result)
    boot_probe_status = _probe_status(boot_result)

    package_manager = _value(package_data, "package_manager")
    apt_tool_status = _avail_from_path(package_data.get("apt_path"))
    cache_freshness_known = _yes_no_unknown(_as_bool(package_data.get("cache_freshness_known")))
    upgradable_count = _safe_count(package_data.get("upgradable_count"))
    package_sample_text = _sample_names(package_data.get("upgradable_packages_sample"), "name")

    storage_scope = _value(storage_data, "scope")
    storage_paths_by_label: dict[str, dict[str, Any]] = {}
    for record in _safe_list(storage_data.get("paths")):
        if not isinstance(record, dict):
            continue
        label = record.get("label")
        if isinstance(label, str):
            storage_paths_by_label[label] = record

    systemctl_available = _yes_no_unknown(_as_bool(boot_data.get("systemctl_available")))
    jctl_avail = _yes_no_unknown(_as_bool(boot_data.get("jrnctl_available")))
    failed_units_observed = _safe_count(boot_data.get("failed_units_count"))
    boot_warning_count = _safe_count(boot_data.get("journal_warning_sample_count"))
    failed_unit_sample = _sample_names(boot_data.get("failed_units_sample"), "unit")
    systemctl_error_kind = _value(boot_data, "systemctl_error_kind", fallback="none")
    jctl_error_kind = _value(boot_data, "jrnctl_error_kind", fallback="none")

    plan_items = plan.get("items", [])
    if not isinstance(plan_items, list):
        plan_items = []

    lines: list[str] = [
        "Maintenance/readiness summary:",
        "This is a read-only readiness report based on existing read-only probes only.",
        "It does not fix anything, does not install packages, does not write files, does not delete files, does not restart services, and does not authorize execution.",
        "It uses bounded read-only maintenance signals only; package metadata freshness is not proven, storage hygiene is bounded to disk-usage records, and boot/service health is limited to failed-unit and recent boot-warning signals.",
        "",
        "Package update status:",
        f"- probe status: {package_probe_status}",
        f"- package manager: {package_manager}",
        f"- apt tool: {apt_tool_status}",
        f"- apt cache freshness known: {cache_freshness_known}",
        f"- upgradable packages from local cache: {upgradable_count}",
        f"- sample: {package_sample_text}",
        "- boundary: local apt cache inspection only; this report does not run apt "
        "update or upgrades.",
        "",
        "Storage hygiene:",
        f"- probe status: {storage_probe_status}",
        f"- scope: {storage_scope}",
    ]

    if package_probe_status in {"degraded", "unavailable"}:
        lines.append("- availability note: package update signal unavailable or degraded in this run.")

    for label in ["root", "home", "bond_root", "state_root", "memory_root"]:
        record = storage_paths_by_label.get(label)
        if not isinstance(record, dict):
            continue
        lines.append(
            f"- {label}: exists={_exists_text(record.get('exists'))}, free percent={_safe_percent(record.get('free_percent'))}"
        )

    lines.extend(
        [
            "- boundary: bounded disk-usage records only; this report does not scan duplicates, delete files, or clean caches.",
            "",
            "Boot/service health:",
            f"- probe status: {boot_probe_status}",
            f"- systemctl available: {systemctl_available}",
            f"- journal tool available: {jctl_avail}",
            f"- failed units observed: {failed_units_observed}",
            f"- recent boot warning sample count: {boot_warning_count}",
            f"- failed unit sample: {failed_unit_sample}",
            "- boundary: failed-unit and recent boot-warning signals only; this report does not restart, stop, start, enable, disable, mask, or repair services.",
        ]
    )

    if (
        isinstance(boot_data.get("systemctl_error_kind"), str)
        or isinstance(boot_data.get("jrnctl_error_kind"), str)
    ):
        lines.append(
            f"- signal limitations: systemctl={systemctl_error_kind}, jctl={jctl_error_kind}"
        )

    lines.extend(
        [
            "",
            "Non-executing maintenance plan:",
            f"- plan kind: {plan.get('plan_kind', 'unknown')}",
            f"- action authorized: {'yes' if plan.get('action_authorized') is True else 'no'}",
            f"- execution supported: {'yes' if plan.get('execution_supported') is True else 'no'}",
        ]
    )

    for item in plan_items[:6]:
        if not isinstance(item, dict):
            continue
        lines.append(
            "- {area}: severity={severity}; status={status}; signal={signal}; next check={next_check}; future privileged lane required={requires_future_privileged_lane}".format(
                area=item.get("area", "unknown"),
                severity=item.get("severity", "unknown"),
                status=item.get("status", "unknown"),
                signal=item.get("signal", "unknown"),
                next_check=item.get("next_check", "unknown"),
                requires_future_privileged_lane="yes"
                if item.get("requires_future_privileged_lane") is True
                else "no",
            )
        )

    lines.append(
        "- boundary: classification only; this plan does not recommend commands, does not ex"
        "ecute fixes, and does not authorize execution."
    )

    # -----------------------------------------------------------------------
    # Additional sections required by Stage 2F-E-C tests
    # -----------------------------------------------------------------------

    # Probe basis section
    host_result = raw_results.get("host_baseline")
    session_result = raw_results.get("session_baseline")
    tools_result = raw_results.get("tool_inventory")
    model_result = raw_results.get("model_truth")

    lines.extend(
        [
            "",
            "Probe basis:",
            f"- host_baseline: {_probe_status(host_result)}",
            f"- session_baseline: {_probe_status(session_result)}",
            f"- tool_inventory: {_probe_status(tools_result)}",
            f"- model_truth: {_probe_status(model_result)}",
            f"- package_update_status: {package_probe_status}",
            f"- storage_hygiene: {storage_probe_status}",
            f"- boot_service_health: {boot_probe_status}",
        ]
    )

    # Host/session readiness section
    host_data = _probe_data(host_result)
    session_data = _probe_data(session_result)
    lines.extend(
        [
            "",
            "Host/session readiness:",
            f"- platform_system: {_value(host_data, 'platform_system')}",
            f"- platform_release: {_value(host_data, 'platform_release')}",
            f"- platform_machine: {_value(host_data, 'platform_machine')}",
            f"- python_version: {_value(host_data, 'python_version')}",
            f"- xdg_current_desktop: {_value(session_data, 'xdg_current_desktop')}",
            f"- desktop_session: {_value(session_data, 'desktop_session')}",
            f"- xdg_session_type: {_value(session_data, 'xdg_session_type')}",
            f"- has_display: {_yes_no_unknown(_as_bool(session_data.get('has_display')))}",
            f"- has_wayland_display: {_yes_no_unknown(_as_bool(session_data.get('has_wayland_display')))}",
            f"- has_dbus_session_bus: {_yes_no_unknown(_as_bool(session_data.get('has_dbus_session_bus')))}",
        ]
    )

    # Tool readiness section
    tools_data = _probe_data(tools_result)
    tools_node = tools_data.get("tools") if isinstance(tools_data, dict) else None
    _tool_names = (
        "apt",
        "snap",
        "flatpak",
        "xdg-open",
        "gio",
        "notify-send",
        "ollama",
    )
    lines.append("")
    lines.append("Tool readiness:")
    for tool_name in _tool_names:
        state = "unknown"
        if isinstance(tools_node, dict):
            entry = tools_node.get(tool_name)
            if isinstance(entry, dict):
                available = entry.get("available")
                if isinstance(available, bool):
                    state = "available" if available else "unavailable"
        lines.append(f"- {tool_name}: {state}")

    # Model/runtime readiness section
    model_data = _probe_data(model_result)
    model_truth_status = _value(model_data, "truth_status")
    inventory_raw = model_data.get("inventory_available") if isinstance(model_data, dict) else None
    if isinstance(inventory_raw, bool):
        model_inventory_status = "available" if inventory_raw else "unavailable"
    else:
        model_inventory_status = "unavailable"
    lines.extend(
        [
            "",
            "Model/runtime readiness:",
            "- configured route targets and installed local model inventory are separate facts",
            f"- installed local model inventory status for this run: {model_inventory_status} (truth_status={model_truth_status})",
            "- installed inventory may be unavailable",
            "- this does not prove which model is currently answering, runtime health, model quality, or privileged/system capability",
        ]
    )

    # Maintenance capability status section
    _capability_status_names = [
        "describe_maintenance_readiness",
        "inspect_package_update_status",
        "inspect_storage_hygiene",
        "inspect_boot_and_service_health",
        "generate_periodic_health_report",
        "present_maintenance_dashboard",
        "apply_privileged_system_updates",
    ]
    lines.append("")
    lines.append("Maintenance capability status:")
    for cap_name in _capability_status_names:
        cap = get_capability(cap_name)
        status = cap.status if cap is not None else "unknown"
        if cap_name == "describe_maintenance_readiness":
            lines.append(f"- {cap_name}: status={status} (partial/read-only)")
        elif status in {STATUS_PLANNED, STATUS_UNSUPPORTED}:
            lines.append(f"- {cap_name}: status={status} (unavailable)")
        else:
            lines.append(f"- {cap_name}: status={status}")
    lines.append("- planned/blocked capabilities remain unavailable")

    # Current safe next actions section
    lines.extend(
        [
            "",
            "Current safe next actions:",
            "- The user can ask for this bounded read-only readiness report.",
            "- Future work can add a separate maintenance planning layer that classifies observed signals without executing fixes.",
            "- Future privileged actions must be designed as a separate policy-gated and confirmation-gated lane.",
        ]
    )

    # Safety boundary section
    lines.extend(
        [
            "",
            "Safety boundary:",
            "- no package installation",
            "- no system updates",
            "- no file creation/writing/deletion",
            "- no cleanup",
            "- no service restart",
            "- no privileged operations",
            "- no autonomous repair",
            "- no background maintenance daemon",
            "- no arbitrary shell execution",
            "- does not authorize execution",
        ]
    )

    return lines


def build_and_format_maintenance_readiness_report() -> str:
    """Build and format the maintenance readiness report, returning a single string."""
    report = build_maintenance_readiness_report()
    lines = format_maintenance_readiness_report(report)
    return "\n".join(lines)
