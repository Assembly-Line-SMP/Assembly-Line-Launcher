#!/usr/bin/env python3
"""Build a standalone executable with Nuitka.

Usage:
    python packaging/build.py

Reads target platform from the running OS (no cross-compiling -- Nuitka
builds native to the host it runs on, which is why CI builds this on one
runner per target OS instead of building once and copying around).

Produces a single-folder distribution (not --onefile) under dist/, because
--onefile's self-extracting startup cost is a bad fit for a launcher that
should feel instant, and because PySide6/Qt's plugin discovery is far more
reliable when the actual DLLs/so files live next to the executable rather
than getting unpacked to a temp dir on every launch.
"""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
ENTRY_POINT = SRC / "launcher" / "app.py"
DIST_DIR = ROOT / "dist"

APP_NAME = "AssemblyLineLauncher"


def _platform_suffix() -> str:
    system = platform.system().lower()
    if system == "windows":
        return "windows"
    if system == "darwin":
        return "macos"
    return "linux"


def _icon_args() -> list[str]:
    icon_dir = SRC / "launcher" / "ui" / "resources"
    system = platform.system().lower()
    if system == "windows":
        icon = icon_dir / "icon.ico"
        return [f"--windows-icon-from-ico={icon}"] if icon.exists() else []
    if system == "darwin":
        icon = icon_dir / "icon.icns"
        return [f"--macos-app-icon={icon}"] if icon.exists() else []
    icon = icon_dir / "icon.png"
    return [f"--linux-icon={icon}"] if icon.exists() else []


def build() -> int:
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    DIST_DIR.mkdir(parents=True)

    system = platform.system().lower()
    use_lto = os.environ.get("LAUNCHER_BUILD_LTO", "0") == "1"

    cmd = [
        sys.executable,
        "-m",
        "nuitka",
        "--standalone",
        "--enable-plugin=pyside6",
        "--include-package=launcher",
        "--assume-yes-for-downloads",
        f"--output-dir={DIST_DIR}",
        f"--output-filename={APP_NAME}",
        "--company-name=Pavle012",
        "--product-name=Assembly Line Launcher",
        "--file-description=Launcher for the Assembly Line SMP",
        "--file-version=1.0.0.0",
        "--product-version=1.0.0.0",
        "--remove-output",
        f"--lto={'yes' if use_lto else 'no'}",
    ]

    if system == "windows":
        cmd.append("--windows-console-mode=disable")
    elif system == "darwin":
        cmd.append("--macos-create-app-bundle")
        cmd.append("--macos-app-name=Assembly Line Launcher")

    cmd.extend(_icon_args())
    cmd.append(str(ENTRY_POINT))

    print("Running:", " ".join(cmd))
    env = dict(os.environ)
    existing_pp = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = str(SRC) + (os.pathsep + existing_pp if existing_pp else "")
    result = subprocess.run(cmd, cwd=str(ROOT), env=env)  # noqa: S603
    if result.returncode != 0:
        return result.returncode

    _rename_output_dir()
    return 0


def _rename_output_dir() -> None:
    """Nuitka names the standalone output dir after the entry script
    (app.dist). Rename it to something clearer for release artifacts.
    """
    produced = DIST_DIR / "app.dist"
    if not produced.exists():
        return
    target = DIST_DIR / f"{APP_NAME}-{_platform_suffix()}"
    if target.exists():
        shutil.rmtree(target)
    produced.rename(target)
    print(f"Build output: {target}")


if __name__ == "__main__":
    sys.exit(build())
