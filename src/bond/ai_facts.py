#!/usr/bin/env python3
import re
from pathlib import Path

from ai_core import (
    BOND_ROOT,
    CONFIG_FILE,
    fact_value,
    get_archive_root,
    get_memory_root,
    get_router_config_path,
    get_second_drive,
    get_state_root,
    load_fact_bucket,
    load_json,
)
from ai_linguistics import contains_bond_variant, match_any, simplify_text

HOME = Path.home()
PROJECT_ROOT = BOND_ROOT
TOOLS_ROOT = BOND_ROOT / "src" / "bond"
STATE_ROOT = get_state_root()
MEMORY_ROOT = get_memory_root()
ROUTER_CONFIG = get_router_config_path()
ARCHIVE_ROOT = get_archive_root()
SYSTEM_PROFILE = STATE_ROOT / "system_profile.json"
MAIN_WRAPPER = BOND_ROOT / "scripts" / "ai"

ROLE_ALIASES = {
    "stuart": {"stuart", "fast", "light", "lightweight", "chat", "front"},
    "bob": {"bob", "dispatcher", "router", "gatekeeper", "strict router", "parser"},
    "polly": {"polly", "research", "researcher", "scout", "extract", "extraction"},
    "nick": {"nick", "editor", "formatter", "writer", "writing", "mason"},
    "james": {"james", "builder", "technical", "system", "code", "coder", "forge", "reason", "default", "workhorse"},
    "lily": {"lily", "memory", "memory hygiene", "reflect", "reflection"},
    "terminator": {"terminator", "execution", "privileged", "privileged execution", "danger", "dangerous"},
}

DEFAULT_PROFILE = "stuart"
ASSISTANT_NAME = "Bond"


def load_system_profile() -> dict:
    data = load_json(SYSTEM_PROFILE, {})
    return data if isinstance(data, dict) else {}


def normalize_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", name.lower())


def iter_profile_entries(profiles):
    if isinstance(profiles, dict):
        if "profiles" in profiles:
            yield from iter_profile_entries(profiles["profiles"])
            return

        for key, value in profiles.items():
            if isinstance(value, dict):
                entry = dict(value)
                entry.setdefault("name", key)
                yield entry

    elif isinstance(profiles, list):
        for item in profiles:
            if isinstance(item, dict):
                yield item


def choose_profile_config(name: str, profiles) -> dict | None:
    wanted = normalize_name(name)

    canonical = None
    for target, aliases in ROLE_ALIASES.items():
        if wanted in {normalize_name(a) for a in aliases}:
            canonical = target
            break

    for entry in iter_profile_entries(profiles):
        entry_name = str(entry.get("name", "")).strip()
        if not entry_name:
            continue

        norm_entry = normalize_name(entry_name)
        if wanted == norm_entry:
            return entry

        if canonical and canonical == norm_entry:
            return entry

        aliases = entry.get("aliases", [])
        if isinstance(aliases, list):
            for alias in aliases:
                if wanted == normalize_name(str(alias)):
                    return entry

    return None


def canonical_role_name(name: str) -> str | None:
    wanted = normalize_name(name)

    for target, aliases in ROLE_ALIASES.items():
        if wanted in {normalize_name(a) for a in aliases}:
            return target

    return None


def extract_model_from_profile(profile_cfg: dict, fallback: str = "qwen2.5:7b-instruct") -> str:
    if not isinstance(profile_cfg, dict):
        return fallback

    for key in ("model", "ollama_model", "model_name"):
        value = profile_cfg.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    return fallback


