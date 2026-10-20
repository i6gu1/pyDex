"""Global code search across all decompiled Java files."""

from __future__ import annotations

import re
from pathlib import Path

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk

from .i18n import t, is_rtl
from .theme import (
    CARD_BG, ACCENT, ACCENT_BRIGHT, ACCENT_DEEP, TEXT, MUTED, TEXT_DIM,
    DARK_BG, CODE_BG, FONT_JP, FONT_UI, FONT_CODE,
)


class SearchDialog(ctk.CTkToplevel):
    def __init__(self, java_root: Path, parent=None, lang: str = "ar"):
        super().__init__(parent)
        self.lang = lang
        self.rtl = is_rtl(lang)
        self.java_root = Path(java_root)
        self.title(t(lang, "search_title"))
        self.geometry("980x640")
        self.minsize(760, 480)
        self.configure(fg_color=DARK_BG)
        justify = "right" if self.rtl else "left"

        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=18, pady=14)

        self.query = tk.StringVar()
        entry = ctk.CTkEntry(
            bar, textvariable=self.query, placeholder_text=t(lang, "search_placeholder"),
            fg_color=CODE_BG, border_color=ACCENT_DEEP, height=40,
            font=ctk.CTkFont(family=FONT_UI, size=13))
        if self.rtl:
            entry.pack(side="right", fill="x", expand=True)
        else:
            entry.pack(side="left", fill="x", expand=True)
        entry.bind("<Return>", lambda _e: self._run())
        entry.focus_set()

        self.case_var = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(bar, text=t(lang, "case_sensitive"), variable=self.case_var,
                        text_color=MUTED, fg_color=ACCENT, hover_color=ACCENT_BRIGHT,
                        font=ctk.CTkFont(family=FONT_UI, size=11)).pack(
            side="right" if self.rtl else "left", padx=10)

        ctk.CTkButton(bar, text=t(lang, "search_btn"), command=self._run,
                      fg_color=ACCENT, hover_color=ACCENT_BRIGHT, height=40,
                      font=ctk.CTkFont(family=FONT_JP, size=12, weight="bold")).pack(
            side="left" if self.rtl else "right")

        self.status = ctk.CTkLabel(self, text="", text_color=MUTED,
                                   font=ctk.CTkFont(family=FONT_UI, size=11))
        self.status.pack(anchor="e" if self.rtl else "w", padx=20)

        # results tree
        tree_card = ctk.CTkFrame(self, corner_radius=16, fg_color=CARD_BG,
                                 border_color=ACCENT_DEEP, border_width=1)
        tree_card.pack(fill="both", expand=True, padx=18, pady=(0, 14))
        tc = tk.Frame(tree_card, bg=CARD_BG)
        tc.pack(fill="both", expand=True, padx=8, pady=8)
        tc.rowconfigure(0, weight=1)
        tc.columnconfigure(0, weight=1)
        self.tree = ttk.Treeview(tc, show="headings",
                                 columns=("file", "line", "text"))
        self.tree.heading("file", text=t(lang, "col_file"))
        self.tree.heading("line", text=t(lang, "col_line"))
        self.tree.heading("text", text=t(lang, "col_text"))
        self.tree.column("file", width=340, anchor="w")
        self.tree.column("line", width=60, anchor="center")
        self.tree.column("text", width=480, anchor="w")
        vsb = ttk.Scrollbar(tc, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        self.tree.bind("<Double-1>", self._open_result)

        self._results: list[tuple[Path, int, str]] = []

    def _run(self):
        q = self.query.get().strip()
        for iid in self.tree.get_children():
            self.tree.delete(iid)
        self._results.clear()
        if not q:
            self.status.configure(text=t(lang, "search_empty"))
            return
        try:
            rx = re.compile(re.escape(q), 0 if self.case_var.get() else re.I)
        except re.error:
            self.status.configure(text=t(lang, "search_invalid"))
            return
        files = sorted(self.java_root.rglob("*.java"))
        count = 0
        for f in files:
            try:
                lines = f.read_text(encoding="utf-8", errors="replace").splitlines()
            except Exception:
                continue
            for i, line in enumerate(lines, 1):
                if rx.search(line):
                    rel = str(f.relative_to(self.java_root))
                    snippet = line.strip()[:120]
                    self.tree.insert("", "end", values=(rel, i, snippet))
                    self._results.append((f, i, snippet))
                    count += 1
                    if count >= 2000:
                        break
            if count >= 2000:
                break
        self.status.configure(text=t(lang, "search_results", n=count, total=len(files)))

    def _open_result(self, _e=None):
        sel = self.tree.selection()
        if not sel:
            return
        idx = self.tree.index(sel[0])
        if 0 <= idx < len(self._results):
            f, line, _ = self._results[idx]
            try:
                import subprocess, sys, os
                if sys.platform.startswith("win"):
                    subprocess.Popen(["cmd", "/c", "start", "", str(f)])
                elif sys.platform == "darwin":
                    subprocess.Popen(["open", str(f)])
                else:
                    subprocess.Popen(["xdg-open", str(f)])
            except Exception:
                pass
