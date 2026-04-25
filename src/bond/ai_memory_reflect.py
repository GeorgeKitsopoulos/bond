#!/usr/bin/env python3
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from ai_core import (
    FILES,
    append_jsonl,
    build_active_context,
    ensure_memory_dirs,
    get_state_root,
    load_json,
    tail_jsonl,
    utc_now,
)

DEFAULT_MODEL = "gemma2:2b"
DEFAULT_TIMEOUT = 15
DEFAULT_MAX_ITEMS_PER_BUCKET = 6
DEFAULT_MIN_NEW_EVENTS = 3


def log_failure(message: str, meta=None) -> None:
    append_jsonl(
        FILES["failures"],
        {
            "ts": utc_now(),
            "message": message,
            "meta": meta or {},
        },
    )


def parse_iso_utc(value: str | None):
    if not value or not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None


def get_reflection_settings() -> dict:
    assistant_config = get_state_root() / "assistant_config.json"
    data = load_json(assistant_config, {})
    if not isinstance(data, dict):
        data = {}

    cfg = data.get("reflection")
    if not isinstance(cfg, dict):
        cfg = {}

    model = cfg.get("model")
    if not isinstance(model, str) or not model.strip():
        model = DEFAULT_MODEL
    else:
        model = model.strip()

    timeout_seconds = cfg.get("timeout_seconds")
    if not isinstance(timeout_seconds, int) or timeout_seconds <= 0:
        timeout_seconds = DEFAULT_TIMEOUT

    enabled = cfg.get("enabled")
    if not isinstance(enabled, bool):
        enabled = True

    max_items_per_bucket = cfg.get("max_items_per_bucket")
    if not isinstance(max_items_per_bucket, int) or max_items_per_bucket <= 0:
        max_items_per_bucket = DEFAULT_MAX_ITEMS_PER_BUCKET

    min_new_events = cfg.get("min_new_events")
    if not isinstance(min_new_events, int) or min_new_events <= 0:
        min_new_events = DEFAULT_MIN_NEW_EVENTS

    include_actions = cfg.get("include_actions")
    if not isinstance(include_actions, bool):
        include_actions = True

    include_failures = cfg.get("include_failures")
    if not isinstance(include_failures, bool):
        include_failures = True

    include_chats = cfg.get("include_chats")
    if not isinstance(include_chats, bool):
        include_chats = True

    return {
        "enabled": enabled,
        "model": model,
        "timeout_seconds": timeout_seconds,
        "max_items_per_bucket": max_items_per_bucket,
        "min_new_events": min_new_events,
        "include_actions": include_actions,
        "include_failures": include_failures,
        "include_chats": include_chats,
    }


def run_ollama(model: str, prompt: str, timeout_seconds: int) -> str:
    proc = subprocess.run(
        ["ollama", "run", model],
        input=prompt,
        text=True,
        capture_output=True,
        check=False,
        timeout=timeout_seconds,
    )
    if proc.returncode != 0:
        err = (proc.stderr or "").strip()
        raise RuntimeError(err or f"ollama run failed with code {proc.returncode}")
    return (proc.stdout or "").strip()


def normalize_text(text: str) -> str:
    return " ".join(text.lower().split())


def existing_reflection_messages(limit: int = 200) -> set[str]:
    seen = set()
    for item in tail_jsonl(FILES["reflections"], limit):
        msg = str(item.get("message", "")).strip()
        if msg:
            seen.add(normalize_text(msg))
    return seen


def latest_reflection_ts(limit: int = 50):
    latest = None
    for item in tail_jsonl(FILES["reflections"], limit):
        ts = parse_iso_utc(item.get("ts"))
        meta = item.get("meta", {})
        source = meta.get("source") if isinstance(meta, dict) else None
        if source != "ai_memory_reflect":
            continue
        if ts and (latest is None or ts > latest):
            latest = ts
    return latest


def count_new_events_since(items: list[dict], threshold) -> int:
    if threshold is None:
        return len(items)

    count = 0
    for item in items:
        ts = parse_iso_utc(item.get("ts"))
        if ts and ts > threshold:
            count += 1
    return count


def build_payload(
    actions: list[dict],
    failures: list[dict],
    chats: list[dict],
    settings: dict,
) -> dict:
    max_items = settings["max_items_per_bucket"]

    payload = {}

    if settings["include_failures"]:
        payload["failures"] = failures[-max_items:]

    if settings["include_actions"]:
        payload["actions"] = actions[-max_items:]

    if settings["include_chats"]:
        payload["chats"] = chats[-max_items:]

    return payload


