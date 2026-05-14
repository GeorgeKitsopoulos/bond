import os
import platform
import shutil
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

STORAGE_PROFILE_KIND = "storage_portability_profile"
STORAGE_PROFILE_SCHEMA_VERSION = 1
STORAGE_STRATEGY_EXTERNAL_LARGE_DATA_PREFERRED = "external_large_data_preferred"
STORAGE_STRATEGY_HOME_LOCAL_FALLBACK = "home_local_fallback"
STORAGE_STRATEGY_MANUAL_REVIEW = "manual_review"
ROLE_CONFIG = "config"
ROLE_DATA = "data"
ROLE_CACHE = "cache"
ROLE_MODELS = "models"
ROLE_TELEMETRY = "telemetry"
ROLE_LOGS = "logs"
ROLE_BACKUPS = "backups"

_DEFAULT_EXTERNAL_ROOTS = ("/run/media", "/media", "/mnt")
_LARGE_DATA_FILESYSTEMS = {
    "ext2",
    "ext3",
    "ext4",
    "btrfs",
    "xfs",
    "f2fs",
    "exfat",
    "vfat",
    "ntfs",
    "ntfs3",
    "fuseblk",
}
_PSEUDO_FILESYSTEMS = {
    "proc",
    "sysfs",
    "devtmpfs",
    "devpts",
    "tmpfs",
    "securityfs",
    "cgroup",
    "cgroup2",
    "pstore",
    "bpf",
    "autofs",
    "debugfs",
    "tracefs",
    "fusectl",
    "configfs",
    "efivarfs",
    "mqueue",
    "hugetlbfs",
    "overlay",
}

_BACKSLASH_SENTINEL = "__PROC_MOUNTS_BACKSLASH__"


def _text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if value is None:
        return ""
    return str(value)


def _coerce_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "ro", "on"}:
            return True
        if normalized in {"0", "false", "no", "rw", "off"}:
            return False
    return bool(value)


def _path_is_under(path: str, root: str) -> bool:
    if not path or not root:
        return False
    if root == "/":
        return path.startswith("/")
    normalized_root = root.rstrip("/")
    if not normalized_root:
        return path.startswith("/")
    return path == normalized_root or path.startswith(normalized_root + "/")


def _is_external_media_path(mount_point: str, external_roots: list[str] | None) -> bool:
    roots = external_roots or list(_DEFAULT_EXTERNAL_ROOTS)
    for root in roots:
        if _path_is_under(mount_point, _text(root)):
            return True
    return False


def _is_steam_deck_sd_path(device: str, mount_point: str) -> bool:
    lower_blob = f"{device} {mount_point}".lower()
    lower_device = device.lower()
    if _path_is_under(mount_point, "/run/media/deck"):
        return True
    is_removable_mount = _is_external_media_path(mount_point, list(_DEFAULT_EXTERNAL_ROOTS))
    if "mmcblk" in lower_device:
        return is_removable_mount
    for token in ("sdcard", "steamdeck", "steam-deck"):
        if token in lower_blob and is_removable_mount:
            return True
    return False


def _mount_recommendation_reason(record: Mapping[str, object]) -> str:
    if _coerce_bool(record.get("is_pseudo")):
        return "pseudo_or_runtime_filesystem"
    if _coerce_bool(record.get("read_only")):
        return "read_only_mount"
    if _coerce_bool(record.get("is_bond_large_data_candidate")):
        if _coerce_bool(record.get("is_steam_deck_sd_path")):
            return "steam_deck_sd_candidate"
        return "external_large_data_candidate"
    if _coerce_bool(record.get("is_steam_deck_sd_path")):
        return "steam_deck_sd_candidate"
    if _coerce_bool(record.get("is_home_mount_candidate")):
        return "home_mount_candidate"
    return "not_large_data_candidate"


def decode_proc_mount_escape(value: str) -> str:
    if not value:
        return value
    decoded = value.replace("\\134", _BACKSLASH_SENTINEL)
    decoded = decoded.replace("\\040", " ")
    decoded = decoded.replace("\\011", "\t")
    decoded = decoded.replace("\\012", "\n")
    return decoded.replace(_BACKSLASH_SENTINEL, "\\")


