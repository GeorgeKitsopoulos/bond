#!/usr/bin/env python3
import os
import platform
import shutil
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

HOST_PROFILE_KIND = "host_portability_profile"
HOST_PROFILE_SCHEMA_VERSION = 1

STRATEGY_NATIVE_PACKAGE_MANAGER_PLAN_FIRST = "native_package_manager_plan_first"
STRATEGY_ROOTLESS_USER_SPACE_FIRST = "rootless_user_space_first"
STRATEGY_AVOID_HOST_MUTATION = "avoid_host_mutation"
STRATEGY_UNKNOWN_PLAN_FIRST = "unknown_plan_first"

_TOOL_NAMES = (
    "apt",
    "dnf",
    "rpm-ostree",
    "bootc",
    "pacman",
    "zypper",
    "apk",
    "xbps-install",
    "nix",
    "brew",
    "flatpak",
    "podman",
    "distrobox",
    "pipx",
    "git",
    "ujust",
    "systemctl",
    "journalctl",
)

_OS_RELEASE_SIGNAL_KEYS = ("ID", "ID_LIKE", "NAME", "PRETTY_NAME", "VARIANT", "VARIANT_ID")
_SANITIZED_OS_RELEASE_KEYS = (
    "ID",
    "ID_LIKE",
    "NAME",
    "PRETTY_NAME",
    "VARIANT",
    "VARIANT_ID",
    "VERSION_ID",
)


def _strip_matching_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def _as_lower(value: str | None) -> str:
    return (value or "").strip().lower()


def _field_blob(os_release: Mapping[str, str], keys: tuple[str, ...] = _OS_RELEASE_SIGNAL_KEYS) -> str:
    parts: list[str] = []
    for key in keys:
        val = os_release.get(key)
        if isinstance(val, str) and val.strip():
            parts.append(val.strip())
    return " ".join(parts).lower()


def _tool_available(tool_map: Mapping[str, Mapping[str, object]], name: str) -> bool:
    details = tool_map.get(name)
    if not isinstance(details, Mapping):
        return False
    return bool(details.get("available") is True)


def parse_os_release_text(text: str) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        if not key:
            continue

        normalized_value = _strip_matching_quotes(value.strip())
        parsed[str(key)] = str(normalized_value)
    return parsed


def read_os_release(path: str | os.PathLike[str] = "/etc/os-release") -> dict[str, str]:
    try:
        text = Path(path).read_text(encoding="utf-8")
    except Exception:
        return {}
    return parse_os_release_text(text)


def detect_distro_family(os_release: Mapping[str, str], platform_system: str | None = None) -> str:
    distro_id = _as_lower(os_release.get("ID"))
    id_like = _as_lower(os_release.get("ID_LIKE"))
    linux_signal_text = f"{distro_id} {id_like}".strip()

    def has_any(tokens: tuple[str, ...]) -> bool:
        return any(token in linux_signal_text for token in tokens)

    if has_any(("linuxmint", "ubuntu", "debian", " pop", "neon")) or distro_id in {
        "linuxmint",
        "ubuntu",
        "debian",
        "pop",
        "neon",
    }:
        return "debian"

    if has_any(("fedora", "bazzite", "rhel", "centos", "ublue", "silverblue", "kinoite")) or distro_id in {
        "fedora",
        "bazzite",
        "rhel",
        "centos",
        "ublue",
        "silverblue",
        "kinoite",
    }:
        return "fedora"

    if has_any(("arch", "steamos", "manjaro")) or distro_id in {"arch", "steamos", "manjaro"}:
        return "arch"

    if has_any(("opensuse", "suse")) or distro_id in {"opensuse", "suse"}:
        return "opensuse"

    if has_any(("alpine",)) or distro_id == "alpine":
        return "alpine"

    if has_any(("void",)) or distro_id == "void":
        return "void"

    if has_any(("nixos", "nix")) or distro_id in {"nixos", "nix"}:
        return "nix"

    if _as_lower(platform_system) == "darwin":
        return "macos"

    return "unknown"


def detect_package_manager_tools(
    which_func: Callable[[str], str | None] | None = None,
) -> dict[str, dict[str, object]]:
    checker = which_func or shutil.which
    tool_map: dict[str, dict[str, object]] = {}
    for name in _TOOL_NAMES:
        path = checker(name)
        tool_map[name] = {
            "available": path is not None,
            "path": path,
        }
    return tool_map


def detect_service_backends(tool_map: Mapping[str, Mapping[str, object]]) -> dict[str, object]:
    systemctl_available = _tool_available(tool_map, "systemctl")
    return {
        "systemd_user_possible": systemctl_available,
        "foreground_supported": True,
        "none_supported": True,
        "preferred_initial_backend": "systemd-user" if systemctl_available else "foreground",
        "boundaries": [
            "this does not create services",
            "this does not enable services",
            "this does not disable services",
            "this does not restart services",
            "this does not mutate services",
        ],
    }


