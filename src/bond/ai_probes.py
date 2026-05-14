#!/usr/bin/env python3
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from ai_host_profile import build_current_host_portability_profile
from ai_install_manifest import build_install_manifest, compare_install_manifest
from ai_storage_profile import build_current_storage_portability_profile
from ai_core import BOND_ROOT, CONFIG_FILE, get_memory_root, get_router_config_path, get_state_root
from ai_probe_contract import (
    CERTAINTY_AUTHORITATIVE,
    CERTAINTY_DERIVED,
    CERTAINTY_UNKNOWN,
    REFRESH_HIGH_CHURN,
    REFRESH_LOW_CHURN,
    REFRESH_MEDIUM_CHURN,
    SOURCE_CONFIG,
    SOURCE_OS_API,
    SOURCE_RUNTIME_PROBE,
    ProbeResult,
    probe_error,
    probe_ok,
    standard_error,
)

AVAILABLE_PROBES = (
    "host_baseline",
    "host_portability_profile",
    "storage_portability_profile",
    "install_manifest_drift",
    "session_baseline",
    "tool_inventory",
    "router_config_models",
    "ollama_model_inventory",
    "model_truth",
    "package_update_status",
    "storage_hygiene",
    "boot_service_health",
)


def list_probe_names() -> list[str]:
    return list(AVAILABLE_PROBES)


def probe_host_baseline() -> ProbeResult:
    return probe_ok(
        probe_name="host_baseline",
        layer=0,
        source_type=SOURCE_OS_API,
        certainty_class=CERTAINTY_AUTHORITATIVE,
        refresh_class=REFRESH_LOW_CHURN,
        supports_live_truth=True,
        data={
            "platform_system": platform.system(),
            "platform_release": platform.release(),
            "platform_machine": platform.machine(),
            "python_version": platform.python_version(),
            "bond_root": str(BOND_ROOT),
            "config_file": str(CONFIG_FILE),
            "memory_root": str(get_memory_root()),
            "state_root": str(get_state_root()),
        },
    )


def probe_host_portability_profile() -> ProbeResult:
    return probe_ok(
        probe_name="host_portability_profile",
        layer=0,
        source_type=SOURCE_OS_API,
        certainty_class=CERTAINTY_DERIVED,
        refresh_class=REFRESH_LOW_CHURN,
        supports_live_truth=True,
        data=build_current_host_portability_profile(),
        notes="Read-only host portability profile for future installer/updater/satellite planning; it does not authorize host mutation.",
    )


def probe_storage_portability_profile() -> ProbeResult:
    return probe_ok(
        probe_name="storage_portability_profile",
        layer=0,
        source_type=SOURCE_OS_API,
        certainty_class=CERTAINTY_DERIVED,
        refresh_class=REFRESH_LOW_CHURN,
        supports_live_truth=True,
        data=build_current_storage_portability_profile(),
        notes="Read-only storage portability profile for future installer/updater/satellite planning; it does not authorize directory creation, cleanup, data movement, or mount mutation.",
    )


def probe_install_manifest_drift() -> ProbeResult:
    host_result = probe_host_portability_profile()
    storage_result = probe_storage_portability_profile()
    host_profile = host_result.data if host_result.ok else {}
    storage_profile = storage_result.data if storage_result.ok else {}
    current_manifest = build_install_manifest(
        host_profile=host_profile,
        storage_profile=storage_profile,
        bond_root=str(BOND_ROOT),
        repo_commit=None,
        python_version=platform.python_version(),
        env_paths=storage_profile.get("env_paths") if isinstance(storage_profile, dict) else None,
        service_backend=(
            storage_profile.get("service_backend")
            if isinstance(storage_profile, dict)
            else None
        ),
        created_at=None,
    )
    report = compare_install_manifest(None, current_manifest)
    return probe_ok(
        probe_name="install_manifest_drift",
        layer=1,
        source_type=SOURCE_RUNTIME_PROBE,
        certainty_class=CERTAINTY_DERIVED,
        refresh_class=REFRESH_LOW_CHURN,
        supports_live_truth=True,
        data=report,
        notes="Read-only install manifest drift probe; no saved manifest persistence exists in this stage, so default output requires manual review before any future reconfiguration.",
    )


