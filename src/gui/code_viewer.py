"""Java code viewer — package tree + highlighted source + search (Tk/CustomTkinter)."""

from __future__ import annotations

import shutil
from pathlib import Path

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, filedialog
from PIL import Image, ImageOps

from .i18n import t, is_rtl
from .theme import (
    APP_NAME_JP, FOOTER_TEXT, find_artwork,
    DARK_RED, CARD_BG, ACCENT, ACCENT_BRIGHT, ACCENT_DEEP, TEXT, MUTED, TEXT_DIM,
    DARK_BG, CODE_BG, FONT_JP, FONT_UI, FONT_CODE,
)

JAVA_KEYWORDS = frozenset(
    {"abstract", "assert", "boolean", "break", "byte", "case", "catch", "char",
     "class", "const", "continue", "default", "do", "double", "else", "enum",
     "extends", "final", "finally", "float", "for", "goto", "if", "implements",
     "import", "instanceof", "int", "interface", "long", "native", "new",
     "package", "private", "protected", "public", "return", "short", "static",
     "strictfp", "super", "switch", "synchronized", "this", "throw", "throws",
     "transient", "try", "void", "volatile", "while", "var", "null", "true",
     "false", "record", "sealed", "permits"}
)


class CodeViewer(ctk.CTkToplevel):
    def __init__(self, java_dir, parent=None, lang: str = "ar"):
        super().__init__(parent)
        self.lang = lang
        self.rtl = is_rtl(lang)
        self.java_root = Path(java_dir)
        self._files = sorted(self.java_root.rglob("*.java"))

        self.title(t(lang, "privacy_title").replace(" الخصوصية", " • Java Source Viewer") if False else "パイデックス • Java Source Viewer")
        self.geometry("1200x820")
        self.minsize(900, 600)
        self.configure(fg_color=DARK_BG)

        justify = "right" if self.rtl else "left"

        # toolbar
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=18, pady=14)

        self.search_var = tk.StringVar()
        search = ctk.CTkEntry(
            bar, textvariable=self.search_var,
            placeholder_text=t(lang, "search_placeholder"),
            fg_color=CODE_BG, border_color=ACCENT_DEEP, width=320,
            font=ctk.CTkFont(family=FONT_UI, size=11),

        )
        if self.rtl:
            search.pack(side="right")
        else:
            search.pack(side="left")
        search.bind("<KeyRelease>", lambda _e: self._filter_tree())

        self.count_lbl = ctk.CTkLabel(bar, text=t(lang, "java_files_count", shown=len(self._files), total=len(self._files)),
                                     font=ctk.CTkFont(family=FONT_UI, size=11),
                                     text_color=MUTED)
        self.count_lbl.pack(side="right" if self.rtl else "left", padx=12)

        export_btn = ctk.CTkButton(
            bar, text=t(lang, "export"), command=self._export,
            fg_color="transparent", border_color=ACCENT_DEEP, border_width=1,
            hover_color=ACCENT_DEEP, text_color=TEXT,
            font=ctk.CTkFont(family=FONT_JP, size=11))
        export_btn.pack(side="left" if self.rtl else "right")

        zip_btn = ctk.CTkButton(
            bar, text=t(lang, "export_zip"), command=self._export_zip,
            fg_color="transparent", border_color=ACCENT_DEEP, border_width=1,
            hover_color=ACCENT_DEEP, text_color=TEXT,
            font=ctk.CTkFont(family=FONT_JP, size=11))
        zip_btn.pack(side="left" if self.rtl else "right", padx=(0, 8) if self.rtl else (8, 0))

        # splitter
        pane = ctk.CTkFrame(self, fg_color="transparent")
        pane.pack(fill="both", expand=True, padx=18, pady=(0, 6))

        tree_frame = ctk.CTkFrame(pane, corner_radius=16, fg_color=CARD_BG,
                                  border_color=ACCENT_DEEP, border_width=1)
        # editor first decision
        editor_card = ctk.CTkFrame(pane, corner_radius=16, fg_color=CARD_BG,
                                   border_color=ACCENT_DEEP, border_width=1)

        # put tree on the reading-start side
        if self.rtl:
            # tree on right, editor on left
            editor_card.pack(side="left", fill="both", expand=True, padx=(0, 10))
            tree_frame.pack(side="right", fill="y")
        else:
            tree_frame.pack(side="left", fill="y", padx=(0, 10))
            editor_card.pack(side="left", fill="both", expand=True)

        ctk.CTkLabel(tree_frame, text=t(lang, "packages"),
                     font=ctk.CTkFont(family=FONT_JP, size=12, weight="bold"),
                     text_color=TEXT, justify=justify).pack(
            anchor="e" if self.rtl else "w", padx=12, pady=8)

        tree_container = tk.Frame(tree_frame, bg=CARD_BG)
        tree_container.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        tree_container.rowconfigure(0, weight=1)
        tree_container.columnconfigure(0, weight=1)

        self.tree = ttk.Treeview(tree_container, show="tree")
        vsb = ttk.Scrollbar(tree_container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.tree.bind("<Double-1>", self._on_select)

        path_bar = ctk.CTkFrame(editor_card, fg_color="transparent")
        path_bar.pack(fill="x", padx=12, pady=8)
        self.path_lbl = ctk.CTkLabel(path_bar, text="", text_color=MUTED,
                                     font=ctk.CTkFont(family=FONT_UI, size=10),
                                     justify=justify)
        self.path_lbl.pack(side="right" if self.rtl else "left")

        txt_frame = tk.Frame(editor_card, bg=CODE_BG)
        txt_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        txt_frame.rowconfigure(0, weight=1)
        txt_frame.columnconfigure(0, weight=1)
        self.txt = tk.Text(txt_frame, bg=CODE_BG, fg=TEXT, font=(FONT_CODE, 11),
                           relief="flat", insertbackground=TEXT, wrap="none",
                           selectbackground=ACCENT, undo=False)
        xsb = ttk.Scrollbar(txt_frame, orient="horizontal", command=self.txt.xview)
        vsb2 = ttk.Scrollbar(txt_frame, orient="vertical", command=self.txt.yview)
        self.txt.configure(xscrollcommand=xsb.set, yscrollcommand=vsb2.set)
        self.txt.grid(row=0, column=0, sticky="nsew")
        xsb.grid(row=1, column=0, sticky="ew")
        vsb2.grid(row=0, column=1, sticky="ns")
        self.txt.tag_configure("kw", foreground="#ff6b6b", font=(FONT_CODE, 11, "bold"))
        self.txt.tag_configure("str", foreground="#a5ff8a")
        self.txt.tag_configure("com", foreground="#6a5a5a",
                               font=(FONT_CODE, 11, "italic"))
        self.txt.tag_configure("num", foreground="#ffd9a0")
        self.txt.tag_configure("ann", foreground="#ff9ad9")
        self.txt.configure(state="disabled")

        foot = ctk.CTkLabel(self, text=t(lang, "footer"),
                            font=ctk.CTkFont(family=FONT_UI, size=10), text_color=MUTED)
        foot.pack(pady=(4, 10))

        self._build_tree()
        if self._files:
            self._open_file(self._files[0])
        else:
            self.txt.configure(state="normal")
            self.txt.insert("1.0", t(lang, "no_java"))
            self.txt.configure(state="disabled")

    def _build_tree(self, filt=""):
        self.tree.delete(*self.tree.get_children())
        filt = filt.lower().strip()
        roots_by_key = {}
        shown = 0
        for f in self._files:
            rel = f.relative_to(self.java_root)
            if filt and filt not in str(rel).lower():
                continue
            parts = rel.parts
            parent_iid = ""
            for i, part in enumerate(parts[:-1]):
                key = "/".join(parts[:i + 1])
                if key not in roots_by_key:
                    iid = self.tree.insert(parent_iid, "end", text=part, open=True)
                    roots_by_key[key] = iid
                parent_iid = roots_by_key[key]
            self.tree.insert(parent_iid, "end", text=parts[-1],
                            values=(str(f),))
            shown += 1
        self.count_lbl.configure(
            text=t(self.lang, "java_files_count", shown=shown, total=len(self._files)))

    def _filter_tree(self):
        self._build_tree(self.search_var.get())

    def _on_select(self, _event=None):
        sel = self.tree.selection()
        if not sel:
            return
        vals = self.tree.item(sel[0], "values")
        if not vals or not vals[0]:
            return
        self._open_file(Path(vals[0]))

    def _open_file(self, path):
        try:
            code = path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            code = f"// Failed to load {path.name}: {e}"
        self.txt.configure(state="normal")
        self.txt.delete("1.0", "end")
        self.txt.insert("1.0", code)
        self._highlight(code)
        self.txt.configure(state="disabled")
        try:
            rel = path.relative_to(self.java_root)
        except ValueError:
            rel = path.name
        self.path_lbl.configure(
            text=t(self.lang, "lines", rel=rel, n=len(code.splitlines())))

    def _highlight(self, code):
        for tag in ("kw", "str", "com", "num", "ann"):
            self.txt.tag_remove(tag, "1.0", "end")
        import re
        for ln_idx, line in enumerate(code.splitlines(), start=1):
            ls = f"{ln_idx}.0"
            m = re.search(r"//.*", line)
            if m:
                self.txt.tag_add("com", f"{ls}+{m.start()}c", f"{ls}+{len(line)}c")
            for mm in re.finditer(r'"(?:\\.|[^"\\])*"', line):
                self.txt.tag_add("str", f"{ls}+{mm.start()}c",
                                 f"{ls}+{mm.end()}c")
            for mm in re.finditer(r"@\w+", line):
                self.txt.tag_add("ann", f"{ls}+{mm.start()}c",
                                 f"{ls}+{mm.end()}c")
            for mm in re.finditer(r"\b\d[\w.]*\b", line):
                self.txt.tag_add("num", f"{ls}+{mm.start()}c",
                                 f"{ls}+{mm.end()}c")
            for mm in re.finditer(r"\b[A-Za-z_$][\w$]*\b", line):
                if mm.group(0) in JAVA_KEYWORDS:
                    self.txt.tag_add("kw", f"{ls}+{mm.start()}c",
                                     f"{ls}+{mm.end()}c")

    def _export(self):
        dst = filedialog.askdirectory(title=t(self.lang, "export"))
        if not dst:
            return
        target = Path(dst) / (self.java_root.parent.name or "decompiled")
        shutil.copytree(self.java_root, target, dirs_exist_ok=True)
        self.path_lbl.configure(text=t(self.lang, "exported", target=target))

    def _export_zip(self):
        import zipfile
        dst = filedialog.asksaveasfilename(
            title=t(self.lang, "export_zip"),
            defaultextension=".zip",
            filetypes=[("ZIP archive", "*.zip")])
        if not dst:
            return
        target = Path(dst)
        with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as zf:
            for f in self.java_root.rglob("*.java"):
                zf.write(f, str(f.relative_to(self.java_root.parent)))
        self.path_lbl.configure(text=t(self.lang, "exported", target=target))
