"""Static-analysis helpers for decompiled APKs (secrets, manifest, cert, stats)."""

from __future__ import annotations

import hashlib
import re
import zipfile
from pathlib import Path

# ----------------------------------------------------------------------
# Secret / URL / endpoint scanning
# ----------------------------------------------------------------------
URL_RE = re.compile(
    r"""https?://[a-zA-Z0-9\-._~:/?#\[\]@!$&'()*+,;=%]{4,200}""")
IP_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}(?::\d{1,5})?\b")
SECRET_RES = [
    ("API Key", re.compile(r"""(?:api[_-]?key|apikey)["']?\s*[:=]\s*["'][A-Za-z0-9_\-]{16,}["']""", re.I)),
    ("AWS Key", re.compile(r"""AKIA[0-9A-Z]{16}""")),
    ("Token", re.compile(r"""(?:token|access[_-]?token)["']?\s*[:=]\s*["'][A-Za-z0-9_\-.]{12,}["']""", re.I)),
    ("Password", re.compile(r"""(?:password|passwd|pwd)["']?\s*[:=]\s*["'][^"']{4,}["']""", re.I)),
    ("Private Key", re.compile(r"""-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----""")),
    ("Google API Key", re.compile(r"""AIza[0-9A-Za-z_\-]{35}""")),
    ("Firebase/GA", re.compile(r"""[0-9a-z\-]{30,}\.apps\.googleusercontent\.com""")),
    ("Slack Token", re.compile(r"""xox[baprs]-[A-Za-z0-9-]{10,}""")),
    ("Stripe Key", re.compile(r"""sk_live_[0-9a-zA-Z]{24,}""")),
    ("JWT", re.compile(r"""eyJ[A-Za-z0-9_\-]+\.eyJ[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+""")),
]


def scan_secrets(java_root: Path, apk_path: Path | None = None) -> list[dict]:
    """Return a list of findings: {kind, file, line, text}."""
    findings: list[dict] = []
    files: list[Path] = []
    if java_root and java_root.is_dir():
        files = sorted(java_root.rglob("*.java"))
    for f in files:
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        rel = str(f)
        for i, line in enumerate(text.splitlines(), 1):
            s = line.strip()
            if not s or s.startswith(("//", "*", "/*")):
                continue
            for m in URL_RE.finditer(line):
                findings.append({"kind": "URL", "file": rel, "line": i,
                                 "text": m.group(0)[:160]})
            for m in IP_RE.finditer(line):
                findings.append({"kind": "IP", "file": rel, "line": i,
                                 "text": m.group(0)})
            for name, rx in SECRET_RES:
                m = rx.search(line)
                if m:
                    findings.append({"kind": name, "file": rel, "line": i,
                                     "text": m.group(0)[:160]})
    # dedupe
    seen = set()
    out = []
    for f in findings:
        key = (f["kind"], f["file"], f["line"], f["text"])
        if key in seen:
            continue
        seen.add(key)
        out.append(f)
    return out


# ----------------------------------------------------------------------
# Manifest parsing
# ----------------------------------------------------------------------
DANGEROUS_PERMISSIONS = {
    "android.permission.READ_SMS", "android.permission.SEND_SMS",
    "android.permission.RECEIVE_SMS", "android.permission.READ_CONTACTS",
    "android.permission.WRITE_CONTACTS", "android.permission.RECORD_AUDIO",
    "android.permission.CAMERA", "android.permission.ACCESS_FINE_LOCATION",
    "android.permission.ACCESS_COARSE_LOCATION", "android.permission.READ_PHONE_STATE",
    "android.permission.CALL_PHONE", "android.permission.READ_CALL_LOG",
    "android.permission.WRITE_CALL_LOG", "android.permission.SYSTEM_ALERT_WINDOW",
    "android.permission.BIND_ACCESSIBILITY_SERVICE",
    "android.permission.READ_EXTERNAL_STORAGE", "android.permission.WRITE_EXTERNAL_STORAGE",
    "android.permission.MANAGE_EXTERNAL_STORAGE", "android.permission.QUERY_ALL_PACKAGES",
}


