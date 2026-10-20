#!/usr/bin/env python3
"""Download and unpack the third-party decompiler tools used by PyDex.

The tools (jadx, dex2jar, jd-cli) are ~100 MB and are NOT committed to the
repository. Run this script once after cloning to fetch them:

    python tools/download_tools.py

It writes into the ``tools/`` folder so the app works unchanged.
"""

from __future__ import annotations

import shutil
import sys
import tarfile
import urllib.request
import zipfile
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent

DOWNLOADS = [
    {
        "name": "jadx 1.5.6",
        "url": "https://github.com/skylot/jadx/releases/download/v1.5.6/jadx-1.5.6.zip",
        "archive": "jadx-1.5.6.zip",
        "kind": "zip",
        "dest": TOOLS_DIR / "jadx",
        "strip": 0,
    },
    {
        "name": "dex2jar 2.4",
        "url": "https://github.com/pxb1988/dex2jar/releases/download/v2.4/dex-tools-v2.4.zip",
        "archive": "dex-tools-v2.4.zip",
        "kind": "zip",
        "dest": TOOLS_DIR / "dex2jar",
        "strip": 0,
    },
    {
        "name": "jd-cli 1.2.0",
        "url": "https://github.com/intoolswetrust/jd-cli/releases/download/jd-cli-1.2.0/jd-cli-1.2.0-dist.tar.gz",
        "archive": "jd-cli-1.2.0-dist.tar.gz",
        "kind": "tar",
        "dest": TOOLS_DIR,
        "strip": 0,
    },
]


def _progress(block_num: int, block_size: int, total: int) -> None:
    if total <= 0:
        return
    done = min(100, int(block_num * block_size * 100 / total))
    sys.stdout.write(f"\r  {done:3d}%")
    sys.stdout.flush()


def fetch(spec: dict) -> bool:
    name = spec["name"]
    dest: Path = spec["dest"]
    archive = TOOLS_DIR / spec["archive"]
    if dest.exists() and any(dest.iterdir()):
        print(f"✓ {name} already present — skipping")
        return True

    print(f"→ Downloading {name} …")
    try:
        urllib.request.urlretrieve(spec["url"], archive, _progress)
        print()
    except Exception as e:  # noqa: BLE001
        print(f"\n✗ Download failed for {name}: {e}")
        archive.unlink(missing_ok=True)
        return False

    print(f"  Extracting {archive.name} …")
    try:
        dest.mkdir(parents=True, exist_ok=True)
        if spec["kind"] == "zip":
            with zipfile.ZipFile(archive) as zf:
                zf.extractall(dest)
        else:
            with tarfile.open(archive) as tf:
                tf.extractall(dest)
        archive.unlink(missing_ok=True)
    except Exception as e:  # noqa: BLE001
        print(f"✗ Extraction failed for {name}: {e}")
        return False

    print(f"✓ {name} installed → {dest}")
    return True


def main() -> int:
    print("PyDex tool fetcher")
    print("=" * 40)
    ok = True
    for spec in DOWNLOADS:
        if not fetch(spec):
            ok = False
    print("=" * 40)
    if ok:
        print("All tools ready. Run:  python src/main.py")
        return 0
    print("Some tools could not be downloaded. Re-run this script later.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
