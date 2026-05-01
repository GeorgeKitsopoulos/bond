from __future__ import annotations

from dataclasses import dataclass, field

STATUS_AVAILABLE = "available"
STATUS_PARTIAL = "partial"
STATUS_PLANNED = "planned"
STATUS_BLOCKED = "blocked"
STATUS_UNSUPPORTED = "unsupported"

CLASS_INSPECTOR = "inspector"
CLASS_HANDOFF = "handoff"
CLASS_BOUNDED_MUTATOR = "bounded_mutator"
CLASS_PRIVILEGED_LANE = "privileged_lane"

EXECUTION_DETERMINISTIC_PROBE = "deterministic_probe"
EXECUTION_GUARDED_ACTION = "guarded_action"
EXECUTION_HANDOFF = "handoff"
EXECUTION_NONE = "none"

RISK_LOW = "low"
RISK_MEDIUM = "medium"
RISK_HIGH = "high"
RISK_NA = "n/a"

VALID_STATUSES = frozenset(
    {
        STATUS_AVAILABLE,
        STATUS_PARTIAL,
        STATUS_PLANNED,
        STATUS_BLOCKED,
        STATUS_UNSUPPORTED,
    }
)
VALID_CLASSES = frozenset(
    {
        CLASS_INSPECTOR,
        CLASS_HANDOFF,
        CLASS_BOUNDED_MUTATOR,
        CLASS_PRIVILEGED_LANE,
    }
)
VALID_EXECUTION_MODES = frozenset(
    {
        EXECUTION_DETERMINISTIC_PROBE,
        EXECUTION_GUARDED_ACTION,
        EXECUTION_HANDOFF,
        EXECUTION_NONE,
    }
)
VALID_RISK_LEVELS = frozenset({RISK_LOW, RISK_MEDIUM, RISK_HIGH, RISK_NA})

CURRENTLY_USABLE_STATUSES = frozenset({STATUS_AVAILABLE, STATUS_PARTIAL})


@dataclass(frozen=True)
class Capability:
    name: str
    capability_class: str
    status: str
    execution_mode: str
    risk_level: str
    read_only: bool | None = None
    rootless: bool | None = None
    side_effects: tuple[str, ...] = ()
    requires_confirmation: bool = False
    interactive: bool = False
    needs_gui_session: bool = False
    needs_network: bool = False
    needs_elevated_lane: bool = False
    backends: dict[str, tuple[str, ...]] = field(default_factory=dict)
    degraded_modes: tuple[str, ...] = ()
    result_schema: str = ""
    error_schema: str = ""
    audit_tag: str = ""
    required_tools: tuple[str, ...] = ()
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "class": self.capability_class,
            "status": self.status,
            "execution_mode": self.execution_mode,
            "risk_level": self.risk_level,
            "read_only": self.read_only,
            "rootless": self.rootless,
            "side_effects": list(self.side_effects),
            "requires_confirmation": self.requires_confirmation,
            "interactive": self.interactive,
            "needs_gui_session": self.needs_gui_session,
            "needs_network": self.needs_network,
            "needs_elevated_lane": self.needs_elevated_lane,
            "backends": {key: list(value) for key, value in self.backends.items()},
            "degraded_modes": list(self.degraded_modes),
            "result_schema": self.result_schema,
            "error_schema": self.error_schema,
            "audit_tag": self.audit_tag,
            "required_tools": list(self.required_tools),
            "notes": self.notes,
        }


