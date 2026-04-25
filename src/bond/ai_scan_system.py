#!/usr/bin/env python3
import json
import os
import shutil
import subprocess
from pathlib import Path
from configparser import ConfigParser

from ai_core import get_state_root

OUT = get_state_root() / "system_profile.json"


def run(cmd, timeout=12):
    try:
        r = subprocess.run(
            cmd,
            shell=True,
            text=True,
            capture_output=True,
            timeout=timeout
        )
        out = (r.stdout or "").strip()
        err = (r.stderr or "").strip()
        return out if out else err
    except Exception as e:
        return f"ERROR: {e}"


def read_text(path, limit=20000):
    p = Path(path).expanduser()
    try:
        if p.exists() and p.is_file():
            return p.read_text(errors="ignore")[:limit]
    except Exception as e:
        return f"ERROR: {e}"
    return ""


def file_exists(path):
    try:
        return Path(path).expanduser().exists()
    except Exception:
        return False


def which(names):
    return {name: shutil.which(name) for name in names}


def parse_desktop_file(path):
    cp = ConfigParser(interpolation=None)
    cp.optionxform = str
    try:
        cp.read(path, encoding="utf-8")
        if "Desktop Entry" not in cp:
            return None
        d = cp["Desktop Entry"]
        return {
            "name": d.get("Name", ""),
            "exec": d.get("Exec", ""),
            "icon": d.get("Icon", ""),
            "type": d.get("Type", ""),
            "categories": d.get("Categories", ""),
            "mime": d.get("MimeType", ""),
            "terminal": d.get("Terminal", ""),
            "nodisplay": d.get("NoDisplay", ""),
            "hidden": d.get("Hidden", ""),
            "filename": Path(path).name,
            "path": str(path),
        }
    except Exception:
        return None


def scan_desktop_entries():
    dirs = [
        Path("/usr/share/applications"),
        HOME / ".local/share/applications",
        Path("/var/lib/flatpak/exports/share/applications"),
        HOME / ".local/share/flatpak/exports/share/applications",
    ]
    found = []
    seen = set()

    for d in dirs:
        if not d.exists():
            continue
        for f in d.glob("*.desktop"):
            item = parse_desktop_file(f)
            if not item:
                continue
            key = item["filename"]
            if key in seen:
                continue
            seen.add(key)
            found.append(item)

    return found


def xdg_default(mime):
    return run(f"xdg-mime query default {mime}")


def xdg_setting(key):
    return run(f"xdg-settings get {key}")


def infer_app_from_desktop_id(desktop_id, entries):
    if not desktop_id:
        return None
    desktop_id = desktop_id.strip()
    for e in entries:
        if e["filename"] == desktop_id:
            return e
    return None


def infer_preferred_browser(entries):
    xdg_web = xdg_setting("default-web-browser")
    http_h = xdg_default("x-scheme-handler/http")
    https_h = xdg_default("x-scheme-handler/https")

    chosen = None
    for candidate in [xdg_web, http_h, https_h]:
        chosen = infer_app_from_desktop_id(candidate, entries)
        if chosen:
            break

    candidates = []
    for bin_name in ["firefox", "google-chrome", "chromium", "brave-browser", "microsoft-edge"]:
        p = shutil.which(bin_name)
        if p:
            candidates.append({"binary": bin_name, "path": p})

    return {
        "xdg_web": xdg_web,
        "http_handler": http_h,
        "https_handler": https_h,
        "resolved_desktop": chosen,
        "installed_candidates": candidates,
    }


def infer_mail_client(entries):
    mailto = xdg_default("x-scheme-handler/mailto")
    resolved = infer_app_from_desktop_id(mailto, entries)

    candidates = []
    for bin_name in ["thunderbird", "evolution", "geary", "kmail"]:
        p = shutil.which(bin_name)
        if p:
            candidates.append({"binary": bin_name, "path": p})

    return {
        "mailto_handler": mailto,
        "resolved_desktop": resolved,
        "installed_candidates": candidates,
    }


