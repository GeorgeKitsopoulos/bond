#!/usr/bin/env python3
import re
from pathlib import Path

from ai_core import (
    BOND_ROOT,
    CONFIG_FILE,
    FILES,
    get_archive_root,
    get_changelog_path,
    get_memory_root,
    get_router_config_path,
    get_second_drive,
    get_state_root,
)

HOME = Path.home()
PROJECT_ROOT = BOND_ROOT
TOOLS_ROOT = BOND_ROOT / "src" / "bond"
SCRIPTS_ROOT = BOND_ROOT / "scripts"


def read_user_dirs() -> dict:
    mapping = {}
    cfg = HOME / ".config" / "user-dirs.dirs"
    if not cfg.exists():
        return mapping

    try:
        for raw in cfg.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"')
            value = value.replace("$HOME", str(HOME))
            mapping[key] = value
    except Exception:
        return mapping

    return mapping


def localized_folder_aliases() -> dict:
    user_dirs = read_user_dirs()
    aliases = {}

    candidates = {
        "downloads": ["XDG_DOWNLOAD_DIR"],
        "documents": ["XDG_DOCUMENTS_DIR"],
        "desktop": ["XDG_DESKTOP_DIR"],
        "pictures": ["XDG_PICTURES_DIR"],
        "music": ["XDG_MUSIC_DIR"],
        "videos": ["XDG_VIDEOS_DIR"],
        "templates": ["XDG_TEMPLATES_DIR"],
        "public": ["XDG_PUBLICSHARE_DIR"],
    }

    for alias, keys in candidates.items():
        for key in keys:
            path = user_dirs.get(key)
            if path:
                aliases[alias] = path
                break

    aliases.setdefault("home", str(HOME))
    return aliases


def collapse_spaces(text: str) -> str:
    return " ".join(text.strip().split())


def strip_leading_filler(text: str) -> str:
    t = collapse_spaces(text)
    changed = True
    while changed:
        changed = False
        for prefix in (
            "the ",
            "my ",
            "your ",
            "a ",
            "an ",
            "that ",
            "this ",
            "these ",
            "those ",
        ):
            if t.startswith(prefix):
                t = t[len(prefix):].strip()
                changed = True
    return t


def strip_trailing_filler(text: str) -> str:
    t = collapse_spaces(text)
    changed = True
    while changed:
        changed = False
        for suffix in (
            " please",
            " for me",
            " now",
            " thanks",
            " thank you",
        ):
            if t.endswith(suffix):
                t = t[: -len(suffix)].strip()
                changed = True
    return t


def normalize_target_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", name.lower())


def normalize_target_phrase(text: str) -> str:
    t = collapse_spaces(text.lower())
    t = strip_leading_filler(t)
    t = strip_trailing_filler(t)

    replacements = [
        (r"\bjson file\b", "config"),
        (r"\bconfiguration file\b", "config"),
        (r"\bconfiguration\b", "config"),
        (r"\bsettings\b", "config"),
        (r"\bdirectory\b", "folder"),
        (r"\bdir\b", "folder"),
        (r"\bplease\b", ""),
        (r"\bfor me\b", ""),
        (r"\bright now\b", ""),
        (r"\bcan you\b", ""),
        (r"\bcould you\b", ""),
        (r"\bwould you\b", ""),
    ]
    for pattern, replacement in replacements:
        t = re.sub(pattern, replacement, t)

    t = collapse_spaces(t)

    filler_prefixes = (
        "to ",
        "into ",
        "inside ",
        "up ",
    )
    changed = True
    while changed:
        changed = False
        for prefix in filler_prefixes:
            if t.startswith(prefix):
                t = t[len(prefix):].strip()
                changed = True

    return collapse_spaces(t)


