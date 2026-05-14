#!/usr/bin/env python3
"""Pure deterministic package-manager strategy classification contract.

Does not call package managers, inspect live system, or authorize installation.
Accepts facts either directly or from host_profile dictionary.
Direct keyword arguments override host_profile values.
"""

from typing import Any

PACKAGE_MANAGER_SCHEMA_VERSION = 1
PACKAGE_MANAGER_KIND = "bond_package_manager_strategy"


def classify_package_manager_strategy(
    *,
    host_profile: dict[str, Any] | None = None,
    available_tools: list[str] | None = None,
    package_manager: str | None = None,
    os_family: str | None = None,
    distro_id: str | None = None,
    distro_like: str | None = None,
    immutable_hint: bool | None = None,
    steam_deck_hint: bool | None = None,
) -> dict[str, Any]:
    """
    Classify package manager strategy from supplied facts.
    
    Returns a deterministic dictionary with strategy classification.
    Does not inspect live system state, call package managers, or authorize execution.
    
    Args:
        host_profile: Dictionary containing host facts (os_family, distro_id, package_manager, etc).
        available_tools: Explicit supplied list of available tools (not discovered).
        package_manager: Direct package_manager value (overrides host_profile).
        os_family: Direct os_family value (overrides host_profile).
        distro_id: Direct distro_id value (overrides host_profile).
        distro_like: Direct distro_like value (overrides host_profile).
        immutable_hint: Whether to treat host as immutable.
        steam_deck_hint: Whether to treat host as Steam Deck-like.
    
    Returns:
        Dictionary with strategy classification and authorization fields.
    """
    host_profile = host_profile or {}
    available_tools = available_tools or []

    # Resolve values: direct keyword arguments override host_profile
    pm = package_manager or host_profile.get("package_manager")
    os_fam = os_family or host_profile.get("os_family")
    distro_i = distro_id or host_profile.get("distro_id")
    distro_l = distro_like or host_profile.get("distro_like")
    immut_hint = immutable_hint if immutable_hint is not None else host_profile.get("immutable_hint", False)
    steam_hint = steam_deck_hint if steam_deck_hint is not None else host_profile.get("steam_deck_hint", False)

    # Normalize strings
    pm_lower = (pm or "").strip().lower() if pm else ""
    os_fam_lower = (os_fam or "").strip().lower() if os_fam else ""
    distro_i_lower = (distro_i or "").strip().lower() if distro_i else ""
    distro_l_lower = (distro_l or "").strip().lower() if distro_l else ""

    # Determine if Steam Deck-like
    is_steam_deck_like = (
        steam_hint
        or "steamos" in distro_i_lower
        or "bazzite" in distro_i_lower
        or "steamos" in distro_l_lower
        or "bazzite" in distro_l_lower
    )

    # Determine strategy based on package manager
    supported = True
    strategy = "unknown_requires_manual_review"
    preferred_surface = "manual_review"
    requires_review = True
    host_mutation_allowed = False
    notes = ""

    if pm_lower in ("apt", "dnf", "zypper", "apk", "xbps", "nix", "brew"):
        # Standard mutable package managers
        supported = True
        strategy = "mutable_package_manager_plan"
        preferred_surface = "host_package_manager"
        requires_review = immut_hint  # Only if explicitly marked immutable
        host_mutation_allowed = False
        notes = f"Standard mutable package manager {pm_lower} supported"

    elif pm_lower == "rpm-ostree":
        # Immutable rpm-ostree strategy
        supported = True
        strategy = "immutable_host_user_space_preferred"
        preferred_surface = "distrobox_or_user_space"
        requires_review = True
        host_mutation_allowed = False
        notes = "rpm-ostree immutable host requires user-space or container approach"

    elif pm_lower == "pacman":
        # Arch/Pacman - check for Steam Deck or immutable hints
        supported = True
        if is_steam_deck_like or immut_hint:
            strategy = "steam_deck_or_atomic_user_space_preferred"
            preferred_surface = "distrobox_or_user_space"
            requires_review = True
            notes = "Steam Deck or atomic variant requires user-space/container approach"
        else:
            strategy = "mutable_package_manager_plan"
            preferred_surface = "host_package_manager"
            requires_review = False
            notes = "Standard Arch pacman mutable package manager supported"
        host_mutation_allowed = False

    else:
        # Unknown or missing package manager
        supported = False
        strategy = "unknown_requires_manual_review"
        preferred_surface = "manual_review"
        requires_review = True
        host_mutation_allowed = False
        notes = f"Unknown or unsupported package manager: {pm_lower or '(empty)'}"

    # If immutable_hint is true for any package manager, enforce stricter settings
    if immut_hint and strategy != "unknown_requires_manual_review":
        host_mutation_allowed = False
        requires_review = True
        if strategy not in ("immutable_host_user_space_preferred", "steam_deck_or_atomic_user_space_preferred"):
            strategy = "immutable_host_user_space_preferred"
            preferred_surface = "distrobox_or_user_space"

    return {
        "kind": PACKAGE_MANAGER_KIND,
        "schema_version": PACKAGE_MANAGER_SCHEMA_VERSION,
        "execution_authorized": False,
        "install_authorized": False,
        "package_manager": pm_lower or "(unknown)",
        "os_family": os_fam_lower or "(unknown)",
        "distro_id": distro_i_lower or "(unknown)",
        "distro_like": distro_l_lower or "(unknown)",
        "immutable_hint": bool(immut_hint),
        "steam_deck_hint": bool(is_steam_deck_like),
        "strategy_kind": strategy,
        "host_mutation_default_allowed": host_mutation_allowed,
        "requires_manual_review": requires_review,
        "supported_package_manager": supported,
        "preferred_install_surface": preferred_surface,
        "package_manager_notes": notes,
    }