def infer_file_manager():
    candidates = []
    for bin_name in ["nemo", "nautilus", "thunar", "pcmanfm", "dolphin"]:
        p = shutil.which(bin_name)
        if p:
            candidates.append({"binary": bin_name, "path": p})

    likely = None
    if shutil.which("nemo"):
        likely = {"binary": "nemo", "path": shutil.which("nemo")}

    return {
        "likely_default": likely,
        "installed_candidates": candidates,
    }


def infer_terminal():
    xdg_terminals = read_text("~/.config/xdg-terminals.list", 8000)
    candidates = []
    for bin_name in [
        "gnome-terminal", "xfce4-terminal", "konsole", "mate-terminal",
        "x-terminal-emulator", "kitty", "alacritty", "wezterm", "terminator",
        "tilix", "lxterminal"
    ]:
        p = shutil.which(bin_name)
        if p:
            candidates.append({"binary": bin_name, "path": p})

    return {
        "xdg_terminals_list": xdg_terminals,
        "installed_candidates": candidates,
    }


def infer_editors():
    candidates = []
    for bin_name in [
        "xed", "gedit", "mousepad", "kate", "geany", "code", "codium",
        "nano", "vim", "nvim"
    ]:
        p = shutil.which(bin_name)
        if p:
            candidates.append({"binary": bin_name, "path": p})
    return candidates


def detect_flatpaks():
    if not shutil.which("flatpak"):
        return []
    out = run("flatpak list --app --columns=application,name,origin")
    return [x.strip() for x in out.splitlines() if x.strip()][:200]


def detect_snaps():
    if not shutil.which("snap"):
        return []
    out = run("snap list")
    return out.splitlines()[:120]


def detect_cinnamon():
    keys = {
        "theme": "org.cinnamon.theme name",
        "icon_theme": "org.cinnamon.desktop.interface icon-theme",
        "gtk_theme": "org.cinnamon.desktop.interface gtk-theme",
        "cursor_theme": "org.cinnamon.desktop.interface cursor-theme",
        "wallpaper_uri": "org.cinnamon.desktop.background picture-uri",
        "wallpaper_uri_dark": "org.cinnamon.desktop.background picture-uri-dark",
        "scaling_factor": "org.cinnamon.desktop.interface text-scaling-factor",
    }
    out = {}
    for k, setting in keys.items():
        out[k] = run(f"gsettings get {setting}")

    out["can_set_wallpaper"] = shutil.which("gsettings") is not None
    out["can_notify"] = shutil.which("notify-send") is not None
    out["can_open_url"] = shutil.which("xdg-open") is not None
    return out


def detect_session():
    return {
        "user": os.environ.get("USER", ""),
        "home": str(HOME),
        "shell": os.environ.get("SHELL", ""),
        "xdg_current_desktop": os.environ.get("XDG_CURRENT_DESKTOP", ""),
        "desktop_session": os.environ.get("DESKTOP_SESSION", ""),
        "xdg_session_type": os.environ.get("XDG_SESSION_TYPE", ""),
        "display": os.environ.get("DISPLAY", ""),
        "wayland_display": os.environ.get("WAYLAND_DISPLAY", ""),
        "dbus_session_bus_address": bool(os.environ.get("DBUS_SESSION_BUS_ADDRESS", "")),
    }


def detect_os():
    return {
        "os_release": read_text("/etc/os-release", 5000),
        "kernel": run("uname -a"),
        "hostnamectl": run("hostnamectl"),
    }


def detect_hardware():
    return {
        "cpu": run("lscpu"),
        "memory": run("free -h"),
        "blocks": run("lsblk -o NAME,SIZE,FSTYPE,MOUNTPOINT"),
        "gpu": run("lspci | grep -Ei 'vga|3d|display'"),
        "inxi": run("inxi -F"),
        "sensors": run("sensors"),
    }


def detect_network_tools():
    return {
        "nmcli": shutil.which("nmcli"),
        "ip": shutil.which("ip"),
        "ss": shutil.which("ss"),
        "network_summary": run("nmcli general status"),
        "wifi_summary": run("nmcli device status"),
    }