def _cap(
    *,
    name: str,
    capability_class: str,
    status: str,
    execution_mode: str,
    risk_level: str,
    read_only: bool | None = None,
    rootless: bool | None = None,
    side_effects: tuple[str, ...] = (),
    requires_confirmation: bool = False,
    interactive: bool = False,
    needs_gui_session: bool = False,
    needs_network: bool = False,
    needs_elevated_lane: bool = False,
    backends: dict[str, tuple[str, ...]] | None = None,
    degraded_modes: tuple[str, ...] = (),
    result_schema: str = "",
    error_schema: str = "",
    audit_tag: str = "",
    required_tools: tuple[str, ...] = (),
    notes: str = "",
) -> Capability:
    if not isinstance(name, str) or not name.strip():
        raise ValueError("name must be non-empty")
    if capability_class not in VALID_CLASSES:
        raise ValueError(f"invalid capability class: {capability_class}")
    if status not in VALID_STATUSES:
        raise ValueError(f"invalid status: {status}")
    if execution_mode not in VALID_EXECUTION_MODES:
        raise ValueError(f"invalid execution mode: {execution_mode}")
    if risk_level not in VALID_RISK_LEVELS:
        raise ValueError(f"invalid risk level: {risk_level}")
    if needs_elevated_lane and capability_class != CLASS_PRIVILEGED_LANE:
        raise ValueError("needs_elevated_lane requires privileged_lane class")
    if capability_class == CLASS_PRIVILEGED_LANE and risk_level not in {RISK_MEDIUM, RISK_HIGH}:
        raise ValueError("privileged_lane capability risk_level must be medium or high")
    if status == STATUS_UNSUPPORTED and execution_mode != EXECUTION_NONE:
        raise ValueError("unsupported capabilities must have execution_mode none")

    normalized_backends: dict[str, tuple[str, ...]] = {}
    for key, value in (backends or {}).items():
        normalized_backends[str(key)] = tuple(value)

    return Capability(
        name=name.strip(),
        capability_class=capability_class,
        status=status,
        execution_mode=execution_mode,
        risk_level=risk_level,
        read_only=read_only,
        rootless=rootless,
        side_effects=tuple(side_effects),
        requires_confirmation=requires_confirmation,
        interactive=interactive,
        needs_gui_session=needs_gui_session,
        needs_network=needs_network,
        needs_elevated_lane=needs_elevated_lane,
        backends=normalized_backends,
        degraded_modes=tuple(degraded_modes),
        result_schema=result_schema,
        error_schema=error_schema,
        audit_tag=audit_tag,
        required_tools=tuple(required_tools),
        notes=notes,
    )