def detect_fact_query(text: str) -> dict | None:
    t = simplify_text(text)

    if match_any(
        t,
        [
            r"\bwho are you\b",
            r"\bwhat is your name\b",
            r"\bwhats your name\b",
            r"\bwhat s your name\b",
            r"\bare you\b",
            r"\bwhat should i call you\b",
            r"\bπως σε λενε\b",
            r"\bποιο ειναι το ονομα σου\b",
            r"\bποιο ειναι τ ονομα σου\b",
            r"\bποιo ειναι το ονομα σου\b",
            r"\bπες μου το ονομα σου\b",
            r"\bεισαι\b",
            r"\bσε λενε\b",
        ],
    ):
        if contains_bond_variant(t) or match_any(
            t,
            [
                r"\bwho are you\b",
                r"\bwhat is your name\b",
                r"\bwhats your name\b",
                r"\bwhat s your name\b",
                r"\bwhat should i call you\b",
                r"\bπως σε λενε\b",
                r"\bποιο ειναι το ονομα σου\b",
                r"\bποιο ειναι τ ονομα σου\b",
                r"\bπες μου το ονομα σου\b",
            ],
        ):
            return {"source": "assistant_name"}

    rules = [
        (
            [
                r"\bwhat editor do i use\b",
                r"\bwhich editor do i use\b",
                r"\bwhat is my editor\b",
                r"\bwhats my editor\b",
                r"\bwhat s my editor\b",
                r"\bwhat editor am i using\b",
                r"\bwhich editor am i using\b",
                r"\bποιον editor χρησιμοποιω\b",
                r"\bτι editor χρησιμοποιω\b",
                r"\bποιον κειμενογραφο χρησιμοποιω\b",
                r"\bτι κειμενογραφο χρησιμοποιω\b",
            ],
            {"source": "fact", "target": ("preferences", "editor")},
        ),
        (
            [
                r"\bwhat browser do i use\b",
                r"\bwhich browser do i use\b",
                r"\bwhat is my browser\b",
                r"\bwhats my browser\b",
                r"\bwhat browser am i using\b",
                r"\bποιο browser χρησιμοποιω\b",
                r"\bτι browser χρησιμοποιω\b",
                r"\bποιον περιηγητη χρησιμοποιω\b",
                r"\bτι περιηγητη χρησιμοποιω\b",
            ],
            {"source": "system", "target": "browser"},
        ),
        (
            [
                r"\bwhat mail client do i use\b",
                r"\bwhich mail client do i use\b",
                r"\bwhat email client do i use\b",
                r"\bwhat is my email client\b",
                r"\bwhat mail app do i use\b",
                r"\bποιο mail client χρησιμοποιω\b",
                r"\bτι email client χρησιμοποιω\b",
                r"\bποια εφαρμογη mail χρησιμοποιω\b",
            ],
            {"source": "system", "target": "mail"},
        ),
        (
            [
                r"\bwhat file manager do i use\b",
                r"\bwhich file manager do i use\b",
                r"\bwhat is my file manager\b",
                r"\bwhat files app do i use\b",
                r"\bποιο file manager χρησιμοποιω\b",
                r"\bτι file manager χρησιμοποιω\b",
                r"\bποιον διαχειριστη αρχειων χρησιμοποιω\b",
            ],
            {"source": "system", "target": "file_manager"},
        ),
        (
            [
                r"\bwhat terminal do i use\b",
                r"\bwhich terminal do i use\b",
                r"\bwhat is my terminal\b",
                r"\bwhat terminal app do i use\b",
                r"\bποιο terminal χρησιμοποιω\b",
                r"\bτι terminal χρησιμοποιω\b",
            ],
            {"source": "system", "target": "terminal"},
        ),
        (
            [
                r"\bwhat is my second drive\b",
                r"\bwhere is my second drive\b",
                r"\bwhere is the second drive\b",
                r"\bwhat path is my second drive\b",
                r"\bwhat is the second drive path\b",
                r"\bπου ειναι ο δευτερος δισκος\b",
                r"\bποιο ειναι το path του δευτερου δισκου\b",
                r"\bποιο ειναι το path του δευτερου drive\b",
            ],
            {"source": "path_value", "target": "second_drive"},
        ),
        (
            [
                r"\bwhat backup style do i use\b",
                r"\bhow do i back up\b",
                r"\bwhat is my backup style\b",
                r"\bwhat backup method do i use\b",
                r"\bhow is backup configured\b",
                r"\bτι backup method χρησιμοποιω\b",
                r"\bτι backup style χρησιμοποιω\b",
                r"\bπως ειναι ρυθμισμενο το backup\b",
            ],
            {"source": "fact", "target": ("workflows", "backup_style")},
        ),
        (
            [
                r"\bwhat aliases do i have\b",
                r"\bwhat folder aliases do i have\b",
                r"\bshow my aliases\b",
                r"\bshow folder aliases\b",
                r"\bτι aliases εχω\b",
                r"\bτι folder aliases εχω\b",
            ],
            {"source": "fact_bucket", "target": "aliases"},
        ),
        (
            [
                r"\bwhere is the router config\b",
                r"\bwhere is router config\b",
                r"\bwhat is the router config path\b",
                r"\bwhere can i find the router config\b",
                r"\bwhere do you keep the router config\b",
                r"\bwhere are router profiles\b",
                r"\bπου ειναι το router config\b",
                r"\bπου βρισκεται το router config\b",
                r"\bπου ειναι το profiles json\b",
                r"\bποιο ειναι το path του router config\b",
            ],
            {"source": "path", "target": "router_config"},
        ),
        (
            [
                r"\bwhere is the assistant config\b",
                r"\bwhere is assistant config\b",
                r"\bwhat is the assistant config path\b",
                r"\bwhere can i find the assistant config\b",
                r"\bwhere do you keep the assistant config\b",
                r"\bπου ειναι το assistant config\b",
                r"\bπου βρισκεται το assistant config\b",
                r"\bποιο ειναι το path του assistant config\b",
            ],
            {"source": "path", "target": "assistant_config"},
        ),
        (
            [
                r"\bwhere is the memory root\b",
                r"\bwhere is memory\b",
                r"\bwhat is the memory root\b",
                r"\bwhere can i find the memory root\b",
                r"\bwhere do you keep memory\b",
                r"\bπου ειναι το memory root\b",
                r"\bπου βρισκεται το memory root\b",
                r"\bποιο ειναι το path του memory root\b",
            ],
            {"source": "path", "target": "memory_root"},
        ),
        (
            [
                r"\bwhere is the state root\b",
                r"\bwhere is state\b",
                r"\bwhat is the state root\b",
                r"\bwhere can i find the state root\b",
                r"\bwhere do you keep state\b",
                r"\bπου ειναι το state root\b",
                r"\bπου βρισκεται το state root\b",
                r"\bποιο ειναι το path του state root\b",
            ],
            {"source": "path", "target": "state_root"},
        ),
        (
            [
                r"\bwhere is the archive root\b",
                r"\bwhat is the archive root\b",
                r"\bwhere can i find the archive root\b",
                r"\bwhere do you keep the archive\b",
                r"\bπου ειναι το archive root\b",
                r"\bπου βρισκεται το archive root\b",
                r"\bποιο ειναι το path του archive root\b",
            ],
            {"source": "path", "target": "archive_root"},
        ),
        (
            [
                r"\bwhere is the tools root\b",
                r"\bwhere are the tools\b",
                r"\bwhat is the tools root\b",
                r"\bwhere can i find the tools root\b",
                r"\bwhere do you keep the tools\b",
                r"\bπου ειναι το tools root\b",
                r"\bπου βρισκονται τα tools\b",
            ],
            {"source": "path", "target": "tools_root"},
        ),
        (
            [
                r"\bwhere is the main wrapper\b",
                r"\bwhat is the main wrapper path\b",
                r"\bwhere is ai wrapper\b",
                r"\bwhere can i find the main wrapper\b",
                r"\bwhere is the ai wrapper\b",
                r"\bπου ειναι το main wrapper\b",
                r"\bπου ειναι το ai wrapper\b",
            ],
            {"source": "path", "target": "main_wrapper"},
        ),
        (
            [
                r"\bwho is the default assistant\b",
                r"\bwhat is the default assistant\b",
                r"\bwho is the workhorse assistant\b",
                r"\bwhich assistant is the default\b",
                r"\bποιος ειναι ο default assistant\b",
                r"\bποιος ειναι ο βασικος assistant\b",
            ],
            {"source": "default_profile_name"},
        ),
        (
            [
                r"\bwhat model do you use by default\b",
                r"\bwhat is the default model\b",
                r"\bwhich model is the default\b",
                r"\bwhat model does the default assistant use\b",
                r"\bποιο ειναι το default model\b",
                r"\bτι model χρησιμοποιει ο default assistant\b",
            ],
            {"source": "default_profile_model"},
        ),
        (
            [r"\bwho is the heavy assistant\b", r"\bwhat is the heavy assistant\b", r"\bποιος ειναι ο heavy assistant\b"],
            {"source": "role_name", "target": "james"},
        ),
        (
            [r"\bwho is the fast assistant\b", r"\bwhat is the fast assistant\b", r"\bποιος ειναι ο fast assistant\b"],
            {"source": "role_name", "target": "stuart"},
        ),
        (
            [r"\bwho is the balanced assistant\b", r"\bwhat is the balanced assistant\b", r"\bποιος ειναι ο balanced assistant\b"],
            {"source": "role_name", "target": "bob"},
        ),
        (
            [r"\bwho is the planning assistant\b", r"\bwhat is the planning assistant\b", r"\bποιος ειναι ο planning assistant\b"],
            {"source": "role_name", "target": "atlas"},
        ),
        (
            [r"\bwho is the writing assistant\b", r"\bwhat is the writing assistant\b", r"\bποιος ειναι ο writing assistant\b"],
            {"source": "role_name", "target": "mason"},
        ),
        (
            [r"\bwho is the research assistant\b", r"\bwhat is the research assistant\b", r"\bποιος ειναι ο research assistant\b"],
            {"source": "role_name", "target": "scout"},
        ),
        (
            [r"\bwho is the coding assistant\b", r"\bwhat is the coding assistant\b", r"\bwho is the automation assistant\b", r"\bποιος ειναι ο coding assistant\b"],
            {"source": "role_name", "target": "forge"},
        ),
        (
            [r"\bwho is the gatekeeper\b", r"\bwhat is the gatekeeper\b", r"\bποιος ειναι ο gatekeeper\b"],
            {"source": "role_name", "target": "gatekeeper"},
        ),
        (
            [r"\bwhat model does james use\b", r"\bwhich model does james use\b", r"\bτι model χρησιμοποιει ο james\b"],
            {"source": "role_model", "target": "james"},
        ),
        (
            [r"\bwhat model does bob use\b", r"\bwhich model does bob use\b", r"\bτι model χρησιμοποιει ο bob\b"],
            {"source": "role_model", "target": "bob"},
        ),
        (
            [r"\bwhat model does stuart use\b", r"\bwhich model does stuart use\b", r"\bτι model χρησιμοποιει ο stuart\b"],
            {"source": "role_model", "target": "stuart"},
        ),
        (
            [r"\bwhat model does atlas use\b", r"\bwhich model does atlas use\b", r"\bτι model χρησιμοποιει ο atlas\b"],
            {"source": "role_model", "target": "atlas"},
        ),
        (
            [r"\bwhat model does mason use\b", r"\bwhich model does mason use\b", r"\bτι model χρησιμοποιει ο mason\b"],
            {"source": "role_model", "target": "mason"},
        ),
        (
            [r"\bwhat model does scout use\b", r"\bwhich model does scout use\b", r"\bτι model χρησιμοποιει ο scout\b"],
            {"source": "role_model", "target": "scout"},
        ),
        (
            [r"\bwhat model does forge use\b", r"\bwhich model does forge use\b", r"\bτι model χρησιμοποιει ο forge\b"],
            {"source": "role_model", "target": "forge"},
        ),
        (
            [r"\bwhat model does gatekeeper use\b", r"\bwhich model does gatekeeper use\b", r"\bτι model χρησιμοποιει ο gatekeeper\b"],
            {"source": "role_model", "target": "gatekeeper"},
        ),
    ]

    for patterns, spec in rules:
        if match_any(t, patterns):
            return spec

    return None


