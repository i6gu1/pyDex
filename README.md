# パイデックス · PyDex

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/GUI-CustomTkinter-1f6feb?style=for-the-badge" alt="GUI">
  <img src="https://img.shields.io/badge/Decompiler-jadx%20%C2%B7%20jd--cli-c12727?style=for-the-badge" alt="Decompiler">
  <img src="https://img.shields.io/badge/Platform-Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white" alt="Windows">
  <img src="https://img.shields.io/badge/License-MIT-8f1d1d?style=for-the-badge" alt="License">
</p>

<p align="center">
  <b>A premium desktop suite that turns any APK into readable Java source — 100% locally, with a dark "blood-red liquid-glass" interface.</b><br>
  <sub>パイデックス · developed by <b>the l house</b></sub>
</p>

---

> **العربية:** تطبيق سطح مكتب يفكّ أي ملف APK إلى كود Java مقروء — محليًا بالكامل دون رفع أي ملف، مع واجهة زجاجية بلون قرمزي داكن ودعم كامل للعربية (RTL) والإنجليزية (LTR).

---

## ✨ Features

PyDex is not just a decompiler — it is a complete APK analysis workbench.

| # | Feature | Description |
|---|---------|-------------|
| 1 | ⚡ **jadx engine** | Fast single-pass decompilation (primary engine) |
| 2 | 🔁 **Auto fallback** | Falls back to the dex2jar + jd-cli pipeline if jadx fails |
| 3 | 🎚️ **Engine selector** | Choose `Auto` / `jadx` / `jd-cli` |
| 4 | 🔓 **Deobfuscation** | One-click jadx deobfuscation toggle |
| 5 | 🔍 **Global code search** | Search every line of the decompiled sources |
| 6 | 📋 **Manifest viewer** | Decoded `AndroidManifest.xml` with metadata |
| 7 | ⚠️ **Permission risk analyzer** | Highlights dangerous permissions automatically |
| 8 | 🗂️ **Resource browser** | Browse decoded XML resources |
| 9 | 🖼️ **Asset / image preview** | Inline preview of images and assets |
| 10 | 🔑 **Secret & endpoint scanner** | Finds URLs, API keys, tokens, JWTs, private keys |
| 11 | 📜 **Signing certificate** | Subject, issuer, validity, SHA-1 / SHA-256 |
| 12 | 📊 **Code statistics** | Classes, methods, fields, lines of code |
| 13 | 🧬 **Dex statistics** | Per-DEX class and method counts |
| 14 | 🧩 **Native library browser** | Lists `lib/` binaries |
| 15 | ⚖️ **Version diff** | Compare two decompiled builds side-by-side |
| 16 | 💻 **Open in IDE** | Launch VS Code (or the file manager) on the output |
| 17 | 📦 **Export to ZIP** | Package the whole project as a single archive |
| 18 | 📚 **Batch processing** | Decompile multiple APKs in one run |
| 19 | 🎨 **Syntax highlighting** | Java keywords, strings, comments, annotations |
| 20 | 🌐 **Bilingual UI** | Arabic (RTL) and English (LTR), persisted across runs |

---

## 🚀 Getting started

### 1. Requirements

- **Python 3.10+**
- **Java Runtime (JDK/JRE 8+)** — required by jadx, dex2jar and jd-cli
- Windows 10/11 (the bundled tools ship as Windows binaries)

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 3. Fetch the decompiler tools

The third-party tools are **not** committed to the repository (they total ~100 MB).
Fetch them with the bundled helper:

```bash
python tools/download_tools.py
```

This downloads and unpacks **jadx 1.5.6**, **dex2jar 2.4** and **jd-cli 1.2.0**
into the `tools/` folder.

### 4. Run

```bash
python src/main.py
```

Select an APK (or drag it onto the window), pick an output folder, and press **Start**.

---

## 🔧 Building the installer

```bash
# 1. Freeze the app into dist/
python -m PyInstaller setup.spec --noconfirm

# 2. Build the installer with Inno Setup 6
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" /Qp installer.iss
```

The result is `installer/PyDex-Setup-1.0.0.exe`.

---

## ⚙️ How it works

```
        APK
         │
         ▼
   ┌───────────┐     ┌─────────────────────────────────────────┐
   │  jadx     │────▶│  sources/  →  java_source/*.java          │
   │ (primary) │     │  resources/ → decoded XML + assets        │
   └───────────┘     └─────────────────────────────────────────┘
         │  (on failure)
         ▼
   ┌───────────┐   ┌──────────────┐   ┌───────────────────────┐
   │  dex2jar  │──▶│  *.jar       │──▶│  jd-cli (batched 40)  │
   └───────────┘   └──────────────┘   └───────────────────────┘
         │                                     │
         ▼                                     ▼
   XML resources (pyaxmlparser)        java_source/*.java
```

- **jadx** handles the whole APK in a single pass and also decodes resources.
- **dex2jar + jd-cli** is the fallback; jd-cli runs in **batches of 40 classes**
  with a hard watchdog timeout, so a single pathological class can never hang the run.
- **XML resources** are decoded with `pyaxmlparser` (AXML → readable XML).

---

## 🗂️ Project structure

```
PyDex/
├── src/
│   ├── main.py                 # entry point
│   ├── core/
│   │   ├── decompiler.py       # jadx / dex2jar + jd-cli orchestration
│   │   ├── file_manager.py     # APK extraction, output directories
│   │   └── analyzer.py         # secrets, manifest, cert, statistics
│   └── gui/
│       ├── main_window.py      # main window + worker thread
│       ├── code_viewer.py      # package tree + highlighted source
│       ├── search_dialog.py    # global code search
│       ├── manifest_viewer.py  # manifest + permission risk analysis
│       ├── resource_browser.py # resource / image browser
│       ├── secret_scanner.py   # URL & secret scanning
│       ├── cert_info.py        # signing certificate details
│       ├── stats_viewer.py     # code & dex statistics
│       ├── diff_tool.py        # compare two builds
│       ├── batch_dialog.py     # multi-APK batch processing
│       ├── i18n.py             # Arabic / English strings
│       ├── settings.py         # persisted preferences
│       ├── privacy_dialog.py   # in-app privacy policy
│       └── theme.py            # dark-red liquid-glass theme
├── tools/
│   ├── download_tools.py       # fetches jadx / dex2jar / jd-cli
│   ├── jd-cli.bat              # launcher
│   ├── make_icon.py            # icon generator
│   ├── smoke_gui.py            # headless GUI smoke test
│   └── e2e_pipeline.py         # end-to-end pipeline test
├── setup.spec                  # PyInstaller configuration
├── installer.iss               # Inno Setup installer script
├── build.bat                   # one-command build
└── requirements.txt
```

---

## 🔒 Privacy

- **No data collection.** The app never contacts a server.
- **100% local.** Decompilation runs entirely on your machine.
- **No uploads.** Your APKs and their source never leave your disk.
- Output is written to a folder **you** choose (defaults to `%LOCALAPPDATA%\PyDex\output`).

A bilingual privacy policy is built into the app.

---

## ⚠️ Disclaimer

PyDex is provided for **legitimate security research, education, and interoperability**.
You are responsible for complying with the licenses and laws that apply to the
software you analyze. The authors are not responsible for any misuse.

The bundled third-party tools (jadx, dex2jar, jd-cli) retain their own licenses.

---

## 📄 License

Released under the **MIT License**. See `LICENSE`.

---

<sub>developed by the l house · パイデックス</sub>
