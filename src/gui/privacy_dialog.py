"""Arabic/English privacy / disclaimer dialog (CustomTkinter)."""

from __future__ import annotations

import customtkinter as ctk

from .i18n import t, is_rtl
from .theme import FOOTER_TEXT, DARK_BG, CARD_BG, ACCENT, ACCENT_BRIGHT, ACCENT_DEEP, TEXT, MUTED

PRIVACY_AR = (
    "اتفاقية الخصوصية وشروط الاستخدام — パイデックス\n\n"
    "1. نحن لا نريد أي شيء من معلوماتك.\n"
    "تطبيق パイデックス (PyDex) يعمل بالكامل محليًا (Local / Offline) على جهازك.\n"
    "لا جمع أو تخزين أو إرسال any بيانات شخصية أو ملفات أو إحصاءات.\n"
    "لا حسابات، لا تحليلات، لا اتصالات شبكية، ولا any خدمة سحابية.\n\n"
    "2. ملفاتك تبقى على جهازك.\n"
    "كل ملفات APK والكود الناتج والمجلدات المؤقتة تُعالـَج وتُحفظ على القرص المحلي فقط،\n"
    "ويمكنك حذف مجلد output/ في أي وقت.\n\n"
    "3. عدم المسؤولية عن سوء الاستخدام.\n"
    "الأداة مخصصة للأغراض التعليمية والبحثية وتحليل تطبيقاتك الخاصة.\n"
    "أنت وحدك المسؤول عن كيفية استخدامها.\n"
    "the l house غير مسؤولة عن أي استخدام غير قانوني أو مخالف لتراخيص وحقوق الملكية.\n"
    "يرجى تحليل التطبيقات التي تملكها أو لديك إذن صريح لتحليلها فقط، واحترام قوانين بلدك.\n\n"
    "4. الملكية.\n"
    "التطبيق من تطوير the l house. الأدوات المضمّنة (dex2jar و jd-cli) مفتوحة المصدر.\n"
    "بتشغيل البرنامج أنت توافق على هذه الشروط.\n"
)

PRIVACY_EN = (
    "Privacy Policy & Terms of Use — パイデックス\n\n"
    "1. We do not want any of your information.\n"
    "PyDex (パイデックス) runs entirely locally (offline) on your device.\n"
    "No personal data, files, or analytics are collected, stored, or sent.\n"
    "No accounts, no analytics, no network, no cloud service.\n\n"
    "2. Your files stay on your device.\n"
    "All APKs and resulting code are processed and saved locally only;\n"
    "you can delete the output/ folder at any time.\n\n"
    "3. No liability for misuse.\n"
    "The tool is intended for educational/research purposes and analysis of your own apps.\n"
    "You are solely responsible for how you use it.\n"
    "the l house is not responsible for illegal or license-violating usage.\n"
    "Only analyze apps you own or have explicit permission to analyze, and respect your local laws.\n\n"
    "4. Ownership.\n"
    "Developed by the l house. Bundled decompilers (dex2jar, jd-cli) are open source.\n"
    "By running the program you agree to these terms.\n"
)


class PrivacyDialog(ctk.CTkToplevel):
    def __init__(self, parent=None, lang: str = "ar"):
        super().__init__(parent)
        self.lang = lang
        self.rtl = is_rtl(lang)
        self.title(t(lang, "privacy_title"))
        self.geometry("640x560")
        self.configure(fg_color=DARK_BG)
        if parent is not None:
            self.transient(parent)
            self.grab_set()

        frame = ctk.CTkFrame(self, corner_radius=20, fg_color=CARD_BG,
                             border_color=ACCENT_DEEP, border_width=1)
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(frame, text=t(lang, "privacy_heading"), text_color=TEXT,
                     font=ctk.CTkFont(family="Meiryo UI", size=16, weight="bold"),
                     justify="right" if self.rtl else "left").pack(
            pady=(16, 8), anchor="e" if self.rtl else "w", padx=14)

        txt = ctk.CTkTextbox(frame, fg_color="#140303", text_color=TEXT,
                             font=ctk.CTkFont(size=12), wrap="word", corner_radius=12,
                             activate_scrollbars=True)
        txt.pack(fill="both", expand=True, padx=14, pady=8)
        try:
            txt._textbox.configure(justify="right" if self.rtl else "left")
        except Exception:
            pass
        txt.insert("1.0", PRIVACY_AR if lang == "ar" else PRIVACY_EN)
        txt.configure(state="disabled")

        ctk.CTkButton(frame, text=t(lang, "privacy_ok"), command=self.destroy,
                      fg_color=ACCENT, hover_color=ACCENT_BRIGHT,
                      height=38).pack(pady=(8, 6))

        ctk.CTkLabel(frame, text=FOOTER_TEXT,
                     font=ctk.CTkFont(size=9), text_color=MUTED).pack(pady=(0, 12))
