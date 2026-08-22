#!/usr/bin/env python3
"""Build a standalone executable with Nuitka.

Usage:
    python packaging/build.py

Reads target platform from the running OS (no cross-compiling -- Nuitka
builds native to the host it runs on, which is why CI builds this on one
runner per target OS instead of building once and copying around).

Produces a single-folder distribution under dist/ and packages it into a
native installer for the host platform. The standalone layout keeps
PySide6/Qt plugin discovery reliable because the actual DLLs/so files live
next to the executable rather than getting unpacked to a temp directory.
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

APPIMAGE_ICON = """/* XPM */
static char *assembly_line_launcher[] = {
"16 16 2 1",
"  c None",
"X c #d97706",
"                ",
"       XX       ",
"      XXXX      ",
"     XXXXXX     ",
"    XXXXXXXX    ",
"   XXXXXXXXXX   ",
"  XXXXXXXXXXXX  ",
" XXXXXXXXXXXXXX ",
"XXXXXXXXXXXXXXXX",
" XXXXXXXXXXXXXX ",
"  XXXXXXXXXXXX  ",
"   XXXXXXXXXX   ",
"    XXXXXXXX    ",
"     XXXXXX     ",
"      XXXX      ",
"       XX       ",
"                "};
"""


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
    return _package_installer()


def _rename_output_dir() -> None:
    """Nuitka names the standalone output dir after the entry script
    (app.dist). Rename it to something clearer for release artifacts.
    """
    produced = DIST_DIR / "app.dist"
    if not produced.exists() and platform.system().lower() == "darwin":
        produced = DIST_DIR / "app.app"
    if not produced.exists():
        return
    target = DIST_DIR / f"{APP_NAME}-{_platform_suffix()}"
    if target.exists():
        shutil.rmtree(target)
    produced.rename(target)
    print(f"Build output: {target}")


def _run_required(command: list[str], tool_name: str) -> int:
    if shutil.which(command[0]) is None:
        print(f"Missing packaging tool '{tool_name}' ({command[0]}).")
        return 1
    print("Running:", " ".join(command))
    return subprocess.run(command, cwd=str(ROOT)).returncode  # noqa: S603


def _package_installer() -> int:
    platform_name = _platform_suffix()
    distribution = DIST_DIR / f"{APP_NAME}-{platform_name}"

    if platform_name == "windows":
        script = DIST_DIR / "installer.iss"
        script.write_text(
            "[Setup]\n"
            "AppName=Assembly Line Launcher\n"
            "AppVersion=1.0.0\n"
            f"DefaultDirName={{autopf}}\\{APP_NAME}\n"
            f"OutputBaseFilename={APP_NAME}-windows-installer\n"
            f"SourceDir={distribution}\n"
            f"OutputDir={DIST_DIR}\n\n"
            "[Files]\n"
            f'Source: "{distribution}\\*"; DestDir: "{{app}}"; Flags: recursesubdirs ignoreversion\n\n'
            "[Icons]\n"
            f'Name: "{{autodesktop}}\\Assembly Line Launcher"; Filename: "{{app}}\\{APP_NAME}.exe"\n',
            encoding="utf-8",
        )
        return _run_required(["ISCC", str(script)], "Inno Setup")

    if platform_name == "linux":
        appdir = DIST_DIR / f"{APP_NAME}.AppDir"
        if appdir.exists():
            shutil.rmtree(appdir)
        appdir.mkdir()
        shutil.copytree(distribution, appdir / "usr" / "bin")
        (appdir / "assembly-line-launcher.xpm").write_text(
            APPIMAGE_ICON, encoding="utf-8"
        )
        (appdir / "AppRun").write_text(
            f"#!/bin/sh\nexec \"$APPDIR/usr/bin/{APP_NAME}\" \"$@\"\n",
            encoding="utf-8",
        )
        (appdir / "AppRun").chmod(0o755)
        desktop = appdir / "assembly-line-launcher.desktop"
        desktop.write_text(
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=Assembly Line Launcher\n"
            "Exec=AssemblyLineLauncher\n"
            "Icon=assembly-line-launcher\n"
            "Categories=Game;\n",
            encoding="utf-8",
        )
        return _run_required(
            ["appimagetool", str(appdir), str(DIST_DIR / f"{APP_NAME}-linux.AppImage")],
            "appimagetool",
        )

    dmg = DIST_DIR / f"{APP_NAME}-macos.dmg"
    return _run_required(
        ["hdiutil", "create", "-volname", APP_NAME, "-srcfolder", str(distribution), "-ov", str(dmg)],
        "hdiutil",
    )


if __name__ == "__main__":
    sys.exit(build())
