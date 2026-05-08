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
        "It does not inspect real package freshness, does not inspect real logs, and does not inspect real storage usage.",
        "",
        "Probe basis:",
        f"- host_baseline: {probe_basis['host_baseline']}",
        f"- session_baseline: {probe_basis['session_baseline']}",
        f"- tool_inventory: {probe_basis['tool_inventory']}",
        f"- model_truth: {probe_basis['model_truth']}",
        "",
        "Host/session readiness:",
        f"- platform_system: {_value(host_data, 'platform_system')}",
        f"- platform_release: {_value(host_data, 'platform_release')}",
        f"- platform_machine: {_value(host_data, 'platform_machine')}",
        f"- python_version: {_value(host_data, 'python_version')}",
        f"- xdg_current_desktop: {_value(session_data, 'xdg_current_desktop')}",
        f"- desktop_session: {_value(session_data, 'desktop_session')}",
        f"- xdg_session_type: {_value(session_data, 'xdg_session_type')}",
        f"- has_display: {_bool_value(session_data, 'has_display')}",
        f"- has_wayland_display: {_bool_value(session_data, 'has_wayland_display')}",
        f"- has_dbus_session_bus: {_bool_value(session_data, 'has_dbus_session_bus')}",
        "",
        "Tool readiness:",
    ]

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
            "- Future work can add real read-only maintenance probes under explicit contracts.",
            "- Any future fix/update/cleanup action must be separately designed, policy-gated, and confirmation-gated.",
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