def answer_fact_query(spec: dict, profiles) -> str | None:
    profile = load_system_profile()
    source = spec["source"]

    if source == "assistant_name":
        return ASSISTANT_NAME

    if source == "system":
        key = spec["target"]
        value = profile.get(key)
        return str(value) if value else None

    if source == "fact":
        bucket, key = spec["target"]
        value = fact_value(bucket, key)
        return str(value) if value is not None else None

    if source == "fact_bucket":
        bucket = spec["target"]
        data = load_fact_bucket(bucket)
        if not data:
            return f"{bucket}: none"

        lines = []
        for key in sorted(data.keys()):
            item = data[key]
            value = item["value"] if isinstance(item, dict) and "value" in item else item
            lines.append(f"{key} = {value}")
        return "\n".join(lines)

    if source == "path_value":
        if spec["target"] == "second_drive":
            value = get_second_drive()
            return str(value) if value else None
        return None

    if source == "path":
        mapping = {
            "router_config": ROUTER_CONFIG,
            "assistant_config": CONFIG_FILE,
            "memory_root": MEMORY_ROOT,
            "state_root": STATE_ROOT,
            "archive_root": ARCHIVE_ROOT,
            "tools_root": TOOLS_ROOT,
            "main_wrapper": MAIN_WRAPPER,
        }
        value = mapping.get(spec["target"])
        return str(value) if value is not None else None

    if source == "default_profile_name":
        return DEFAULT_PROFILE

    if source == "default_profile_model":
        cfg = choose_profile_config(DEFAULT_PROFILE, profiles) or {}
        return extract_model_from_profile(cfg)

    if source == "role_name":
        return str(spec["target"])

    if source == "role_model":
        role = canonical_role_name(str(spec["target"])) or str(spec["target"])
        cfg = choose_profile_config(role, profiles)
        if not cfg:
            return None
        return extract_model_from_profile(cfg)

    return None