def probe_session_baseline() -> ProbeResult:
    display = os.environ.get("DISPLAY", "")
    wayland_display = os.environ.get("WAYLAND_DISPLAY", "")
    dbus_session_bus = os.environ.get("DBUS_SESSION_BUS_ADDRESS", "")
    return probe_ok(
        probe_name="session_baseline",
        layer=0,
        source_type=SOURCE_OS_API,
        certainty_class=CERTAINTY_AUTHORITATIVE,
        refresh_class=REFRESH_LOW_CHURN,
        supports_live_truth=True,
        data={
            "xdg_current_desktop": os.environ.get("XDG_CURRENT_DESKTOP", ""),
            "desktop_session": os.environ.get("DESKTOP_SESSION", ""),
            "xdg_session_type": os.environ.get("XDG_SESSION_TYPE", ""),
            "has_display": bool(display),
            "has_wayland_display": bool(wayland_display),
            "has_dbus_session_bus": bool(dbus_session_bus),
        },
    )


def probe_tool_inventory() -> ProbeResult:
    names = [
        "python3",
        "xdg-open",
        "gio",
        "xdg-mime",
        "xdg-settings",
        "notify-send",
        "gsettings",
        "systemctl",
        "journalctl",
        "flatpak",
        "snap",
        "apt",
        "ollama",
        "nemo",
        "xed",
        "firefox",
    ]
    tools = {}
    for name in names:
        path = shutil.which(name)
        tools[name] = {
            "available": path is not None,
            "path": path,
        }
    return probe_ok(
        probe_name="tool_inventory",
        layer=1,
        source_type=SOURCE_OS_API,
        certainty_class=CERTAINTY_AUTHORITATIVE,
        refresh_class=REFRESH_MEDIUM_CHURN,
        supports_live_truth=True,
        data={"tools": tools},
    )


def probe_router_config_models() -> ProbeResult:
    router_config_path = get_router_config_path()
    try:
        payload = json.loads(router_config_path.read_text(encoding="utf-8"))
        profiles_node = payload.get("profiles", {})
        if not isinstance(profiles_node, dict):
            raise ValueError("profiles must be a mapping")
        profiles: dict[str, str] = {}
        configured_models: set[str] = set()
        for name, entry in profiles_node.items():
            if not isinstance(name, str):
                continue
            if not isinstance(entry, dict):
                continue
            model = entry.get("model")
            if not isinstance(model, str) or not model.strip():
                continue
            profiles[name] = model
            configured_models.add(model)
        return probe_ok(
            probe_name="router_config_models",
            layer=2,
            source_type=SOURCE_CONFIG,
            certainty_class=CERTAINTY_DERIVED,
            refresh_class=REFRESH_LOW_CHURN,
            supports_live_truth=True,
            data={
                "profiles": profiles,
                "configured_models": sorted(configured_models),
                "router_config_path": str(router_config_path),
            },
        )
    except Exception as exc:
        return probe_error(
            probe_name="router_config_models",
            layer=2,
            source_type=SOURCE_CONFIG,
            certainty_class=CERTAINTY_DERIVED,
            refresh_class=REFRESH_LOW_CHURN,
            supports_live_truth=True,
            data={
                "profiles": {},
                "configured_models": [],
                "router_config_path": str(router_config_path),
            },
            error=standard_error("router_config_error", str(exc)),
        )


