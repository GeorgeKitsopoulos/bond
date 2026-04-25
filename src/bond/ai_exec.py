#!/usr/bin/env python3
import json
import shlex
import subprocess
import sys
from pathlib import Path

from ai_action_catalog import resolve_target
from ai_action_parse import parse_request
from ai_action_policy import resolve_explicit_path
from ai_core import (
    build_active_context,
    ensure_memory_dirs,
    get_state_root,
    load_json,
    log_memory,
)

HOME = Path.home()
SYSTEM_PROFILE = get_state_root() / "system_profile.json"


def run_cmd(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(args, check=False, capture_output=True, text=True)


def load_system_profile() -> dict:
    data = load_json(SYSTEM_PROFILE, {})
    return data if isinstance(data, dict) else {}


def choose_app(profile: dict, key: str, fallback: str | None = None) -> str | None:
    value = profile.get(key)
    if isinstance(value, str) and value.strip():
        return value.strip()
    return fallback


def open_with_xdg(path_or_url: str) -> bool:
    proc = run_cmd(["xdg-open", path_or_url])
    return proc.returncode == 0


def send_notification(text: str) -> bool:
    proc = run_cmd(["notify-send", "AI Assistant", text])
    return proc.returncode == 0


def set_wallpaper(path: str) -> bool:
    image = str(Path(path).expanduser())
    if not Path(image).exists():
        return False

    proc = run_cmd(
        [
            "gsettings",
            "set",
            "org.cinnamon.desktop.background",
            "picture-uri",
            f"file://{image}",
        ]
    )
    return proc.returncode == 0


def open_app_command(command: str, extra_args=None) -> bool:
    try:
        parts = shlex.split(command)
    except Exception:
        return False

    if extra_args:
        parts.extend(extra_args)

    if not parts:
        return False

    try:
        proc = subprocess.Popen(parts)
    except Exception:
        return False

    return proc.poll() is None or proc.returncode == 0


def open_in_editor(profile: dict, target: Path) -> bool:
    app = choose_app(profile, "editor_cmd", "xed")
    return open_app_command(app, [str(target)])


def open_in_file_manager(profile: dict, target: Path) -> bool:
    app = choose_app(profile, "file_manager_cmd", "nemo")
    return open_app_command(app, [str(target)])


def llm_parse_intent(text: str) -> dict | None:
    return None


def execute_intent(intent: dict) -> tuple[bool, str]:
    profile = load_system_profile()
    name = intent.get("intent")

    if name == "open_browser":
        app = choose_app(profile, "browser_cmd", "firefox")
        ok = open_app_command(app)
        return ok, f"open_browser via {app}"

    if name == "open_mail":
        app = choose_app(profile, "mail_cmd", "thunderbird")
        ok = open_app_command(app)
        return ok, f"open_mail via {app}"

    if name == "open_terminal":
        app = choose_app(profile, "terminal_cmd", "gnome-terminal")
        ok = open_app_command(app)
        return ok, f"open_terminal via {app}"

    if name == "open_editor":
        app = choose_app(profile, "editor_cmd", "xed")
        ok = open_app_command(app)
        return ok, f"open_editor via {app}"

    if name == "open_file_manager":
        app = choose_app(profile, "file_manager_cmd", "nemo")
        ok = open_app_command(app)
        return ok, f"open_file_manager via {app}"

    if name == "open_url":
        url = str(intent.get("url", "")).strip()
        if not url.lower().startswith(("http://", "https://")):
            return False, f"blocked non-http url: {url}"
        ok = open_with_xdg(url)
        return ok, f"open_url {url}"

    if name == "notify":
        text = str(intent.get("text", "")).strip()
        if not text:
            return False, "empty notification text"
        ok = send_notification(text)
        return ok, f"notify {text}"

    if name == "set_wallpaper":
        path = str(intent.get("path", "")).strip()
        expanded = str(Path(path).expanduser())
        ok = set_wallpaper(expanded)
        return ok, f"set_wallpaper {expanded}"

    if name in {"open_path", "open_path_in_editor", "open_path_in_file_manager"}:
        raw_path = str(intent.get("path", "")).strip()
        ok_path, detail, target = resolve_explicit_path(raw_path)
        if not ok_path or not target:
            return False, detail

        if not target.exists():
            return False, f"missing_path: {target}"

        if name == "open_path_in_editor":
            ok = open_in_editor(profile, target)
            return ok, f"open_path_in_editor {target}"

        if name == "open_path_in_file_manager":
            ok = open_in_file_manager(profile, target)
            return ok, f"open_path_in_file_manager {target}"

        ok = open_with_xdg(str(target))
        return ok, f"open_path {target}"

    if name in {"open_known_target", "open_known_in_editor", "open_known_in_file_manager"}:
        raw_target = str(intent.get("target", "")).strip()
        label, target = resolve_target(raw_target)
        if not target or not target.exists():
            return False, f"unknown_or_missing_target: {raw_target}"

        if name == "open_known_in_editor":
            ok = open_in_editor(profile, target)
            return ok, f"open_in_editor {label} -> {target}"

        if name == "open_known_in_file_manager":
            ok = open_in_file_manager(profile, target)
            return ok, f"open_in_file_manager {label} -> {target}"

        ok = open_with_xdg(str(target))
        return ok, f"open_known_target {label} -> {target}"

    return False, f"unsupported intent: {name}"


def main():
    ensure_memory_dirs()

    if len(sys.argv) < 2:
        print(json.dumps({"ok": False, "error": "missing request"}))
        raise SystemExit(1)

    request = " ".join(sys.argv[1:]).strip()
    intent = parse_request(request)

    if intent is None:
        intent = llm_parse_intent(request)

    if intent is None:
        print(json.dumps({"ok": False, "error": "no_safe_action_detected"}))
        raise SystemExit(2)

    ok, detail = execute_intent(intent)

    if ok:
        log_memory("actions", detail, {"request": request, "intent": intent})
        build_active_context()
        print(json.dumps({"ok": True, "detail": detail, "intent": intent}, ensure_ascii=False))
        return

    log_memory("failures", detail, {"request": request, "intent": intent})
    build_active_context()
    print(json.dumps({"ok": False, "error": detail, "intent": intent}, ensure_ascii=False))
    raise SystemExit(3)


if __name__ == "__main__":
    main()
