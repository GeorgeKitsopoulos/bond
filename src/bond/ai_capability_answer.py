from __future__ import annotations

import unicodedata

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
    ),
    "timer": (
        "timer",
        "timers",
        "reminder",
        "reminders",
        "χρονομετρο",
        "υπενθυμιση",
        "υπενθυμισεις",
        "timers are a thing",
        "are timers a thing",
        "reminders work",
        "υπενθυμίσεις",
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
        "current environment",
        "current session capabilities",
        "what can you do here",
        "context capabilities",
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
        "answer me in greek",
        "answer me in greek from now on",
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
    "are you able to",
    "do you support",
    "can bond",
    "does bond support",
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
    "pretend",
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
    if not has_question_phrase and not has_assertive_probe and not has_question_mark:
        return False

    return bool(mentioned_capabilities(normalized))


def is_capability_question(text: str) -> bool:
    return is_general_capability_question(text) or is_specific_capability_question(text)


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

    return "\n".join(lines)


def answer_capability_question(text: str) -> str | None:
    if not is_capability_question(text):
        return None

    if is_general_capability_question(text):
        return _build_general_answer()

    return _build_specific_answer(text)


def maybe_answer_capability_question(text: str) -> str | None:
    return answer_capability_question(text)