def detect_host_platform_signals(
    os_release: Mapping[str, str],
    hardware_text: str = "",
    tool_map: Mapping[str, Mapping[str, object]] | None = None,
    platform_system: str | None = None,
) -> dict[str, object]:
    del platform_system
    normalized_tools = dict(tool_map or {})
    signal_text = _field_blob(os_release)
    hardware_lower = (hardware_text or "").lower()

    is_bazzite_like = "bazzite" in signal_text
    is_steamos_like = ("steamos" in signal_text) or ("steam os" in signal_text)
    is_steam_deck_hardware_signal = any(
        token in hardware_lower for token in ("steam deck", "jupiter", "galileo", "valve")
    )
    is_steam_deck_like = is_steam_deck_hardware_signal or is_steamos_like or ("deck" in signal_text)

    distro_family = detect_distro_family(os_release)
    atomic_terms = (
        "silverblue",
        "kinoite",
        "atomic",
        "ostree",
        "bazzite",
        "ublue",
        "universal blue",
        "image-based",
    )
    atomic_signal = any(term in signal_text for term in atomic_terms)
    has_rpm_ostree = _tool_available(normalized_tools, "rpm-ostree")
    has_bootc = _tool_available(normalized_tools, "bootc")

    is_fedora_atomic_like = (
        (distro_family == "fedora" and (has_rpm_ostree or has_bootc)) or atomic_signal
    )
    is_atomic_or_image_based_like = (
        is_fedora_atomic_like or has_rpm_ostree or has_bootc or atomic_signal
    )

    return {
        "is_bazzite_like": is_bazzite_like,
        "is_steamos_like": is_steamos_like,
        "is_steam_deck_hardware_signal": is_steam_deck_hardware_signal,
        "is_steam_deck_like": is_steam_deck_like,
        "is_fedora_atomic_like": is_fedora_atomic_like,
        "is_atomic_or_image_based_like": is_atomic_or_image_based_like,
        "confidence": "signals_only",
        "boundaries": [
            "conservative detection only",
            "signals are not proof that host mutation is safe",
        ],
    }


