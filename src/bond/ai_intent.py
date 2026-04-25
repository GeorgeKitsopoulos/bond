#!/usr/bin/env python3
import re

from ai_facts import detect_fact_query
from ai_linguistics import normalize_action_text, simplify_text, split_chain_candidate

MAX_CHAIN_STEPS = 3

QUESTION_PATTERNS = [
    r"\bwho are you\b",
    r"\bwhat is your name\b",
    r"\bwhats your name\b",
    r"\bwhat s your name\b",
    r"\bwhat should i call you\b",
    r"\bare you\b",
    r"\bwhat\b",
    r"\bwhich\b",
    r"\bwhere\b",
    r"\bwhy\b",
    r"\bhow\b",
    r"\bwhen\b",
    r"\bcan you tell me\b",
    r"\btell me\b",
    r"\bπως\b",
    r"\bποιο\b",
    r"\bποια\b",
    r"\bτι\b",
    r"\bπου\b",
    r"\bγιατι\b",
    r"\bπες μου\b",
    r"\bεισαι\b",
]

CHAT_DIRECTIVE_PATTERNS = [
    r"^\s*plan\b",
    r"^\s*suggest\b",
    r"^\s*explain\b",
    r"^\s*analyze\b",
    r"^\s*analyse\b",
    r"^\s*summarize\b",
    r"^\s*describe\b",
    r"^\s*compare\b",
    r"^\s*review\b",
    r"^\s*brainstorm\b",
    r"^\s*outline\b",
    r"^\s*walk me through\b",
    r"^\s*help me understand\b",
    r"^\s*think through\b",
    r"^\s*βρες τροπο\b",
    r"^\s*εξηγησε\b",
    r"^\s*εξήγησε\b",
    r"^\s*αναλυσε\b",
    r"^\s*ανάλυσε\b",
    r"^\s*περιεγραψε\b",
    r"^\s*περιέγραψε\b",
    r"^\s*συγκρινε\b",
    r"^\s*σύγκρινε\b",
    r"^\s*προτεινε\b",
    r"^\s*πρότεινε\b",
    r"^\s*σχεδιασε\b",
    r"^\s*σχεδίασε\b",
]

ACTION_START_PATTERNS = [
    r"^\s*open\b",
    r"^\s*launch\b",
    r"^\s*start\b",
    r"^\s*show\b",
    r"^\s*display\b",
    r"^\s*edit\b",
    r"^\s*view\b",
    r"^\s*go to\b",
    r"^\s*take me to\b",
    r"^\s*notify\b",
    r"^\s*set\b.*\bwallpaper\b",
    r"^\s*change\b.*\bwallpaper\b",
    r"^\s*open\s+https?://",
    r"^\s*ανοιξε\b",
    r"^\s*άνοιξε\b",
    r"^\s*δειξε\b",
    r"^\s*δείξε\b",
    r"^\s*εμφανισε\b",
    r"^\s*εμφάνισε\b",
    r"^\s*πηγαινε\b",
    r"^\s*πήγαινε\b",
    r"^\s*παμε\b",
    r"^\s*πάμε\b",
]

EXPLICIT_ACTION_PATTERNS = [
    r"\bnotify me\b",
    r"\bset\b.*\bwallpaper\b",
    r"\bchange\b.*\bwallpaper\b",
    r"\bshow\b.+\bin\s+(the\s+)?file manager\b",
    r"\bedit\b.+\bin\s+(the\s+)?editor\b",
    r"\bopen\b.+\bin\s+(the\s+)?editor\b",
    r"\bopen\s+https?://",
]

ACTION_TARGET_HINTS = [
    "config",
    "profile",
    "summary",
    "context",
    "manifest",
    "log",
    "downloads",
    "documents",
    "desktop",
    "pictures",
    "music",
    "videos",
    "router",
    "memory",
    "state",
    "tools",
    "home",
    "bin",
    "folder",
    "assistant config",
    "router config",
    "system profile",
    "system summary",
    "active context",
    "memory manifest",
    "archive map",
    "actions log",
    "failures log",
    "chats log",
    "reflections log",
    "preferences",
    "environment",
    "workflows",
    "aliases",
    "changelog",
    "ai",
    "~/",
    "/",
]

ACTION_DISQUALIFIER_PATTERNS = [
    r"^\s*what did\b",
    r"^\s*what changed\b",
    r"^\s*what do we\b",
    r"^\s*why did\b",
    r"^\s*how do\b",
    r"^\s*how did\b",
    r"^\s*how to\b",
    r"^\s*recently\b",
    r"^\s*next steps\b",
    r"\brecently change\b",
    r"\bchange in\b",
    r"\bsuggest how\b",
    r"\bplan the next steps\b",
    r"\bwhat happened\b",
    r"\bwhat did we\b",
    r"\bτι αλλαξαμε\b",
    r"\bτι αλλάξαμε\b",
    r"\bτι εχουμε αλλαξει\b",
    r"\bτι έχουμε αλλάξει\b",
    r"\bπως να\b",
    r"\bπώς να\b",
    r"\bεξηγησε\b",
    r"\bεξήγησε\b",
]

