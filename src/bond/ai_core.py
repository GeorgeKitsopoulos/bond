#!/usr/bin/env python3
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

APP_NAME = "bond"
HOME = Path.home()

# Compatibility fallback for older local layouts that stored state under $HOME/AI.
LEGACY_LAYOUT_ROOT = HOME / "AI"


def _env_path(name: str) -> Path | None:
    """Read environment variable and convert to resolved Path, or None if missing."""
    value = os.getenv(name)
    if not value or not value.strip():
        return None
    return Path(value).expanduser().resolve(strict=False)


def _running_on_windows() -> bool:
    """Check if running on Windows."""
    return os.name == "nt" or sys.platform.startswith("win")


def _running_on_macos() -> bool:
    """Check if running on macOS."""
    return sys.platform == "darwin"


def _running_on_android_like() -> bool:
    """Check if running on Android-like environment (Termux, etc)."""
    if os.getenv("ANDROID_ROOT"):
        return True
    prefix = os.getenv("PREFIX", "")
    return "com.termux" in prefix


def resolve_xdg_config_home() -> Path:
    """Resolve XDG_CONFIG_HOME with platform awareness."""
    # Check Bond override first
    path = _env_path("BOND_CONFIG_HOME")
    if path:
        return path
    
    # Check XDG_CONFIG_HOME
    path = _env_path("XDG_CONFIG_HOME")
    if path:
        return path
    
    # Platform-specific defaults
    if _running_on_windows():
        appdata = _env_path("APPDATA")
        if appdata:
            return appdata
        return HOME / "AppData" / "Roaming"
    
    if _running_on_macos():
        return HOME / "Library" / "Application Support"
    
    # Linux and others
    return HOME / ".config"


def resolve_xdg_data_home() -> Path:
    """Resolve XDG_DATA_HOME with platform awareness."""
    # Check Bond override first
    path = _env_path("BOND_DATA_HOME")
    if path:
        return path
    
    # Check XDG_DATA_HOME
    path = _env_path("XDG_DATA_HOME")
    if path:
        return path
    
    # Platform-specific defaults
    if _running_on_windows():
        localappdata = _env_path("LOCALAPPDATA")
        if localappdata:
            return localappdata
        appdata = _env_path("APPDATA")
        if appdata:
            return appdata
        return HOME / "AppData" / "Local"
    
    if _running_on_macos():
        return HOME / "Library" / "Application Support"
    
    # Linux and others
    return HOME / ".local" / "share"


def resolve_xdg_state_home() -> Path:
    """Resolve XDG_STATE_HOME with platform awareness."""
    # Check Bond override first
    path = _env_path("BOND_STATE_HOME")
    if path:
        return path
    
    # Check XDG_STATE_HOME
    path = _env_path("XDG_STATE_HOME")
    if path:
        return path
    
    # Platform-specific defaults
    if _running_on_windows():
        localappdata = _env_path("LOCALAPPDATA")
        if localappdata:
            return localappdata
        appdata = _env_path("APPDATA")
        if appdata:
            return appdata
        return HOME / "AppData" / "Local"
    
    if _running_on_macos():
        return HOME / "Library" / "Application Support"
    
    # Linux and others
    return HOME / ".local" / "state"


def resolve_xdg_cache_home() -> Path:
    """Resolve XDG_CACHE_HOME with platform awareness."""
    # Check Bond override first
    path = _env_path("BOND_CACHE_HOME")
    if path:
        return path
    
    # Check XDG_CACHE_HOME
    path = _env_path("XDG_CACHE_HOME")
    if path:
        return path
    
    # Platform-specific defaults
    if _running_on_windows():
        localappdata = _env_path("LOCALAPPDATA")
        if localappdata:
            return localappdata
        return HOME / "AppData" / "Local"
    
    if _running_on_macos():
        return HOME / "Library" / "Caches"
    
    # Linux and others
    return HOME / ".cache"


def _looks_like_repo_root(path: Path) -> bool:
    """Check if path looks like bond repository root."""
    if not (path / "pyproject.toml").exists():
        return False
    if not (path / "src" / "bond").is_dir():
        return False
    return True