def choose_dependency_strategy(
    distro_family: str,
    platform_signals: Mapping[str, object],
    tool_map: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    strategy = STRATEGY_UNKNOWN_PLAN_FIRST
    native_package_manager: str | None = None
    prefer_rootless = True
    requires_opt_in = True
    avoid_blind = True
    reason = "unknown_or_unsupported_host"

    if bool(platform_signals.get("is_steamos_like") is True):
        strategy = STRATEGY_AVOID_HOST_MUTATION
        native_package_manager = "pacman" if _tool_available(tool_map, "pacman") else None
        prefer_rootless = True
        requires_opt_in = True
        avoid_blind = True
        reason = "steamos_like_host"
    elif bool(platform_signals.get("is_atomic_or_image_based_like") is True):
        strategy = STRATEGY_ROOTLESS_USER_SPACE_FIRST
        if _tool_available(tool_map, "rpm-ostree"):
            native_package_manager = "rpm-ostree"
        elif _tool_available(tool_map, "bootc"):
            native_package_manager = "bootc"
        else:
            native_package_manager = None
        prefer_rootless = True
        requires_opt_in = True
        avoid_blind = True
        reason = "atomic_or_image_based_host"
    elif distro_family == "debian" and _tool_available(tool_map, "apt"):
        strategy = STRATEGY_NATIVE_PACKAGE_MANAGER_PLAN_FIRST
        native_package_manager = "apt"
        prefer_rootless = False
        requires_opt_in = False
        avoid_blind = True
        reason = "debian_family_apt_available"
    elif distro_family == "fedora" and _tool_available(tool_map, "dnf"):
        strategy = STRATEGY_NATIVE_PACKAGE_MANAGER_PLAN_FIRST
        native_package_manager = "dnf"
        prefer_rootless = False
        requires_opt_in = False
        avoid_blind = True
        reason = "fedora_family_dnf_available"
    elif distro_family == "arch" and _tool_available(tool_map, "pacman"):
        strategy = STRATEGY_NATIVE_PACKAGE_MANAGER_PLAN_FIRST
        native_package_manager = "pacman"
        prefer_rootless = False
        requires_opt_in = False
        avoid_blind = True
        reason = "arch_family_pacman_available"
    elif distro_family == "opensuse" and _tool_available(tool_map, "zypper"):
        strategy = STRATEGY_NATIVE_PACKAGE_MANAGER_PLAN_FIRST
        native_package_manager = "zypper"
        prefer_rootless = False
        requires_opt_in = False
        avoid_blind = True
        reason = "opensuse_family_zypper_available"
    elif distro_family == "alpine" and _tool_available(tool_map, "apk"):
        strategy = STRATEGY_NATIVE_PACKAGE_MANAGER_PLAN_FIRST
        native_package_manager = "apk"
        prefer_rootless = False
        requires_opt_in = False
        avoid_blind = True
        reason = "alpine_family_apk_available"
    elif distro_family == "void" and _tool_available(tool_map, "xbps-install"):
        strategy = STRATEGY_NATIVE_PACKAGE_MANAGER_PLAN_FIRST
        native_package_manager = "xbps-install"
        prefer_rootless = False
        requires_opt_in = False
        avoid_blind = True
        reason = "void_family_xbps_available"
    elif distro_family == "nix" and _tool_available(tool_map, "nix"):
        strategy = STRATEGY_NATIVE_PACKAGE_MANAGER_PLAN_FIRST
        native_package_manager = "nix"
        prefer_rootless = False
        requires_opt_in = False
        avoid_blind = True
        reason = "nix_family_nix_available"

    return {
        "strategy": strategy,
        "native_package_manager": native_package_manager,
        "prefer_rootless_container_or_user_space": prefer_rootless,
        "host_layering_requires_explicit_opt_in": requires_opt_in,
        "avoid_blind_host_mutation": avoid_blind,
        "reason": reason,
        "boundaries": [
            "plan-first only",
            "no package installation in this stage",
            "no system update in this stage",
            "no package layering in this stage",
            "no service mutation in this stage",
            "explicit authorization would be required in a future execution stage",
        ],
    }


def build_host_portability_profile(
    os_release: Mapping[str, str] | None = None,
    tool_map: Mapping[str, Mapping[str, object]] | None = None,
    hardware_text: str = "",
    platform_system: str | None = None,
    platform_machine: str | None = None,
    python_version: str | None = None,
) -> dict[str, object]:
    resolved_os_release = dict(os_release if os_release is not None else read_os_release())
    resolved_tool_map = dict(tool_map if tool_map is not None else detect_package_manager_tools())
    resolved_platform_system = platform_system if platform_system is not None else platform.system()
    resolved_platform_machine = platform_machine if platform_machine is not None else platform.machine()
    resolved_python_version = python_version if python_version is not None else platform.python_version()

    sanitized_os_release: dict[str, str] = {}
    for key in _SANITIZED_OS_RELEASE_KEYS:
        value = resolved_os_release.get(key)
        if isinstance(value, str):
            sanitized_os_release[key] = value

    distro_family = detect_distro_family(
        sanitized_os_release,
        platform_system=resolved_platform_system,
    )
    platform_signals = detect_host_platform_signals(
        sanitized_os_release,
        hardware_text=hardware_text,
        tool_map=resolved_tool_map,
        platform_system=resolved_platform_system,
    )
    dependency_strategy = choose_dependency_strategy(
        distro_family,
        platform_signals,
        resolved_tool_map,
    )
    service_backends = detect_service_backends(resolved_tool_map)

    return {
        "profile_kind": HOST_PROFILE_KIND,
        "schema_version": HOST_PROFILE_SCHEMA_VERSION,
        "platform_system": resolved_platform_system,
        "platform_machine": resolved_platform_machine,
        "python_version": resolved_python_version,
        "os_release": sanitized_os_release,
        "distro_family": distro_family,
        "tools": resolved_tool_map,
        "platform_signals": platform_signals,
        "dependency_strategy": dependency_strategy,
        "service_backends": service_backends,
        "action_authorized": False,
        "execution_supported": False,
        "package_install_supported": False,
        "host_mutation_supported": False,
        "boundaries": [
            "read-only host profiling only",
            "no package installation",
            "no system updates",
            "no package layering",
            "no service mutation",
            "no privileged execution",
            "does not authorize execution",
            "not an installer",
            "not an updater",
        ],
    }


def _read_optional_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8").strip()
    except Exception:
        return ""


def build_current_host_portability_profile() -> dict[str, object]:
    os_release = read_os_release()
    hardware_parts: list[str] = []
    for raw_path in (
        "/sys/devices/virtual/dmi/id/product_name",
        "/sys/devices/virtual/dmi/id/board_name",
        "/sys/devices/virtual/dmi/id/sys_vendor",
    ):
        text = _read_optional_text(Path(raw_path))
        if text:
            hardware_parts.append(text)

    hardware_text = "\n".join(hardware_parts)
    return build_host_portability_profile(
        os_release=os_release,
        hardware_text=hardware_text,
    )
