from __future__ import annotations

import unicodedata
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
from ai_linguistics import strip_assistant_invocation_prefix
from ai_probe_contract import validate_probe_result
from ai_probes import run_named_probe


_CAPABILITY_ALIASES: dict[str, tuple[str, ...]] = {
    "open_known_target": (
        "open known target",
        "known target",
        "open app",
        "open application",
        "launch app",
    ),
    "open_explicit_path": (
        "open path",
        "open file",
        "open folder",
        "open directory",
        "local path",
    ),
    "query_shell": (
        "shell query",
        "query shell",
        "terminal query",
        "command output",
        "shell information",
        "terminal commands",
        "run terminal commands",
        "terminal command",
        "run commands",
        "shell commands",
    ),
    "query_directory": (
        "directory query",
        "query directory",
        "list directory",
        "folder state",
        "directory state",
    ),
    "query_model": (
        "model",
        "models",
        "ollama",
        "installed models",
        "model inventory",
        "runtime model",
        "what model are you using",
        "what models are installed",
        "which local model are you using right now",
        "local models",
        "use qwen",
        "nomic embed text",
        "τι μοντέλα έχεις",
        "τι μοντελα εχεις",
        "ποια μοντέλα έχεις",
        "ποια μοντελα εχεις",
        "τι μοντέλο χρησιμοποιείς",
        "τι μοντελο χρησιμοποιεις",
        "ποιο μοντέλο χρησιμοποιείς",
        "ποιο μοντελο χρησιμοποιεις",
    ),
    "timer": (
        "timer",
        "timers",
        "reminder",
        "reminders",
        "remind me",
        "remind me in",
        "set a reminder",
        "set reminder",
        "χρονομετρο",
        "υπενθυμιση",
        "υπενθυμισεις",
        "timers are a thing",
        "are timers a thing",
        "reminders work",
        "υπενθυμίσεις",
        "timers are implemented",
        "tell me timers are implemented",
        "timer implemented",
        "timer implementation",
    ),
    "clipboard": (
        "clipboard",
        "copy paste",
        "copy/paste",
        "προχειρο",
    ),
    "describe_capabilities": (
        "capabilities",
        "what can you do",
        "what are your capabilities",
        "list capabilities",
        "show capabilities",
        "available capabilities",
        "τι μπορεις να κανεις",
        "δυνατοτητες",
        "ικανοτητες",
        "τι ξερεις να κανεις",
    ),
    "describe_context_capabilities": (
        "what can you do here",
        "what can you do on this system",
        "what can you do in this environment",
        "what can you do in this session",
        "current environment capabilities",
        "current session capabilities",
        "system capabilities",
        "context capabilities",
        "local environment capabilities",
        "probe backed capabilities",
        "τι μπορεις να κανεις εδω",
        "τι μπορείς να κάνεις εδώ",
        "τι μπορεις να κανεις σε αυτο το συστημα",
        "τι μπορείς να κάνεις σε αυτό το σύστημα",
        "δυνατοτητες σε αυτο το συστημα",
        "δυνατότητες σε αυτό το σύστημα",
        "δυνατοτητες εδω",
        "δυνατότητες εδώ",
    ),
    "preview_action": (
        "preview action",
        "dry run action",
        "show action plan",
        "what would you do",
    ),
    "explain_decision": (
        "explain decision",
        "why did you choose",
        "why did you route",
        "policy reason",
    ),
    "register_plugin_capability": (
        "register plugin",
        "plugin capability",
        "extension capability",
    ),
    "resolve_invocation_alias": (
        "alias",
        "aliases",
        "command alias",
        "invocation alias",
    ),
    "detect_utterance_language": (
        "detect language",
        "language detection",
        "greek detection",
        "english detection",
        "detect greek",
        "detect whether i write greek or english",
        "μιλας ελληνικα",
        "μιλάς ελληνικά",
        "καταλαβαινεις ελληνικα",
        "καταλαβαίνεις ελληνικά",
        "μπορεις να καταλαβεις ελληνικα",
        "μπορείς να καταλάβεις ελληνικά",
    ),
    "apply_response_language_policy": (
        "response language",
        "answer language",
        "language policy",
        "can you answer in greek",
        "can you respond in greek",
        "answer me in greek",
        "answer me in greek from now on",
        "μπορεις να απαντησεις στα ελληνικα",
        "μπορείς να απαντήσεις στα ελληνικά",
        "μπορεις να απαντας στα ελληνικα",
        "μπορείς να απαντάς στα ελληνικά",
        "απαντα ελληνικα",
        "απάντα ελληνικά",
        "απαντα μου ελληνικα",
        "απάντα μου ελληνικά",
        "γραφε ελληνικα",
        "γράφε ελληνικά",
    ),
    "localize_user_message": (
        "localization",
        "localisation",
        "localize",
        "translate ui",
        "greek ui",
    ),
    "inspect_package_update_status": (
        "package updates",
        "update status",
        "apt updates",
        "flatpak updates",
        "snap updates",
        "available updates",
    ),
    "plan_safe_system_update": (
        "plan system update",
        "safe system update",
        "update plan",
        "upgrade plan",
    ),
    "apply_privileged_system_updates": (
        "update my system",
        "upgrade my system",
        "apply updates",
        "install updates",
        "system upgrade",
        "system updates",
        "update packages",
        "system update",
        "ενημερωση συστηματος",
        "ενημέρωση συστήματος",
        "αναβαθμιση συστηματος",
        "αναβάθμιση συστήματος",
        "ενημερωσεις",
        "ενημερώσεις",
        "privileged maintenance",
        "update my packages",
        "can you update my packages",
        "package updates",
        "do you support package updates",
    ),
    "voice_interface": (
        "voice",
        "voice interface",
        "voice chat",
        "talk with voice",
        "speak with voice",
        "microphone",
        "φωνη",
        "φωνή",
        "εχεις φωνη",
        "έχεις φωνή",
        "μιλας με φωνη",
        "μιλάς με φωνή",
    ),
    "desktop_applet": (
        "tray applet",
        "desktop applet",
        "cinnamon applet",
        "applet",
        "tray icon",
    ),
    "web_search": (
        "web search",
        "search the web",
        "search online",
        "browser search",
        "open a browser and search the web",
        "browser and search the web",
    ),
    "persistent_memory": (
        "remember things between chats",
        "remember between chats",
        "memory between chats",
        "persistent memory",
        "long term memory",
        "do you remember things between chats",
        "μνημη",
        "μνήμη",
        "εχεις μνημη",
        "έχεις μνήμη",
        "θυμασαι",
        "θυμάσαι",
    ),
    "local_file_read": (
        "read local files",
        "local files",
        "read files",
        "inspect local files",
        "file reading",
    ),
    "package_installation": (
        "install packages",
        "install package",
        "apt install",
        "package installation",
        "can you install packages",
    ),
    "dangerous_action_confirmation": (
        "restart the laptop",
        "restart laptop",
        "reboot the computer",
        "reboot computer",
        "shutdown the system",
        "shutdown system",
        "delete files",
        "delete file",
        "delete my files",
        "run rm -rf",
        "rm -rf",
        "destructive actions",
        "dangerous actions",
        "high risk actions",
    ),
    "inspect_storage_hygiene": (
        "storage hygiene",
        "disk cleanup",
        "disk space",
        "clean storage",
        "storage report",
    ),
    "inspect_boot_and_service_health": (
        "boot health",
        "service health",
        "systemd",
        "journalctl",
        "systemctl",
        "boot time",
    ),
    "generate_periodic_health_report": (
        "health report",
        "periodic health report",
        "monthly report",
        "maintenance report",
    ),
    "present_maintenance_dashboard": (
        "maintenance dashboard",
        "dashboard",
        "system dashboard",
    ),
    "inspect_document_corpus_status": (
        "document corpus",
        "corpus status",
        "knowledge status",
    ),
    "retrieve_document_knowledge": (
        "retrieve documents",
        "document search",
        "knowledge retrieval",
        "rag",
        "search my documents",
        "search documents",
        "ψαξεις τα εγγραφα μου",
        "ψάξεις τα έγγραφά μου",
        "ψαξε τα εγγραφα",
        "ψάξε τα έγγραφα",
        "αναζητηση εγγραφων",
        "αναζήτηση εγγράφων",
    ),
    "ingest_knowledge_sources": (
        "ingest documents",
        "ingest knowledge",
        "add documents",
        "index documents",
    ),
    "reindex_document_corpus": (
        "reindex documents",
        "reindex corpus",
        "refresh index",
        "rebuild index",
    ),
}

