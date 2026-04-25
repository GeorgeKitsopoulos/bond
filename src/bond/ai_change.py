#!/usr/bin/env python3
import difflib
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

from ai_core import get_archive_root, get_changelog_path

CHANGELOG = get_changelog_path()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def ensure_text(value) -> str:
    if value is None:
        return ""
    return str(value)


def load_changelog_entries() -> list[dict]:
    if not CHANGELOG.exists():
        return []

    entries = []
    try:
        with CHANGELOG.open("r", encoding="utf-8", errors="ignore") as f:
            for raw in f:
                line = raw.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                if isinstance(obj, dict):
                    entries.append(obj)
    except Exception:
        return []

    return entries


def last_entry_for_file(file_path: Path) -> dict | None:
    target = str(file_path)
    entries = load_changelog_entries()
    for entry in reversed(entries):
        if ensure_text(entry.get("file")) == target:
            return entry
    return None


def read_backup_text(backup_path: Path) -> str:
    return backup_path.read_text(encoding="utf-8", errors="ignore")


def current_file_text(file_path: Path) -> str:
    return file_path.read_text(encoding="utf-8", errors="ignore")


def diff_summary(old_text: str, new_text: str, context: int = 1, max_lines: int = 40) -> dict:
    old_lines = old_text.splitlines()
    new_lines = new_text.splitlines()

    matcher = difflib.SequenceMatcher(None, old_lines, new_lines)
    changed_ranges = []
    added = 0
    removed = 0

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        removed += max(0, i2 - i1)
        added += max(0, j2 - j1)
        changed_ranges.append(
            {
                "tag": tag,
                "old_start": i1 + 1,
                "old_end": i2,
                "new_start": j1 + 1,
                "new_end": j2,
            }
        )

    unified = list(
        difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile="previous",
            tofile="current",
            lineterm="",
            n=context,
        )
    )
    preview = unified[:max_lines]

    return {
        "changed": old_text != new_text,
        "added_lines": added,
        "removed_lines": removed,
        "changed_ranges": changed_ranges,
        "preview": preview,
        "preview_truncated": len(unified) > max_lines,
    }


def short_hash(value: str, length: int = 12) -> str:
    return value[:length]


def classify_change(diff: dict) -> str:
    if not diff.get("changed"):
        return "no_change"

    added = int(diff.get("added_lines", 0))
    removed = int(diff.get("removed_lines", 0))
    total = added + removed

    if total <= 4:
        return "tiny"
    if total <= 20:
        return "small"
    if total <= 100:
        return "medium"
    return "large"


def write_entry(entry: dict) -> None:
    CHANGELOG.parent.mkdir(parents=True, exist_ok=True)
    with CHANGELOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def main():
    if len(sys.argv) < 3:
        print("usage: ai_change.py <file> <message>")
        raise SystemExit(1)

    file_path = Path(sys.argv[1]).expanduser().resolve()
    message = " ".join(sys.argv[2:]).strip()

    if not file_path.exists():
        print("file does not exist")
        raise SystemExit(2)

    archive_root = get_archive_root()
    if archive_root is None:
        print("no archive root available")
        raise SystemExit(3)

    backup_root = archive_root / "source_backups"
    backup_root.mkdir(parents=True, exist_ok=True)

    now_ts = utc_now()
    current_hash = sha256_file(file_path)
    current_text = current_file_text(file_path)

    previous = last_entry_for_file(file_path)

    if previous:
        prev_hash = ensure_text(previous.get("sha256"))
        prev_backup = ensure_text(previous.get("backup"))
        prev_message = ensure_text(previous.get("message"))

        if prev_hash and prev_hash == current_hash:
            skip_entry = {
                "ts": now_ts,
                "file": str(file_path),
                "message": message,
                "status": "duplicate_skipped",
                "reason": "unchanged_since_last_logged_version",
                "sha256": current_hash,
                "same_as_backup": prev_backup or None,
                "same_as_message": prev_message or None,
            }
            write_entry(skip_entry)
            print("duplicate skipped")
            if prev_backup:
                print(f"same as backup: {prev_backup}")
            raise SystemExit(0)

    previous_text = ""
    previous_backup_path = None
    previous_hash = None

    if previous:
        prev_backup = ensure_text(previous.get("backup"))
        previous_hash = ensure_text(previous.get("sha256")) or None
        if prev_backup:
            candidate = Path(prev_backup)
            if candidate.exists():
                previous_backup_path = candidate
                try:
                    previous_text = read_backup_text(candidate)
                except Exception:
                    previous_text = ""

    diff = diff_summary(previous_text, current_text)
    change_kind = classify_change(diff)

    safe_ts = now_ts.replace(":", "-")
    backup_file = backup_root / f"{file_path.name}_{safe_ts}"
    shutil.copy2(file_path, backup_file)

    entry = {
        "ts": now_ts,
        "file": str(file_path),
        "backup": str(backup_file),
        "message": message,
        "status": "logged",
        "sha256": current_hash,
        "short_hash": short_hash(current_hash),
        "size_bytes": file_path.stat().st_size,
        "previous_sha256": previous_hash,
        "previous_backup": str(previous_backup_path) if previous_backup_path else None,
        "change_kind": change_kind,
        "diff": {
            "changed": diff["changed"],
            "added_lines": diff["added_lines"],
            "removed_lines": diff["removed_lines"],
            "changed_ranges": diff["changed_ranges"],
            "preview": diff["preview"],
            "preview_truncated": diff["preview_truncated"],
        },
    }

    write_entry(entry)

    print("change logged")
    print(f"backup: {backup_file}")
    print(f"hash: {current_hash}")
    print(f"change_kind: {change_kind}")
    print(f"added_lines: {diff['added_lines']}")
    print(f"removed_lines: {diff['removed_lines']}")

    if diff["preview"]:
        print("diff_preview:")
        for line in diff["preview"]:
            print(line)
        if diff["preview_truncated"]:
            print("... diff preview truncated ...")


if __name__ == "__main__":
    main()