def parse_proc_mounts_text(text: str) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) < 4:
            continue
        device, mount_point, fs_type, options_text = parts[:4]
        options = [option for option in options_text.split(",") if option]
        records.append(
            {
                "device": decode_proc_mount_escape(device),
                "mount_point": decode_proc_mount_escape(mount_point),
                "fs_type": fs_type,
                "options": options,
                "read_only": "ro" in options,
                "source": "proc_mounts",
            }
        )
    return records


def read_proc_mounts(path: str | os.PathLike[str] = "/proc/mounts") -> list[dict[str, object]]:
    try:
        text = Path(path).read_text(encoding="utf-8")
    except Exception:
        return []
    return parse_proc_mounts_text(text)


def is_pseudo_filesystem(fs_type: str) -> bool:
    return _text(fs_type).strip().lower() in _PSEUDO_FILESYSTEMS


def is_large_data_filesystem_candidate(fs_type: str) -> bool:
    return _text(fs_type).strip().lower() in _LARGE_DATA_FILESYSTEMS


def classify_mount_record(
    record: Mapping[str, object],
    home_path: str | None = None,
    external_roots: list[str] | None = None,
) -> dict[str, object]:
    device = _text(record.get("device"))
    mount_point = _text(record.get("mount_point"))
    fs_type = _text(record.get("fs_type"))
    raw_options = record.get("options", [])
    if isinstance(raw_options, list):
        options = [_text(option) for option in raw_options if _text(option)]
    elif isinstance(raw_options, tuple):
        options = [_text(option) for option in raw_options if _text(option)]
    else:
        options = [option for option in _text(raw_options).split(",") if option]

    normalized_options = [_text(option).strip().lower() for option in options if _text(option).strip()]
    if "read_only" in record:
        read_only = _coerce_bool(record.get("read_only"))
    else:
        read_only = "ro" in normalized_options
    is_pseudo = is_pseudo_filesystem(fs_type)
    is_large_candidate = is_large_data_filesystem_candidate(fs_type)
    is_external = _is_external_media_path(mount_point, external_roots)
    is_steam_deck = _is_steam_deck_sd_path(device, mount_point)
    is_home_candidate = False
    if home_path is not None:
        is_home_candidate = _path_is_under(_text(home_path), mount_point)
    is_bond_candidate = (
        not is_pseudo
        and not read_only
        and is_large_candidate
        and (is_external or is_steam_deck)
    )

    result: dict[str, object] = {
        "device": device,
        "mount_point": mount_point,
        "fs_type": fs_type,
        "options": options,
        "read_only": read_only,
        "source": _text(record.get("source") or "proc_mounts"),
        "is_pseudo": is_pseudo,
        "is_large_data_filesystem_candidate": is_large_candidate,
        "is_external_media_path": is_external,
        "is_steam_deck_sd_path": is_steam_deck,
        "is_home_mount_candidate": is_home_candidate,
        "is_bond_large_data_candidate": is_bond_candidate,
    }
    result["recommendation_reason"] = _mount_recommendation_reason(result)
    return result


def collect_disk_usage(
    path: str,
    disk_usage_func: Callable[[str], object] | None = None,
) -> dict[str, object]:
    usage_func = disk_usage_func or shutil.disk_usage
    result: dict[str, object] = {
        "path": path,
        "available": False,
        "total_bytes": None,
        "used_bytes": None,
        "free_bytes": None,
        "used_percent": None,
        "error_kind": None,
    }
    try:
        usage = usage_func(path)
        total = int(getattr(usage, "total"))
        used = int(getattr(usage, "used"))
        free = int(getattr(usage, "free"))
        used_percent = None
        if total > 0:
            used_percent = (used / total) * 100.0
        result.update(
            {
                "available": True,
                "total_bytes": total,
                "used_bytes": used,
                "free_bytes": free,
                "used_percent": used_percent,
                "error_kind": None,
            }
        )
    except FileNotFoundError:
        result["error_kind"] = "path_missing"
    except PermissionError:
        result["error_kind"] = "permission_denied"
    except NotADirectoryError:
        result["error_kind"] = "path_not_directory"
    except (AttributeError, TypeError, ValueError):
        result["error_kind"] = "invalid_usage_result"
    except OSError:
        result["error_kind"] = "disk_usage_error"
    except Exception:
        result["error_kind"] = "disk_usage_error"
    return result


