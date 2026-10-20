"""Persistent user settings (language etc.) for PyDex."""

from __future__ import annotations

import json
from pathlib import Path


def _cfg_path() -> Path:
    if __import__("sys").platform == "win32":
        base = Path(__import__("os").environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local")))
    else:
        base = Path.home() / ".config"
    d = base / "PyDex"
    d.mkdir(parents=True, exist_ok=True)
    return d / "settings.json"


def load_lang(default: str = "ar") -> str:
    p = _cfg_path()
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        v = data.get("lang", default)
        if v in ("ar", "en"):
            return v
    except Exception:
        pass
    return default


def save_lang(lang: str) -> None:
    p = _cfg_path()
    data = {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        pass
    data["lang"] = lang
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
