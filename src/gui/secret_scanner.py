"""Secret & endpoint scanner — find URLs, API keys, tokens in decompiled code."""

from __future__ import annotations

from pathlib import Path

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk

from ..core.analyzer import scan_secrets
from .i18n import t, is_rtl
from .theme import (
    CARD_BG, ACCENT, ACCENT_BRIGHT, ACCENT_DEEP, TEXT, MUTED,
    DARK_BG, CODE_BG, FONT_JP, FONT_UI, FONT_CODE,
)


class SecretScanner(ctk.CTkToplevel):
    def __init__(self, java_root: Path, apk_path: Path, parent=None, lang: str = "ar"):
        super().__init__(parent)
        self.lang = lang
        self.rtl = is_rtl(lang)
        self.java_root = Path(java_root)
        self.apk_path = Path(apk_path)
        self.title(t(lang, "secrets_title"))
        self.geometry("1000x660")
        self.minsize(780, 500)
        self.configure(fg_color=DARK_BG)
        justify = "right" if self.rtl else "left"

        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=18, pady=14)
        ctk.CTkButton(bar, text=t(lang, "scan_btn"), command=self._scan,
                      fg_color=ACCENT, hover_color=ACCENT_BRIGHT, height=38,
                      font=ctk.CTkFont(family=FONT_JP, size=12, weight="bold")).pack(
            side="left" if self.rtl else "right")
        self.status = ctk.CTkLabel(bar, text="",
                                   font=ctk.CTkFont(family=FONT_UI, size=11),
                                   text_color=MUTED)
        self.status.pack(side="right" if self.rtl else "left", padx=12)

        tree_card = ctk.CTkFrame(self, corner_radius=16, fg_color=CARD_BG,
                                 border_color=ACCENT_DEEP, border_width=1)
        tree_card.pack(fill="both", expand=True, padx=18, pady=(0, 14))
        tc = tk.Frame(tree_card, bg=CARD_BG)
        tc.pack(fill="both", expand=True, padx=8, pady=8)
        tc.rowconfigure(0, weight=1)
        tc.columnconfigure(0, weight=1)
        self.tree = ttk.Treeview(tc, show="headings",
                                 columns=("kind", "file", "line", "text"))
        self.tree.heading("kind", text=t(lang, "col_kind"))
        self.tree.heading("file", text=t(lang, "col_file"))
        self.tree.heading("line", text=t(lang, "col_line"))
        self.tree.heading("text", text=t(lang, "col_text"))
        self.tree.column("kind", width=120, anchor="w")
        self.tree.column("file", width=300, anchor="w")
        self.tree.column("line", width=50, anchor="center")
        self.tree.column("text", width=420, anchor="w")
        vsb = ttk.Scrollbar(tc, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")

    def _scan(self):
        for iid in self.tree.get_children():
            self.tree.delete(iid)
        findings = scan_secrets(self.java_root, self.apk_path)
        for f in findings:
            rel = str(Path(f["file"]).relative_to(self.java_root)) if self.java_root in Path(f["file"]).parents else f["file"]
            self.tree.insert("", "end", values=(
                f["kind"], rel, f["line"], f["text"]))
        self.status.configure(text=t(lang, "secrets_found", n=len(findings)))