def classify_space_pressure(usage: Mapping[str, object]) -> str:
    available = _coerce_bool(usage.get("available"))
    free_bytes = usage.get("free_bytes")
    total_bytes = usage.get("total_bytes")
    used_percent = usage.get("used_percent")
    if (
        not available
        or not isinstance(free_bytes, int)
        or not isinstance(total_bytes, int)
        or total_bytes <= 0
        or not isinstance(used_percent, (int, float))
    ):
        return "unknown"

    free_gib = free_bytes / float(1024**3)
    free_percent = 100.0 - float(used_percent)

    if free_gib >= 100.0 and free_percent >= 20.0:
        return "large_data_friendly"
    if free_gib < 5.0 or free_percent < 5.0:
        return "critical"
    if free_gib < 15.0 or free_percent < 10.0:
        return "low"
    return "adequate"


def summarize_mount_candidates(
    mounts: list[Mapping[str, object]],
    home_path: str | None = None,
    disk_usage_func: Callable[[str], object] | None = None,
) -> dict[str, object]:
    classified_mounts: list[dict[str, object]] = []
    external_candidates: list[dict[str, object]] = []
    steam_deck_sd_candidates: list[dict[str, object]] = []
    large_data_candidates: list[dict[str, object]] = []
    home_mount: dict[str, object] | None = None
    space_pressure_summary = {
        "unknown": 0,
        "critical": 0,
        "low": 0,
        "adequate": 0,
        "large_data_friendly": 0,
    }
    disk_usage_cache: dict[str, dict[str, object]] = {}

    def _mount_specificity(path: str) -> int:
        normalized = path.strip("/")
        if not normalized:
            return 0
        return len([segment for segment in normalized.split("/") if segment])

    for record in mounts[:64]:
        classified = classify_mount_record(record, home_path=home_path)
        mount_point = _text(classified.get("mount_point"))
        needs_usage = False

        if classified["is_home_mount_candidate"]:
            candidate_mount = _text(classified.get("mount_point"))
            if home_mount is None:
                home_mount = classified
                needs_usage = True
            else:
                current_mount = _text(home_mount.get("mount_point"))
                candidate_depth = _mount_specificity(candidate_mount)
                current_depth = _mount_specificity(current_mount)
                if candidate_depth > current_depth or (
                    candidate_depth == current_depth and candidate_mount < current_mount
                ):
                    home_mount = classified
                    needs_usage = True
        if classified["is_external_media_path"]:
            external_candidates.append(classified)
            needs_usage = True
        if classified["is_steam_deck_sd_path"]:
            steam_deck_sd_candidates.append(classified)
            needs_usage = True
        if classified["is_bond_large_data_candidate"]:
            large_data_candidates.append(classified)
            needs_usage = True

        if needs_usage and mount_point and mount_point not in disk_usage_cache:
            disk_usage_cache[mount_point] = collect_disk_usage(mount_point, disk_usage_func)
            pressure = classify_space_pressure(disk_usage_cache[mount_point])
            space_pressure_summary[pressure] = space_pressure_summary.get(pressure, 0) + 1
        if mount_point in disk_usage_cache:
            classified["disk_usage"] = disk_usage_cache[mount_point]

        classified_mounts.append(classified)

    return {
        "mounts": classified_mounts[:64],
        "home_mount": home_mount,
        "external_candidates": external_candidates,
        "steam_deck_sd_candidates": steam_deck_sd_candidates,
        "large_data_candidates": large_data_candidates,
        "space_pressure_summary": space_pressure_summary,
    }


def collect_bond_environment_paths(env: Mapping[str, str] | None = None) -> dict[str, dict[str, object]]:
    observed_env = os.environ if env is None else env
    role_map = {
        "BOND_HOME": "home",
        "BOND_CONFIG_DIR": ROLE_CONFIG,
        "BOND_DATA_DIR": ROLE_DATA,
        "BOND_CACHE_DIR": ROLE_CACHE,
        "BOND_MODEL_DIR": ROLE_MODELS,
        "BOND_TELEMETRY_DIR": ROLE_TELEMETRY,
        "BOND_LOG_DIR": ROLE_LOGS,
        "BOND_BACKUP_DIR": ROLE_BACKUPS,
    }
    collected: dict[str, dict[str, object]] = {}
    for name, role in role_map.items():
        raw_value = observed_env.get(name)
        path_value = raw_value if isinstance(raw_value, str) and raw_value else None
        collected[name] = {
            "set": path_value is not None,
            "path": path_value,
            "role": role,
            "observed_only": True,
            "created": False,
        }
    return collected