def get_target_registry() -> dict:
    aliases = localized_folder_aliases()
    memory_root = get_memory_root()
    state_root = get_state_root()
    router_config = get_router_config_path()

    registry = {
        "home": HOME,
        "home folder": HOME,
        "project": PROJECT_ROOT,
        "project folder": PROJECT_ROOT,
        "ai": PROJECT_ROOT,
        "ai folder": PROJECT_ROOT,
        "tools": TOOLS_ROOT,
        "tools folder": TOOLS_ROOT,
        "scripts": SCRIPTS_ROOT,
        "scripts folder": SCRIPTS_ROOT,
        "bin": SCRIPTS_ROOT,
        "bin folder": SCRIPTS_ROOT,
        "memory": memory_root,
        "memory folder": memory_root,
        "state": state_root,
        "state folder": state_root,
        "router": router_config.parent,
        "router folder": router_config.parent,
        "downloads": Path(aliases.get("downloads", str(HOME / "Downloads"))),
        "downloads folder": Path(aliases.get("downloads", str(HOME / "Downloads"))),
        "documents": Path(aliases.get("documents", str(HOME / "Documents"))),
        "documents folder": Path(aliases.get("documents", str(HOME / "Documents"))),
        "desktop": Path(aliases.get("desktop", str(HOME / "Desktop"))),
        "desktop folder": Path(aliases.get("desktop", str(HOME / "Desktop"))),
        "pictures": Path(aliases.get("pictures", str(HOME / "Pictures"))),
        "pictures folder": Path(aliases.get("pictures", str(HOME / "Pictures"))),
        "music": Path(aliases.get("music", str(HOME / "Music"))),
        "music folder": Path(aliases.get("music", str(HOME / "Music"))),
        "videos": Path(aliases.get("videos", str(HOME / "Videos"))),
        "videos folder": Path(aliases.get("videos", str(HOME / "Videos"))),
        "router config": router_config,
        "profiles": router_config,
        "profiles file": router_config,
        "assistant config": CONFIG_FILE,
        "system profile": state_root / "system_profile.json",
        "system summary": state_root / "system_summary.txt",
        "active context": FILES["active_context"],
        "memory manifest": FILES["manifest"],
        "archive map": FILES["archive_map"],
        "actions log": FILES["actions"],
        "failures log": FILES["failures"],
        "chats log": FILES["chats"],
        "reflections log": FILES["reflections"],
        "preferences": FILES["preferences"],
        "environment": FILES["environment"],
        "workflows": FILES["workflows"],
        "aliases": FILES["aliases"],
        "changelog": get_changelog_path(),
    }

    archive_root = get_archive_root()
    if archive_root:
        registry["archive root"] = archive_root
        registry["archive"] = archive_root

    second_drive = get_second_drive()
    if second_drive:
        registry["second drive"] = Path(second_drive)

    extra_aliases = {
        "download": "downloads",
        "downloads dir": "downloads",
        "download folder": "downloads folder",
        "downloads directory": "downloads folder",
        "document": "documents",
        "documents dir": "documents",
        "document folder": "documents folder",
        "picture": "pictures",
        "pictures dir": "pictures",
        "picture folder": "pictures folder",
        "photo": "pictures",
        "photos": "pictures",
        "music dir": "music",
        "video": "videos",
        "video folder": "videos folder",
        "videos dir": "videos",
        "ai root": "ai",
        "ai project": "ai",
        "ai project folder": "ai folder",
        "project folder": "ai folder",
        "router profile": "router config",
        "router profiles": "router config",
        "profiles json": "router config",
        "assistant settings": "assistant config",
        "config": "assistant config",
        "system summary file": "system summary",
        "memory state": "memory manifest",
        "manifest": "memory manifest",
        "archive mapping": "archive map",
        "action log": "actions log",
        "failure log": "failures log",
        "chat log": "chats log",
        "reflection log": "reflections log",
    }

    for alias, canonical in extra_aliases.items():
        registry[alias] = registry[canonical]

    return registry


def resolve_target(name: str) -> tuple[str | None, Path | None]:
    wanted = normalize_target_phrase(name)
    if not wanted:
        return None, None

    registry = get_target_registry()

    if wanted in registry:
        return wanted, Path(registry[wanted]).expanduser()

    normalized = normalize_target_name(wanted)
    for key, path in registry.items():
        if normalized == normalize_target_name(key):
            return key, Path(path).expanduser()

    return None, None
