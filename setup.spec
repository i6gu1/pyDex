# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for PyDex (パイデックス). Build with: pyinstaller setup.spec"""
from pathlib import Path

block_cipher = None

ROOT = Path(SPECPATH).resolve()

a = Analysis(
    ["src/main.py"],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[
        ("tools", "tools"),
        ("Lain.jfif", "."),
        ("ii'm like antoher.jfif", "."),
        ("assets", "assets"),
    ],
    hiddenimports=[
        "tkinter", "tkinter.ttk", "tkinter.filedialog", "tkinter.messagebox",
        "src.gui.main_window", "src.gui.code_viewer",
        "src.gui.search_dialog", "src.gui.manifest_viewer",
        "src.gui.resource_browser", "src.gui.secret_scanner",
        "src.gui.cert_info", "src.gui.stats_viewer", "src.gui.diff_tool",
        "src.gui.privacy_dialog", "src.gui.theme",
        "src.core.decompiler", "src.core.file_manager", "src.core.analyzer",
        "PIL", "customtkinter", "pyaxmlparser", "lxml",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["PyQt5", "PyQt6", "PySide6"],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    exclude_binaries=True,
    name="PyDex",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=str(ROOT / "assets" / "icon.ico") if (ROOT / "assets" / "icon.ico").exists() else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name="PyDex",
)
