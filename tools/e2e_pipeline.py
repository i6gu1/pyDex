"""End-to-end smoke of the decompilation pipeline on a real-ish APK.

Builds a minimal APK by compiling a Java class, converting it to dex with
dx/d8 (if available), zipping it, then running the full pipeline and
inspecting the result.
"""
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

# 0. locate a dex converter (d8 preferred, then dx)
def find_d8():
    cand = ["d8", "d8.bat", "dx", "dx.bat"]
    for c in cand:
        w = shutil.which(c)
        if w:
            return w
    # android sdk build-tools common locations
    for root in [os.environ.get("ANDROID_HOME", ""), os.environ.get("ANDROID_SDK_ROOT", "")]:
        if root and os.path.isdir(root):
            for dp, _, fs in os.walk(root):
                for f in fs:
                    if f.lower() in ("d8.bat", "d8", "dx.bat", "dx"):
                        return os.path.join(dp, f)
    return None

tmp = Path(tempfile.mkdtemp(prefix="pydex_e2e_"))
work = tmp / "src"; work.mkdir()
hello = work / "Hello.java"
hello.write_text(
    "public class Hello {\n"
    "  public static void main(String[] a){\n"
    '    System.out.println("hi pydex");\n'
    "  }\n"
    "  public int add(int x, int y){ return x + y; }\n"
    "}\n", encoding="utf-8")

# compile
if shutil.which("javac") is None:
    print("SKIP: javac not available")
    sys.exit(0)
subprocess.run(["javac", "-d", str(work), str(hello)], check=True)

d8 = find_d8()
if d8 is None:
    print("SKIP: no d8/dx tool available (dex converter)")
    # Still test core paths? pipeline cannot run. just report.
    sys.exit(0)

# convert classes to dex
outdex = tmp / "dexout"; outdex.mkdir()
classes = list(work.glob("*.class"))
print("d8:", d8)
if d8.lower().endswith("dx") or d8.lower().endswith("dx.bat"):
    cmd = [d8, "--dex", f"--output={outdex}", *map(str, classes)]
else:
    cmd = [d8, *map(str, classes), "--output", str(outdex / "classes.dex")]
subprocess.run(cmd, check=True, capture_output=True)
# find produced dex
dex_files = list(outdex.rglob("*.dex"))
print("dex produced:", dex_files)
if not dex_files:
    print("FAIL: no dex produced")
    sys.exit(1)

# build apk
apk = tmp / "test.apk"
with zipfile.ZipFile(apk, "w") as z:
    z.write(dex_files[0], "classes.dex")
    z.writestr("AndroidManifest.xml", '<manifest package="com.example" />')
print("apk:", apk, apk.stat().st_size, "bytes")

# run pipeline
from src.core.decompiler import DecompilerEngine
eng = DecompilerEngine(ROOT)
problems = eng.check_tools()
print("tool problems:", problems)
if problems:
    print("FAIL: missing tools")
    sys.exit(1)

java_dir = eng.decompile(str(apk))
print("java_dir:", java_dir)
js = list(java_dir.rglob("*.java"))
print("java files:", len(js))
for j in js:
    print("----", j.name)
    print(j.read_text(encoding="utf-8", errors="replace")[:600])
assert js, "no java output"
text = js[0].read_text(encoding="utf-8", errors="replace")
assert "public class Hello" in text
assert "add" in text
print("E2E-OK")
shutil.rmtree(tmp, ignore_errors=True)