def _observed_path(env_paths: Mapping[str, Mapping[str, object]], name: str) -> str | None:
    value = env_paths.get(name)
    if not isinstance(value, Mapping):
        return None
    path_value = value.get("path")
    if isinstance(path_value, str) and path_value:
        return path_value
    return None


def build_storage_recommendations(
    candidate_summary: Mapping[str, object],
    env_paths: Mapping[str, Mapping[str, object]],
    home_path: str | None = None,
) -> dict[str, object]:
    large_data_candidates = candidate_summary.get("large_data_candidates")
    home_mount = candidate_summary.get("home_mount")
    home_mount_point = None
    if isinstance(home_mount, Mapping):
        home_mount_point = _text(home_mount.get("mount_point")) or None

    preferred_large_data_base: str | None = None
    preferred_config_base: str | None = None
    strategy = STORAGE_STRATEGY_MANUAL_REVIEW
    requires_manual_review = True
    reason = "manual_review_required"
    bond_home_path = _observed_path(env_paths, "BOND_HOME") or home_path

    def _candidate_pressure(candidate: Mapping[str, object]) -> str:
        usage = candidate.get("disk_usage")
        if isinstance(usage, Mapping):
            return classify_space_pressure(usage)
        return "unknown"

    def _candidate_sort_key(candidate: Mapping[str, object]) -> tuple[int, str]:
        pressure = _candidate_pressure(candidate)
        pressure_rank = {
            "large_data_friendly": 0,
            "adequate": 1,
            "low": 2,
            "critical": 3,
            "unknown": 4,
        }.get(pressure, 5)
        mount_point = _text(candidate.get("mount_point"))
        return (pressure_rank, mount_point)

    if isinstance(large_data_candidates, list) and large_data_candidates:
        mapping_candidates = [candidate for candidate in large_data_candidates if isinstance(candidate, Mapping)]
        suitable_candidates = [
            candidate
            for candidate in mapping_candidates
            if not _coerce_bool(candidate.get("read_only"))
            and _candidate_pressure(candidate) in {"adequate", "large_data_friendly"}
        ]
        if suitable_candidates:
            selected_candidate = sorted(suitable_candidates, key=_candidate_sort_key)[0]
            preferred_large_data_base = _text(selected_candidate.get("mount_point")) or None
            preferred_config_base = _observed_path(env_paths, "BOND_CONFIG_DIR") or bond_home_path or home_mount_point
            strategy = STORAGE_STRATEGY_EXTERNAL_LARGE_DATA_PREFERRED
            requires_manual_review = False
            reason = STORAGE_STRATEGY_EXTERNAL_LARGE_DATA_PREFERRED
        else:
            preferred_config_base = _observed_path(env_paths, "BOND_CONFIG_DIR") or bond_home_path or home_mount_point
            strategy = STORAGE_STRATEGY_MANUAL_REVIEW
            requires_manual_review = True
            reason = "manual_review_required_external_candidate_pressure"
    elif home_mount_point:
        preferred_large_data_base = bond_home_path or home_mount_point
        preferred_config_base = _observed_path(env_paths, "BOND_CONFIG_DIR") or bond_home_path or home_mount_point
        strategy = STORAGE_STRATEGY_HOME_LOCAL_FALLBACK
        requires_manual_review = False
        reason = STORAGE_STRATEGY_HOME_LOCAL_FALLBACK
    else:
        preferred_config_base = _observed_path(env_paths, "BOND_CONFIG_DIR") or bond_home_path

    def _role_base(role: str) -> str | None:
        role_env_map: dict[str, tuple[str, ...]] = {
            ROLE_CONFIG: ("BOND_CONFIG_DIR",),
            ROLE_DATA: ("BOND_DATA_DIR",),
            ROLE_CACHE: ("BOND_CACHE_DIR",),
            ROLE_MODELS: ("BOND_MODEL_DIR",),
            ROLE_TELEMETRY: ("BOND_TELEMETRY_DIR",),
            ROLE_LOGS: ("BOND_TELEMETRY_DIR", "BOND_LOG_DIR"),
            ROLE_BACKUPS: ("BOND_BACKUP_DIR",),
        }
        for env_name in role_env_map.get(role, ()): 
            observed_path = _observed_path(env_paths, env_name)
            if observed_path:
                return observed_path
        if role == ROLE_CONFIG:
            return preferred_config_base
        if strategy in {
            STORAGE_STRATEGY_EXTERNAL_LARGE_DATA_PREFERRED,
            STORAGE_STRATEGY_HOME_LOCAL_FALLBACK,
        }:
            return preferred_large_data_base or preferred_config_base
        return preferred_config_base or preferred_large_data_base

    role_recommendations: list[dict[str, object]] = []
    for role in [ROLE_CONFIG, ROLE_DATA, ROLE_CACHE, ROLE_MODELS, ROLE_TELEMETRY, ROLE_LOGS, ROLE_BACKUPS]:
        base_path = _role_base(role)
        if strategy == STORAGE_STRATEGY_MANUAL_REVIEW:
            role_reason = "manual_review_only"
        elif role == ROLE_CONFIG:
            role_reason = "home_path_preferred_for_config"
        else:
            role_reason = strategy
        role_recommendations.append(
            {
                "role": role,
                "preferred_base": base_path,
                "reason": role_reason,
                "create_authorized": False,
                "move_authorized": False,
            }
        )

    return {
        "strategy": strategy,
        "preferred_large_data_base": preferred_large_data_base,
        "preferred_config_base": preferred_config_base,
        "role_recommendations": role_recommendations,
        "requires_manual_review": requires_manual_review,
        "reason": reason,
        "boundaries": [
            "recommendations only",
            "no directory creation",
            "no data movement",
            "no cleanup",
            "no mount or unmount",
            "no formatting or partitioning",
            "no execution authorized",
        ],
    }