def detect_user_configs():
    return {
        "bashrc": read_text("~/.bashrc", 12000),
        "profile": read_text("~/.profile", 8000),
        "user_dirs_locale": read_text("~/.config/user-dirs.locale", 2000),
        "geany_conf_exists": file_exists("~/.config/geany/geany.conf"),
        "nemo_config_exists": file_exists("~/.config/nemo"),
        "cinnamon_config_exists": file_exists("~/.config/cinnamon"),
        "mullvad_config_exists": file_exists("~/.config/Mullvad VPN"),
    }


def detect_recent_user_signals():
    signals = {
        "browser_like_configs": [],
        "app_like_configs": [],
    }
    cfg = HOME / ".config"
    if cfg.exists():
        for child in sorted(cfg.iterdir()):
            name = child.name.lower()
            if any(x in name for x in ["firefox", "chrome", "chromium", "brave", "browser"]):
                signals["browser_like_configs"].append(child.name)
            if any(x in name for x in ["thunderbird", "geany", "nemo", "cinnamon", "mullvad", "celluloid", "pix"]):
                signals["app_like_configs"].append(child.name)
    return signals


def detect_agent_tools():
    names = [
        "python3", "bash", "sh", "xdg-open", "gio", "gsettings", "notify-send",
        "nemo", "firefox", "thunderbird", "geany", "xed", "curl", "wget",
        "flatpak", "snap", "systemctl", "journalctl", "nmcli", "pkill",
        "pgrep", "xdotool", "wmctrl", "playerctl", "xclip", "wl-copy",
        "grim", "gnome-screenshot", "scrot"
    ]
    return which(names)


def derive_actions(browser, mail, filemgr, terminal, editors, cinnamon, tools):
    actions = []

    if tools.get("xdg-open"):
        actions.append({"action": "open_url", "method": "xdg-open URL"})
        actions.append({"action": "open_path", "method": "xdg-open PATH"})

    if browser.get("resolved_desktop") or browser.get("installed_candidates"):
        actions.append({"action": "open_browser", "method": "preferred browser or xdg-open"})

    if mail.get("resolved_desktop") or mail.get("installed_candidates"):
        actions.append({"action": "open_mail", "method": "mailto: or mail client binary"})

    if filemgr.get("likely_default") or filemgr.get("installed_candidates"):
        actions.append({"action": "open_file_manager", "method": "nemo or xdg-open folder"})

    if terminal.get("installed_candidates"):
        actions.append({"action": "open_terminal", "method": "preferred terminal candidate"})

    if editors:
        actions.append({"action": "open_editor", "method": "preferred GUI editor candidate"})

    if cinnamon.get("can_set_wallpaper"):
        actions.append({"action": "set_wallpaper", "method": "gsettings org.cinnamon.desktop.background picture-uri"})

    if tools.get("notify-send"):
        actions.append({"action": "send_notification", "method": "notify-send"})

    if tools.get("playerctl"):
        actions.append({"action": "media_control", "method": "playerctl"})

    if tools.get("xclip") or tools.get("wl-copy"):
        actions.append({"action": "clipboard_write", "method": "xclip/wl-copy"})

    if tools.get("gnome-screenshot") or tools.get("scrot") or tools.get("grim"):
        actions.append({"action": "take_screenshot", "method": "available screenshot tool"})

    return actions


def main():
    entries = scan_desktop_entries()

    browser = infer_preferred_browser(entries)
    mail = infer_mail_client(entries)
    filemgr = infer_file_manager()
    terminal = infer_terminal()
    editors = infer_editors()
    cinnamon = detect_cinnamon()
    tools = detect_agent_tools()

    data = {
        "session": detect_session(),
        "os": detect_os(),
        "hardware": detect_hardware(),
        "network": detect_network_tools(),
        "browser": browser,
        "mail": mail,
        "file_manager": filemgr,
        "terminal": terminal,
        "editors": editors,
        "cinnamon": cinnamon,
        "agent_tools": tools,
        "flatpaks": detect_flatpaks(),
        "snaps": detect_snaps(),
        "desktop_entries_count": len(entries),
        "desktop_entries_sample": entries[:120],
        "user_configs": detect_user_configs(),
        "recent_user_signals": detect_recent_user_signals(),
    }

    data["possible_actions"] = derive_actions(
        browser, mail, filemgr, terminal, editors, cinnamon, tools
    )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
