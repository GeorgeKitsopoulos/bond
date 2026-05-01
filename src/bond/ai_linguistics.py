#!/usr/bin/env python3
import re
import unicodedata

BOND_VARIANTS = {
    "bond",
    "mpont",
    "mpond",
    "μποντ",
}

ACTION_NOISE_PATTERNS = [
    r"^\s*please\s+",
    r"^\s*just\s+",
    r"^\s*can you\s+",
    r"^\s*could you\s+",
    r"^\s*would you\s+",
    r"^\s*can you like\s+",
    r"^\s*i want to\s+",
    r"^\s*i wanna\s+",
    r"^\s*let me\s+",
    r"^\s*maybe\s+",
    r"^\s*please\b",
    r"^\s*λιγο\s+",
    r"^\s*λίγο\s+",
    r"^\s*μπορεις να\s+",
    r"^\s*μπορείς να\s+",
    r"^\s*θελω να\s+",
    r"^\s*θέλω να\s+",
    r"^\s*να\s+",
    r"^\s*μηπως\s+",
    r"^\s*μήπως\s+",
    r"^\s*σε παρακαλω\s+",
    r"^\s*σε παρακαλώ\s+",
]

ASSISTANT_INVOCATION_PATTERNS = [
    r"^\s*(?:(?:hey|hi|hello|ok|okay|λοιπον|λοιπόν|γεια|please|σε παρακαλω|σε παρακαλώ|παρακαλω|παρακαλώ)[\s,.;:!?-]+)*(?:bond|μποντ|μποντ|μπόντ)(?:[\s,.;:!?-]+|$)",
]

GREEK_ACTION_NORMALIZATIONS = [
    (r"\bάνοιξε\b", "open"),
    (r"\bανοιξε\b", "open"),
    (r"\bδείξε μου\b", "show"),
    (r"\bδειξε μου\b", "show"),
    (r"\bδείξε\b", "show"),
    (r"\bδειξε\b", "show"),
    (r"\bεμφάνισε\b", "show"),
    (r"\bεμφανισε\b", "show"),
    (r"\bπήγαινε\b", "go to"),
    (r"\bπηγαινε\b", "go to"),
    (r"\bπάμε\b", "go to"),
    (r"\bπαμε\b", "go to"),
    (r"\bστον editor\b", "in editor"),
    (r"\bστο editor\b", "in editor"),
    (r"\bσε editor\b", "in editor"),
    (r"\bστον κειμενογραφο\b", "in editor"),
    (r"\bστο κειμενογραφο\b", "in editor"),
    (r"\bστον file manager\b", "in file manager"),
    (r"\bστο file manager\b", "in file manager"),
    (r"\bστον διαχειριστη αρχειων\b", "in file manager"),
    (r"\bστο διαχειριστη αρχειων\b", "in file manager"),
    (r"\bτις ληψεις\b", "downloads"),
    (r"\bτις λήψεις\b", "downloads"),
    (r"\bτα εγγραφα\b", "documents"),
    (r"\bτα έγγραφα\b", "documents"),
    (r"\bληψεις\b", "downloads"),
    (r"\bλήψεις\b", "downloads"),
    (r"\bεγγραφα\b", "documents"),
    (r"\bέγγραφα\b", "documents"),
    (r"\bφακελος ληψεις\b", "downloads folder"),
    (r"\bφάκελος λήψεις\b", "downloads folder"),
    (r"\bφακελο ληψεις\b", "downloads folder"),
    (r"\bφάκελο λήψεις\b", "downloads folder"),
    (r"\bφακελος εγγραφα\b", "documents folder"),
    (r"\bφάκελος έγγραφα\b", "documents folder"),
    (r"\bφακελο εγγραφα\b", "documents folder"),
    (r"\bφάκελο έγγραφα\b", "documents folder"),
]

CHAIN_REPLACEMENTS = [
    (r"\band then\b", " and "),
    (r"\bthen\b", " and "),
    (r"\band also\b", " and "),
    (r"\bκαι μετα\b", " και "),
    (r"\bκαι μετά\b", " και "),
    (r"\bκαθως και\b", " και "),
    (r"\bκαθώς και\b", " και "),
]


def strip_accents(text: str) -> str:
    normalized = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")


def simplify_text(text: str) -> str:
    t = text.strip().lower()
    t = strip_accents(t)
    t = t.replace("'", " ")
    t = re.sub(r"[^a-z0-9α-ω/_:.\-\s?]+", " ", t)
    t = " ".join(t.split())
    return t


def match_any(text: str, patterns: list[str]) -> bool:
    return any(re.search(pattern, text) for pattern in patterns)


def contains_bond_variant(text: str) -> bool:
    compact = re.sub(r"\s+", "", text)
    return any(variant in compact for variant in BOND_VARIANTS)


def strip_assistant_invocation_prefix(text: str) -> str:
    cleaned = text.strip()
    changed = True
    while changed and cleaned:
        changed = False
        for pattern in ASSISTANT_INVOCATION_PATTERNS:
            new_cleaned = re.sub(pattern, "", cleaned, flags=re.I).strip()
            if new_cleaned != cleaned:
                cleaned = new_cleaned
                changed = True
    return cleaned.strip(" ,.;:!?-")


def strip_action_noise(text: str) -> str:
    cleaned = text.strip()
    changed = True
    while changed:
        changed = False
        for pattern in ACTION_NOISE_PATTERNS:
            new_cleaned = re.sub(pattern, "", cleaned, flags=re.I).strip()
            if new_cleaned != cleaned:
                cleaned = new_cleaned
                changed = True
    return cleaned.strip(" ,.;")


def normalize_action_text(text: str) -> str:
    t = strip_assistant_invocation_prefix(text)
    t = strip_action_noise(t)
    for pattern, replacement in GREEK_ACTION_NORMALIZATIONS:
        t = re.sub(pattern, replacement, t, flags=re.I)
    t = re.sub(r"\s+", " ", t).strip(" ,.;")
    return t


def normalize_chain_text(text: str) -> str:
    t = text.strip()
    for pattern, replacement in CHAIN_REPLACEMENTS:
        t = re.sub(pattern, replacement, t, flags=re.I)
    return " ".join(t.split())


def split_chain_candidate(text: str) -> list[str]:
    normalized = normalize_chain_text(text)
    if not normalized:
        return []

    parts = re.split(r"\s+(?:and|και)\s+", normalized, flags=re.I)
    cleaned = []
    for part in parts:
        p = part.strip(" ,.;")
        if p:
            cleaned.append(p)
    return cleaned