MIXED_QUESTION_CLAUSE_PATTERNS = [
    r"\btell me\b",
    r"\bwhat\b",
    r"\bwhich\b",
    r"\bwhere\b",
    r"\bwhy\b",
    r"\bhow\b",
    r"\bwhen\b",
    r"\bπες μου\b",
    r"\bτι\b",
    r"\bποιο\b",
    r"\bπου\b",
    r"\bπως\b",
    r"\bγιατι\b",
]


def looks_like_question_request(text: str) -> bool:
    t = simplify_text(text)
    if not t:
        return False

    if "?" in text:
        return True

    if any(re.search(pattern, t) for pattern in CHAT_DIRECTIVE_PATTERNS):
        return True

    return any(re.search(pattern, t) for pattern in QUESTION_PATTERNS)


def _has_action_target_hint(text: str) -> bool:
    return any(target in text for target in ACTION_TARGET_HINTS)


def _starts_like_action(text: str) -> bool:
    return any(re.search(pattern, text) for pattern in ACTION_START_PATTERNS)


def _contains_explicit_action_pattern(text: str) -> bool:
    return any(re.search(pattern, text) for pattern in EXPLICIT_ACTION_PATTERNS)


def _contains_action_disqualifier(text: str) -> bool:
    return any(re.search(pattern, text) for pattern in ACTION_DISQUALIFIER_PATTERNS)


def looks_like_action_request(text: str) -> bool:
    if detect_fact_query(text):
        return False

    normalized = normalize_action_text(text)
    t = simplify_text(normalized)
    if not t:
        return False

    if any(re.search(pattern, t) for pattern in CHAT_DIRECTIVE_PATTERNS):
        return False

    if _contains_action_disqualifier(t):
        return False

    if _contains_explicit_action_pattern(t):
        return True

    starts_like_action = _starts_like_action(t)
    has_target_hint = _has_action_target_hint(t)

    if starts_like_action and has_target_hint:
        return True

    if starts_like_action and t.startswith("open http"):
        return True

    return False


def detect_action_chain(text: str) -> list[str] | None:
    parts = split_chain_candidate(text)
    if len(parts) < 2:
        return None

    normalized_parts = [normalize_action_text(part) for part in parts]

    if len(normalized_parts) > MAX_CHAIN_STEPS:
        return normalized_parts[: MAX_CHAIN_STEPS + 1]

    if not all(looks_like_action_request(part) for part in normalized_parts):
        return None

    return normalized_parts


def _single_clause_is_mixed(text: str) -> bool:
    t = simplify_text(normalize_action_text(text))
    if not t:
        return False

    if not looks_like_action_request(text):
        return False

    if not any(re.search(pattern, t) for pattern in MIXED_QUESTION_CLAUSE_PATTERNS):
        return False

    if t.startswith("open ") or t.startswith("show ") or t.startswith("edit ") or t.startswith("view "):
        if " and " in t or " και " in t:
            return True

    if re.search(r"\b(and|και)\b.+\b(tell me|what|which|where|why|how|when|τι|ποιο|που|πως|γιατι)\b", t):
        return True

    return False


def classify_single_intent(text: str) -> str:
    fact_spec = detect_fact_query(text)
    if fact_spec:
        return "question"

    is_action = looks_like_action_request(text)
    is_question = looks_like_question_request(text)

    if _single_clause_is_mixed(text):
        return "mixed"

    if is_action and is_question:
        if "?" in text:
            return "question"
        return "question"

    if is_action:
        return "action"

    if is_question:
        return "question"

    return "unknown"


def classify_request(text: str) -> tuple[str, list[str] | None]:
    parts = split_chain_candidate(text)

    if len(parts) >= 2:
        intents = [classify_single_intent(part) for part in parts]

        has_action = any(intent == "action" for intent in intents)
        has_question = any(intent == "question" for intent in intents)
        has_mixed = any(intent == "mixed" for intent in intents)

        if has_mixed or (has_action and has_question):
            return "mixed", None

        if all(intent == "action" for intent in intents):
            chain = detect_action_chain(text)
            if chain:
                return "pure_action", chain
            return "unknown", None

        if all(intent in {"question", "unknown"} for intent in intents):
            return "pure_question", None

    single = classify_single_intent(text)
    if single == "action":
        return "pure_action", None
    if single == "question":
        return "pure_question", None
    if single == "mixed":
        return "mixed", None
    return "unknown", None