_GENERAL_QUESTION_PHRASES = (
    "what can you do",
    "what are your capabilities",
    "list capabilities",
    "show capabilities",
    "available capabilities",
    "what tools do you have",
    "τι μπορεις να κανεις",
    "τι ξερεις να κανεις",
    "ποιες ειναι οι δυνατοτητες",
    "δυνατοτητες σου",
    "ικανοτητες σου",
)

_SPECIFIC_QUESTION_PHRASES = (
    "can you",
    "do you",
    "do you have",
    "do you remember",
    "are you able to",
    "do you support",
    "can bond",
    "does bond support",
    "tell me",
    "claim that",
    "lie and say",
    "μπορεις να",
    "υποστηριζεις",
    "μπορει ο bond",
    "μπορει το bond",
    "say that",
    "pretend",
    "correct",
    "or not",
    "answer me in greek",
    "answer me in greek from now on",
    "απαντα ελληνικα",
    "απάντα ελληνικά",
    "απαντα μου ελληνικα",
    "απάντα μου ελληνικά",
    "γραφε ελληνικα",
    "γράφε ελληνικά",
    "μιλας ελληνικα",
    "μιλάς ελληνικά",
    "καταλαβαινεις ελληνικα",
    "καταλαβαίνεις ελληνικά",
    "μπορεις να καταλαβεις ελληνικα",
    "μπορείς να καταλάβεις ελληνικά",
)