def should_reflect(
    actions: list[dict],
    failures: list[dict],
    chats: list[dict],
    settings: dict,
) -> tuple[bool, str]:
    if not settings["enabled"]:
        return False, "reflection disabled by config"

    if not actions and not failures and not chats:
        return False, "no recent logs to reflect on"

    last_reflection = latest_reflection_ts()

    new_actions = count_new_events_since(actions, last_reflection)
    new_failures = count_new_events_since(failures, last_reflection)
    new_chats = count_new_events_since(chats, last_reflection)
    new_total = new_actions + new_failures + new_chats

    if new_total == 0:
        return False, "no new events since last reflection"

    # Failures are higher-value than normal actions/chats.
    if new_failures >= 1:
        return True, "recent failure activity"

    if new_total < settings["min_new_events"]:
        return False, f"not enough new events ({new_total} < {settings['min_new_events']})"

    return True, f"sufficient new events ({new_total})"


def build_prompt(payload: dict) -> str:
    return f"""
You are reviewing recent local AI assistant logs.

Return ONLY a JSON array of strings.
No markdown.
No explanation.

Rules:
- Each item must be a short operational lesson.
- Focus on concrete routing, execution safety, ambiguity, repeated corrections, or memory hygiene.
- Prefer lessons that help future assistant behavior.
- Do not give generic advice.
- Do not repeat the same idea with different wording.
- If there is nothing worth learning, return [].
- Maximum 2 items.
- Each item should be under 140 characters.

Logs:
{json.dumps(payload, ensure_ascii=False, indent=2)}
""".strip()


def parse_lessons(raw: str) -> list[str]:
    raw = raw.strip()
    if not raw:
        return []

    try:
        data = json.loads(raw)
    except Exception:
        return []

    if not isinstance(data, list):
        return []

    out = []
    for item in data:
        if not isinstance(item, str):
            continue
        text = " ".join(item.strip().split())
        if not text:
            continue
        if len(text) > 140:
            continue
        out.append(text)

    return out


def main():
    ensure_memory_dirs()

    settings = get_reflection_settings()

    actions = tail_jsonl(FILES["actions"], 20)
    failures = tail_jsonl(FILES["failures"], 20)
    chats = tail_jsonl(FILES["chats"], 20)

    should_run, reason = should_reflect(actions, failures, chats, settings)
    if not should_run:
        print(reason)
        build_active_context()
        return

    payload = build_payload(actions, failures, chats, settings)
    prompt = build_prompt(payload)

    try:
        raw = run_ollama(
            settings["model"],
            prompt,
            settings["timeout_seconds"],
        )
    except subprocess.TimeoutExpired:
        log_failure(
            "reflection skipped: timed out",
            {
                "model": settings["model"],
                "timeout_seconds": settings["timeout_seconds"],
                "source": "ai_memory_reflect",
            },
        )
        print(f"reflection skipped: timed out after {settings['timeout_seconds']}s")
        build_active_context()
        return
    except Exception as e:
        log_failure(
            "reflection skipped: model run failed",
            {
                "model": settings["model"],
                "timeout_seconds": settings["timeout_seconds"],
                "error": str(e),
                "source": "ai_memory_reflect",
            },
        )
        print(f"reflection skipped: {e}")
        build_active_context()
        return

    lessons = parse_lessons(raw)
    if not lessons:
        print("no useful lessons produced")
        build_active_context()
        return

    seen = existing_reflection_messages()
    written = 0

    for lesson in lessons:
        norm = normalize_text(lesson)
        if norm in seen:
            continue

        append_jsonl(
            FILES["reflections"],
            {
                "ts": utc_now(),
                "message": lesson,
                "meta": {
                    "model": settings["model"],
                    "timeout_seconds": settings["timeout_seconds"],
                    "source": "ai_memory_reflect",
                    "policy_reason": reason,
                    "max_items_per_bucket": settings["max_items_per_bucket"],
                    "min_new_events": settings["min_new_events"],
                },
            },
        )
        seen.add(norm)
        written += 1

    build_active_context()
    print(f"reflection complete: {written} new lesson(s)")


if __name__ == "__main__":
    main()