_REGISTRY_ENTRIES: tuple[Capability, ...] = (
    _cap(
        name="open_known_target",
        capability_class=CLASS_HANDOFF,
        status=STATUS_PARTIAL,
        execution_mode=EXECUTION_GUARDED_ACTION,
        risk_level=RISK_LOW,
        read_only=False,
        rootless=True,
        side_effects=("opens a known local target through platform handler",),
        requires_confirmation=False,
        interactive=True,
        needs_gui_session=True,
        needs_network=False,
        needs_elevated_lane=False,
        audit_tag="open_known_target",
        notes="Current bounded open action for known targets only; not arbitrary desktop automation.",
    ),
    _cap(
        name="open_explicit_path",
        capability_class=CLASS_HANDOFF,
        status=STATUS_PARTIAL,
        execution_mode=EXECUTION_GUARDED_ACTION,
        risk_level=RISK_MEDIUM,
        read_only=False,
        rootless=True,
        side_effects=("opens an explicit local path through platform handler",),
        requires_confirmation=False,
        interactive=True,
        needs_gui_session=True,
        needs_network=False,
        needs_elevated_lane=False,
        audit_tag="open_explicit_path",
        notes="Current path-based open action with policy checks; not arbitrary file mutation.",
    ),
    _cap(
        name="query_shell",
        capability_class=CLASS_INSPECTOR,
        status=STATUS_PARTIAL,
        execution_mode=EXECUTION_DETERMINISTIC_PROBE,
        risk_level=RISK_MEDIUM,
        read_only=True,
        rootless=True,
        side_effects=(),
        requires_confirmation=False,
        interactive=False,
        needs_gui_session=False,
        needs_network=False,
        needs_elevated_lane=False,
        audit_tag="query_shell",
        notes="Query-only shell information through bounded probe wrappers; not arbitrary shell command execution.",
    ),
    _cap(
        name="query_directory",
        capability_class=CLASS_INSPECTOR,
        status=STATUS_PARTIAL,
        execution_mode=EXECUTION_DETERMINISTIC_PROBE,
        risk_level=RISK_LOW,
        read_only=True,
        rootless=True,
        side_effects=(),
        requires_confirmation=False,
        interactive=False,
        needs_gui_session=False,
        needs_network=False,
        needs_elevated_lane=False,
        audit_tag="query_directory",
        notes="Directory state query without arbitrary execution or mutation.",
    ),
    _cap(
        name="query_model",
        capability_class=CLASS_INSPECTOR,
        status=STATUS_PARTIAL,
        execution_mode=EXECUTION_DETERMINISTIC_PROBE,
        risk_level=RISK_LOW,
        read_only=True,
        rootless=True,
        side_effects=(),
        requires_confirmation=False,
        interactive=False,
        needs_gui_session=False,
        needs_network=False,
        needs_elevated_lane=False,
        audit_tag="query_model",
        required_tools=("route_config_probe", "model_inventory_probe", "model_runtime_probe"),
        notes="Must distinguish configured route targets, installed local model inventory, and runtime reachability. Current lean roster remains qwen2.5:3b-instruct, gemma2:2b, qwen2.5:7b-instruct, and nomic-embed-text:latest.",
    ),
    _cap(
        name="timer",
        capability_class=CLASS_INSPECTOR,
        status=STATUS_UNSUPPORTED,
        execution_mode=EXECUTION_NONE,
        risk_level=RISK_NA,
        read_only=True,
        rootless=True,
        notes="Not implemented in current phase.",
    ),
    _cap(
        name="clipboard",
        capability_class=CLASS_INSPECTOR,
        status=STATUS_UNSUPPORTED,
        execution_mode=EXECUTION_NONE,
        risk_level=RISK_NA,
        read_only=True,
        rootless=True,
        notes="Not implemented in current phase.",
    ),
    _cap(
        name="describe_capabilities",
        capability_class=CLASS_INSPECTOR,
        status=STATUS_PARTIAL,
        execution_mode=EXECUTION_DETERMINISTIC_PROBE,
        risk_level=RISK_LOW,
        read_only=True,
        rootless=True,
        side_effects=(),
        requires_confirmation=False,
        interactive=False,
        needs_gui_session=False,
        needs_network=False,
        needs_elevated_lane=False,
        audit_tag="describe_capabilities",
        notes="Code-level registry helpers exist in src/bond/ai_capabilities.py; not yet wired into normal assistant answers.",
    ),
    _cap(
        name="describe_context_capabilities",
        capability_class=CLASS_INSPECTOR,
        status=STATUS_PLANNED,
        execution_mode=EXECUTION_DETERMINISTIC_PROBE,
        risk_level=RISK_LOW,
        read_only=True,
        rootless=True,
        notes="Future registry plus live probe answer for what Bond can do in the current environment/session.",
    ),
    _cap(
        name="preview_action",
        capability_class=CLASS_INSPECTOR,
        status=STATUS_PLANNED,
        execution_mode=EXECUTION_DETERMINISTIC_PROBE,
        risk_level=RISK_LOW,
        read_only=True,
        rootless=True,
        notes="Future action preview over target, side effects, reversibility, confirmation requirement, and policy reason code.",
    ),
    _cap(
        name="explain_decision",
        capability_class=CLASS_INSPECTOR,
        status=STATUS_PLANNED,
        execution_mode=EXECUTION_DETERMINISTIC_PROBE,
        risk_level=RISK_LOW,
        read_only=True,
        rootless=True,
        notes="Future high-level route/policy/capability explanation without exposing hidden chain-of-thought.",
    ),
    _cap(
        name="register_plugin_capability",
        capability_class=CLASS_PRIVILEGED_LANE,
        status=STATUS_PLANNED,
        execution_mode=EXECUTION_GUARDED_ACTION,
        risk_level=RISK_HIGH,
        read_only=False,
        rootless=False,
        side_effects=("registers future extension capability metadata",),
        requires_confirmation=True,
        interactive=True,
        needs_elevated_lane=True,
        audit_tag="register_plugin_capability",
        notes="Future extension path only; must not bypass policy or registry validation.",
    ),
    _cap(
        name="resolve_invocation_alias",
        capability_class=CLASS_INSPECTOR,
        status=STATUS_PARTIAL,
        execution_mode=EXECUTION_DETERMINISTIC_PROBE,
        risk_level=RISK_LOW,
        read_only=True,
        rootless=True,
        notes="Support capability for invocation alias matching across English/Greek/mixed forms; does not imply full Greek support today.",
    ),
    _cap(
        name="detect_utterance_language",
        capability_class=CLASS_INSPECTOR,
        status=STATUS_PARTIAL,
        execution_mode=EXECUTION_DETERMINISTIC_PROBE,
        risk_level=RISK_LOW,
        read_only=True,
        rootless=True,
        notes="Support capability for el/en/mixed/unknown utterance language classification; not full bilingual correctness.",
    ),
    _cap(
        name="apply_response_language_policy",
        capability_class=CLASS_INSPECTOR,
        status=STATUS_PLANNED,
        execution_mode=EXECUTION_DETERMINISTIC_PROBE,
        risk_level=RISK_LOW,
        read_only=True,
        rootless=True,
        notes="Future response language continuity/policy; does not imply complete localization support today.",
    ),
    _cap(
        name="localize_user_message",
        capability_class=CLASS_INSPECTOR,
        status=STATUS_PLANNED,
        execution_mode=EXECUTION_DETERMINISTIC_PROBE,
        risk_level=RISK_LOW,
        read_only=True,
        rootless=True,
        notes="Future UI/user-message localization via message catalogs; must not imply full Greek/UI localization today.",
    ),
    _cap(
        name="inspect_package_update_status",
        capability_class=CLASS_INSPECTOR,
        status=STATUS_PLANNED,
        execution_mode=EXECUTION_DETERMINISTIC_PROBE,
        risk_level=RISK_LOW,
        read_only=True,
        rootless=True,
        needs_network=True,
        required_tools=("apt", "snap", "flatpak"),
        audit_tag="inspect_package_update_status",
        result_schema="package_update_status_result",
        error_schema="standard_error",
        notes="Planned read-only package update inspection. Not permission to apply updates.",
    ),
    _cap(
        name="plan_safe_system_update",
        capability_class=CLASS_INSPECTOR,
        status=STATUS_PLANNED,
        execution_mode=EXECUTION_DETERMINISTIC_PROBE,
        risk_level=RISK_MEDIUM,
        read_only=True,
        rootless=True,
        needs_network=True,
        required_tools=("apt", "snap", "flatpak"),
        audit_tag="plan_safe_system_update",
        result_schema="system_update_plan_result",
        error_schema="standard_error",
        notes="Planned dry-run style update planner. Must not perform updates.",
    ),
    _cap(
        name="apply_privileged_system_updates",
        capability_class=CLASS_PRIVILEGED_LANE,
        status=STATUS_PLANNED,
        execution_mode=EXECUTION_GUARDED_ACTION,
        risk_level=RISK_HIGH,
        read_only=False,
        rootless=False,
        side_effects=(
            "modifies installed system packages",
            "may restart services",
            "may require reboot",
            "may change package-manager state",
        ),
        requires_confirmation=True,
        interactive=True,
        needs_network=True,
        needs_elevated_lane=True,
        required_tools=(
            "policy_gate",
            "confirmation_token",
            "privileged_lane",
            "rollback_snapshot",
            "post_update_validation",
        ),
        audit_tag="apply_privileged_system_updates",
        result_schema="privileged_update_result",
        error_schema="standard_error",
        notes="Future privileged capability only. Bond must never silently run system upgrades.",
    ),
    _cap(
        name="inspect_storage_hygiene",
        capability_class=CLASS_INSPECTOR,
        status=STATUS_PLANNED,
        execution_mode=EXECUTION_DETERMINISTIC_PROBE,
        risk_level=RISK_LOW,
        read_only=True,
        rootless=True,
        required_tools=("filesystem_probe",),
        audit_tag="inspect_storage_hygiene",
        result_schema="storage_hygiene_result",
        error_schema="standard_error",
        notes="Planned read-only storage hygiene report. No deletion is allowed by this capability.",
    ),
    _cap(
        name="inspect_boot_and_service_health",
        capability_class=CLASS_INSPECTOR,
        status=STATUS_PLANNED,
        execution_mode=EXECUTION_DETERMINISTIC_PROBE,
        risk_level=RISK_LOW,
        read_only=True,
        rootless=True,
        required_tools=("systemctl", "systemd-analyze", "journalctl"),
        audit_tag="inspect_boot_and_service_health",
        result_schema="boot_service_health_result",
        error_schema="standard_error",
        notes="Planned read-only service and boot health inspection. Must not restart or edit services.",
    ),
    _cap(
        name="generate_periodic_health_report",
        capability_class=CLASS_INSPECTOR,
        status=STATUS_PLANNED,
        execution_mode=EXECUTION_DETERMINISTIC_PROBE,
        risk_level=RISK_LOW,
        read_only=True,
        rootless=True,
        side_effects=("writes a local report artifact when enabled",),
        required_tools=(
            "inspect_package_update_status",
            "inspect_storage_hygiene",
            "inspect_boot_and_service_health",
        ),
        audit_tag="generate_periodic_health_report",
        result_schema="periodic_health_report_result",
        error_schema="standard_error",
        notes="Planned monthly or user-requested local report. Must not perform cleanup or updates by itself.",
    ),
    _cap(
        name="present_maintenance_dashboard",
        capability_class=CLASS_HANDOFF,
        status=STATUS_PLANNED,
        execution_mode=EXECUTION_HANDOFF,
        risk_level=RISK_LOW,
        read_only=True,
        rootless=True,
        side_effects=(
            "displays local report state",
            "may submit explicit user requests back to core",
        ),
        interactive=True,
        needs_gui_session=True,
        required_tools=("service_health_endpoint", "report_store"),
        audit_tag="present_maintenance_dashboard",
        result_schema="maintenance_dashboard_result",
        error_schema="standard_error",
        notes="Planned GUI-facing presentation capability. Must not duplicate parser, policy, memory, probes, or execution logic.",
    ),
    _cap(
        name="inspect_document_corpus_status",
        capability_class=CLASS_INSPECTOR,
        status=STATUS_PLANNED,
        execution_mode=EXECUTION_DETERMINISTIC_PROBE,
        risk_level=RISK_LOW,
        read_only=True,
        rootless=True,
        audit_tag="inspect_document_corpus_status",
        result_schema="document_corpus_status_result",
        error_schema="standard_error",
        notes="Planned read-only document corpus status probe. Not implemented in current phase.",
    ),
    _cap(
        name="retrieve_document_knowledge",
        capability_class=CLASS_INSPECTOR,
        status=STATUS_PLANNED,
        execution_mode=EXECUTION_DETERMINISTIC_PROBE,
        risk_level=RISK_LOW,
        read_only=True,
        rootless=True,
        audit_tag="retrieve_document_knowledge",
        result_schema="document_retrieval_result",
        error_schema="standard_error",
        notes="Planned semantic or hybrid retrieval over ingested document knowledge. Not implemented in current phase.",
    ),
    _cap(
        name="ingest_knowledge_sources",
        capability_class=CLASS_BOUNDED_MUTATOR,
        status=STATUS_PLANNED,
        execution_mode=EXECUTION_GUARDED_ACTION,
        risk_level=RISK_LOW,
        read_only=False,
        rootless=True,
        side_effects=(
            "writes parsed content and chunk embeddings to local knowledge store",
            "updates metadata index and embedding index",
        ),
        audit_tag="ingest_knowledge_sources",
        result_schema="ingestion_result",
        error_schema="standard_error",
        notes="Planned controlled local-file ingestion into Bond knowledge structures. Not model training or fine-tuning.",
    ),
    _cap(
        name="reindex_document_corpus",
        capability_class=CLASS_BOUNDED_MUTATOR,
        status=STATUS_PLANNED,
        execution_mode=EXECUTION_GUARDED_ACTION,
        risk_level=RISK_LOW,
        read_only=False,
        rootless=True,
        side_effects=(
            "updates or replaces stale chunk embeddings and metadata records for changed source files",
            "removes orphaned chunks when source files are deleted",
        ),
        audit_tag="reindex_document_corpus",
        result_schema="reindex_result",
        error_schema="standard_error",
        notes="Planned hash-based incremental reindexing and deletion propagation. Not implemented in current phase.",
    ),
)


