from __future__ import annotations

from typing import Any

from ai_capabilities import (
    STATUS_BLOCKED,
    STATUS_PARTIAL,
    STATUS_PLANNED,
    STATUS_UNSUPPORTED,
    capability_status,
    get_capability,
    is_capability_available,
    list_capabilities,
)
from ai_capability_classifier import (
    ANSWER_KIND_CONTEXT,
    ANSWER_KIND_GENERAL,
    ANSWER_KIND_SPECIFIC,
    classify_capability_question,
    is_explicit_maintenance_readiness_question,
    is_capability_question,
    is_context_capability_question,
    is_general_capability_question,
    is_specific_capability_question,
    mentioned_capabilities,
    normalize_text,
)
from ai_probe_contract import validate_probe_result
from ai_maintenance_plan import build_maintenance_plan
from ai_probes import run_named_probe


def _specific_status_note(name: str, status: str) -> str:
    if status == STATUS_PARTIAL:
        note = "This capability is partial and usable with caveats."
    elif status == STATUS_PLANNED:
        note = "This capability is planned, not currently available."
    elif status == STATUS_UNSUPPORTED:
        note = "This capability is unsupported in the current phase."
    elif status == STATUS_BLOCKED:
        note = "This capability is blocked and not currently available."
    else:
        note = ""

    if name == "apply_privileged_system_updates":
        extra = "Bond cannot currently apply system updates and must never silently run upgrades."
        return f"{note} {extra}".strip()

    if name == "package_installation":
        extra = "Bond cannot currently install packages and must never silently run package-manager commands."
        return f"{note} {extra}".strip()

    if name == "dangerous_action_confirmation":
        extra = "Bond can require explicit confirmation for recognized high-risk requests, but this is not silent execution or full privileged system control."
        return f"{note} {extra}".strip()

    if name == "web_search":
        extra = "Web search is not currently wired."
        return f"{note} {extra}".strip()

    if name == "voice_interface":
        extra = "Voice input/output is not currently wired."
        return f"{note} {extra}".strip()

    if name == "desktop_applet":
        extra = "The desktop/tray applet is not currently wired."
        return f"{note} {extra}".strip()
    return note


def _build_general_answer() -> str:
    usable = [cap for cap in list_capabilities() if is_capability_available(cap.name)]

    lines = [
        "Capability summary:",
        "Current usable capabilities are partial and bounded, not broad autonomy.",
        "",
        "Usable with caveats:",
    ]

    for cap in usable:
        lines.append(f"- {cap.name} ({cap.status}, {cap.risk_level}): {cap.notes}")

    lines.extend(
        [
            "",
            "Planned or unavailable:",
            "- Planned entries exist for maintenance, document knowledge, localization, and richer capability explanations, but they are not currently available.",
            "- Unsupported in this phase: timer, clipboard.",
            "",
            "Safety boundary:",
            "Planned, blocked, unsupported, or unknown capabilities are not executable. Privileged system maintenance is not available and must never run silently.",
        ]
    )

    return "\n".join(lines)


def _safe_list_to_text(value: Any) -> str:
    try:
        if isinstance(value, (list, tuple)):
            items = [str(item).strip() for item in value if str(item).strip()]
            return ", ".join(items) if items else "none"
    except Exception:
        return "none"
    return "none"


