#!/usr/bin/env python3
import json
import os
import sys
import time
from collections.abc import Mapping


TRUTHY_VALUES = frozenset({"1", "true", "yes", "on"})


def dev_telemetry_enabled(env: Mapping[str, str] | None = None) -> bool:
    source = os.environ if env is None else env
    raw = str(source.get("BOND_DEV_TELEMETRY", ""))
    return raw.strip().lower() in TRUTHY_VALUES


def now_perf() -> float:
    return time.perf_counter()


def elapsed_ms(start_perf: float, end_perf: float | None = None) -> float:
    end_value = time.perf_counter() if end_perf is None else end_perf
    return round((end_value - start_perf) * 1000.0, 3)


def safe_value(value):
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, (list, tuple)):
        return [safe_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): safe_value(item) for key, item in value.items()}
    return str(value)


def build_dev_telemetry_record(
    *,
    start_perf: float,
    exit_code: int,
    answer_path: str = "",
    route_worker: str = "",
    route_reason: str = "",
    policy_mode: str = "",
    action_contract_mode: str = "",
    intent: str = "",
    profile: str = "",
    model: str = "",
    deterministic: bool | None = None,
    dry_run: bool | None = None,
    confirmation_required: bool | None = None,
    error_kind: str = "",
    extra: Mapping[str, object] | None = None,
) -> dict:
    record = {
        "schema": "bond_dev_telemetry_v1",
        "telemetry_enabled": True,
        "elapsed_ms": elapsed_ms(start_perf),
        "exit_code": exit_code,
        "answer_path": answer_path,
        "route_worker": route_worker,
        "route_reason": route_reason,
        "policy_mode": policy_mode,
        "action_contract_mode": action_contract_mode,
        "intent": intent,
        "profile": profile,
        "model": model,
        "deterministic": deterministic,
        "dry_run": dry_run,
        "confirmation_required": confirmation_required,
        "error_kind": error_kind,
    }
    if extra:
        record["extra"] = safe_value(dict(extra))
    return safe_value(record)


def format_dev_telemetry_line(record: Mapping[str, object]) -> str:
    return "BOND_DEV_TELEMETRY " + json.dumps(dict(record), sort_keys=True, ensure_ascii=False)


def emit_dev_telemetry(record: Mapping[str, object], stream=None) -> None:
    out = sys.stderr if stream is None else stream
    print(format_dev_telemetry_line(record), file=out, flush=True)


def maybe_emit_dev_telemetry(
    *,
    start_perf: float,
    exit_code: int,
    env: Mapping[str, str] | None = None,
    stream=None,
    **metadata,
) -> None:
    if not dev_telemetry_enabled(env):
        return
    record = build_dev_telemetry_record(start_perf=start_perf, exit_code=exit_code, **metadata)
    emit_dev_telemetry(record, stream=stream)