def resolve_bond_root() -> Path:
    """Resolve Bond repository root."""
    # Check environment variable first
    env_path = _env_path("BOND_ROOT")
    if env_path:
        return env_path
    
    # Walk upward from current file
    current_file = Path(__file__).resolve(strict=False)
    for parent in current_file.parents:
        if _looks_like_repo_root(parent):
            return parent
    
    # Fallback to parent.parent.parent of current file
    return current_file.parent.parent.parent.resolve(strict=False)


def resolve_config_file() -> Path:
    """Resolve assistant config file location."""
    # Check environment variable first
    env_path = _env_path("BOND_CONFIG_PATH")
    if env_path:
        return env_path
    
    # Check XDG config location
    xdg_config = resolve_xdg_config_home() / APP_NAME / "assistant_config.json"
    if xdg_config.exists():
        return xdg_config
    
    # Check repository config
    repo_config = BOND_ROOT / "config" / "bond" / "assistant_config.json"
    if repo_config.exists():
        return repo_config
    
    # Check legacy compatibility location
    legacy_config = LEGACY_LAYOUT_ROOT / "state" / "assistant_config.json"
    if legacy_config.exists():
        return legacy_config
    
    # Default to XDG location
    return xdg_config


# Central path roots
BOND_ROOT = resolve_bond_root()
XDG_CONFIG_HOME = resolve_xdg_config_home()
XDG_DATA_HOME = resolve_xdg_data_home()
XDG_STATE_HOME = resolve_xdg_state_home()
XDG_CACHE_HOME = resolve_xdg_cache_home()

CONFIG_HOME = XDG_CONFIG_HOME / APP_NAME
DATA_HOME = XDG_DATA_HOME / APP_NAME
STATE_HOME = XDG_STATE_HOME / APP_NAME
CACHE_HOME = XDG_CACHE_HOME / APP_NAME

RUNTIME_ROOT = DATA_HOME
AI_ROOT = BOND_ROOT
TOOLS = BOND_ROOT / "src" / "bond"
STATE_ROOT = STATE_HOME / "state"
MEMORY_ROOT = DATA_HOME / "memory"
CHANGELOG_PATH = STATE_HOME / "changelog" / "changelog.jsonl"

CONFIG_FILE = resolve_config_file()

FACTS = MEMORY_ROOT / "facts"
LOGS = MEMORY_ROOT / "logs"
MEM_STATE = MEMORY_ROOT / "state"

FACT_BUCKETS = ("preferences", "environment", "workflows", "aliases")
LOG_BUCKETS = ("actions", "failures", "chats", "events", "reflections")

ACTIVE_FAILURE_WINDOW_MINUTES = 30
ACTIVE_ACTION_LIMIT = 5
ACTIVE_FAILURE_LIMIT = 3
ACTIVE_REFLECTION_LIMIT = 4


_PATH_VARIABLES = {
    "BOND_ROOT": BOND_ROOT,
    "BOND_CONFIG_HOME": CONFIG_HOME,
    "BOND_DATA_HOME": DATA_HOME,
    "BOND_STATE_HOME": STATE_HOME,
    "BOND_CACHE_HOME": CACHE_HOME,
    "HOME": HOME,
}


def _replace_known_path_vars(value: str) -> str:
    """Replace known path variables in value string."""
    # Replace ${NAME} format
    for var_name, var_path in _PATH_VARIABLES.items():
        value = value.replace(f"${{{var_name}}}", str(var_path))
    
    # Replace $NAME format (only when not followed by alphanumeric or _)
    for var_name, var_path in _PATH_VARIABLES.items():
        pattern = rf"\${var_name}(?![a-zA-Z0-9_])"
        value = re.sub(pattern, str(var_path), value)
    
    # Use os.path.expandvars for remaining variables
    return os.path.expandvars(value)


