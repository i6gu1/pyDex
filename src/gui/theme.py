"""Shared dark-red / blood-red liquid-glass theme for PyDex (パイデックス)."""

from __future__ import annotations

from pathlib import Path

APP_NAME_JP = "パイデックス"
APP_NAME_LATIN = "PyDex"
APP_SUBTITLE = "Reverse Engineering Suite"
FOOTER_TEXT = "developed by the l house  •  パイデックス"

# Palette — very dark red + bloody red, easy on the eyes
DARK_BG = "#0d0202"        # almost black, warm tint
DARK_RED = "#1a0404"       # main background
CARD_BG = "#230707"        # glass card (semi-opaque over bg)
CARD_BG2 = "#2a0a0a"
ACCENT = "#8f1d1d"         # bloody red
ACCENT_BRIGHT = "#c12727"  # hover / glow
ACCENT_DEEP = "#5c1212"    # borders
TEXT = "#ffe3e3"           # warm white
MUTED = "#c98a8a"          # muted rose
TEXT_DIM = "#8f6a6a"
CODE_BG = "#160404"
GOLD = "#ffd9a0"           # tiny premium accent (sparingly)

FONT_UI = "Segoe UI"
FONT_JP = "Meiryo UI"
FONT_CODE = "Consolas"

QSS = f"""
* {{ font-family: "{FONT_UI}", "{FONT_JP}", sans-serif; }}
QMainWindow, QDialog {{
    background: {DARK_BG};
}}
QWidget#AppRoot {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 {DARK_BG}, stop:0.45 {DARK_RED}, stop:1 #080101);
}}
QFrame#GlassCard {{
    background: rgba(42, 10, 10, 0.72);
    border: 1px solid {ACCENT_DEEP};
    border-radius: 18px;
}}
QFrame#GlassCard:hover {{
    border: 1px solid {ACCENT};
}}
QLabel#AppTitle {{
    color: {TEXT};
    font-size: 30px;
    font-weight: 800;
    font-family: "{FONT_JP}", "{FONT_UI}", sans-serif;
}}
QLabel#AppSubtitle {{
    color: {MUTED};
    font-size: 12px;
    letter-spacing: 2px;
}}
QLabel#BodyText {{
    color: {TEXT};
    font-size: 12px;
}}
QLabel#MutedText, QLabel#Footer {{
    color: {MUTED};
    font-size: 11px;
}}
QLabel#Footer {{
    font-size: 10px;
}}
QPushButton {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {ACCENT_BRIGHT}, stop:1 {ACCENT});
    color: white;
    border: 1px solid {ACCENT_BRIGHT};
    border-radius: 12px;
    padding: 10px 22px;
    font-size: 12px;
    font-weight: 700;
}}
QPushButton:hover {{
    background: {ACCENT_BRIGHT};
    border: 1px solid #ff6b6b;
}}
QPushButton:pressed {{
    background: {ACCENT_DEEP};
}}
QPushButton:disabled {{
    background: #3a1414;
    color: {TEXT_DIM};
    border: 1px solid #3a1414;
}}
QPushButton#GhostBtn {{
    background: rgba(255,255,255,0.04);
    border: 1px solid {ACCENT_DEEP};
    color: {TEXT};
    font-weight: 600;
}}
QPushButton#GhostBtn:hover {{
    background: rgba(193,39,39,0.25);
    border: 1px solid {ACCENT};
}}
QProgressBar {{
    background: rgba(255,255,255,0.06);
    border: 1px solid {ACCENT_DEEP};
    border-radius: 10px;
    height: 18px;
    text-align: center;
    color: {TEXT};
    font-size: 11px;
}}
QProgressBar::chunk {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {ACCENT}, stop:1 {ACCENT_BRIGHT});
    border-radius: 9px;
}}
QLineEdit, QComboBox, QTreeWidget, QPlainTextEdit, QTextBrowser {{
    background: {CODE_BG};
    color: {TEXT};
    border: 1px solid {ACCENT_DEEP};
    border-radius: 10px;
    padding: 6px;
    selection-background-color: {ACCENT};
}}
QTreeWidget::item:selected, QComboBox QAbstractItemView::item:selected {{
    background: {ACCENT};
    color: white;
}}
QScrollBar:vertical {{
    background: transparent;
    width: 10px;
}}
QScrollBar::handle:vertical {{
    background: {ACCENT_DEEP};
    border-radius: 5px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background: {ACCENT};
}}
QTabWidget::pane {{
    border: 1px solid {ACCENT_DEEP};
    border-radius: 12px;
    background: rgba(35,7,7,0.6);
}}
QTabBar::tab {{
    background: transparent;
    color: {MUTED};
    padding: 8px 18px;
    border-top-left-radius: 10px;
    border-top-right-radius: 10px;
}}
QTabBar::tab:selected {{
    background: {CARD_BG2};
    color: {TEXT};
}}
QLabel#DropHint {{
    color: {MUTED};
    font-size: 11px;
}}
"""


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def find_artwork() -> tuple[Path | None, Path | None]:
    """Return (hero_banner, avatar_logo) from the loose jfif files in root."""
    root = project_root()
    # 'Another' (schoolgirl, red eye) → wide hero banner
    hero = root / "ii'm like antoher.jfif"
    # 'Lain' (dark face) → small avatar / logo
    avatar = root / "Lain.jfif"
    return (hero if hero.is_file() else None,
            avatar if avatar.is_file() else None)
