#!/usr/bin/env python3
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Iterable

SOURCE_OS_API = "os_api"
SOURCE_DESKTOP_API = "desktop_api"
SOURCE_WRAPPED_COMMAND = "wrapped_command"
SOURCE_CONFIG = "config"
SOURCE_RUNTIME_PROBE = "runtime_probe"

CERTAINTY_AUTHORITATIVE = "authoritative"
CERTAINTY_DERIVED = "derived"
CERTAINTY_HEURISTIC = "heuristic"
CERTAINTY_UNKNOWN = "unknown"

REFRESH_LOW_CHURN = "low_churn"
REFRESH_MEDIUM_CHURN = "medium_churn"
REFRESH_HIGH_CHURN = "high_churn"

VALID_SOURCE_TYPES = {
    SOURCE_OS_API,
    SOURCE_DESKTOP_API,
    SOURCE_WRAPPED_COMMAND,
    SOURCE_CONFIG,
    SOURCE_RUNTIME_PROBE,
}

VALID_CERTAINTY_CLASSES = {
    CERTAINTY_AUTHORITATIVE,
    CERTAINTY_DERIVED,
    CERTAINTY_HEURISTIC,
    CERTAINTY_UNKNOWN,
}

VALID_REFRESH_CLASSES = {
    REFRESH_LOW_CHURN,
    REFRESH_MEDIUM_CHURN,
    REFRESH_HIGH_CHURN,
}


@dataclass(frozen=True)
class ProbeResult:
    ok: bool
    probe_name: str
    layer: int
    source_type: str
    certainty_class: str
    collected_at: str
    data: dict[str, Any]
    warnings: tuple[str, ...] = ()
    error: dict[str, Any] | None = None
    refresh_class: str = REFRESH_MEDIUM_CHURN
    supports_live_truth: bool = False
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "probe_name": self.probe_name,
            "layer": self.layer,
            "source_type": self.source_type,
            "certainty_class": self.certainty_class,
            "collected_at": self.collected_at,
            "data": self.data,
            "warnings": list(self.warnings),
            "error": self.error,
            "refresh_class": self.refresh_class,
            "supports_live_truth": self.supports_live_truth,
            "notes": self.notes,
        }


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def standard_error(kind: str, message: str, detail: Any | None = None) -> dict[str, Any]:
    error = {
        "kind": kind,
        "message": message,
    }
    if detail is not None:
        error["detail"] = detail
    return error


def probe_ok(
    *,
    probe_name: str,
    layer: int,
    source_type: str,
    certainty_class: str,
    data: dict[str, Any],
    warnings: tuple[str, ...] = (),
    refresh_class: str = REFRESH_MEDIUM_CHURN,
    supports_live_truth: bool = False,
    notes: str = "",
) -> ProbeResult:
    return ProbeResult(
        ok=True,
        probe_name=probe_name,
        layer=layer,
        source_type=source_type,
        certainty_class=certainty_class,
        collected_at=utc_now(),
        data=data,
        warnings=warnings,
        error=None,
        refresh_class=refresh_class,
        supports_live_truth=supports_live_truth,
        notes=notes,
    )


def probe_error(
    *,
    probe_name: str,
    layer: int,
    source_type: str,
    certainty_class: str,
    error: dict[str, Any],
    data: dict[str, Any] | None = None,
    warnings: tuple[str, ...] = (),
    refresh_class: str = REFRESH_MEDIUM_CHURN,
    supports_live_truth: bool = False,
    notes: str = "",
) -> ProbeResult:
    return ProbeResult(
        ok=False,
        probe_name=probe_name,
        layer=layer,
        source_type=source_type,
        certainty_class=certainty_class,
        collected_at=utc_now(),
        data=data or {},
        warnings=warnings,
        error=error,
        refresh_class=refresh_class,
        supports_live_truth=supports_live_truth,
        notes=notes,
    )


def validate_probe_result(result: ProbeResult) -> list[str]:
    errors: list[str] = []

    if not isinstance(result.probe_name, str) or not result.probe_name.strip():
        errors.append("probe_name must be non-empty")
    if result.layer not in {0, 1, 2}:
        errors.append("layer must be 0, 1, or 2")
    if result.source_type not in VALID_SOURCE_TYPES:
        errors.append("source_type must be a known source constant")
    if result.certainty_class not in VALID_CERTAINTY_CLASSES:
        errors.append("certainty_class must be a known certainty constant")
    if result.refresh_class not in VALID_REFRESH_CLASSES:
        errors.append("refresh_class must be a known refresh constant")
    if not isinstance(result.data, dict):
        errors.append("data must be a dict")
    if not isinstance(result.warnings, tuple):
        errors.append("warnings must be a tuple of strings")
    else:
        for warning in result.warnings:
            if not isinstance(warning, str):
                errors.append("warnings must contain only strings")
                break
    if result.error is not None and not isinstance(result.error, dict):
        errors.append("error must be None or a dict")
    if result.ok is False and not isinstance(result.error, dict):
        errors.append("failed probe results must include a structured error dict")
    if not isinstance(result.collected_at, str) or not result.collected_at.strip():
        errors.append("collected_at must be a non-empty string")

    return errors


def results_to_dicts(results: Iterable[ProbeResult]) -> list[dict[str, Any]]:
    return [result.to_dict() for result in results]