"""Main window — パイデックス reverse-engineering suite (CustomTkinter + Tk)."""

from __future__ import annotations

import os
import subprocess
import sys
import threading
from pathlib import Path

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageOps

from ..core.decompiler import DecompilerEngine
from .code_viewer import CodeViewer
from .search_dialog import SearchDialog
from .manifest_viewer import ManifestViewer
from .resource_browser import ResourceBrowser
from .secret_scanner import SecretScanner
from .cert_info import CertInfo
from .stats_viewer import StatsViewer
from .diff_tool import DiffTool
from .batch_dialog import BatchDialog
from .i18n import t, is_rtl, LANGUAGES, LANG_AR
from .privacy_dialog import PrivacyDialog
from .settings import load_lang, save_lang
from .theme import (
    APP_NAME_JP, APP_SUBTITLE, FOOTER_TEXT, find_artwork,
    DARK_RED, CARD_BG, ACCENT, ACCENT_BRIGHT, ACCENT_DEEP, TEXT, MUTED, TEXT_DIM,
    DARK_BG, CODE_BG, FONT_JP, FONT_UI, FONT_CODE,
)


ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")


class DecompilerWorker(threading.Thread):
    def __init__(self, engine, apk_path, on_progress, on_done, on_log=None,
                 engine_kind="auto", deobf=False):
        super().__init__(daemon=True)
        self.engine = engine
        self.apk = apk_path
        self.on_progress = on_progress
        self.on_done = on_done
        self.on_log = on_log
        self.engine_kind = engine_kind
        self.deobf = deobf

    def run(self):
        try:
            java_dir = self.engine.decompile(
                self.apk, on_progress=lambda p, m: self.on_progress(p, m),
                on_log=self.on_log, engine=self.engine_kind, deobf=self.deobf)
            self.on_done(True, str(java_dir), t(self._lang, "done_msg"))
        except Exception as e:  # noqa: BLE001
            self.on_done(False, "", str(e))

    # lang injected later
    _lang = "ar"


def load_rounded_image(path, size):
    try:
        im = Image.open(path).convert("RGBA")
        im = ImageOps.fit(im, size, method=Image.LANCZOS)
        mask = Image.new("L", size, 0)
        from PIL import ImageDraw
        d = ImageDraw.Draw(mask)
        d.rounded_rectangle([0, 0, size[0] - 1, size[1] - 1], radius=18, fill=255)
        im.putalpha(mask)
        return ctk.CTkImage(light_image=im, dark_image=im, size=size)
    except Exception:
        return None


