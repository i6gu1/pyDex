"""AndroidManifest viewer with permission risk analysis."""

from __future__ import annotations

from pathlib import Path

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk

from ..core.analyzer import parse_manifest, DANGEROUS_PERMISSIONS
from .i18n import t, is_rtl
from .theme import (
    CARD_BG, ACCENT, ACCENT_BRIGHT, ACCENT_DEEP, TEXT, MUTED, TEXT_DIM,
    DARK_BG, CODE_BG, FONT_JP, FONT_UI, FONT_CODE,
)


class ManifestViewer(ctk.CTkToplevel):
    def __init__(self, apk_path: Path, parent=None, lang: str = "ar"):
        super().__init__(parent)
        self.lang = lang
        self.rtl = is_rtl(lang)
        self.apk_path = Path(apk_path)
        self.title(t(lang, "manifest_title"))
        self.geometry("980x680")
        self.minsize(760, 520)
        self.configure(fg_color=DARK_BG)
        justify = "right" if self.rtl else "left"

        self.info = parse_manifest(self.apk_path)

        # header card
        head = ctk.CTkFrame(self, corner_radius=18, fg_color=CARD_BG,
                            border_color=ACCENT_DEEP, border_width=1)
        head.pack(fill="x", padx=18, pady=14)
        pkg = self.info.get("package") or "?"
        ctk.CTkLabel(head, text=pkg,
                     font=ctk.CTkFont(family=FONT_UI, size=18, weight="bold"),
                     text_color=TEXT, justify=justify).pack(
            anchor="e" if self.rtl else "w", padx=18, pady=(12, 2))
        meta = t(lang, "manifest_meta",
                 ver=self.info.get("version_name", "?"),
                 code=self.info.get("version_code", "?"),
                 min=self.info.get("min_sdk", "?"),
                 tgt=self.info.get("target_sdk", "?"))
        ctk.CTkLabel(head, text=meta,
                     font=ctk.CTkFont(family=FONT_UI, size=11),
                     text_color=MUTED, justify=justify).pack(
            anchor="e" if self.rtl else "w", padx=18, pady=(0, 12))

        # tabs
        self.tabview = ctk.CTkTabview(self, fg_color=CARD_BG,
                                      segmented_button_fg_color=ACCENT_DEEP,
                                      segmented_button_selected_color=ACCENT,
                                      segmented_button_selected_hover_color=ACCENT_BRIGHT,
                                      text_color=TEXT)
        self.tabview.pack(fill="both", expand=True, padx=18, pady=(0, 14))
        self.tabview.add(t(lang, "tab_permissions"))
        self.tabview.add(t(lang, "tab_components"))
        self.tabview.add(t(lang, "tab_raw"))

        self._build_permissions(self.tabview.tab(t(lang, "tab_permissions")))
        self._build_components(self.tabview.tab(t(lang, "tab_components")))
        self._build_raw(self.tabview.tab(t(lang, "tab_raw")))

    def _build_permissions(self, tab):
        # dangerous perms summary
        perms = self.info.get("permissions", [])
        dangerous = [p for p in perms if p in DANGEROUS_PERMISSIONS]
        warn = t(lang, "perm_dangerous", n=len(dangerous), total=len(perms))
        ctk.CTkLabel(tab, text=warn,
                     font=ctk.CTkFont(family=FONT_UI, size=11, weight="bold"),
                     text_color=ACCENT_BRIGHT if dangerous else MUTED).pack(
            anchor="e" if self.rtl else "w", padx=12, pady=(10, 4))

        tc = tk.Frame(tab, bg=CARD_BG)
        tc.pack(fill="both", expand=True, padx=8, pady=8)
        tc.rowconfigure(0, weight=1)
        tc.columnconfigure(0, weight=1)
        tree = ttk.Treeview(tc, show="headings", columns=("perm", "risk"))
        tree.heading("perm", text=t(lang, "col_permission"))
        tree.heading("risk", text=t(lang, "col_risk"))
        tree.column("perm", width=560, anchor="w")
        tree.column("risk", width=120, anchor="center")
        vsb = ttk.Scrollbar(tc, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        for p in perms:
            risk = t(lang, "risk_high") if p in DANGEROUS_PERMISSIONS else t(lang, "risk_normal")
            tree.insert("", "end", values=(p, risk))

    def _build_components(self, tab):
        tc = tk.Frame(tab, bg=CARD_BG)
        tc.pack(fill="both", expand=True, padx=8, pady=8)
        tc.rowconfigure(0, weight=1)
        tc.columnconfigure(0, weight=1)
        tree = ttk.Treeview(tc, show="headings", columns=("type", "name"))
        tree.heading("type", text=t(lang, "col_type"))
        tree.heading("name", text=t(lang, "col_name"))
        tree.column("type", width=140, anchor="w")
        tree.column("name", width=560, anchor="w")
        vsb = ttk.Scrollbar(tc, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        for key, label in (("activities", "component_activity"),
                           ("services", "component_service"),
                           ("receivers", "component_receiver"),
                           ("providers", "component_provider")):
            for name in self.info.get(key, []):
                tree.insert("", "end", values=(t(lang, label), name))

    def _build_raw(self, tab):
        txt = tk.Text(tab, bg=CODE_BG, fg=TEXT, font=(FONT_CODE, 10),
                      relief="flat", insertbackground=TEXT, wrap="none")
        xsb = ttk.Scrollbar(tab, orient="horizontal", command=txt.xview)
        vsb = ttk.Scrollbar(tab, orient="vertical", command=txt.yview)
        txt.configure(xscrollcommand=xsb.set, yscrollcommand=vsb.set)
        txt.pack(fill="both", expand=True, padx=8, pady=8)
        xsb.pack(fill="x")
        vsb.pack(side="right", fill="y")
        raw = self.info.get("raw") or t(lang, "manifest_error",
                                        err=self.info.get("error", "unknown"))
        txt.insert("1.0", raw)
        txt.configure(state="disabled")
