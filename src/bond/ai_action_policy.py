#!/usr/bin/env python3
from pathlib import Path

from ai_core import get_archive_root, get_second_drive

HOME = Path.home()


def is_explicit_path_text(text: str) -> bool:
    t = text.strip()
    return t.startswith("~/") or t.startswith("/")


def allowed_path_roots() -> list[Path]:
    roots = [HOME.resolve()]

    second_drive = get_second_drive()
    if second_drive:
        try:
            roots.append(Path(second_drive).expanduser().resolve())
        except Exception:
            pass

    archive_root = get_archive_root()
    if archive_root:
        try:
            roots.append(Path(archive_root).expanduser().resolve())
        except Exception:
            pass

    deduped = []
    seen = set()
    for root in roots:
        key = str(root)
        if key not in seen:
            seen.add(key)
            deduped.append(root)
    return deduped


def path_is_allowed(path: Path) -> bool:
    try:
        resolved = path.expanduser().resolve(strict=False)
    except Exception:
        return False

    blocked_prefixes = [
        Path("/etc"),
        Path("/proc"),
        Path("/sys"),
        Path("/dev"),
        Path("/run"),
        Path("/boot"),
        Path("/root"),
        Path("/usr"),
        Path("/var"),
        Path("/lib"),
        Path("/lib64"),
        Path("/sbin"),
        Path("/bin"),
        Path("/opt"),
    ]

    for blocked in blocked_prefixes:
        try:
            resolved.relative_to(blocked)
            return False
        except ValueError:
            pass

    for root in allowed_path_roots():
        try:
            resolved.relative_to(root)
            return True
        except ValueError:
            continue

    return False


def resolve_explicit_path(text: str) -> tuple[bool, str, Path | None]:
    raw = text.strip()
    if not is_explicit_path_text(raw):
        return False, "not_explicit_path", None

    try:
        expanded = Path(raw).expanduser()
        resolved = expanded.resolve(strict=False)
    except Exception:
        return False, f"invalid_path: {raw}", None

    if not path_is_allowed(resolved):
        return False, f"blocked_path: {resolved}", None

    return True, str(resolved), resolved
