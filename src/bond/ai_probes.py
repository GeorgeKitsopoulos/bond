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
    "session_baseline",
    "tool_inventory",
    "router_config_models",
    "ollama_model_inventory",
    "model_truth",
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
        "session_baseline": probe_session_baseline,
        "tool_inventory": probe_tool_inventory,
        "router_config_models": probe_router_config_models,
        "ollama_model_inventory": probe_ollama_model_inventory,
        "model_truth": probe_model_truth,
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