def probe_ollama_model_inventory() -> ProbeResult:
    ollama_path = shutil.which("ollama")
    base_data = {
        "installed_models": [],
        "raw_line_count": 0,
        "ollama_path": ollama_path,
    }
    if not ollama_path:
        return probe_error(
            probe_name="ollama_model_inventory",
            layer=1,
            source_type=SOURCE_RUNTIME_PROBE,
            certainty_class=CERTAINTY_UNKNOWN,
            refresh_class=REFRESH_HIGH_CHURN,
            supports_live_truth=True,
            data=base_data,
            error=standard_error("tool_missing", "ollama is not installed on this system"),
        )

    try:
        proc = subprocess.run(
            ["ollama", "list"],
            text=True,
            capture_output=True,
            timeout=3,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return probe_error(
            probe_name="ollama_model_inventory",
            layer=1,
            source_type=SOURCE_RUNTIME_PROBE,
            certainty_class=CERTAINTY_UNKNOWN,
            refresh_class=REFRESH_HIGH_CHURN,
            supports_live_truth=True,
            data=base_data,
            error=standard_error("timeout", "ollama list timed out", {"timeout_seconds": 3}),
        )
    except Exception as exc:
        return probe_error(
            probe_name="ollama_model_inventory",
            layer=1,
            source_type=SOURCE_RUNTIME_PROBE,
            certainty_class=CERTAINTY_UNKNOWN,
            refresh_class=REFRESH_HIGH_CHURN,
            supports_live_truth=True,
            data=base_data,
            error=standard_error("command_failed", str(exc)),
        )

    stdout_lines = [line for line in (proc.stdout or "").splitlines() if line.strip()]
    if proc.returncode != 0:
        stderr_preview = (proc.stderr or "").strip()[:400]
        return probe_error(
            probe_name="ollama_model_inventory",
            layer=1,
            source_type=SOURCE_RUNTIME_PROBE,
            certainty_class=CERTAINTY_UNKNOWN,
            refresh_class=REFRESH_HIGH_CHURN,
            supports_live_truth=True,
            data={
                **base_data,
                "raw_line_count": len(stdout_lines),
            },
            error=standard_error(
                "command_failed",
                "ollama list returned a non-zero exit code",
                {"returncode": proc.returncode, "stderr_preview": stderr_preview},
            ),
        )

    installed_models: list[str] = []
    for index, line in enumerate(stdout_lines):
        if index == 0:
            continue
        parts = re.split(r"\s{2,}", line.strip())
        if not parts:
            continue
        model_name = parts[0].strip()
        if model_name:
            installed_models.append(model_name)

    return probe_ok(
        probe_name="ollama_model_inventory",
        layer=1,
        source_type=SOURCE_RUNTIME_PROBE,
        certainty_class=CERTAINTY_AUTHORITATIVE,
        refresh_class=REFRESH_HIGH_CHURN,
        supports_live_truth=True,
        data={
            "installed_models": sorted(set(installed_models)),
            "raw_line_count": len(stdout_lines),
            "ollama_path": ollama_path,
        },
        notes="Installed-model inventory is distinct from runtime health or route selection.",
    )


def probe_model_truth() -> ProbeResult:
    router_result = probe_router_config_models()
    inventory_result = probe_ollama_model_inventory()

    configured_models = []
    installed_models = []
    warnings: list[str] = []
    truth_status = "configured_only"

    if router_result.ok:
        configured_models = list(router_result.data.get("configured_models", []))
    else:
        truth_status = "router_config_unavailable"
        warnings.append("Router configuration was unavailable, so model truth is partial.")

    if inventory_result.ok:
        installed_models = list(inventory_result.data.get("installed_models", []))
        if truth_status != "router_config_unavailable":
            truth_status = "configured_and_inventory_checked"
    else:
        if truth_status != "router_config_unavailable":
            truth_status = "configured_only"
        error_kind = "unknown"
        if isinstance(inventory_result.error, dict):
            error_kind = str(inventory_result.error.get("kind", "unknown"))
        warnings.append(
            f"Installed model inventory is unavailable ({error_kind}); configured route targets remain separate from local inventory truth."
        )

    configured_set = set(configured_models)
    installed_set = set(installed_models)
    return probe_ok(
        probe_name="model_truth",
        layer=2,
        source_type=SOURCE_RUNTIME_PROBE,
        certainty_class=CERTAINTY_DERIVED,
        refresh_class=REFRESH_HIGH_CHURN,
        supports_live_truth=True,
        warnings=tuple(warnings),
        data={
            "configured_models": sorted(configured_set),
            "installed_models": sorted(installed_set),
            "inventory_available": inventory_result.ok,
            "missing_configured_models": sorted(configured_set - installed_set) if inventory_result.ok else sorted(configured_set),
            "extra_installed_models": sorted(installed_set - configured_set) if inventory_result.ok else [],
            "truth_status": truth_status,
        },
        notes="Configured route targets and installed local model inventory are separate facts.",
    )


def _run_read_only_command(
    argv: list[str], timeout_seconds: int = 5
) -> tuple[int | None, str, str, str | None]:
    try:
        if not isinstance(argv, list) or any(not isinstance(part, str) for part in argv):
            raise TypeError("argv must be a list of strings")

        normalized = tuple(argv)
        if normalized == ("apt", "list", "--upgradable"):
            proc = subprocess.run(
                ["apt", "list", "--upgradable"],
                text=True,
                capture_output=True,
                timeout=timeout_seconds,
                check=False,
            )
        elif normalized == ("systemctl", "--failed", "--no-legend", "--plain", "--no-pager"):
            proc = subprocess.run(
                ["systemctl", "--failed", "--no-legend", "--plain", "--no-pager"],
                text=True,
                capture_output=True,
                timeout=timeout_seconds,
                check=False,
            )
        elif normalized == (
            "journalctl",
            "-p",
            "warning..alert",
            "-b",
            "-n",
            "20",
            "--no-pager",
            "--output=short",
        ):
            proc = subprocess.run(
                ["journalctl", "-p", "warning..alert", "-b", "-n", "20", "--no-pager", "--output=short"],
                text=True,
                capture_output=True,
                timeout=timeout_seconds,
                check=False,
            )
        else:
            raise ValueError("unsupported read-only command shape")

        return proc.returncode, proc.stdout or "", proc.stderr or "", None
    except subprocess.TimeoutExpired:
        return None, "", "", "timeout"
    except Exception as exc:
        return None, "", str(exc)[:400], "command_failed"


def _preview_lines(text: str, limit: int = 20) -> list[str]:
    lines = [(line or "").strip() for line in (text or "").splitlines()]
    lines = [line for line in lines if line]
    return lines[:limit]


def _disk_usage_record(label: str, path: Path) -> dict[str, object]:
    resolved_path = path.expanduser().resolve(strict=False)
    if not resolved_path.exists():
        return {
            "label": label,
            "path": str(resolved_path),
            "exists": False,
            "total_bytes": None,
            "used_bytes": None,
            "free_bytes": None,
            "free_percent": None,
        }

    usage = shutil.disk_usage(resolved_path)
    return {
        "label": label,
        "path": str(resolved_path),
        "exists": True,
        "total_bytes": usage.total,
        "used_bytes": usage.used,
        "free_bytes": usage.free,
        "free_percent": round((usage.free / usage.total) * 100, 2) if usage.total else None,
    }


def probe_package_update_status() -> ProbeResult:
    apt_path = shutil.which("apt")
    base_data = {
        "package_manager": "apt",
        "apt_path": apt_path,
        "cache_freshness_known": False,
        "upgradable_count": None,
        "upgradable_packages_sample": [],
        "sample_limit": 50,
        "raw_line_count": 0,
    }

    if not apt_path:
        return probe_error(
            probe_name="package_update_status",
            layer=1,
            source_type=SOURCE_RUNTIME_PROBE,
            certainty_class=CERTAINTY_UNKNOWN,
            refresh_class=REFRESH_HIGH_CHURN,
            supports_live_truth=True,
            data=base_data,
            error=standard_error("tool_missing", "apt is not installed on this system"),
        )

    returncode, stdout, stderr, error_kind = _run_read_only_command(
        ["apt", "list", "--upgradable"],
        timeout_seconds=5,
    )

    if error_kind == "timeout":
        return probe_error(
            probe_name="package_update_status",
            layer=1,
            source_type=SOURCE_RUNTIME_PROBE,
            certainty_class=CERTAINTY_UNKNOWN,
            refresh_class=REFRESH_HIGH_CHURN,
            supports_live_truth=True,
            data=base_data,
            error=standard_error(
                "timeout",
                "apt list --upgradable timed out",
                {"timeout_seconds": 5},
            ),
        )

    raw_non_empty_lines = [line for line in (stdout or "").splitlines() if line.strip()]
    if error_kind == "command_failed" or returncode != 0:
        return probe_error(
            probe_name="package_update_status",
            layer=1,
            source_type=SOURCE_RUNTIME_PROBE,
            certainty_class=CERTAINTY_UNKNOWN,
            refresh_class=REFRESH_HIGH_CHURN,
            supports_live_truth=True,
            data={
                **base_data,
                "raw_line_count": len(raw_non_empty_lines),
            },
            error=standard_error(
                "command_failed",
                "apt list --upgradable returned a non-zero exit code",
                {
                    "returncode": returncode,
                    "stderr_preview": (stderr or "")[:400],
                },
            ),
        )

    parsed_packages: list[dict[str, str]] = []
    for raw_line in raw_non_empty_lines:
        stripped = raw_line.strip()
        if stripped.startswith("Listing"):
            continue
        package_name = stripped.split("/", 1)[0].strip()
        parsed_packages.append(
            {
                "name": package_name,
                "raw": stripped,
            }
        )

    return probe_ok(
        probe_name="package_update_status",
        layer=1,
        source_type=SOURCE_RUNTIME_PROBE,
        certainty_class=CERTAINTY_DERIVED,
        refresh_class=REFRESH_HIGH_CHURN,
        supports_live_truth=True,
        data={
            **base_data,
            "upgradable_count": len(parsed_packages),
            "upgradable_packages_sample": parsed_packages[:50],
            "raw_line_count": len(raw_non_empty_lines),
        },
        notes="Read-only apt cache inspection only; cache freshness is unknown because this probe does not run apt update.",
    )


def probe_storage_hygiene() -> ProbeResult:
    return probe_ok(
        probe_name="storage_hygiene",
        layer=1,
        source_type=SOURCE_OS_API,
        certainty_class=CERTAINTY_AUTHORITATIVE,
        refresh_class=REFRESH_HIGH_CHURN,
        supports_live_truth=True,
        data={
            "paths": [
                _disk_usage_record("root", Path("/")),
                _disk_usage_record("home", Path.home()),
                _disk_usage_record("bond_root", BOND_ROOT),
                _disk_usage_record("state_root", get_state_root()),
                _disk_usage_record("memory_root", get_memory_root()),
            ],
            "scope": "bounded_disk_usage_only",
        },
        notes="Storage hygiene probe is read-only and bounded to disk-usage signals; it does not scan duplicates, delete files, or clean caches.",
    )


def probe_boot_service_health() -> ProbeResult:
    systemctl_path = shutil.which("systemctl")
    journalctl_path = shutil.which("journalctl")

    data: dict[str, Any] = {
        "systemctl_path": systemctl_path,
        "journalctl_path": journalctl_path,
        "failed_units_count": None,
        "failed_units_sample": [],
        "journal_warning_sample": [],
        "journal_warning_sample_count": None,
        "systemctl_available": bool(systemctl_path),
        "journalctl_available": bool(journalctl_path),
        "systemctl_error_kind": None,
        "journalctl_error_kind": None,
    }

    systemctl_ok = False
    journalctl_ok = False

    if systemctl_path:
        returncode, stdout, _stderr, error_kind = _run_read_only_command(
            ["systemctl", "--failed", "--no-legend", "--plain", "--no-pager"],
            timeout_seconds=5,
        )
        if error_kind is None and returncode == 0:
            failed_units: list[dict[str, str]] = []
            for line in _preview_lines(stdout, limit=1000):
                parts = line.split(None, 4)
                failed_units.append(
                    {
                        "unit": parts[0] if len(parts) > 0 else "",
                        "load": parts[1] if len(parts) > 1 else "",
                        "active": parts[2] if len(parts) > 2 else "",
                        "sub": parts[3] if len(parts) > 3 else "",
                        "description": parts[4] if len(parts) > 4 else "",
                    }
                )
            data["failed_units_count"] = len(failed_units)
            data["failed_units_sample"] = failed_units[:25]
            systemctl_ok = True
        else:
            data["systemctl_error_kind"] = error_kind if error_kind else "command_failed"
    else:
        data["systemctl_error_kind"] = "tool_missing"

    if journalctl_path:
        returncode, stdout, _stderr, error_kind = _run_read_only_command(
            ["journalctl", "-p", "warning..alert", "-b", "-n", "20", "--no-pager", "--output=short"],
            timeout_seconds=5,
        )
        if error_kind is None and returncode == 0:
            journal_lines = _preview_lines(stdout, limit=20)
            data["journal_warning_sample"] = journal_lines
            data["journal_warning_sample_count"] = len(journal_lines)
            journalctl_ok = True
        else:
            data["journalctl_error_kind"] = error_kind if error_kind else "command_failed"
    else:
        data["journalctl_error_kind"] = "tool_missing"

    if not systemctl_ok and not journalctl_ok:
        return probe_error(
            probe_name="boot_service_health",
            layer=1,
            source_type=SOURCE_RUNTIME_PROBE,
            certainty_class=CERTAINTY_UNKNOWN,
            refresh_class=REFRESH_HIGH_CHURN,
            supports_live_truth=True,
            data=data,
            error=standard_error(
                "maintenance_probe_unavailable",
                "boot/service health signals are unavailable in this run",
            ),
        )

    warnings: list[str] = []
    if not systemctl_ok:
        warnings.append(
            f"systemctl failed-unit signal unavailable: {data['systemctl_error_kind']}"
        )
    if not journalctl_ok:
        warnings.append(
            f"journalctl boot-warning signal unavailable: {data['journalctl_error_kind']}"
        )

    return probe_ok(
        probe_name="boot_service_health",
        layer=1,
        source_type=SOURCE_RUNTIME_PROBE,
        certainty_class=CERTAINTY_DERIVED,
        refresh_class=REFRESH_HIGH_CHURN,
        supports_live_truth=True,
        data=data,
        warnings=tuple(warnings),
        notes="Boot/service health probe is read-only and bounded; it reports failed-unit and recent boot-warning signals only.",
    )


def run_named_probe(name: str) -> ProbeResult:
    if name == "all":
        return probe_error(
            probe_name="all",
            layer=2,
            source_type=SOURCE_RUNTIME_PROBE,
            certainty_class=CERTAINTY_UNKNOWN,
            refresh_class=REFRESH_MEDIUM_CHURN,
            supports_live_truth=False,
            data={},
            error=standard_error("unknown_probe", "run_named_probe handles one probe only; use run_all_probes for all probes"),
        )

    dispatch = {
        "host_baseline": probe_host_baseline,
        "host_portability_profile": probe_host_portability_profile,
        "storage_portability_profile": probe_storage_portability_profile,
        "install_manifest_drift": probe_install_manifest_drift,
        "session_baseline": probe_session_baseline,
        "tool_inventory": probe_tool_inventory,
        "router_config_models": probe_router_config_models,
        "ollama_model_inventory": probe_ollama_model_inventory,
        "model_truth": probe_model_truth,
        "package_update_status": probe_package_update_status,
        "storage_hygiene": probe_storage_hygiene,
        "boot_service_health": probe_boot_service_health,
    }
    func = dispatch.get(name)
    if func is None:
        return probe_error(
            probe_name=name,
            layer=2,
            source_type=SOURCE_RUNTIME_PROBE,
            certainty_class=CERTAINTY_UNKNOWN,
            refresh_class=REFRESH_MEDIUM_CHURN,
            supports_live_truth=False,
            data={},
            error=standard_error("unknown_probe", f"unknown probe: {name}"),
        )
    return func()


def run_all_probes() -> list[ProbeResult]:
    return [run_named_probe(name) for name in AVAILABLE_PROBES]