def _build_model_truth_detail() -> str:
    fallback_lines = [
        "Model truth probe: unavailable in this run.",
        "configured route targets: unavailable",
        "installed local model inventory: unavailable",
        "inventory_available=false",
        "truth_status=unavailable",
        "missing configured models: unknown",
        "extra installed models: unknown",
        "Boundary: configured route targets and installed local model inventory are separate facts and must not be treated as the same thing. This does not prove currently answering model identity, runtime health, model quality, or privileged/system capability.",
    ]

    try:
        result = run_named_probe("model_truth")
        validation_errors = validate_probe_result(result)
        if validation_errors:
            return "\n".join(fallback_lines)

        data = result.data if isinstance(result.data, dict) else {}
        configured_models = _safe_list_to_text(data.get("configured_models"))
        inventory_available = bool(data.get("inventory_available"))
        truth_status = str(data.get("truth_status", "unknown")).strip() or "unknown"
        warnings = _safe_list_to_text(getattr(result, "warnings", ()))

        lines = [
            "Model truth probe:",
            f"configured route targets: {configured_models}",
            f"inventory_available={str(inventory_available).lower()}",
            f"truth_status={truth_status}",
        ]

        if inventory_available:
            installed_models = _safe_list_to_text(data.get("installed_models"))
            missing_models = _safe_list_to_text(data.get("missing_configured_models"))
            extra_models = _safe_list_to_text(data.get("extra_installed_models"))
            lines.extend(
                [
                    f"installed local model inventory: {installed_models}",
                    f"missing configured models: {missing_models}",
                    f"extra installed models: {extra_models}",
                ]
            )
        else:
            lines.extend(
                [
                    "installed local model inventory: unavailable in this run",
                    "missing configured models: unknown because installed inventory is unavailable",
                    "extra installed models: unknown because installed inventory is unavailable",
                ]
            )

        if warnings != "none":
            lines.append(f"warnings: {warnings}")

        lines.append(
            "Boundary: configured route targets and installed local model inventory are separate facts. This does not prove which model is currently answering, runtime health, model quality, or privileged/system capability."
        )
        return "\n".join(lines)
    except Exception:
        return "\n".join(fallback_lines)


def _build_context_capability_answer() -> str:
    def _validated_probe_data(probe_name: str) -> dict[str, Any] | None:
        try:
            result = run_named_probe(probe_name)
            validation_errors = validate_probe_result(result)
            if validation_errors:
                return None
            if getattr(result, "ok", False) is not True:
                return None
            if not isinstance(result.data, dict):
                return None
            return result.data
        except Exception:
            return None

    def _value(data: dict[str, Any] | None, key: str, fallback: str = "unknown") -> str:
        if not isinstance(data, dict):
            return fallback
        raw = data.get(key)
        if isinstance(raw, str):
            cleaned = raw.strip()
            return cleaned if cleaned else fallback
        if raw is None:
            return fallback
        return str(raw)

    def _bool_value(data: dict[str, Any] | None, key: str) -> str:
        if not isinstance(data, dict):
            return "unknown"
        raw = data.get(key)
        if isinstance(raw, bool):
            return "yes" if raw else "no"
        return "unknown"

    host_data = _validated_probe_data("host_baseline")
    session_data = _validated_probe_data("session_baseline")
    tools_data = _validated_probe_data("tool_inventory")
    model_data = _validated_probe_data("model_truth")

    probe_basis = {
        "host_baseline": "available" if host_data is not None else "unavailable",
        "session_baseline": "available" if session_data is not None else "unavailable",
        "tool_inventory": "available" if tools_data is not None else "unavailable",
        "model_truth": "available" if model_data is not None else "unavailable",
    }

    tools_node = tools_data.get("tools") if isinstance(tools_data, dict) else None
    tool_names = (
        "xdg-open",
        "gio",
        "xdg-mime",
        "xdg-settings",
        "notify-send",
        "systemctl",
        "journalctl",
        "flatpak",
        "snap",
        "apt",
        "ollama",
    )
    tool_status: dict[str, str] = {}
    for tool_name in tool_names:
        state = "unknown"
        if isinstance(tools_node, dict):
            entry = tools_node.get(tool_name)
            if isinstance(entry, dict):
                available = entry.get("available")
                if isinstance(available, bool):
                    state = "available" if available else "unavailable"
                else:
                    state = "unknown"
            elif entry is None:
                state = "unknown"
        tool_status[tool_name] = state

    model_truth_status = _value(model_data, "truth_status")
    model_inventory = _value(
        model_data,
        "inventory_available",
        fallback="unknown",
    )
    if model_inventory not in {"True", "False", "unknown"}:
        model_inventory = "unknown"
    elif model_inventory == "True":
        model_inventory = "available"
    elif model_inventory == "False":
        model_inventory = "unavailable"

    lines = [
        "Context capability summary:",
        "Bounded explicit context-capability answer using existing read-only probes only; this does not authorize execution, and normal assistant answers are not broadly probe-backed.",
        "",
        "Probe basis:",
        f"- host_baseline: {probe_basis['host_baseline']}",
        f"- session_baseline: {probe_basis['session_baseline']}",
        f"- tool_inventory: {probe_basis['tool_inventory']}",
        f"- model_truth: {probe_basis['model_truth']}",
        "",
        "Environment:",
        f"- platform_system: {_value(host_data, 'platform_system')}",
        f"- platform_release: {_value(host_data, 'platform_release')}",
        f"- platform_machine: {_value(host_data, 'platform_machine')}",
        f"- python_version: {_value(host_data, 'python_version')}",
        "",
        "Session:",
        f"- xdg_current_desktop: {_value(session_data, 'xdg_current_desktop')}",
        f"- desktop_session: {_value(session_data, 'desktop_session')}",
        f"- xdg_session_type: {_value(session_data, 'xdg_session_type')}",
        f"- has_display: {_bool_value(session_data, 'has_display')}",
        f"- has_wayland_display: {_bool_value(session_data, 'has_wayland_display')}",
        f"- has_dbus_session_bus: {_bool_value(session_data, 'has_dbus_session_bus')}",
        "",
        "Capability-relevant tools:",
    ]

    for tool_name in tool_names:
        lines.append(f"- {tool_name}: {tool_status[tool_name]}")

    lines.extend(
        [
            "",
            "Model/runtime boundary:",
            "- configured route targets and installed local model inventory are separate facts",
            f"- installed local model inventory status for this run: {model_inventory} (truth_status={model_truth_status})",
            "- installed inventory may be unavailable",
            "- this does not prove which model is currently answering, runtime health, model quality, or privileged/system capability",
            "",
            "Current bounded usable areas:",
            "- guarded known-target/path open behavior remains policy-gated and parser-bounded",
            "- registry-backed capability answers exist",
            "- explicit model/context capability questions can use bounded read-only probe detail",
            "- planned/blocked/unsupported capabilities remain unavailable",
            "",
            "Safety boundary:",
            "- no arbitrary shell execution",
            "- no privileged updates or package installation",
            "- no file creation/writing/deletion",
            "- no voice interface",
            "- no applet/service layer",
            "- no document RAG/ingestion execution",
            "- no broad autonomous desktop automation",
            "- this does not authorize execution",
            "- normal assistant answers are not broadly probe-backed",
        ]
    )

    return "\n".join(lines)


