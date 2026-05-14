#!/usr/bin/env python3
"""Pure deterministic dependency planning contract.

Does not call package managers, check networks, execute commands, or authorize installation.
Accepts facts and profiles as explicit inputs only; does not discover or inspect live system.
Returns deterministic in-memory plans.
"""

from typing import Any

from ai_package_manager import classify_package_manager_strategy

DEPENDENCY_PLAN_SCHEMA_VERSION = 1
DEPENDENCY_PLAN_KIND = "bond_dependency_plan"

# Bounded default capabilities
_DEFAULT_REQUESTED_CAPABILITIES = (
    "core_python_runtime",
    "git_source_checkout",
    "selftest_validation",
    "local_llm_runtime_optional",
    "container_user_space_optional",
)

# Capability mapping to package names by manager
_CAPABILITY_PACKAGES = {
    "core_python_runtime": {
        "requirement_kind": "runtime",
        "package_names_by_manager": {
            "apt": ["python3"],
            "dnf": ["python3"],
            "zypper": ["python3"],
            "pacman": ["python"],
            "apk": ["python3"],
            "xbps": ["python3"],
            "nix": ["python3"],
            "brew": ["python"],
        },
    },
    "git_source_checkout": {
        "requirement_kind": "source_control",
        "package_names_by_manager": {
            "apt": ["git"],
            "dnf": ["git"],
            "zypper": ["git"],
            "pacman": ["git"],
            "apk": ["git"],
            "xbps": ["git"],
            "nix": ["git"],
            "brew": ["git"],
        },
    },
    "selftest_validation": {
        "requirement_kind": "validation",
        "package_names_by_manager": {
            "apt": ["make"],
            "dnf": ["make"],
            "zypper": ["make"],
            "pacman": ["make"],
            "apk": ["make"],
            "xbps": ["make"],
            "nix": ["make"],
            "brew": ["make"],
        },
        "note": "Python stdlib compile/selftest remains primary; package install not authorized.",
    },
    "local_llm_runtime_optional": {
        "requirement_kind": "optional_runtime",
        "package_names_by_manager": {},
        "note": "Manual installation recommended for Ollama in this stage.",
    },
    "container_user_space_optional": {
        "requirement_kind": "optional_user_space",
        "package_names_by_manager": {
            "apt": ["podman"],
            "dnf": ["podman"],
            "zypper": ["podman"],
            "pacman": ["podman"],
            "apk": ["podman"],
            "xbps": ["podman"],
            "nix": ["podman"],
            "brew": [],
        },
    },
}