def _build_registry() -> dict[str, Capability]:
    return {cap.name: cap for cap in _REGISTRY_ENTRIES}


_REGISTRY = _build_registry()


def list_capabilities(
    include_planned: bool = True,
    include_unsupported: bool = True,
) -> list[Capability]:
    caps = sorted(_REGISTRY.values(), key=lambda cap: cap.name)
    filtered: list[Capability] = []
    for cap in caps:
        if not include_planned and cap.status == STATUS_PLANNED:
            continue
        if not include_unsupported and cap.status == STATUS_UNSUPPORTED:
            continue
        filtered.append(cap)
    return list(filtered)


def list_capability_dicts(
    include_planned: bool = True,
    include_unsupported: bool = True,
) -> list[dict]:
    return [
        cap.to_dict()
        for cap in list_capabilities(
            include_planned=include_planned,
            include_unsupported=include_unsupported,
        )
    ]


def get_capability(name: str) -> Capability | None:
    if not isinstance(name, str):
        return None
    key = name.strip()
    if not key:
        return None
    return _REGISTRY.get(key)


def capability_status(name: str) -> str:
    capability = get_capability(name)
    if capability is None:
        return STATUS_UNSUPPORTED
    return capability.status


def is_capability_available(name: str) -> bool:
    capability = get_capability(name)
    if capability is None:
        return False
    if capability.status not in CURRENTLY_USABLE_STATUSES:
        return False
    return capability.execution_mode != EXECUTION_NONE


