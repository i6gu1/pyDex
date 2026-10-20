"""Batch decompile — process multiple APKs sequentially."""

from __future__ import annotations

import threading
from pathlib import Path

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox

from ..core.decompiler import DecompilerEngine
from .i18n import t, is_rtl
from .theme import (
    CARD_BG, ACCENT, ACCENT_BRIGHT, ACCENT_DEEP, TEXT, MUTED,
    DARK_BG, CODE_BG, FONT_JP, FONT_UI, FONT_CODE,
)


class BatchDialog(ctk.CTkToplevel):
    def __init__(self, parent=None, lang: str = "ar"):
        super().__init__(parent)
        self.lang = lang
        self.rtl = is_rtl(lang)
        self.title(t(lang, "batch_title"))
        self.geometry("760x560")
        self.minsize(620, 440)
        self.configure(fg_color=DARK_BG)
        self.worker = None
        self._results: list[tuple[str, bool, str]] = []

        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=18, pady=14)
        ctk.CTkButton(bar, text=t(lang, "batch_add"), command=self._add,
                      fg_color=ACCENT, hover_color=ACCENT_BRIGHT, height=38,
                      font=ctk.CTkFont(family=FONT_JP, size=12, weight="bold")).pack(
            side="left" if self.rtl else "right")
        ctk.CTkButton(bar, text=t(lang, "batch_start"), command=self._start,
                      fg_color="transparent", border_color=ACCENT_DEEP, border_width=1,
                      hover_color=ACCENT_DEEP, text_color=TEXT, height=38,
                      font=ctk.CTkFont(family=FONT_JP, size=12, weight="bold")).pack(
            side="left" if self.rtl else "right", padx=8)
        self.status = ctk.CTkLabel(bar, text="",
                                   font=ctk.CTkFont(family=FONT_UI, size=11),
                                   text_color=MUTED)
        self.status.pack(side="right" if self.rtl else "left", padx=12)

        list_card = ctk.CTkFrame(self, corner_radius=16, fg_color=CARD_BG,
                                 border_color=ACCENT_DEEP, border_width=1)
        list_card.pack(fill="both", expand=True, padx=18, pady=(0, 14))
        self.listbox = tk.Listbox(list_card, bg=CODE_BG, fg=TEXT,
                                  font=(FONT_UI, 11), relief="flat",
                                  selectbackground=ACCENT, highlightthickness=0)
        self.listbox.pack(fill="both", expand=True, padx=8, pady=8)

    def _add(self):
        paths = filedialog.askopenfilenames(
            title=t(self.lang, "batch_add"),
            filetypes=[("APK files", "*.apk"), ("All", "*.*")])
        for p in paths:
            self.listbox.insert("end", p)

    def _start(self):
        items = list(self.listbox.get(0, "end"))
        if not items:
            return
        if self.worker and self.worker.is_alive():
            return
        self.worker = threading.Thread(target=self._run, args=(items,), daemon=True)
        self.worker.start()

    def _run(self, items):
        for i, path in enumerate(items, 1):
            self._set_status(t(lang, "batch_progress", i=i, total=len(items), name=Path(path).name))
            try:
                eng = DecompilerEngine()
                java_dir = eng.decompile(path, engine="jadx")
                n = len(list(java_dir.rglob("*.java")))
                self._results.append((path, True, str(java_dir)))
                self._append(f"✅ {Path(path).name} — {n} java")
            except Exception as e:
                self._results.append((path, False, str(e)))
                self._append(f"❌ {Path(path).name} — {str(e)[:80]}")
        self._set_status(t(lang, "batch_done", ok=sum(1 for _, ok, _ in self._results if ok),
                                          fail=sum(1 for _, ok, _ in self._results if not ok)))

    def _append(self, msg):
        self.listbox.insert("end", msg)
        self.listbox.see("end")

    def _set_status(self, msg):
        try:
            self.status.configure(text=msg)
        except Exception:
            pass
