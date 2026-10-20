"""Offscreen smoke test for the rebuilt Tk/CustomTkinter GUI."""
import os
import sys
import tempfile
from pathlib import Path

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

import customtkinter as ctk

from src.gui.main_window import MainWindow
from src.gui.privacy_dialog import PrivacyDialog
from src.gui.code_viewer import CodeViewer
from src.gui.theme import DARK_BG

# headless-ish: need display; on CI without display may fail. This window server
# may provide one. We still try.
try:
    m = MainWindow()
except Exception as e:
    print("MainWindow failed:", repr(e))
    raise

# feed a dummy apk-ish file
tmp = Path(tempfile.mkdtemp(prefix="pydex_smoke_"))
apk = tmp / "demo.apk"
apk.write_bytes(b"PK\x03\x04dummy")
m._set_apk(apk)
assert m.btn_run.cget("state") in ("normal", "Normal"), m.btn_run.cget("state")
print("MainWindow OK", m.btn_run.cget("state"))

p = PrivacyDialog(m)
print("PrivacyDialog OK")
p.destroy()

# code viewer with a fake java tree
cvtmp = Path(tempfile.mkdtemp(prefix="pydex_cv_"))
pkg = cvtmp / "com" / "example"
pkg.mkdir(parents=True)
(pkg / "Main.java").write_text(
    'package com.example;\npublic class Main {\n'
    '  public static void main(String[] a){\n'
    '    System.out.println("hi pydex"); // comment\n  }\n}\n',
    encoding="utf-8")
cv = CodeViewer(cvtmp, m)
assert "public class Main" in cv.txt.get("1.0", "end")
print("CodeViewer OK:", len(cv._files), "file(s)", "lines:", cv.txt.index("end"))

cv.destroy()
m.destroy()
print("SMOKE-OK")
