#!/usr/bin/env python3
import shutil
from pathlib import Path

from ai_core import (
    FACT_BUCKETS,
    FILES,
    append_jsonl,
    build_active_context,
    ensure_memory_dirs,
    get_archive_root,
    get_state_root,
    load_json,
    save_json,
    utc_now,
)

MAX_LOG_SIZE = 2 * 1024 * 1024  # 2MB
DEFAULT_KEEP_LOG_ARCHIVES = 10
DEFAULT_KEEP_FACT_SNAPSHOTS = 20


def log_action(message: str, meta=None) -> None:
    append_jsonl(
        FILES["actions"],
        {
            "ts": utc_now(),
            "message": message,
            "meta": meta or {},
        },
    )


def log_failure(message: str, meta=None) -> None:
    append_jsonl(
        FILES["failures"],
        {
            "ts": utc_now(),
            "message": message,
            "meta": meta or {},
        },
    )


def get_retention_settings() -> tuple[int, int]:
    assistant_config = get_state_root() / "assistant_config.json"
    data = load_json(assistant_config, {})
    if not isinstance(data, dict):
        data = {}

    rotation_cfg = data.get("rotation")
    if not isinstance(rotation_cfg, dict):
        rotation_cfg = {}

    keep_log_archives = rotation_cfg.get("keep_log_archives")
    if not isinstance(keep_log_archives, int) or keep_log_archives < 1:
        keep_log_archives = DEFAULT_KEEP_LOG_ARCHIVES

    keep_fact_snapshots = rotation_cfg.get("keep_fact_snapshots")
    if not isinstance(keep_fact_snapshots, int) or keep_fact_snapshots < 1:
        keep_fact_snapshots = DEFAULT_KEEP_FACT_SNAPSHOTS

    return keep_log_archives, keep_fact_snapshots


def rotate_log(log_name: str, archive_root: Path, archive_map: dict) -> bool:
    path = FILES[log_name]
    if not path.exists():
        return False

    size = path.stat().st_size
    if size < MAX_LOG_SIZE:
        return False

    archive_root.mkdir(parents=True, exist_ok=True)

    ts = utc_now().replace(":", "-")
    archive_file = archive_root / f"{log_name}_{ts}.jsonl"

    try:
        shutil.move(str(path), str(archive_file))
        path.touch()
    except Exception as e:
        log_failure(
            f"rotation failed for {log_name}",
            {
                "archive_file": str(archive_file),
                "error": str(e),
            },
        )
        return False

    archive_map.setdefault(log_name, []).append(str(archive_file))

    log_action(
        f"rotated {log_name} to archive",
        {"archive_file": str(archive_file)},
    )

    return True


def snapshot_facts(archive_root: Path, archive_map: dict) -> bool:
    archive_root.mkdir(parents=True, exist_ok=True)

    ts = utc_now().replace(":", "-")
    snapshot = archive_root / f"facts_snapshot_{ts}.json"

    data = {}
    try:
        for bucket in FACT_BUCKETS:
            data[bucket] = load_json(FILES[bucket], {})
        save_json(snapshot, data)
    except Exception as e:
        log_failure(
            "facts snapshot failed",
            {
                "snapshot": str(snapshot),
                "error": str(e),
            },
        )
        return False

    archive_map.setdefault("facts_snapshots", []).append(str(snapshot))

    log_action(
        "created facts snapshot",
        {"snapshot": str(snapshot)},
    )
    return True


def normalize_archive_entries(entries) -> list[str]:
    if not isinstance(entries, list):
        return []
    out = []
    for item in entries:
        if not isinstance(item, str):
            continue
        text = item.strip()
        if not text:
            continue
        out.append(text)
    return out


def prune_archive_list(
    key: str,
    archive_map: dict,
    keep_count: int,
) -> int:
    entries = normalize_archive_entries(archive_map.get(key, []))
    if len(entries) <= keep_count:
        archive_map[key] = entries
        return 0

    existing = []
    missing = []

    for item in entries:
        path = Path(item)
        if path.exists():
            existing.append(item)
        else:
            missing.append(item)

    existing.sort(key=lambda p: Path(p).name)

    if len(existing) <= keep_count:
        kept = existing
        removed = missing
    else:
        kept = existing[-keep_count:]
        removed = existing[:-keep_count] + missing

    pruned = 0

    for item in removed:
        path = Path(item)
        if path.exists():
            try:
                path.unlink()
                pruned += 1
                log_action(
                    f"pruned archived item from {key}",
                    {"archive_file": str(path), "archive_key": key},
                )
            except Exception as e:
                log_failure(
                    f"failed to prune archived item from {key}",
                    {
                        "archive_file": str(path),
                        "archive_key": key,
                        "error": str(e),
                    },
                )

    archive_map[key] = kept
    return pruned


def prune_archives(archive_map: dict, keep_log_archives: int, keep_fact_snapshots: int) -> int:
    total_pruned = 0

    for key in ("actions", "failures", "chats", "reflections"):
        total_pruned += prune_archive_list(key, archive_map, keep_log_archives)

    total_pruned += prune_archive_list("facts_snapshots", archive_map, keep_fact_snapshots)

    return total_pruned


def main():
    ensure_memory_dirs()

    archive_root = get_archive_root()
    if archive_root is None:
        log_failure(
            "memory rotation skipped: no archive root available",
            {"source": "ai_memory_rotate"},
        )
        print("rotation skipped: no archive_root available from config or memory")
        build_active_context()
        return

    keep_log_archives, keep_fact_snapshots = get_retention_settings()

    archive_map = load_json(FILES["archive_map"], {})
    if not isinstance(archive_map, dict):
        archive_map = {}

    rotated_any = False

    for log_name in ("actions", "failures", "chats", "reflections"):
        if rotate_log(log_name, archive_root, archive_map):
            rotated_any = True

    if rotated_any:
        snapshot_facts(archive_root, archive_map)

    pruned_count = prune_archives(
        archive_map,
        keep_log_archives=keep_log_archives,
        keep_fact_snapshots=keep_fact_snapshots,
    )

    save_json(FILES["archive_map"], archive_map)
    build_active_context()
    print(
        f"memory rotation complete (keep_log_archives={keep_log_archives}, "
        f"keep_fact_snapshots={keep_fact_snapshots}, pruned={pruned_count})"
    )


if __name__ == "__main__":
    main()