def _safe_home_path() -> str | None:
    try:
        return str(Path.home())
    except Exception:
        return None


def build_storage_portability_profile(
    mounts: list[Mapping[str, object]] | None = None,
    home_path: str | None = None,
    env: Mapping[str, str] | None = None,
    platform_system: str | None = None,
    disk_usage_func: Callable[[str], object] | None = None,
) -> dict[str, object]:
    mount_records = mounts if mounts is not None else read_proc_mounts()
    resolved_home_path = home_path if home_path is not None else _safe_home_path()
    resolved_env = os.environ if env is None else env
    resolved_platform_system = platform_system if platform_system is not None else platform.system()
    try:
        cwd = os.getcwd()
    except Exception:
        cwd = None

    candidate_summary = summarize_mount_candidates(
        list(mount_records),
        home_path=resolved_home_path,
        disk_usage_func=disk_usage_func,
    )
    env_paths = collect_bond_environment_paths(resolved_env)
    recommendations = build_storage_recommendations(
        candidate_summary,
        env_paths,
        home_path=resolved_home_path,
    )

    return {
        "profile_kind": STORAGE_PROFILE_KIND,
        "schema_version": STORAGE_PROFILE_SCHEMA_VERSION,
        "platform_system": resolved_platform_system,
        "home_path": resolved_home_path,
        "cwd": cwd,
        "env_paths": env_paths,
        "candidate_summary": candidate_summary,
        "recommendations": recommendations,
        "action_authorized": False,
        "execution_supported": False,
        "directory_creation_supported": False,
        "data_movement_supported": False,
        "cleanup_supported": False,
        "mount_mutation_supported": False,
        "format_or_partition_supported": False,
        "boundaries": [
            "read-only storage profiling only",
            "no directory creation",
            "no data movement",
            "no cleanup",
            "no mount or unmount",
            "no formatting or partitioning",
            "no privileged execution",
            "does not authorize execution",
            "not an installer",
            "not an updater",
            "not a storage mover",
        ],
    }


def build_current_storage_portability_profile() -> dict[str, object]:
    return build_storage_portability_profile(
        mounts=read_proc_mounts(),
        home_path=_safe_home_path(),
        env=os.environ,
        platform_system=platform.system(),
    )