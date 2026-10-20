"""Handles APK extraction, dex discovery and output directories."""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path


def default_output_dir() -> Path:
    """A user-writable directory for decompiled results."""
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local" / "share")))
    return base / "PyDex" / "output"


class FileManager:
    """Handles APK extraction, dex discovery and output directories."""

    def __init__(self, base_output_dir: str | Path | None = None) -> None:
        if base_output_dir is None:
            base_output_dir = default_output_dir()
        self.base_output_dir = Path(base_output_dir).resolve()
        self.base_output_dir.mkdir(parents=True, exist_ok=True)
        self._tmp_dir: Path | None = None

    def extract_apk(self, apk_path: str | Path) -> Path:
        apk_path = Path(apk_path).resolve()
        if not apk_path.is_file():
            raise FileNotFoundError(f"APK not found: {apk_path}")

        tmp = Path(tempfile.mkdtemp(prefix="pydex_apk_"))
        try:
            with zipfile.ZipFile(apk_path, "r") as zf:
                zf.extractall(tmp)
        except zipfile.BadZipFile as e:
            shutil.rmtree(tmp, ignore_errors=True)
            raise ValueError(f"Not a valid APK/ZIP file: {apk_path}") from e

        self._tmp_dir = tmp
        return tmp

    @staticmethod
    def find_dex_files(extract_root: Path) -> list[Path]:
        return sorted(extract_root.rglob("*.dex"))

    @staticmethod
    def find_java_files(java_root: Path) -> list[Path]:
        return sorted(java_root.rglob("*.java")) if java_root.is_dir() else []

    def prepare_output_dir(self, apk_path: str | Path) -> Path:
        stem = Path(apk_path).stem.replace(" ", "_")
        out = self.base_output_dir / f"{stem}_{int(__import__('time').time())}"
        out.mkdir(parents=True, exist_ok=True)
        return out

    def cleanup(self) -> None:
        if self._tmp_dir and self._tmp_dir.exists():
            shutil.rmtree(self._tmp_dir, ignore_errors=True)
            self._tmp_dir = None
