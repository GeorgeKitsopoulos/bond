from __future__ import annotations

import unicodedata
from dataclasses import dataclass

from ai_linguistics import strip_assistant_invocation_prefix


ANSWER_KIND_NONE = "none"
ANSWER_KIND_CONTEXT = "context"
ANSWER_KIND_GENERAL = "general"
ANSWER_KIND_SPECIFIC = "specific"


@dataclass(frozen=True)
class CapabilityClassification:
    is_capability_question: bool
    answer_kind: str
    mentioned_capabilities: tuple[str, ...]
    normalized_text: str
    reason: str


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


def classify_capability_question(text: str) -> CapabilityClassification:
    stripped = strip_assistant_invocation_prefix(text)
    normalized = normalize_text(stripped)

    if not normalized:
        return CapabilityClassification(
            is_capability_question=False,
            answer_kind=ANSWER_KIND_NONE,
            mentioned_capabilities=(),
            normalized_text="",
            reason="empty",
        )

    if is_context_capability_question(text):
        return CapabilityClassification(
            is_capability_question=True,
            answer_kind=ANSWER_KIND_CONTEXT,
            mentioned_capabilities=("describe_context_capabilities",),
            normalized_text=normalized,
            reason="context_capability_question",
        )

    if is_general_capability_question(text):
        return CapabilityClassification(
            is_capability_question=True,
            answer_kind=ANSWER_KIND_GENERAL,
            mentioned_capabilities=("describe_capabilities",),
            normalized_text=normalized,
            reason="general_capability_question",
        )

    if is_specific_capability_question(text):
        return CapabilityClassification(
            is_capability_question=True,
            answer_kind=ANSWER_KIND_SPECIFIC,
            mentioned_capabilities=tuple(mentioned_capabilities(text)),
            normalized_text=normalized,
            reason="specific_capability_question",
        )

    return CapabilityClassification(
        is_capability_question=False,
        answer_kind=ANSWER_KIND_NONE,
        mentioned_capabilities=(),
        normalized_text=normalized,
        reason="not_capability_question",
    )