def resolve_path_value(value, *, default: Path, relative_base: Path | None = None) -> Path:
    """Resolve a path value with variable expansion and URI prefixes."""
    if value is None or (isinstance(value, str) and not value.strip()):
        return default.resolve(strict=False)
    
    raw_value = str(value).strip()
    
    # Expand known variables
    expanded = _replace_known_path_vars(raw_value)
    
    # Handle URI-like prefixes
    uri_prefixes = {
        "repo://": BOND_ROOT,
        "config://": CONFIG_HOME,
        "data://": DATA_HOME,
        "state://": STATE_HOME,
        "cache://": CACHE_HOME,
    }
    
    for prefix, base in uri_prefixes.items():
        if expanded.startswith(prefix):
            rest = expanded[len(prefix):]
            # Strip leading slash or backslash
            rest = rest.lstrip("/\\")
            return (base / rest).resolve(strict=False)
    
    # Process as regular path
    path = Path(expanded).expanduser()
    
    # Make absolute if needed
    if not path.is_absolute():
        relative_base = relative_base or BOND_ROOT
        path = relative_base / path
    
    return path.resolve(strict=False)


def _expand_path(value: str) -> str:
    """Backward compatibility function for path expansion."""
    return str(resolve_path_value(value, default=BOND_ROOT, relative_base=BOND_ROOT))


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_iso_ts(value: str) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None

    raw = value.strip()
    try:
        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"
        dt = datetime.fromisoformat(raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def load_json(path: Path, default=None):
    if default is None:
        default = {}
    try:
        if not path.exists():
            return default
        text = path.read_text(encoding="utf-8", errors="ignore").strip()
        if not text:
            return default
        return json.loads(text)
    except Exception:
        return default


def save_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def append_jsonl(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def tail_jsonl(path: Path, limit: int = 10) -> list[dict]:
    if limit <= 0 or not path.exists():
        return []

    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()[-limit:]
    except Exception:
        return []

    out = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
            if isinstance(obj, dict):
                out.append(obj)
        except Exception:
            continue
    return out


def load_assistant_config() -> dict:
    data = load_json(CONFIG_FILE, {})
    return data if isinstance(data, dict) else {}


def config_value(key: str, default=None):
    """Load a value from assistant config without path expansion."""
    cfg = load_assistant_config()
    return cfg.get(key, default)


def config_path_value(key, *, default: Path, env_name: str | None = None, relative_base: Path | None = None) -> Path:
    """Load a path value from config with environment override and variable expansion."""
    # Check environment variable override first
    if env_name:
        env_path = _env_path(env_name)
        if env_path:
            return env_path
    
    # Get from config and resolve
    config_val = config_value(key)
    return resolve_path_value(config_val, default=default, relative_base=relative_base)


def get_memory_root() -> Path:
    """Get memory root path, respecting config and environment."""
    return config_path_value("memory_root", default=MEMORY_ROOT, env_name="BOND_MEMORY_ROOT", relative_base=DATA_HOME)


def get_state_root() -> Path:
    """Get state root path, respecting config and environment."""
    return config_path_value("state_root", default=STATE_ROOT, env_name="BOND_STATE_ROOT", relative_base=STATE_HOME)


def get_router_config_path() -> Path:
    """Get router config path, respecting config and environment."""
    return config_path_value("router_config", default=BOND_ROOT / "config" / "router" / "profiles.json", env_name="BOND_ROUTER_CONFIG_PATH", relative_base=BOND_ROOT)


def get_changelog_path() -> Path:
    """Get changelog path, respecting config and environment."""
    return config_path_value("changelog_path", default=CHANGELOG_PATH, env_name="BOND_CHANGELOG_PATH", relative_base=STATE_HOME)


def get_second_drive() -> str | None:
    """Get second drive path from env, config, or facts."""
    # Check environment first
    env_val = os.getenv("BOND_SECOND_DRIVE")
    if env_val and env_val.strip():
        return env_val.strip()
    
    # Check config
    config_val = config_value("second_drive")
    if isinstance(config_val, str) and config_val.strip():
        return config_val.strip()
    
    # Check facts
    fact_val = fact_value("environment", "second_drive")
    if isinstance(fact_val, str) and fact_val.strip():
        return fact_val.strip()
    
    return None


def get_archive_root() -> Path | None:
    """Get archive root path from env, config, or second_drive."""
    # Check environment first
    env_val = os.getenv("BOND_ARCHIVE_ROOT")
    if env_val and env_val.strip():
        return resolve_path_value(env_val, default=DATA_HOME / "archive", relative_base=DATA_HOME)
    
    # Check config
    config_val = config_value("archive_root")
    if isinstance(config_val, str) and config_val.strip():
        return resolve_path_value(config_val, default=DATA_HOME / "archive", relative_base=DATA_HOME)
    
    # Check second drive using a neutral archive directory name.
    second_drive = get_second_drive()
    if second_drive:
        return Path(second_drive) / "bond-archive" / "memory"
    
    return None


def get_files() -> dict:
    memory_root = get_memory_root()
    facts = memory_root / "facts"
    logs = memory_root / "logs"
    mem_state = memory_root / "state"

    return {
        "preferences": facts / "preferences.json",
        "environment": facts / "environment.json",
        "workflows": facts / "workflows.json",
        "aliases": facts / "aliases.json",
        "actions": logs / "actions.jsonl",
        "failures": logs / "failures.jsonl",
        "chats": logs / "chats.jsonl",
        "events": logs / "events.jsonl",
        "reflections": logs / "reflections.jsonl",
        "manifest": mem_state / "memory_manifest.json",
        "archive_map": mem_state / "archive_map.json",
        "active_context": mem_state / "active_context.txt",
    }


FILES = get_files()


def ensure_memory_dirs() -> None:
    global FILES
    FILES = get_files()

    facts_dir = get_memory_root() / "facts"
    logs_dir = get_memory_root() / "logs"
    mem_state_dir = get_memory_root() / "state"

    facts_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)
    mem_state_dir.mkdir(parents=True, exist_ok=True)

    for bucket in FACT_BUCKETS:
        path = FILES[bucket]
        if not path.exists():
            save_json(path, {})

    for bucket in LOG_BUCKETS:
        FILES[bucket].touch(exist_ok=True)

    if not FILES["archive_map"].exists():
        save_json(FILES["archive_map"], {})

    if not FILES["manifest"].exists():
        save_json(FILES["manifest"], {})

    if not FILES["active_context"].exists():
        FILES["active_context"].write_text(
            "LIVE MEMORY CONTEXT\n\n"
            "Read exact facts first.\n"
            "Use recent logs for short-term operational context.\n"
            "Use archive_map only if older history is actually needed.\n",
            encoding="utf-8",
        )


def load_fact_bucket(bucket: str) -> dict:
    if bucket not in FACT_BUCKETS:
        raise ValueError(f"Unsupported fact bucket: {bucket}")
    ensure_memory_dirs()
    data = load_json(FILES[bucket], {})
    return data if isinstance(data, dict) else {}


def load_all_facts() -> dict:
    ensure_memory_dirs()
    return {bucket: load_fact_bucket(bucket) for bucket in FACT_BUCKETS}


def fact_value(bucket: str, key: str, default=None):
    data = load_fact_bucket(bucket)
    item = data.get(key)

    if isinstance(item, dict) and "value" in item:
        return item.get("value", default)

    if item is not None:
        return item

    return default


def log_memory(kind: str, message: str, meta=None) -> None:
    if kind not in LOG_BUCKETS:
        raise ValueError(f"Unsupported log kind: {kind}")

    ensure_memory_dirs()
    append_jsonl(
        FILES[kind],
        {
            "ts": utc_now(),
            "message": message,
            "meta": meta or {},
        },
    )


def update_manifest() -> dict:
    ensure_memory_dirs()

    manifest = {
        "updated_at": utc_now(),
        "config_file": str(CONFIG_FILE),
        "config": load_assistant_config(),
        "facts": {bucket: str(FILES[bucket]) for bucket in FACT_BUCKETS},
        "logs": {bucket: str(FILES[bucket]) for bucket in LOG_BUCKETS},
        "state": {
            "active_context": str(FILES["active_context"]),
            "archive_map": str(FILES["archive_map"]),
        },
    }
    save_json(FILES["manifest"], manifest)
    return manifest


def _flatten_fact_lines(title: str, data: dict) -> list[str]:
    lines = []
    if not data:
        return [f"- {title}: none"]

    for key in sorted(data.keys()):
        item = data.get(key)
        if isinstance(item, dict):
            value = item.get("value", "")
        else:
            value = item

        if isinstance(value, (dict, list)):
            rendered = json.dumps(value, ensure_ascii=False)
        else:
            rendered = str(value)

        lines.append(f"- {title}.{key} = {rendered}")

    return lines or [f"- {title}: none"]


def _entry_message(entry: dict) -> str:
    return str(entry.get("message", "")).strip()


def _dedupe_keep_latest(entries: list[dict], limit: int) -> list[dict]:
    if not entries or limit <= 0:
        return []

    seen = set()
    kept_reversed = []

    for entry in reversed(entries):
        message = _entry_message(entry)
        key = message if message else json.dumps(entry, ensure_ascii=False, sort_keys=True)
        if key in seen:
            continue
        seen.add(key)
        kept_reversed.append(entry)
        if len(kept_reversed) >= limit:
            break

    return list(reversed(kept_reversed))


def _recent_failures(entries: list[dict], window_minutes: int, limit: int) -> list[dict]:
    if not entries or limit <= 0:
        return []

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(minutes=window_minutes)

    filtered = []
    for entry in entries:
        ts = _parse_iso_ts(entry.get("ts", ""))
        if ts is None:
            continue
        if ts >= cutoff:
            filtered.append(entry)

    return _dedupe_keep_latest(filtered, limit)


def _recent_actions(entries: list[dict], limit: int) -> list[dict]:
    return _dedupe_keep_latest(entries, limit)


def _recent_reflections(entries: list[dict], limit: int) -> list[dict]:
    return _dedupe_keep_latest(entries, limit)


def build_active_context() -> str:
    ensure_memory_dirs()

    facts = load_all_facts()
    actions = tail_jsonl(FILES["actions"], 20)
    failures = tail_jsonl(FILES["failures"], 20)
    reflections = tail_jsonl(FILES["reflections"], 12)
    archive_map = load_json(FILES["archive_map"], {})

    recent_actions = _recent_actions(actions, ACTIVE_ACTION_LIMIT)
    recent_failures = _recent_failures(failures, ACTIVE_FAILURE_WINDOW_MINUTES, ACTIVE_FAILURE_LIMIT)
    recent_reflections = _recent_reflections(reflections, ACTIVE_REFLECTION_LIMIT)

    lines = []
    lines.append("LIVE MEMORY CONTEXT")
    lines.append("")
    lines.append("RULES")
    lines.append("- Read exact facts first.")
    lines.append("- Use recent logs for short-term operational context.")
    lines.append("- Prefer current successful behavior over stale failures.")
    lines.append("- Use archive_map only if older history is actually needed.")
    lines.append("")

    lines.append("FACT SNAPSHOT")
    for bucket in FACT_BUCKETS:
        lines.extend(_flatten_fact_lines(bucket, facts.get(bucket, {})))
    lines.append("")

    lines.append("RECENT ACTIONS")
    if recent_actions:
        for item in recent_actions:
            lines.append(f"- {item.get('ts', '')}: {item.get('message', '')}")
    else:
        lines.append("- none")
    lines.append("")

    lines.append("RECENT FAILURES")
    if recent_failures:
        for item in recent_failures:
            lines.append(f"- {item.get('ts', '')}: {item.get('message', '')}")
    else:
        lines.append("- none")
    lines.append("")

    lines.append("RECENT REFLECTIONS")
    if recent_reflections:
        for item in recent_reflections:
            lines.append(f"- {item.get('ts', '')}: {item.get('message', '')}")
    else:
        lines.append("- none")
    lines.append("")

    lines.append("ARCHIVE STATUS")
    if isinstance(archive_map, dict) and archive_map:
        lines.append(f"- archive entries: {len(archive_map)}")
        for key in sorted(archive_map.keys())[:5]:
            lines.append(f"- {key}: indexed")
        if len(archive_map) > 5:
            lines.append(f"- ... and {len(archive_map) - 5} more")
    else:
        lines.append("- none")

    text = "\n".join(lines) + "\n"
    FILES["active_context"].write_text(text, encoding="utf-8")
    update_manifest()
    return text