def build_dependency_plan(
    *,
    package_strategy: dict[str, Any] | None = None,
    host_profile: dict[str, Any] | None = None,
    install_manifest: dict[str, Any] | None = None,
    requested_capabilities: tuple[str, ...] | None = None,
    observed_tools: dict[str, Any] | None = None,
    python_version: str | None = None,
    bond_root: str | None = None,
) -> dict[str, Any]:
    """
    Build a deterministic dependency plan from supplied facts.
    
    Returns an in-memory plan with no execution authorization.
    Does not inspect live system, call package managers, or persist to disk.
    
    Args:
        package_strategy: Pre-computed package strategy dict. If missing, computed from host_profile.
        host_profile: Host portability profile facts.
        install_manifest: Install manifest (informational, not used for installation).
        requested_capabilities: Tuple of capability names. Defaults to _DEFAULT_REQUESTED_CAPABILITIES.
        observed_tools: Explicit supplied dict of available tools. Does not discover tools.
        python_version: Python version string (informational).
        bond_root: Bond root path (informational).
    
    Returns:
        Dictionary with dependency plan and authorization fields set to False.
    """
    host_profile = host_profile or {}
    observed_tools = observed_tools or {}
    requested_capabilities = requested_capabilities or _DEFAULT_REQUESTED_CAPABILITIES

    # Get or compute package strategy
    if package_strategy is None:
        package_strategy = classify_package_manager_strategy(host_profile=host_profile)

    # Determine observed tool availability
    observed_python3 = (
        observed_tools.get("python3", {}).get("available")
        or observed_tools.get("python", {}).get("available")
    ) is True
    observed_git = observed_tools.get("git", {}).get("available") is True
    observed_make = observed_tools.get("make", {}).get("available") is True
    observed_podman = observed_tools.get("podman", {}).get("available") is True

    # Build plan items
    plan_items = []
    pkg_manager = package_strategy.get("package_manager", "(unknown)")

    # Determine if this is a manual-review strategy (immutable, steam deck, unknown, etc.)
    is_manual_review_strategy = (
        package_strategy.get("strategy_kind") in (
            "immutable_host_user_space_preferred",
            "steam_deck_or_atomic_user_space_preferred",
            "unknown_requires_manual_review",
        )
        or not package_strategy.get("supported_package_manager", False)
        or bool(package_strategy.get("requires_manual_review"))
    )

    for cap in requested_capabilities:
        cap_info = _CAPABILITY_PACKAGES.get(cap, {})
        req_kind = cap_info.get("requirement_kind", "unknown")

        # Determine status for this capability
        if cap == "core_python_runtime":
            if observed_python3:
                status = "observed_available"
            elif not is_manual_review_strategy:
                status = "plan_needed"
            else:
                status = "manual_review_needed"

        elif cap == "git_source_checkout":
            if observed_git:
                status = "observed_available"
            elif not is_manual_review_strategy:
                status = "plan_needed"
            else:
                status = "manual_review_needed"

        elif cap == "selftest_validation":
            if observed_make:
                status = "observed_available"
            elif not is_manual_review_strategy:
                status = "plan_needed"
            else:
                status = "manual_review_needed"

        elif cap == "local_llm_runtime_optional":
            # Optional: no installation claimed for Ollama
            status = "optional_not_required"

        elif cap == "container_user_space_optional":
            # Optional container support
            if package_strategy.get("strategy_kind") in (
                "immutable_host_user_space_preferred",
                "steam_deck_or_atomic_user_space_preferred",
            ):
                status = "plan_needed"  # Recommended for immutable hosts
            elif observed_podman:
                status = "observed_available"
            else:
                status = "optional_not_required"

        else:
            status = "manual_review_needed"

        # Build package names for this capability
        pkg_names_by_mgr = {}
        if status == "plan_needed" and not is_manual_review_strategy:
            cap_packages = cap_info.get("package_names_by_manager", {})
            if pkg_manager in cap_packages:
                pkg_names_by_mgr = {pkg_manager: cap_packages[pkg_manager]}

        # Determine if manual review is needed
        plan_requires_review = (
            status == "manual_review_needed"
            or package_strategy.get("requires_manual_review")
        )

        # Determine preferred surface
        if status == "observed_available":
            preferred_surf = "already_available"
        elif status == "optional_not_required":
            preferred_surf = "not_required"
        else:
            preferred_surf = package_strategy.get("preferred_install_surface", "manual_review")

        item = {
            "capability": cap,
            "status": status,
            "requirement_kind": req_kind,
            "package_names_by_manager": pkg_names_by_mgr,
            "preferred_surface": preferred_surf,
            "requires_manual_review": plan_requires_review,
            "note": cap_info.get("note", ""),
        }
        plan_items.append(item)

    # Determine recommended next step
    if any(item["status"] == "manual_review_needed" for item in plan_items):
        recommended_next = "manual_dependency_review"
    elif any(item["status"] == "plan_needed" for item in plan_items):
        recommended_next = "review_dependency_plan"
    else:
        recommended_next = "none"

    # Build observed tools summary
    observed_summary = {
        "python3_or_python": observed_python3,
        "git": observed_git,
        "make": observed_make,
        "podman": observed_podman,
        "supplied_tools_count": len(observed_tools),
    }

    return {
        "kind": DEPENDENCY_PLAN_KIND,
        "schema_version": DEPENDENCY_PLAN_SCHEMA_VERSION,
        "execution_authorized": False,
        "install_authorized": False,
        "upgrade_authorized": False,
        "service_authorized": False,
        "write_plan_authorized": False,
        "commands_generated": False,
        "package_strategy": package_strategy,
        "requested_capabilities": list(requested_capabilities),
        "observed_tools_summary": observed_summary,
        "plan_items": plan_items,
        "requires_manual_review": (
            any(item["requires_manual_review"] for item in plan_items)
            or bool(package_strategy.get("requires_manual_review"))
        ),
        "recommended_next_step_kind": recommended_next,
        "plan_notes": "Read-only plan; does not authorize installation or execution.",
    }
