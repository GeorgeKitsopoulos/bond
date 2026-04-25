#!/usr/bin/env python3
import json
import os
import re
import secrets
import tempfile
import time
from pathlib import Path

from ai_core import get_state_root

DEFAULT_CONFIRM_TTL_SECONDS = 600
CONFIRM_TTL_ENV = "BOND_CONFIRM_TTL_SECONDS"
TOKEN_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
TOKEN_LENGTH = 8


def _pending_path() -> Path:
    return get_state_root() / "confirmations" / "pending.json"


def _safe_ttl_seconds() -> int:
    raw = os.environ.get(CONFIRM_TTL_ENV, "").strip()
    if not raw:
        return DEFAULT_CONFIRM_TTL_SECONDS
    try:
        value = int(raw)
    except ValueError:
        return DEFAULT_CONFIRM_TTL_SECONDS
    if value <= 0:
        return DEFAULT_CONFIRM_TTL_SECONDS
    return value


def _write_pending(data: dict) -> None:
    path = _pending_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    fd, temp_name = tempfile.mkstemp(prefix="pending.", suffix=".tmp", dir=str(path.parent))
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        os.replace(temp_path, path)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def _generate_token() -> str:
    return "".join(secrets.choice(TOKEN_ALPHABET) for _ in range(TOKEN_LENGTH))


def create_pending_confirmation(original_text: str, risk_level: str, action_steps: list[str], reason: str) -> dict:
    now = int(time.time())
    ttl_seconds = _safe_ttl_seconds()
    expires_at = now + ttl_seconds
    token = _generate_token()

    payload = {
        "token": token,
        "original_text": original_text,
        "created_at": now,
        "expires_at": expires_at,
        "consumed": False,
        "reason": reason,
        "risk_level": risk_level,
        "action_steps": list(action_steps or []),
    }
    _write_pending(payload)

    result = dict(payload)
    result["expires_in_seconds"] = ttl_seconds
    return result


def parse_confirmation_request(text: str) -> str | None:
    normalized = re.sub(r"\s+", " ", text.strip())
    if not normalized:
        return None

    pattern = re.compile(
        r"^(?:confirm|confirmation|επιβεβαίωση|επιβεβαιωση|επιβεβαιώνω|επιβεβαιωνω)\s*:?[ ]+([A-Za-z0-9_-]+)$",
        flags=re.IGNORECASE,
    )
    match = pattern.match(normalized)
    if not match:
        return None

    token = match.group(1).strip().upper()
    if not token:
        return None
    return token


def load_pending_confirmation() -> dict | None:
    path = _pending_path()
    if not path.exists():
        return None

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None

    if not isinstance(data, dict):
        return None
    return data


def validate_pending_confirmation(token: str) -> tuple[bool, dict | None, str]:
    pending = load_pending_confirmation()
    if pending is None:
        return False, None, "confirmation_missing"

    stored_token = str(pending.get("token", "")).upper()
    if stored_token != token.upper():
        return False, None, "confirmation_invalid"

    if bool(pending.get("consumed", False)):
        return False, pending, "confirmation_consumed"

    try:
        expires_at = int(pending.get("expires_at", 0))
    except Exception:
        expires_at = 0

    now = int(time.time())
    if expires_at <= 0 or now >= expires_at:
        return False, pending, "confirmation_expired"

    return True, pending, "ok"


def consume_pending_confirmation(token: str) -> tuple[bool, dict | None, str]:
    ok, pending, reason = validate_pending_confirmation(token)
    if not ok or pending is None:
        return ok, pending, reason

    updated = dict(pending)
    updated["consumed"] = True
    _write_pending(updated)
    return True, updated, "ok"


def clear_pending_confirmation() -> None:
    path = _pending_path()
    if path.exists():
        path.unlink()
