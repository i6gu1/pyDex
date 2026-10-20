"""APK signing certificate viewer."""

from __future__ import annotations

from pathlib import Path

import customtkinter as ctk
import tkinter as tk

from ..core.analyzer import cert_info
from .i18n import t, is_rtl
from .theme import (
    CARD_BG, ACCENT, ACCENT_BRIGHT, ACCENT_DEEP, TEXT, MUTED,
    DARK_BG, CODE_BG, FONT_JP, FONT_UI, FONT_CODE,
)


class CertInfo(ctk.CTkToplevel):
    def __init__(self, apk_path: Path, parent=None, lang: str = "ar"):
        super().__init__(parent)
        self.lang = lang
        self.rtl = is_rtl(lang)
        self.apk_path = Path(apk_path)
        self.title(t(lang, "cert_title"))
        self.geometry("760x560")
        self.minsize(600, 440)
        self.configure(fg_color=DARK_BG)
        justify = "right" if self.rtl else "left"

        self.info = cert_info(self.apk_path)

        card = ctk.CTkFrame(self, corner_radius=18, fg_color=CARD_BG,
                            border_color=ACCENT_DEEP, border_width=1)
        card.pack(fill="both", expand=True, padx=18, pady=14)

        if not self.info.get("found"):
            ctk.CTkLabel(card, text=t(lang, "cert_not_found"),
                         font=ctk.CTkFont(family=FONT_UI, size=14),
                         text_color=MUTED).pack(pady=40)
            return

        rows = [
            (t(lang, "cert_subject"), self.info.get("subject", "")),
            (t(lang, "cert_issuer"), self.info.get("issuer", "")),
            (t(lang, "cert_valid_from"), self.info.get("valid_from", "")),
            (t(lang, "cert_valid_to"), self.info.get("valid_to", "")),
            (t(lang, "cert_sha1"), self.info.get("sha1", "")),
            (t(lang, "cert_sha256"), self.info.get("sha256", "")),
        ]
        for label, value in rows:
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=18, pady=(10, 0))
            ctk.CTkLabel(row, text=label,
                         font=ctk.CTkFont(family=FONT_UI, size=11, weight="bold"),
                         text_color=ACCENT_BRIGHT, width=140,
                         anchor="e" if self.rtl else "w").pack(
                side="right" if self.rtl else "left")
            ctk.CTkLabel(row, text=value or "—",
                         font=ctk.CTkFont(family=FONT_CODE, size=11),
                         text_color=TEXT, justify=justify).pack(
                side="right" if self.rtl else "left", fill="x", expand=True)
