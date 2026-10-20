"""Code & APK statistics viewer."""

from __future__ import annotations

from pathlib import Path

import customtkinter as ctk

from ..core.analyzer import code_stats, dex_stats, file_list
from .i18n import t, is_rtl
from .theme import (
    CARD_BG, ACCENT, ACCENT_BRIGHT, ACCENT_DEEP, TEXT, MUTED,
    DARK_BG, CODE_BG, FONT_JP, FONT_UI, FONT_CODE,
)


class StatsViewer(ctk.CTkToplevel):
    def __init__(self, java_root: Path, apk_path: Path, parent=None, lang: str = "ar"):
        super().__init__(parent)
        self.lang = lang
        self.rtl = is_rtl(lang)
        self.java_root = Path(java_root)
        self.apk_path = Path(apk_path)
        self.title(t(lang, "stats_title"))
        self.geometry("700x600")
        self.minsize(560, 480)
        self.configure(fg_color=DARK_BG)
        justify = "right" if self.rtl else "left"

        cs = code_stats(self.java_root)
        ds = dex_stats(self.apk_path)
        libs = file_list(self.apk_path, "lib/")
        assets = file_list(self.apk_path, "assets/")

        card = ctk.CTkFrame(self, corner_radius=18, fg_color=CARD_BG,
                            border_color=ACCENT_DEEP, border_width=1)
        card.pack(fill="both", expand=True, padx=18, pady=14)

        sections = [
            (t(lang, "stats_code"), [
                (t(lang, "stats_files"), cs["files"]),
                (t(lang, "stats_classes"), cs["classes"]),
                (t(lang, "stats_methods"), cs["methods"]),
                (t(lang, "stats_fields"), cs["fields"]),
                (t(lang, "stats_loc"), cs["loc"]),
            ]),
            (t(lang, "stats_dex"), [
                (t(lang, "stats_dex_files"), ds.get("dex_files", 0)),
                (t(lang, "stats_dex_classes"), ds.get("classes", 0)),
                (t(lang, "stats_dex_methods"), ds.get("methods", 0)),
            ]),
            (t(lang, "stats_native"), [
                (t(lang, "stats_native_libs"), len(libs)),
                (t(lang, "stats_assets"), len(assets)),
            ]),
        ]
        for section_title, rows in sections:
            ctk.CTkLabel(card, text=section_title,
                         font=ctk.CTkFont(family=FONT_JP, size=13, weight="bold"),
                         text_color=ACCENT_BRIGHT).pack(
                anchor="e" if self.rtl else "w", padx=18, pady=(14, 4))
            for label, value in rows:
                row = ctk.CTkFrame(card, fg_color="transparent")
                row.pack(fill="x", padx=18, pady=2)
                ctk.CTkLabel(row, text=label,
                             font=ctk.CTkFont(family=FONT_UI, size=11),
                             text_color=MUTED).pack(side="right" if self.rtl else "left")
                ctk.CTkLabel(row, text=str(value),
                             font=ctk.CTkFont(family=FONT_CODE, size=12, weight="bold"),
                             text_color=TEXT).pack(side="left" if self.rtl else "right")
