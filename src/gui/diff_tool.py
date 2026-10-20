"""Diff two decompiled Java source trees."""

from __future__ import annotations

import difflib
from pathlib import Path

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, filedialog

from .i18n import t, is_rtl
from .theme import (
    CARD_BG, ACCENT, ACCENT_BRIGHT, ACCENT_DEEP, TEXT, MUTED,
    DARK_BG, CODE_BG, FONT_JP, FONT_UI, FONT_CODE,
)


class DiffTool(ctk.CTkToplevel):
    def __init__(self, parent=None, lang: str = "ar"):
        super().__init__(parent)
        self.lang = lang
        self.rtl = is_rtl(lang)
        self.title(t(lang, "diff_title"))
        self.geometry("1100x720")
        self.minsize(860, 560)
        self.configure(fg_color=DARK_BG)
        justify = "right" if self.rtl else "left"

        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=18, pady=14)

        self.dir_a = tk.StringVar()
        self.dir_b = tk.StringVar()

        for label_text, var in ((t(lang, "diff_dir_a"), self.dir_a),
                                 (t(lang, "diff_dir_b"), self.dir_b)):
            row = ctk.CTkFrame(bar, fg_color="transparent")
            row.pack(fill="x", pady=(0, 6))
            ctk.CTkLabel(row, text=label_text,
                         font=ctk.CTkFont(family=FONT_UI, size=11),
                         text_color=MUTED, width=80).pack(side="right" if self.rtl else "left")
            ctk.CTkEntry(row, textvariable=var, fg_color=CODE_BG,
                         border_color=ACCENT_DEEP, height=34).pack(
                side="right" if self.rtl else "left", fill="x", expand=True)

        ctk.CTkButton(bar, text=t(lang, "diff_browse"), command=self._browse,
                      fg_color="transparent", border_color=ACCENT_DEEP, border_width=1,
                      hover_color=ACCENT_DEEP, text_color=TEXT, height=34,
                      font=ctk.CTkFont(family=FONT_JP, size=11)).pack(
            side="left" if self.rtl else "right", pady=(0, 6))
        ctk.CTkButton(bar, text=t(lang, "diff_run"), command=self._run,
                      fg_color=ACCENT, hover_color=ACCENT_BRIGHT, height=34,
                      font=ctk.CTkFont(family=FONT_JP, size=12, weight="bold")).pack(
            side="left" if self.rtl else "right", padx=8)

        self.status = ctk.CTkLabel(bar, text="", text_color=MUTED,
                                   font=ctk.CTkFont(family=FONT_UI, size=11))
        self.status.pack(anchor="e" if self.rtl else "w", padx=12)

        txt_card = ctk.CTkFrame(self, corner_radius=16, fg_color=CARD_BG,
                                border_color=ACCENT_DEEP, border_width=1)
        txt_card.pack(fill="both", expand=True, padx=18, pady=(0, 14))
        self.txt = tk.Text(txt_card, bg=CODE_BG, fg=TEXT, font=(FONT_CODE, 10),
                           relief="flat", insertbackground=TEXT, wrap="none")
        xsb = ttk.Scrollbar(txt_card, orient="horizontal", command=self.txt.xview)
        vsb = ttk.Scrollbar(txt_card, orient="vertical", command=self.txt.yview)
        self.txt.configure(xscrollcommand=xsb.set, yscrollcommand=vsb.set)
        self.txt.pack(fill="both", expand=True, padx=8, pady=8)
        xsb.pack(fill="x")
        vsb.pack(side="right", fill="y")
        self.txt.configure(state="disabled")

    def _browse(self):
        path = filedialog.askdirectory(title=t(lang, "diff_browse"))
        if path:
            if not self.dir_a.get():
                self.dir_a.set(path)
            else:
                self.dir_b.set(path)

    def _run(self):
        a = Path(self.dir_a.get())
        b = Path(self.dir_b.get())
        if not a.is_dir() or not b.is_dir():
            self.status.configure(text=t(lang, "diff_invalid"))
            return
        files_a = {str(f.relative_to(a)) for f in a.rglob("*.java")}
        files_b = {str(f.relative_to(b)) for f in b.rglob("*.java")}
        only_a = sorted(files_a - files_b)
        only_b = sorted(files_b - files_a)
        common = sorted(files_a & files_b)
        changed = 0
        lines = []
        for rel in only_a:
            lines.append(f"--- ONLY IN A: {rel}")
        for rel in only_b:
            lines.append(f"+++ ONLY IN B: {rel}")
        for rel in common:
            ta = (a / rel).read_text(encoding="utf-8", errors="replace").splitlines()
            tb = (b / rel).read_text(encoding="utf-8", errors="replace").splitlines()
            diff = list(difflib.unified_diff(ta, tb, lineterm="", n=1))
            if diff:
                changed += 1
                lines.append(f"### {rel}")
                lines.extend(diff[2:])
        self.txt.configure(state="normal")
        self.txt.delete("1.0", "end")
        self.txt.insert("1.0", "\n".join(lines) if lines else t(lang, "diff_identical"))
        self.txt.configure(state="disabled")
        self.status.configure(text=t(lang, "diff_result",
                                     only_a=len(only_a), only_b=len(only_b),
                                     changed=changed, common=len(common)))
