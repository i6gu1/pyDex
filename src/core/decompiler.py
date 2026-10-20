"""Orchestrates jadx / dex2jar + jd-cli to turn an APK into readable Java sources."""

from __future__ import annotations

import logging
import shutil
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

from .file_manager import FileManager

log = logging.getLogger("pydex.decompiler")

ProgressCb = Callable[[int, str], None]


class DecompilerEngine:
    def __init__(self, base_dir: str | Path | None = None,
                 output_dir: str | Path | None = None) -> None:
        # base_dir = project root (folder that contains tools/ and output/)
        if base_dir is None:
            base_dir = Path(__file__).resolve().parent.parent.parent
        self.base_dir = Path(base_dir).resolve()
        self.dex2jar_dir = self.base_dir / "tools" / "dex2jar" / "dex-tools-v2.4"
        self.d2j_dex2jar = self.dex2jar_dir / "d2j-dex2jar.bat"
        self.jd_cli_jar = self.base_dir / "tools" / "jd-cli.jar"
        self.jadx_jar = self.base_dir / "tools" / "jadx" / "lib" / "jadx-1.5.6-all.jar"

        self.java_cmd = self._find_java()
        if output_dir is None:
            if getattr(sys, "frozen", False):
                output_dir = None  # triggers default_output_dir()
            else:
                output_dir = self.base_dir / "output"
        self.file_mgr = FileManager(base_output_dir=output_dir)

        # result paths (valid after decompile)
        self.result_java_dir: Path | None = None
        self.result_resources_dir: Path | None = None

    # ------------------------------------------------------------------
    @staticmethod
    def _find_java() -> str:
        found = shutil.which("java")
        if found:
            return found
        return "java"

    def check_tools(self) -> list[str]:
        """Return a list of missing-tool error strings (empty = all good)."""
        problems: list[str] = []
        if not self.d2j_dex2jar.is_file():
            problems.append(f"dex2jar script not found: {self.d2j_dex2jar}")
        if not self.jd_cli_jar.is_file():
            problems.append(f"jd-cli.jar not found: {self.jd_cli_jar}")
        if not self.jadx_jar.is_file():
            problems.append(f"jadx not found: {self.jadx_jar}")
        if shutil.which(self.java_cmd) is None and Path(self.java_cmd).name == "java":
            # shutil.which already failed; java may still run via JAVA_HOME,
            # so only warn if `java -version` fails.
            try:
                subprocess.run(
                    [self.java_cmd, "-version"],
                    capture_output=True, check=False, timeout=10,
                )
            except Exception:
                problems.append("Java runtime not found (needed for jadx/jd-cli).")
        return problems

    # ------------------------------------------------------------------
    def decompile(self, apk_path: str | Path,
                  on_progress: ProgressCb | None = None,
                  on_log: Callable[[str], None] | None = None,
                  engine: str = "auto",
                  deobf: bool = False) -> Path:
        """Decompile an APK. engine: 'auto' | 'jadx' | 'jd-cli'."""
        def emit(pct: int, msg: str) -> None:
            log.info("[%d%%] %s", pct, msg)
            if on_progress:
                on_progress(pct, msg)

        apk_path = Path(apk_path)
        emit(5, f"Extracting {apk_path.name} …")
        extract_root = self.file_mgr.extract_apk(apk_path)
        try:
            dex_files = self.file_mgr.find_dex_files(extract_root)
            if not dex_files:
                raise RuntimeError("No .dex files found inside the APK.")
            emit(20, f"Found {len(dex_files)} dex file(s).")

            out_dir = self.file_mgr.prepare_output_dir(apk_path)

            if engine in ("auto", "jadx"):
                try:
                    return self._decompile_jadx(
                        apk_path, out_dir, emit, on_progress, on_log, deobf)
                except Exception as e:
                    if engine == "jadx":
                        raise
                    if on_log:
                        on_log("jadx failed, falling back to jd-cli: " + str(e)[:160])

            return self._decompile_jdcli(
                apk_path, out_dir, dex_files, emit, on_progress, on_log)
        finally:
            self.file_mgr.cleanup()

    # ------------------------------------------------------------------
    # jadx path (fast, single pass, high quality)
    # ------------------------------------------------------------------
    def _decompile_jadx(self, apk_path, out_dir, emit, on_progress, on_log, deobf):
        raw = out_dir / "_jadx_raw"
        if raw.exists():
            shutil.rmtree(raw, ignore_errors=True)
        cmd = [self.java_cmd, "-Xmx4g", "-cp", str(self.jadx_jar),
               "jadx.cli.JadxCLI", "-d", str(raw), "-j", "4"]
        if deobf:
            cmd += ["--deobf", "--deobf-min", "3"]
        cmd += [str(apk_path)]
        emit(30, "Running jadx (fast decompile) …")
        self._run(cmd, cwd=str(self.base_dir), tool="jadx", on_log=on_log,
                 timeout=1200, check_exit=False)

        src = raw / "sources"
        if not src.is_dir():
            raise RuntimeError("jadx finished but produced no sources/ folder.")

        java_src_dir = out_dir / "java_source"
        if java_src_dir.exists():
            shutil.rmtree(java_src_dir, ignore_errors=True)
        shutil.move(str(src), str(java_src_dir))

        res = raw / "resources"
        resources_dir = out_dir / "resources"
        if res.is_dir():
            if resources_dir.exists():
                shutil.rmtree(resources_dir, ignore_errors=True)
            shutil.move(str(res), str(resources_dir))

        # XML: use jadx's decoded AndroidManifest + resources when present,
        # else fall back to pyaxmlparser extraction.
        n_xml = self._xml_from_jadx_resources(resources_dir, out_dir, on_log)
        if n_xml == 0:
            n_xml = self._extract_xml(apk_path, out_dir, on_log=on_log)

        shutil.rmtree(raw, ignore_errors=True)

        n_java = len(self.file_mgr.find_java_files(java_src_dir))
        self.result_java_dir = java_src_dir
        self.result_resources_dir = resources_dir if resources_dir.is_dir() else None
        emit(100, f"Done — {n_java} .java + {n_xml} .xml (jadx)")
        return java_src_dir

    def _xml_from_jadx_resources(self, resources_dir, out_dir, on_log=None):
        """Copy decoded XML files jadx already produced into the xml/ folder."""
        if not resources_dir.is_dir():
            return 0
        import re as _re
        xml_root = out_dir / "xml"
        count = 0
        for src in resources_dir.rglob("*.xml"):
            safe = str(src.relative_to(resources_dir)).replace(chr(92), "/")
            target = xml_root / safe
            try:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(str(src), str(target))
                count += 1
            except Exception:
                pass
        if on_log:
            on_log(f"Extracted {count} decoded XML files from jadx resources")
        return count

    # ------------------------------------------------------------------
    # dex2jar + jd-cli path (fallback)
    # ------------------------------------------------------------------
    def _decompile_jdcli(self, apk_path, out_dir, dex_files, emit, on_progress, on_log):
        emit(35, "Running dex2jar (dex → jar) …")
        jars = self._run_dex2jar(dex_files, out_dir, on_log=on_log)
        emit(55, f"JAR(s) created ({sum(j.stat().st_size for j in jars) // 1024} KB). Extracting XML …")
        n_xml = self._extract_xml(apk_path, out_dir, on_log=on_log)
        emit(60, f"Extracted {n_xml} XML file(s). Running jd-cli …")
        java_src_dir = out_dir / "java_source"
        java_src_dir.mkdir(parents=True, exist_ok=True)
        for jar in jars:
            self._run_jd_cli_batched(jar, java_src_dir, on_progress=on_progress,
                                     on_log=on_log)
        n_java = len(self.file_mgr.find_java_files(java_src_dir))
        self.result_java_dir = java_src_dir
        self.result_resources_dir = None
        emit(100, f"Done — {n_java} .java + {n_xml} .xml in {out_dir.name}/")
        return java_src_dir

    def _extract_xml(self, apk_path, out_dir, on_log=None):
        count = 0
        try:
            from pyaxmlparser import APK
            from pyaxmlparser.axmlprinter import AXMLPrinter
        except Exception as e:
            if on_log:
                on_log("pyaxmlparser unavailable, skipping XML: " + str(e))
            return 0
        try:
            apk = APK(str(apk_path))
        except Exception as e:
            if on_log:
                on_log("APK parse failed for XML: " + str(e))
            return 0
        xml_root = out_dir / "xml"
        xml_root.mkdir(parents=True, exist_ok=True)
        xml_files = [f for f in apk.get_files() if str(f).lower().endswith(".xml")]
        total = len(xml_files)
        for i, name in enumerate(xml_files, 1):
            safe = str(name).replace(chr(92), "/").lstrip("/")
            target = xml_root / safe
            try:
                target.parent.mkdir(parents=True, exist_ok=True)
                data = apk.get_file(name)
                text = None
                try:
                    text = AXMLPrinter(data).get_xml().decode("utf-8", "replace")
                except Exception:
                    try:
                        text = data.decode("utf-8")
                    except Exception:
                        text = None
                if text is None:
                    target.write_bytes(data)
                else:
                    target.write_text(text, encoding="utf-8")
                count += 1
            except Exception as e:
                if on_log:
                    on_log("xml skip " + str(name) + ": " + str(e))
            if on_log and (i % 100 == 0 or i == total):
                on_log("XML " + str(i) + "/" + str(total))
        if on_log:
            on_log("Extracted " + str(count) + "/" + str(total) + " XML files -> " + str(xml_root))
        return count

    # ------------------------------------------------------------------
    def _run_dex2jar(self, dex_files: list[Path], out_dir: Path, on_log=None) -> list[Path]:
        jars: list[Path] = []
        total = len(dex_files)
        for i, dex in enumerate(dex_files, start=1):
            jar_name = "app_classes.jar" if total == 1 else f"classes{i}.jar"
            jar_output = out_dir / jar_name
            if jar_output.exists():
                jar_output.unlink()
            cmd = [str(self.d2j_dex2jar), "-f", "-o", str(jar_output),
                   str(dex)]
            self._run(cmd, cwd=str(self.dex2jar_dir), tool="dex2jar", on_log=on_log)
            if not jar_output.is_file():
                cands = sorted(jar_output.parent.glob("*.jar"))
                if cands:
                    cands[-1].rename(jar_output)
                else:
                    raise RuntimeError("dex2jar finished but produced no .jar file.")
            jars.append(jar_output)
        return jars

    def _run_jd_cli_batched(self, jar_path, out_dir, on_progress=None, on_log=None):
        import zipfile
        try:
            with zipfile.ZipFile(jar_path) as zf:
                entries = [n for n in zf.namelist() if n.endswith(".class")]
        except Exception as e:
            if on_log:
                on_log("cannot read jar: " + str(e))
            entries = []
        if not entries:
            self._run_jd_cli(jar_path, out_dir, on_log=on_log, timeout=300)
            return
        batch_size = 40
        total = len(entries)
        n_batches = (total + batch_size - 1) // batch_size
        for b in range(n_batches):
            batch = entries[b * batch_size:(b + 1) * batch_size]
            tmp_jar = out_dir / ("_batch_" + str(b) + ".jar")
            try:
                with zipfile.ZipFile(jar_path) as zin:
                    with zipfile.ZipFile(tmp_jar, "w", zipfile.ZIP_DEFLATED) as zout:
                        for name in batch:
                            zout.writestr(name, zin.read(name))
                pct = 60 + int(((b + 1) / n_batches) * 30)
                if on_progress:
                    on_progress(pct, "jd-cli batch " + str(b + 1) + "/" + str(n_batches))
                try:
                    self._run_jd_cli(tmp_jar, out_dir, on_log=on_log, timeout=120)
                except Exception as e:
                    if on_log:
                        on_log("batch " + str(b + 1) + " skipped: " + str(e)[:120])
            finally:
                if tmp_jar.exists():
                    tmp_jar.unlink()
        for leftover in out_dir.glob("_batch_*.jar"):
            leftover.unlink(missing_ok=True)
        for leftover in out_dir.glob("_jdtmp_*"):
            import shutil
            shutil.rmtree(leftover, ignore_errors=True)

    def _run_jd_cli(self, jar_path: Path, out_dir: Path, on_log=None,
                    timeout: int = 600) -> None:
        import shutil
        tmp_out = out_dir / ("_jdtmp_" + jar_path.stem)
        if tmp_out.exists():
            shutil.rmtree(tmp_out, ignore_errors=True)
        tmp_out.mkdir(parents=True, exist_ok=True)
        cmd = [self.java_cmd, "-Xmx4g", "-jar", str(self.jd_cli_jar),
               str(jar_path), "-ods", str(tmp_out), "-g", "OFF"]
        self._run(cmd, cwd=str(self.base_dir), tool="jd-cli", on_log=on_log,
                 timeout=timeout)
        for child in list(tmp_out.iterdir()):
            base = child if child.is_dir() else tmp_out
            for src in base.rglob("*"):
                if src.is_file():
                    rel = src.relative_to(base)
                    dst = out_dir / rel
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    if dst.exists():
                        dst.unlink()
                    shutil.move(str(src), str(dst))
            if child.is_dir():
                shutil.rmtree(child, ignore_errors=True)
        shutil.rmtree(tmp_out, ignore_errors=True)

    @staticmethod
    def _run(cmd: list[str], cwd: str, tool: str,
             on_log: Callable[[str], None] | None = None,
             timeout: int = 600, check_exit: bool = True) -> None:
        # .bat scripts need cmd.exe on Windows
        if cmd[0].lower().endswith(".bat"):
            cmd = ["cmd", "/c", *cmd]
        collected: list[str] = []
        import sys as _sys
        import signal as _signal
        process_group = _sys.platform == "win32" and cmd[0] == "cmd"
        creationflags = (
            subprocess.CREATE_NEW_PROCESS_GROUP if process_group else 0
        )
        try:
            proc = subprocess.Popen(
                cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1, creationflags=creationflags)
        except FileNotFoundError as e:
            raise RuntimeError(
                f"Required tool not found: {cmd[-1] if cmd[0]=='cmd' else cmd[0]}\n"
                f"Make sure it exists under the project's tools/ folder."
            ) from e
        assert proc.stdout is not None
        import threading

        stop = threading.Event()
        killed = threading.Event()

        def _watchdog() -> None:
            # Hard wall-clock kill: guarantees a hung tool can never stall the
            # pipeline (jd-cli can loop forever on some obfuscated classes).
            if not stop.wait(timeout):
                killed.set()
                try:
                    proc.kill()
                except Exception:
                    pass

        watchdog = threading.Thread(target=_watchdog, daemon=True)
        watchdog.start()
        try:
            for line in proc.stdout:
                line = line.rstrip("\r\n")
                if line:
                    collected.append(line)
                    if on_log:
                        on_log(line)
        finally:
            stop.set()
            watchdog.join(timeout=1.0)
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # Still running after stdout closed — force-kill the whole
                # child tree, else an orphaned java.exe burns CPU forever.
                try:
                    if process_group:
                        proc.send_signal(_signal.CTRL_BREAK_EVENT)
                    else:
                        proc.kill()
                except Exception:
                    pass
                try:
                    proc.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    pass
        if killed.is_set():
            raise RuntimeError(
                f"{tool} hit the {timeout}s watchdog limit — process killed."
            )
        if check_exit and proc.returncode != 0:
            raise RuntimeError(
                f"{tool} failed (exit {proc.returncode}).\n"
                f"Command: {' '.join(cmd)}\n\nOutput:\n"
                + "\n".join(collected[-60:])
            )