def _build_maintenance_readiness_report() -> str:
    def _validated_probe_result(probe_name: str) -> Any | None:
        try:
            if probe_name == "package_update_status":
                result = run_named_probe("package_update_status")
            elif probe_name == "storage_hygiene":
                result = run_named_probe("storage_hygiene")
            elif probe_name == "boot_service_health":
                result = run_named_probe("boot_service_health")
            else:
                result = run_named_probe(probe_name)
            validation_errors = validate_probe_result(result)
            if validation_errors:
                return None
            return result
        except Exception:
            return None

    def _probe_status(result: Any | None) -> str:
        if result is None:
            return "unavailable"
        if getattr(result, "ok", False) is True:
            return "available"
        return "degraded"

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

    def _probe_data(result: Any | None) -> dict[str, Any]:
        if result is None:
            return {}
        data = getattr(result, "data", None)
        return data if isinstance(data, dict) else {}

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

    host_result = _validated_probe_result("host_baseline")
    session_result = _validated_probe_result("session_baseline")
    tools_result = _validated_probe_result("tool_inventory")
    model_result = _validated_probe_result("model_truth")
    package_result = _validated_probe_result("package_update_status")
    storage_result = _validated_probe_result("storage_hygiene")
    boot_result = _validated_probe_result("boot_service_health")

    host_data = _probe_data(host_result)
    session_data = _probe_data(session_result)
    tools_data = _probe_data(tools_result)
    model_data = _probe_data(model_result)
    package_data = _probe_data(package_result)
    storage_data = _probe_data(storage_result)
    boot_data = _probe_data(boot_result)

    probe_basis = {
        "host_baseline": _probe_status(host_result),
        "session_baseline": _probe_status(session_result),
        "tool_inventory": _probe_status(tools_result),
        "model_truth": _probe_status(model_result),
        "package_update_status": _probe_status(package_result),
        "storage_hygiene": _probe_status(storage_result),
        "boot_service_health": _probe_status(boot_result),
    }

    tools_node = tools_data.get("tools") if isinstance(tools_data, dict) else None
    tool_names = (
        "apt",
        "snap",
        "flatpak",
        "systemctl",
        "journalctl",
        "systemd-analyze",
        "xdg-open",
        "gio",
        "notify-send",
        "ollama",
    )
    tool_status: dict[str, str] = {}
    for tool_name in tool_names:
        state = "unknown"
        if isinstance(tools_node, dict):
            entry = tools_node.get(tool_name)
            if isinstance(entry, dict):
                available = entry.get("available")
                if isinstance(available, bool):
                    state = "available" if available else "unavailable"
        tool_status[tool_name] = state

    model_truth_status = _value(model_data, "truth_status")
    inventory_raw = model_data.get("inventory_available") if isinstance(model_data, dict) else None
    if isinstance(inventory_raw, bool):
        model_inventory_status = "available" if inventory_raw else "unavailable"
    else:
        model_inventory_status = "unavailable"

    package_sample_text = _sample_names(package_data.get("upgradable_packages_sample"), "name")
    package_probe_status = _probe_status(package_result)
    package_manager = _value(package_data, "package_manager")
    apt_tool_status = _avail_from_path(package_data.get("apt_path"))
    cache_freshness_known = _yes_no_unknown(_as_bool(package_data.get("cache_freshness_known")))
    upgradable_count = _safe_count(package_data.get("upgradable_count"))

    storage_probe_status = _probe_status(storage_result)
    storage_scope = _value(storage_data, "scope")
    storage_paths_by_label: dict[str, dict[str, Any]] = {}
    for record in _safe_list(storage_data.get("paths")):
        if not isinstance(record, dict):
            continue
        label = record.get("label")
        if isinstance(label, str):
            storage_paths_by_label[label] = record

    boot_probe_status = _probe_status(boot_result)
    systemctl_available = _yes_no_unknown(_as_bool(boot_data.get("systemctl_available")))
    journalctl_available = _yes_no_unknown(_as_bool(boot_data.get("journalctl_available")))
    failed_units_observed = _safe_count(boot_data.get("failed_units_count"))
    boot_warning_count = _safe_count(boot_data.get("journal_warning_sample_count"))
    failed_unit_sample = _sample_names(boot_data.get("failed_units_sample"), "unit")
    systemctl_error_kind = _value(boot_data, "systemctl_error_kind", fallback="none")
    journalctl_error_kind = _value(boot_data, "journalctl_error_kind", fallback="none")

    status_names = [
        "describe_maintenance_readiness",
        "inspect_package_update_status",
        "inspect_storage_hygiene",
        "inspect_boot_and_service_health",
        "generate_periodic_health_report",
        "present_maintenance_dashboard",
        "apply_privileged_system_updates",
    ]

    capability_lines: list[str] = []
    for name in status_names:
        cap = get_capability(name)
        status = cap.status if cap is not None else "unknown"
        if name == "describe_maintenance_readiness":
            capability_lines.append(f"- {name}: status={status} (partial/read-only)")
        elif status in {STATUS_PLANNED, STATUS_BLOCKED, STATUS_UNSUPPORTED}:
            capability_lines.append(f"- {name}: status={status} (unavailable)")
        else:
            capability_lines.append(f"- {name}: status={status}")

    lines = [
        "Maintenance/readiness summary:",
        "This is a read-only readiness report based on existing read-only probes only.",
        "It does not fix anything, does not install packages, does not write files, does not delete files, does not restart services, and does not authorize execution.",
        "It uses bounded read-only maintenance signals only; package metadata freshness is not proven, storage hygiene is bounded to disk-usage records, and boot/service health is limited to failed-unit and recent boot-warning signals.",
        "",
        "Probe basis:",
        f"- host_baseline: {probe_basis['host_baseline']}",
        f"- session_baseline: {probe_basis['session_baseline']}",
        f"- tool_inventory: {probe_basis['tool_inventory']}",
        f"- model_truth: {probe_basis['model_truth']}",
        f"- package_update_status: {probe_basis['package_update_status']}",
        f"- storage_hygiene: {probe_basis['storage_hygiene']}",
        f"- boot_service_health: {probe_basis['boot_service_health']}",
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
            f"- journalctl available: {journalctl_available}",
            f"- failed units observed: {failed_units_observed}",
            f"- recent boot warning sample count: {boot_warning_count}",
            f"- failed unit sample: {failed_unit_sample}",
            "- boundary: failed-unit and recent boot-warning signals only; this report does not restart, stop, start, enable, disable, mask, or repair services.",
        ]
    )

    if (
        isinstance(boot_data.get("systemctl_error_kind"), str)
        or isinstance(boot_data.get("journalctl_error_kind"), str)
    ):
        lines.append(
            f"- signal limitations: systemctl={systemctl_error_kind}, journalctl={journalctl_error_kind}"
        )

    maintenance_plan = build_maintenance_plan(
        {
            "package_update_status": package_result,
            "storage_hygiene": storage_result,
            "boot_service_health": boot_result,
        }
    )
    plan_items = maintenance_plan.get("items", [])
    if not isinstance(plan_items, list):
        plan_items = []

    lines.extend(
        [
            "",
            "Non-executing maintenance plan:",
            f"- plan kind: {maintenance_plan.get('plan_kind', 'unknown')}",
            f"- action authorized: {'yes' if maintenance_plan.get('action_authorized') is True else 'no'}",
            f"- execution supported: {'yes' if maintenance_plan.get('execution_supported') is True else 'no'}",
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
            "",
            "Tool readiness:",
        ]
    )

    for tool_name in tool_names:
        lines.append(f"- {tool_name}: {tool_status[tool_name]}")

    lines.extend(
        [
            "",
            "Model/runtime readiness:",
            "- configured route targets and installed local model inventory are separate facts",
            f"- installed local model inventory status for this run: {model_inventory_status} (truth_status={model_truth_status})",
            "- installed inventory may be unavailable",
            "- this does not prove which model is currently answering, runtime health, model quality, or privileged/system capability",
            "",
            "Maintenance capability status:",
            *capability_lines,
            "- planned/blocked capabilities remain unavailable",
            "",
            "Current safe next actions:",
            "- The user can ask for this bounded read-only readiness report.",
            "- Future work can add a separate maintenance planning layer that classifies observed signals without executing fixes.",
            "- Future privileged actions must be designed as a separate policy-gated and confirmation-gated lane.",
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

    return "\n".join(lines)


def _build_specific_answer(text: str, names: tuple[str, ...] | None = None) -> str:
    if names is None:
        names = tuple(mentioned_capabilities(text))

    if "describe_maintenance_readiness" in names:
        if is_explicit_maintenance_readiness_question(text):
            return _build_maintenance_readiness_report()
        if "query_model" not in names:
            return _build_maintenance_readiness_report()

    lines = ["Capability check:"]

    for name in names:
        cap = get_capability(name)
        status = capability_status(name)
        risk = cap.risk_level if cap is not None else "n/a"
        notes = cap.notes if cap is not None else "No registry details available."
        availability = (
            "usable with caveats" if is_capability_available(name) else "not currently available"
        )
        status_note = _specific_status_note(name, status)
        detail_parts = [notes]
        if status_note:
            detail_parts.append(status_note)
        details = " ".join(part for part in detail_parts if part).strip()
        lines.append(
            f"- {name}: {availability}; status={status}; risk={risk}. {details}".strip()
        )
        if name == "query_model":
            lines.append(_build_model_truth_detail())

    return "\n".join(lines)


def answer_capability_question(text: str) -> str | None:
    classification = classify_capability_question(text)
    if not classification.is_capability_question:
        return None

    if classification.answer_kind == ANSWER_KIND_CONTEXT:
        return _build_context_capability_answer()

    if classification.answer_kind == ANSWER_KIND_GENERAL:
        return _build_general_answer()

    if classification.answer_kind == ANSWER_KIND_SPECIFIC:
        return _build_specific_answer(text, classification.mentioned_capabilities)

    return None


def maybe_answer_capability_question(text: str) -> str | None:
    return answer_capability_question(text)