def require_capability(name: str) -> Capability:
    capability = get_capability(name)
    if capability is None:
        raise KeyError(name)
    return capability


def validate_registry() -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()

    for capability in _REGISTRY_ENTRIES:
        if not capability.name:
            errors.append("capability with empty name")
            continue

        if capability.name in seen:
            errors.append(f"duplicate capability name: {capability.name}")
        seen.add(capability.name)

        if capability.capability_class not in VALID_CLASSES:
            errors.append(f"{capability.name}: invalid class {capability.capability_class}")
        if capability.status not in VALID_STATUSES:
            errors.append(f"{capability.name}: invalid status {capability.status}")
        if capability.execution_mode not in VALID_EXECUTION_MODES:
            errors.append(f"{capability.name}: invalid execution_mode {capability.execution_mode}")
        if capability.risk_level not in VALID_RISK_LEVELS:
            errors.append(f"{capability.name}: invalid risk_level {capability.risk_level}")
        if capability.needs_elevated_lane and capability.capability_class != CLASS_PRIVILEGED_LANE:
            errors.append(
                f"{capability.name}: needs_elevated_lane requires class {CLASS_PRIVILEGED_LANE}"
            )
        if (
            capability.capability_class == CLASS_PRIVILEGED_LANE
            and capability.risk_level not in {RISK_MEDIUM, RISK_HIGH}
        ):
            errors.append(f"{capability.name}: privileged_lane risk must be medium or high")
        if capability.status == STATUS_UNSUPPORTED and capability.execution_mode != EXECUTION_NONE:
            errors.append(f"{capability.name}: unsupported capability must use execution_mode none")

    rebuilt = _build_registry()
    if len(rebuilt) != len(_REGISTRY_ENTRIES):
        errors.append("duplicate names collapse registry size")

    return errors


_REGISTRY_VALIDATION_ERRORS = validate_registry()
if _REGISTRY_VALIDATION_ERRORS:
    raise RuntimeError("invalid capability registry: " + "; ".join(_REGISTRY_VALIDATION_ERRORS))