_ASSERTIVE_CAPABILITY_PROMPT_PHRASES = (
    "say that",
    "tell me",
    "pretend",
    "implemented",
    "even if they are not",
    "lie and say",
    "claim that",
    "correct",
    "or not",
    "are timers a thing",
    "timers are a thing",
)


def normalize_text(text: str) -> str:
    if not isinstance(text, str):
        return ""

    stripped = text.strip().lower()
    if not stripped:
        return ""

    decomposed = unicodedata.normalize("NFKD", stripped)
    without_marks = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    cleaned = "".join(ch if (ch.isalnum() or ch in {"/", " "}) else " " for ch in without_marks)
    collapsed = " ".join(cleaned.split())

    if not collapsed or not any(ch.isalnum() for ch in collapsed):
        return ""
    return collapsed


def _contains_phrase(text: str, phrase: str) -> bool:
    return f" {phrase} " in f" {text} "


_NORMALIZED_ALIASES: dict[str, tuple[str, ...]] = {
    name: tuple(alias for alias in (normalize_text(item) for item in aliases) if alias)
    for name, aliases in _CAPABILITY_ALIASES.items()
}


def mentioned_capabilities(text: str) -> list[str]:
    stripped = strip_assistant_invocation_prefix(text)
    normalized = normalize_text(stripped)
    if not normalized:
        return []

    matches: list[str] = []
    for name in sorted(_NORMALIZED_ALIASES):
        aliases = _NORMALIZED_ALIASES[name]
        if any(_contains_phrase(normalized, alias) for alias in aliases):
            matches.append(name)
    return matches


def is_general_capability_question(text: str) -> bool:
    stripped = strip_assistant_invocation_prefix(text)
    normalized = normalize_text(stripped)
    if not normalized:
        return False
    return any(_contains_phrase(normalized, phrase) for phrase in _GENERAL_QUESTION_PHRASES)


def is_context_capability_question(text: str) -> bool:
    stripped = strip_assistant_invocation_prefix(text)
    normalized = normalize_text(stripped)
    if not normalized:
        return False

    aliases = _NORMALIZED_ALIASES.get("describe_context_capabilities", ())
    return any(_contains_phrase(normalized, alias) for alias in aliases)


def _is_bare_capability_reference(text: str) -> bool:
    stripped = strip_assistant_invocation_prefix(text)
    normalized = normalize_text(stripped)
    if not normalized:
        return False

    caps = mentioned_capabilities(normalized)
    if not caps:
        return False

    word_count = len(normalized.split())
    if word_count > 6:
        return False

    return True


def is_specific_capability_question(text: str) -> bool:
    has_question_mark = "?" in text
    stripped = strip_assistant_invocation_prefix(text)
    normalized = normalize_text(stripped)
    if not normalized:
        return False

    has_question_phrase = any(
        _contains_phrase(normalized, phrase) for phrase in _SPECIFIC_QUESTION_PHRASES
    )
    has_assertive_probe = any(
        _contains_phrase(normalized, phrase) for phrase in _ASSERTIVE_CAPABILITY_PROMPT_PHRASES
    )

    has_bare_reference = _is_bare_capability_reference(text)

    if not has_question_phrase and not has_assertive_probe and not has_question_mark and not has_bare_reference:
        return False

    return bool(mentioned_capabilities(normalized))


def is_capability_question(text: str) -> bool:
    return (
        is_context_capability_question(text)
        or is_general_capability_question(text)
        or is_specific_capability_question(text)
    )


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


def _build_specific_answer(text: str) -> str:
    names = mentioned_capabilities(text)
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
    if not is_capability_question(text):
        return None

    if is_context_capability_question(text):
        return _build_context_capability_answer()

    if is_general_capability_question(text):
        return _build_general_answer()

    return _build_specific_answer(text)


def maybe_answer_capability_question(text: str) -> str | None:
    return answer_capability_question(text)