def parse_manifest(apk_path: Path) -> dict:
    """Extract manifest info from APK (best-effort, no external deps)."""
    info = {
        "package": "", "version_name": "", "version_code": "",
        "min_sdk": "", "target_sdk": "", "permissions": [],
        "activities": [], "services": [], "receivers": [], "providers": [],
        "main_activity": "", "raw": "",
    }
    try:
        from pyaxmlparser import APK
        from pyaxmlparser.axmlprinter import AXMLPrinter
        apk = APK(str(apk_path))
        manifest = apk.get_android_manifest_axml().get_xml().decode("utf-8", "replace")
        info["raw"] = manifest
        info["package"] = apk.package
        info["version_name"] = apk.version_name
        info["version_code"] = str(apk.version_code)
        info["min_sdk"] = str(getattr(apk, "min_sdk", ""))
        info["target_sdk"] = str(getattr(apk, "target_sdk", ""))
        # permissions
        for p in apk.get_permissions():
            name = p if isinstance(p, str) else str(p)
            info["permissions"].append(name)
        # components via simple regex on decoded manifest
        for tag, key in (("activity", "activities"), ("service", "services"),
                         ("receiver", "receivers"), ("provider", "providers")):
            for m in re.finditer(rf"<{tag}\b[^>]*android:name=\"([^\"]+)\"", manifest):
                info[key].append(m.group(1))
        # main activity
        m = re.search(
            r'<activity\b[^>]*android:name="([^"]+)"[^>]*>.*?'
            r'<action android:name="android\.intent\.action\.MAIN"',
            manifest, re.S)
        if not m:
            m = re.search(
                r'<activity\b[^>]*>.*?<action android:name="android\.intent\.action\.MAIN"[^>]*/?>.*?'
                r'<category android:name="android\.intent\.category\.LAUNCHER"',
                manifest, re.S)
        if m:
            info["main_activity"] = m.group(1)
    except Exception as e:
        info["error"] = str(e)
    return info


# ----------------------------------------------------------------------
# Certificate info
# ----------------------------------------------------------------------
def cert_info(apk_path: Path) -> dict:
    """Extract signing certificate details from META-INF/*.RSA|*.DSA|*.EC."""
    info = {"found": False, "subject": "", "issuer": "", "valid_from": "",
            "valid_to": "", "sha1": "", "sha256": "", "files": []}
    try:
        with zipfile.ZipFile(apk_path) as zf:
            names = [n for n in zf.namelist()
                     if n.startswith("META-INF/") and n.upper().endswith((".RSA", ".DSA", ".EC"))]
            info["files"] = names
            if not names:
                return info
            data = zf.read(names[0])
            info["found"] = True
            # crude but dependency-free: pull printable strings
            import subprocess, tempfile, os
            with tempfile.NamedTemporaryFile(delete=False, suffix=".rsa") as tf:
                tf.write(data)
                tmp = tf.name
            try:
                out = subprocess.run(
                    ["keytool", "-printcert", "-file", tmp],
                    capture_output=True, text=True, timeout=30)
                text = out.stdout + out.stderr
                info["raw"] = text
                for label, key in (("Subject:", "subject"), ("Issuer:", "issuer"),
                                   ("Valid from:", "valid_from"),
                                   ("SHA1:", "sha1"), ("SHA256:", "sha256")):
                    m = re.search(re.escape(label) + r"\s*([^\n]+)", text)
                    if m:
                        info[key] = m.group(1).strip()
            except Exception as e:
                info["error"] = str(e)
            finally:
                os.unlink(tmp)
    except Exception as e:
        info["error"] = str(e)
    return info


# ----------------------------------------------------------------------
# Statistics
# ----------------------------------------------------------------------
def code_stats(java_root: Path) -> dict:
    """Count classes, methods, fields and estimate LOC."""
    files = sorted(java_root.rglob("*.java")) if java_root.is_dir() else []
    n_files = len(files)
    n_class = 0
    n_method = 0
    n_field = 0
    loc = 0
    for f in files:
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        loc += len(text.splitlines())
        n_class += len(re.findall(r"\b(?:class|interface|enum|record)\s+\w+", text))
        n_method += len(re.findall(
            r"\b(?:public|private|protected|static|final|synchronized|abstract|\s)*"
            r"[\w<>\[\],.?\s]+\s+\w+\s*\([^)]*\)\s*(?:throws [\w.,\s]+)?\{", text))
        n_field += len(re.findall(r"\b(?:private|public|protected|static|final)\s+[\w<>\[\],.]+\s+\w+\s*(?:=|;)", text))
    return {"files": n_files, "classes": n_class, "methods": n_method,
            "fields": n_field, "loc": loc}


def dex_stats(apk_path: Path) -> dict:
    """Count dex classes/methods roughly from the dex string tables."""
    stats = {"dex_files": 0, "classes": 0, "methods": 0}
    try:
        with zipfile.ZipFile(apk_path) as zf:
            dexes = [n for n in zf.namelist() if n.endswith(".dex")]
            stats["dex_files"] = len(dexes)
            for d in dexes:
                data = zf.read(d)
                # class_def count is at offset 96 (4 bytes LE) in dex header
                if len(data) >= 100:
                    n = int.from_bytes(data[96:100], "little")
                    stats["classes"] += n
                if len(data) >= 104:
                    m = int.from_bytes(data[100:104], "little")
                    stats["methods"] += m
    except Exception as e:
        stats["error"] = str(e)
    return stats


def file_list(apk_path: Path, prefix: str = "") -> list[str]:
    """List APK entries, optionally under a path prefix (e.g. 'lib/' or 'assets/')."""
    out = []
    try:
        with zipfile.ZipFile(apk_path) as zf:
            for n in zf.namelist():
                if prefix and not n.startswith(prefix):
                    continue
                out.append(n)
    except Exception:
        pass
    return sorted(out)


def sha256_of(path: Path) -> str:
    try:
        h = hashlib.sha256()
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return ""
