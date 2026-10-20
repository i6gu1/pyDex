"""Resource browser — view decoded XML resources and preview images."""

from __future__ import annotations

from pathlib import Path

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

from .i18n import t, is_rtl
from .theme import (
    CARD_BG, ACCENT, ACCENT_BRIGHT, ACCENT_DEEP, TEXT, MUTED,
    DARK_BG, CODE_BG, FONT_JP, FONT_UI, FONT_CODE,
)

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}


class ResourceBrowser(ctk.CTkToplevel):
    def __init__(self, resources_dir: Path, parent=None, lang: str = "ar"):
        super().__init__(parent)
        self.lang = lang
        self.rtl = is_rtl(lang)
        self.root = Path(resources_dir)
        self.title(t(lang, "resources_title"))
        self.geometry("1100x720")
        self.minsize(860, 560)
        self.configure(fg_color=DARK_BG)
        justify = "right" if self.rtl else "left"
        self._image_ref = None

        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=18, pady=14)
        self.count_lbl = ctk.CTkLabel(bar, text="",
                                      font=ctk.CTkFont(family=FONT_UI, size=11),
                                      text_color=MUTED)
        self.count_lbl.pack(side="right" if self.rtl else "left")

        pane = ctk.CTkFrame(self, fg_color="transparent")
        pane.pack(fill="both", expand=True, padx=18, pady=(0, 14))

        tree_frame = ctk.CTkFrame(pane, corner_radius=16, fg_color=CARD_BG,
                                  border_color=ACCENT_DEEP, border_width=1)
        preview_card = ctk.CTkFrame(pane, corner_radius=16, fg_color=CARD_BG,
                                    border_color=ACCENT_DEEP, border_width=1)
        if self.rtl:
            preview_card.pack(side="left", fill="both", expand=True, padx=(0, 10))
            tree_frame.pack(side="right", fill="y")
        else:
            tree_frame.pack(side="left", fill="y", padx=(0, 10))
            preview_card.pack(side="left", fill="both", expand=True)

        self.tree = ttk.Treeview(tree_frame, show="tree")
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(fill="both", expand=True, padx=8, pady=8)
        vsb.pack(side="right", fill="y")
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        ctk.CTkLabel(preview_card, text=t(lang, "preview_title"),
                     font=ctk.CTkFont(family=FONT_JP, size=12, weight="bold"),
                     text_color=TEXT).pack(anchor="e" if self.rtl else "w", padx=12, pady=8)
        self.preview_lbl = ctk.CTkLabel(preview_card, text="", image=None)
        self.preview_lbl.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.path_lbl = ctk.CTkLabel(preview_card, text="", text_color=MUTED,
                                     font=ctk.CTkFont(family=FONT_UI, size=10))
        self.path_lbl.pack(anchor="e" if self.rtl else "w", padx=12, pady=(0, 10))

        self._all = sorted(p for p in self.root.rglob("*") if p.is_file()) if self.root.is_dir() else []
        self._build_tree()
        self.count_lbl.configure(text=t(lang, "resources_count", n=len(self._all)))

    def _build_tree(self):
        self.tree.delete(*self.tree.get_children())
        dirs: dict[str, str] = {}
        for f in self._all:
            rel = f.relative_to(self.root)
            parent = str(rel.parent)
            if parent not in dirs:
                dirs[parent] = self.tree.insert("", "end", text=parent, open=True)
            self.tree.insert(dirs[parent], "end", text=rel.name, values=(str(f),))

    def _on_select(self, _e=None):
        sel = self.tree.selection()
        if not sel:
            return
        vals = self.tree.item(sel[0], "values")
        if not vals:
            self.preview_lbl.configure(image=None, text="")
            return
        path = Path(vals[0])
        self.path_lbl.configure(text=str(path.relative_to(self.root)))
        if path.suffix.lower() in IMAGE_EXTS:
            self._show_image(path)
        else:
            self.preview_lbl.configure(image=None, text="")

    def _show_image(self, path):
        try:
            im = Image.open(path).convert("RGBA")
            im.thumbnail((520, 520), Image.LANCZOS)
            photo = ImageTk.PhotoImage(im)
            self._image_ref = photo
            self.preview_lbl.configure(image=photo, text="")
        except Exception as e:
            self.preview_lbl.configure(image=None, text=str(e)[:120])