class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.lang = load_lang("ar")
        DecompilerWorker._lang = self.lang
        self.title(f"{APP_NAME_JP} • PyDex")
        self.minsize(940, 740)
        self.geometry("1040x820")

        self.engine = DecompilerEngine()
        self.worker = None
        self.last_java_dir = None
        self.apk_path = None
        self.output_dir = None
        self._progress_val = 0.0

        # thread-safe progress/result state
        self._progress_pct = 0
        self._progress_msg = ""
        self._progress_dirty = False
        self._last_logged_pct = -1
        self._done_flag = False
        self._done_ok = False
        self._done_java_dir = ""
        self._done_msg = ""
        self._polling = False
        self._log_lines = []
        self._log_read_idx = 0

        self._init_tk_style()
        self._build_ui()
        self._apply_state_after_build()

        for p in self.engine.check_tools():
            self._log(t(self.lang, "tool_warn", msg=p))

    def _init_tk_style(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("Treeview",
                        background=CODE_BG, fieldbackground=CODE_BG,
                        foreground=TEXT, rowheight=24, font=(FONT_UI, 10))
        style.map("Treeview", background=[("selected", ACCENT)],
                  foreground=[("selected", "white")])
        style.configure("Treeview.Heading",
                        background=DARK_RED, foreground=TEXT, font=(FONT_UI, 10, "bold"))

        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    @property
    def rtl(self) -> bool:
        return is_rtl(self.lang)

    @staticmethod
    def _side(reverse=False):
        # returns side for a logical "start" element
        pass

    # ---------- UI ----------
    def _build_ui(self):
        # remove old children (for language switching)
        for child in self.winfo_children():
            try:
                child.destroy()
            except Exception:
                pass

        self.configure(fg_color=DARK_BG)
        container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=24, pady=16)

        self._container = container
        rtl = self.rtl
        justify = "right" if rtl else "left"

        # ── Hero glass card ──
        hero = ctk.CTkFrame(container, corner_radius=26, fg_color=CARD_BG,
                            border_color=ACCENT_DEEP, border_width=2)
        hero.pack(fill="x", pady=(0, 14))

        hero_row = ctk.CTkFrame(hero, fg_color="transparent")
        hero_row.pack(fill="both", padx=22, pady=20)

        hero_img, avatar_img = find_artwork()

        # image on leading side
        img_wrap = ctk.CTkFrame(hero_row, fg_color="transparent")
        if hero_img:
            ci = load_rounded_image(hero_img, (360, 230))
            if ci:
                ctk.CTkLabel(img_wrap, text="", image=ci).pack()

        text_wrap = ctk.CTkFrame(hero_row, fg_color="transparent")
        if avatar_img:
            ai = load_rounded_image(avatar_img, (76, 76))
            if ai:
                ctk.CTkLabel(text_wrap, text="", image=ai).pack(
                    anchor="e" if rtl else "w", pady=(0, 6))

        ctk.CTkLabel(text_wrap, text=APP_NAME_JP,
                     font=ctk.CTkFont(family=FONT_JP, size=34, weight="bold"),
                     text_color=TEXT, justify=justify).pack(anchor="e" if rtl else "w")
        ctk.CTkLabel(text_wrap, text=t(self.lang, "subtitle"),
                     font=ctk.CTkFont(family=FONT_UI, size=11),
                     text_color=MUTED, justify=justify).pack(
            anchor="e" if rtl else "w", pady=(2, 10))
        ctk.CTkLabel(text_wrap,
                     text=t(self.lang, "desc"),
                     font=ctk.CTkFont(family=FONT_UI, size=12),
                     text_color=TEXT, wraplength=520, justify=justify).pack(
            anchor="e" if rtl else "w")

        self.file_lbl = ctk.CTkLabel(
            text_wrap, text=t(self.lang, "no_file"),
            font=ctk.CTkFont(family=FONT_UI, size=11), text_color=MUTED,
            wraplength=520, justify=justify)
        self.file_lbl.pack(anchor="e" if rtl else "w", pady=(14, 0))

        # pack hero order depending on direction: text first on RHS in RTL
        if rtl:
            text_wrap.pack(side="right", fill="both", expand=True)
            img_wrap.pack(side="left")
        else:
            img_wrap.pack(side="left", padx=(0, 22))
            text_wrap.pack(side="left", fill="both", expand=True)

        # ── language selector row (top trailing) ──
        langrow = ctk.CTkFrame(container, fg_color="transparent")
        langrow.pack(fill="x", pady=(0, 8))
        # push to trailing side
        spacer = ctk.CTkFrame(langrow, fg_color="transparent")
        spacer.pack(side="left" if rtl else "right", fill="x", expand=True)
        ctk.CTkLabel(langrow, text=t(self.lang, "language"),
                     font=ctk.CTkFont(family=FONT_UI, size=11),
                     text_color=MUTED).pack(side="right" if rtl else "left", padx=6)
        vals = [name for _, name in LANGUAGES]
        cur_name = dict(LANGUAGES).get(self.lang, "العربية")
        self.lang_combo = ctk.CTkComboBox(
            langrow, values=vals, width=120,
            fg_color=CODE_BG, border_color=ACCENT_DEEP,
            font=ctk.CTkFont(family=FONT_UI, size=11),
            command=self._on_lang_combo,
        )
        self.lang_combo.set(cur_name)
        self.lang_combo.pack(side="right" if rtl else "left")

        # ── action buttons ──
        btnrow = ctk.CTkFrame(container, fg_color="transparent")
        btnrow.pack(fill="x", pady=(0, 10))

        def mklabel(key, **kw):
            return t(self.lang, key)

        btn_defs = [
            (t(self.lang, "select_apk"), self._browse, "primary"),
            (t(self.lang, "start"), self._start, "primary"),
            (t(self.lang, "view_java"), self._open_viewer, "ghost"),
            (t(self.lang, "open_folder"), self._open_folder, "ghost"),
            (t(self.lang, "privacy"), lambda: PrivacyDialog(self, lang=self.lang), "ghost"),
            (t(self.lang, "exit"), self.destroy, "neutral"),
        ]

        leads = [d for d in btn_defs]  # logical LTR
        if rtl:
            leads = list(reversed(leads))

        for label, cmd, kind in leads:
            if kind == "primary":
                kwargs = dict(fg_color=ACCENT, hover_color=ACCENT_BRIGHT)
            elif kind == "ghost":
                kwargs = dict(fg_color="transparent", border_color=ACCENT_DEEP,
                             border_width=1, hover_color=ACCENT_DEEP, text_color=TEXT)
            else:
                kwargs = dict(fg_color=CARD_BG, hover_color=ACCENT_DEEP, text_color=TEXT)
            b = ctk.CTkButton(
                btnrow, text=label, command=cmd, height=42,
                font=ctk.CTkFont(family=FONT_JP, size=12, weight="bold"), **kwargs)
            b.pack(side="right" if rtl else "left", padx=4)
            # attach references
            if label == t(self.lang, "select_apk"):
                self.btn_pick = b
            elif label == t(self.lang, "start"):
                self.btn_run = b
            elif label == t(self.lang, "view_java"):
                self.btn_view = b
            elif label == t(self.lang, "open_folder"):
                self.btn_folder = b

        # ── progress + log ──
        self.status_lbl = ctk.CTkLabel(container, text="",
                                      font=ctk.CTkFont(family=FONT_UI, size=11),
                                      text_color=MUTED, justify="right" if self.rtl else "left")
        self.status_lbl.pack(anchor="e" if self.rtl else "w", pady=(0, 2))

        self.progress = ctk.CTkProgressBar(container, progress_color=ACCENT_BRIGHT,
                                           fg_color=CODE_BG, corner_radius=8, height=18)
        self.progress.set(self._progress_val)
        self.progress.pack(fill="x", pady=(2, 8))

        log_card = ctk.CTkFrame(container, corner_radius=18, fg_color=CARD_BG,
                                border_color=ACCENT_DEEP, border_width=1)
        log_card.pack(fill="both", expand=True)

        ctk.CTkLabel(log_card, text=t(self.lang, "log_title"),
                     font=ctk.CTkFont(family=FONT_JP, size=12, weight="bold"),
                     text_color=TEXT, justify=justify).pack(
            anchor="e" if rtl else "w", padx=14, pady=(10, 4))

        self.log = ctk.CTkTextbox(log_card, font=ctk.CTkFont(family=FONT_CODE, size=10),
                                  fg_color=CODE_BG, text_color=TEXT, corner_radius=14,
                                  border_color=ACCENT_DEEP, border_width=1, height=320)
        self.log.pack(fill="both", expand=True, padx=14, pady=(0, 14))
        self.log.configure(state="disabled")

        foot = ctk.CTkLabel(container, text=t(self.lang, "footer"),
                            font=ctk.CTkFont(family=FONT_UI, size=10), text_color=MUTED)
        foot.pack(pady=(8, 0))

        # ── output folder selector ──
        outrow = ctk.CTkFrame(container, fg_color="transparent")
        outrow.pack(fill="x", pady=(0, 8))
        self.output_lbl = ctk.CTkLabel(
            outrow, text=t(self.lang, "output_default"),
            font=ctk.CTkFont(family=FONT_UI, size=11), text_color=MUTED,
            justify="right" if self.rtl else "left")
        self.output_lbl.pack(side="right" if self.rtl else "left", padx=6)
        ctk.CTkButton(
            outrow, text=t(self.lang, "choose_output"), command=self._choose_output,
            fg_color="transparent", border_color=ACCENT_DEEP, border_width=1,
            hover_color=ACCENT_DEEP, text_color=TEXT, height=34,
            font=ctk.CTkFont(family=FONT_JP, size=11)).pack(
            side="right" if self.rtl else "left")

        # ── engine selector + deobfuscation ──
        enginerow = ctk.CTkFrame(container, fg_color="transparent")
        enginerow.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(enginerow, text=t(self.lang, "engine_label"),
                     font=ctk.CTkFont(family=FONT_UI, size=11),
                     text_color=MUTED).pack(side="right" if self.rtl else "left", padx=6)
        self.engine_var = tk.StringVar(value="auto")
        self.engine_combo = ctk.CTkComboBox(
            enginerow, values=[t(self.lang, "engine_auto"),
                               t(self.lang, "engine_jadx"),
                               t(self.lang, "engine_jdcli")],
            variable=self.engine_var, width=220,
            fg_color=CODE_BG, border_color=ACCENT_DEEP,
            font=ctk.CTkFont(family=FONT_UI, size=11))
        self.engine_combo.pack(side="right" if self.rtl else "left")
        self.deobf_var = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(enginerow, text=t(self.lang, "deobf_label"),
                        variable=self.deobf_var, text_color=MUTED,
                        fg_color=ACCENT, hover_color=ACCENT_BRIGHT,
                        font=ctk.CTkFont(family=FONT_UI, size=11)).pack(
            side="left" if self.rtl else "right", padx=14)

        # ── tools toolbar ──
        toolsrow = ctk.CTkFrame(container, fg_color="transparent")
        toolsrow.pack(fill="x", pady=(0, 10))
        tool_defs = [
            (t(self.lang, "search_tool"), self._tool_search),
            (t(self.lang, "manifest_tool"), self._tool_manifest),
            (t(self.lang, "resources_tool"), self._tool_resources),
            (t(self.lang, "secrets_tool"), self._tool_secrets),
            (t(self.lang, "cert_tool"), self._tool_cert),
            (t(self.lang, "stats_tool"), self._tool_stats),
            (t(self.lang, "diff_tool"), self._tool_diff),
            (t(self.lang, "batch_tool"), self._tool_batch),
            (t(self.lang, "open_ide"), self._open_ide),
        ]
        leads = list(reversed(tool_defs)) if rtl else tool_defs
        for label, cmd in leads:
            ctk.CTkButton(
                toolsrow, text=label, command=cmd, height=36,
                fg_color="transparent", border_color=ACCENT_DEEP, border_width=1,
                hover_color=ACCENT_DEEP, text_color=TEXT,
                font=ctk.CTkFont(family=FONT_JP, size=10, weight="bold")).pack(
                side="right" if rtl else "left", padx=3)

        self._try_enable_dnd()

    # ---------- drag & drop ----------
    def _try_enable_dnd(self):
        try:
            import tkinterdnd2  # noqa: F401
            from tkinterdnd2 import DND_FILES
            self.drop_target_register(DND_FILES)
            self.dnd_bind("<<Drop>>", self._on_drop)
        except Exception:
            pass

    def _on_drop(self, event):
        p = event.data.strip().strip("{}").strip('"')
        if p.lower().endswith(".apk"):
            self._set_apk(Path(p))

    def _on_lang_combo(self, choice):
        # map display name back to code
        code = "ar"
        for c, name in LANGUAGES:
            if name == choice:
                code = c
                break
        if code != self.lang:
            self.lang = code
            DecompilerWorker._lang = code
            save_lang(code)
            self._build_ui()
            self._apply_state_after_build()

    # ---------- state restoration ----------
    def _apply_state_after_build(self):
        if self.apk_path is not None and self.apk_path.exists():
            kb = self.apk_path.stat().st_size // 1024
            self.file_lbl.configure(
                text=t(self.lang, "file_picked", name=self.apk_path.name, kb=kb, path=self.apk_path),
                text_color=TEXT)
            busy = bool(self.worker and self.worker.is_alive())
            self.btn_run.configure(state="disabled" if busy else "normal")
            self.btn_pick.configure(state="disabled" if busy else "normal")
        else:
            self.file_lbl.configure(text=t(self.lang, "no_file"), text_color=MUTED)
        if self.output_dir:
            self.output_lbl.configure(
                text=t(self.lang, "output_chosen", path=self.output_dir),
                text_color=TEXT)
        else:
            self.output_lbl.configure(text=t(self.lang, "output_default"),
                                     text_color=MUTED)
        if self.last_java_dir is not None:
            self.btn_view.configure(state="normal")
            self.btn_folder.configure(state="normal")
        self.progress.set(self._progress_val)

    # ---------- slots ----------
    def _choose_output(self):
        path = filedialog.askdirectory(title=t(self.lang, "choose_output"))
        if path:
            self.output_dir = Path(path)
            self.output_lbl.configure(
                text=t(self.lang, "output_chosen", path=self.output_dir),
                text_color=TEXT)
            self._log(t(self.lang, "output_chosen", path=self.output_dir))

    def _browse(self):
        path = filedialog.askopenfilename(
            title=t(self.lang, "file_dialog_title"),
            filetypes=[("APK files", "*.apk"), ("All", "*.*")])
        if path:
            self._set_apk(Path(path))

    def _set_apk(self, path):
        self.apk_path = path
        kb = path.stat().st_size // 1024 if path.exists() else 0
        self.file_lbl.configure(
            text=t(self.lang, "file_picked", name=path.name, kb=kb, path=path),
            text_color=TEXT)
        self.btn_run.configure(state="normal")
        self._log(t(self.lang, "picked_log", path=path))

    def _start(self):
        if not self.apk_path:
            return
        self.btn_run.configure(state="disabled")
        self.btn_pick.configure(state="disabled")
        self.btn_view.configure(state="disabled")
        self.progress.set(0)
        self._progress_val = 0.0
        self._progress_pct = 0
        self._progress_msg = ""
        self._progress_dirty = False
        self._last_logged_pct = -1
        self._done_flag = False
        self._log_lines = []
        self._log_read_idx = 0
        self._log(t(self.lang, "started"))
        eng_map = {"auto": "auto", t(self.lang, "engine_jadx"): "jadx",
                   t(self.lang, "engine_jdcli"): "jd-cli"}
        # map current combo value back to engine code
        eng_label = self.engine_var.get()
        engine = "auto"
        for k, v in ((t(self.lang, "engine_auto"), "auto"),
                     (t(self.lang, "engine_jadx"), "jadx"),
                     (t(self.lang, "engine_jdcli"), "jd-cli")):
            if k == eng_label:
                engine = v
                break
        self.engine = DecompilerEngine(output_dir=self.output_dir)
        self.worker = DecompilerWorker(
            self.engine, str(self.apk_path),
            on_progress=self._worker_progress, on_done=self._worker_done,
            on_log=self._worker_log, engine_kind=engine, deobf=self.deobf_var.get())
        self.worker.start()
        self._polling = True
        self._schedule_progress_poll()

    def _schedule_progress_poll(self):
        if not self._polling:
            return
        self._poll_worker()
        if self.worker is not None and self.worker.is_alive():
            self.after(100, self._schedule_progress_poll)
        else:
            # final poll after thread exit
            self._poll_worker()
            self._polling = False

    def _worker_progress(self, pct, msg):
        self._progress_pct = pct
        self._progress_msg = msg
        self._progress_dirty = True

    def _worker_done(self, ok, java_dir, msg):
        self._done_ok = ok
        self._done_java_dir = java_dir
        self._done_msg = msg
        self._done_flag = True

    def _worker_log(self, line):
        line = (line or "").rstrip()
        if not line.strip():
            return
        stripped = line.lstrip()
        if stripped.startswith("at ") or stripped.startswith("Caused by:") or "ForkJoinTask.doExec" in line:
            return
        self._log_lines.append(line)

    def _poll_worker(self):
        if self._log_read_idx < len(self._log_lines):
            chunk = self._log_lines[self._log_read_idx:]
            self.log.configure(state="normal")
            self.log.insert("end", "\n".join(chunk) + "\n")
            self.log.see("end")
            self.log.configure(state="disabled")
            self._log_read_idx = len(self._log_lines)
        if self._progress_dirty:
            self._progress_dirty = False
            self._progress_val = self._progress_pct / 100.0
            try:
                self.progress.set(self._progress_val)
                self.status_lbl.configure(text=f"[{self._progress_pct}%] {self._progress_msg}")
            except Exception:
                pass
            if self._progress_pct != self._last_logged_pct:
                self._last_logged_pct = self._progress_pct
                self._log(f"[{self._progress_pct}%] {self._progress_msg}")
        if self._done_flag:
            self._done_flag = False
            self._on_done(self._done_ok, self._done_java_dir, self._done_msg)

    def _on_done(self, ok, java_dir, msg):
        self.btn_run.configure(state="normal")
        self.btn_pick.configure(state="normal")
        if ok:
            self.last_java_dir = Path(java_dir)
            n = len(list(self.last_java_dir.rglob("*.java")))
            self._progress_val = 1.0
            self.progress.set(1.0)
            self._log(t(self.lang, "completed", msg=t(self.lang, "done_msg"), n=n))
            self.btn_view.configure(state="normal")
            self.btn_folder.configure(state="normal")
            messagebox.showinfo(APP_NAME_JP, t(self.lang, "success_dialog", msg=t(self.lang, "done_msg"), n=n))
        else:
            self._progress_val = 0.0
            self.progress.set(0)
            self._log(t(self.lang, "failed", msg=msg))
            messagebox.showerror(t(self.lang, "error_title"), t(self.lang, "failed", msg=msg))

    def _open_viewer(self):
        if self.last_java_dir:
            CodeViewer(self.last_java_dir, self, lang=self.lang)

    def _open_folder(self):
        if self.last_java_dir:
            target = str(self.last_java_dir.parent)
            try:
                if sys.platform.startswith("win"):
                    subprocess.Popen(["explorer", target])
                elif sys.platform == "darwin":
                    subprocess.Popen(["open", target])
                else:
                    subprocess.Popen(["xdg-open", target])
            except Exception as e:  # noqa: BLE001
                self._log(t(self.lang, "open_failed", err=e))

    # ---------- tools ----------
    def _require_java(self):
        if self.last_java_dir and self.last_java_dir.is_dir():
            return self.last_java_dir
        messagebox.showinfo(APP_NAME_JP, t(self.lang, "no_java"))
        return None

    def _tool_search(self):
        d = self._require_java()
        if d:
            SearchDialog(d, self, lang=self.lang)

    def _tool_manifest(self):
        if self.apk_path:
            ManifestViewer(self.apk_path, self, lang=self.lang)

    def _tool_resources(self):
        if self.engine and self.engine.result_resources_dir:
            ResourceBrowser(self.engine.result_resources_dir, self, lang=self.lang)
        elif self.last_java_dir:
            # jd-cli mode: no resources/ folder — point at xml/
            xml_dir = self.last_java_dir.parent / "xml"
            if xml_dir.is_dir():
                ResourceBrowser(xml_dir, self, lang=self.lang)
            else:
                messagebox.showinfo(APP_NAME_JP, t(self.lang, "no_java"))
        else:
            messagebox.showinfo(APP_NAME_JP, t(self.lang, "no_java"))

    def _tool_secrets(self):
        d = self._require_java()
        if d and self.apk_path:
            SecretScanner(d, self.apk_path, self, lang=self.lang)

    def _tool_cert(self):
        if self.apk_path:
            CertInfo(self.apk_path, self, lang=self.lang)

    def _tool_stats(self):
        d = self._require_java()
        if d and self.apk_path:
            StatsViewer(d, self.apk_path, self, lang=self.lang)

    def _tool_diff(self):
        DiffTool(self, lang=self.lang)

    def _tool_batch(self):
        BatchDialog(self, lang=self.lang)

    def _open_ide(self):
        if not self.last_java_dir:
            messagebox.showinfo(APP_NAME_JP, t(self.lang, "no_java"))
            return
        target = str(self.last_java_dir.parent)
        try:
            import shutil as _sh
            code = _sh.which("code")
            if code:
                subprocess.Popen([code, target])
            else:
                if sys.platform.startswith("win"):
                    subprocess.Popen(["explorer", target])
                elif sys.platform == "darwin":
                    subprocess.Popen(["open", target])
                else:
                    subprocess.Popen(["xdg-open", target])
        except Exception as e:  # noqa: BLE001
            self._log(t(self.lang, "open_failed", err=e))

    def _log(self, msg):
        self.log.configure(state="normal")
        self.log.insert("end", msg + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _on_closing(self):
        if not self._close_check():
            return
        self.destroy()

    def _close_check(self):
        if self.worker is not None and self.worker.is_alive():
            if not messagebox.askokcancel(
                    APP_NAME_JP, t(self.lang, "decompile_running")):
                return False
        return True


def main():
    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
