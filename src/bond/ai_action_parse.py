#!/usr/bin/env python3
import re
from pathlib import Path

from ai_core import get_state_root
from ai_action_catalog import collapse_spaces, normalize_target_phrase
from ai_action_policy import is_explicit_path_text


def is_legacy_state_assistant_config_path(path_text: str) -> bool:
    try:
        candidate = Path(path_text).expanduser().resolve(strict=False)
        legacy = (get_state_root() / "assistant_config.json").expanduser().resolve(strict=False)
    except Exception:
        return False
    return candidate == legacy


def clean_request_text(text: str) -> str:
    t = text.strip()
    t = re.sub(r"^[\s,.;:!?]+|[\s,.;:!?]+$", "", t)

    specific_rewrites = [
        (r"^(i want to see)\s+", "show "),
        (r"^(show me)\s+", "show "),
        (r"^(let me see)\s+", "show "),
        (r"^(take me to)\s+", "open "),
        (r"^(go to)\s+", "open "),
        (r"^(bring up)\s+", "open "),
        (r"^(pull up)\s+", "open "),
    ]
    for pattern, replacement in specific_rewrites:
        t = re.sub(pattern, replacement, t, flags=re.I)

    generic_prefixes = [
        r"^(can you)\s+",
        r"^(could you)\s+",
        r"^(would you)\s+",
        r"^(please)\s+",
        r"^(i want you to)\s+",
        r"^(i want to)\s+",
        r"^(i need to)\s+",
        r"^(help me)\s+",
        r"^(please can you)\s+",
        r"^(please open)\s+",
    ]
    for pattern in generic_prefixes:
        t = re.sub(pattern, "", t, flags=re.I)

    return collapse_spaces(t)


def parse_path_request(verb: str, target_text: str) -> dict | None:
    target_text = target_text.strip()

    m = re.match(r"^(.+?)\s+in\s+(the\s+)?editor$", target_text, flags=re.I)
    if m:
        path_text = m.group(1).strip()
        if is_explicit_path_text(path_text):
            if is_legacy_state_assistant_config_path(path_text):
                return {"intent": "open_known_in_editor", "target": "assistant config"}
            return {"intent": "open_path_in_editor", "path": path_text}

    m = re.match(r"^(.+?)\s+in\s+(the\s+)?file manager$", target_text, flags=re.I)
    if m:
        path_text = m.group(1).strip()
        if is_explicit_path_text(path_text):
            return {"intent": "open_path_in_file_manager", "path": path_text}

    if is_explicit_path_text(target_text):
        if is_legacy_state_assistant_config_path(target_text):
            if verb in {"show", "view"}:
                return {"intent": "open_known_in_file_manager", "target": "assistant config"}
            return {"intent": "open_known_target", "target": "assistant config"}
        if verb in {"show", "view"}:
            return {"intent": "open_path_in_file_manager", "path": target_text}
        return {"intent": "open_path", "path": target_text}

    return None


def parse_request(text: str) -> dict | None:
    t = clean_request_text(text)
    if not t:
        return None

    m = re.match(r"^(open|edit)\s+(.+?)\s+in\s+(the\s+)?editor$", t, flags=re.I)
    if m:
        raw_target = m.group(2).strip()
        path_intent = parse_path_request(m.group(1).lower(), raw_target + " in editor")
        if path_intent:
            return path_intent
        return {
            "intent": "open_known_in_editor",
            "target": normalize_target_phrase(raw_target),
        }

    m = re.match(r"^(open|show|view)\s+(.+?)\s+in\s+(the\s+)?file manager$", t, flags=re.I)
    if m:
        raw_target = m.group(2).strip()
        path_intent = parse_path_request(m.group(1).lower(), raw_target + " in file manager")
        if path_intent:
            return path_intent
        return {
            "intent": "open_known_in_file_manager",
            "target": normalize_target_phrase(raw_target),
        }

    m = re.search(r"\bopen\s+(https?://\S+)", t, flags=re.I)
    if m:
        return {"intent": "open_url", "url": m.group(1)}

    m = re.search(r"\bnotify me\b\s+(.*)", t, flags=re.I)
    if m and m.group(1).strip():
        return {"intent": "notify", "text": m.group(1).strip()}

    m = re.search(r"\b(set|change)\b.*\bwallpaper\b.*\bto\b\s+(.+)$", t, flags=re.I)
    if m and m.group(2).strip():
        return {"intent": "set_wallpaper", "path": m.group(2).strip()}

    m = re.match(r"^(open|show|view|edit)\s+(.+)$", t, flags=re.I)
    if not m:
        return None

    verb = m.group(1).strip().lower()
    raw_target = m.group(2).strip()

    path_intent = parse_path_request(verb, raw_target)
    if path_intent:
        return path_intent

    target = normalize_target_phrase(raw_target)

    if target in {"browser", "firefox", "web", "web browser"}:
        return {"intent": "open_browser"}

    if target in {"mail", "email", "thunderbird", "mail client"}:
        return {"intent": "open_mail"}

    if target in {"terminal", "shell", "command line"}:
        return {"intent": "open_terminal"}

    if target in {"editor", "text editor", "xed", "geany", "nano"}:
        return {"intent": "open_editor"}

    if target in {"file manager", "files", "nemo"}:
        return {"intent": "open_file_manager"}

    if verb == "edit":
        return {"intent": "open_known_in_editor", "target": target}

    if target.endswith(" folder"):
        return {"intent": "open_known_in_file_manager", "target": target}

    file_manager_targets = {
        "downloads",
        "documents",
        "desktop",
        "pictures",
        "music",
        "videos",
        "home",
        "ai",
        "tools",
        "memory",
        "state",
        "router",
        "bin",
        "downloads folder",
        "documents folder",
        "desktop folder",
        "pictures folder",
        "music folder",
        "videos folder",
        "home folder",
        "ai folder",
        "tools folder",
        "memory folder",
        "state folder",
        "router folder",
        "bin folder",
        "project folder",
        "ai project",
        "ai project folder",
        "archive",
        "archive root",
        "second drive",
    }

    if verb in {"show", "view"} and target in file_manager_targets:
        return {"intent": "open_known_in_file_manager", "target": target}

    return {"intent": "open_known_target", "target": target}
