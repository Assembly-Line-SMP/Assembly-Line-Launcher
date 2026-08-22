# Assembly Line Launcher

A custom Minecraft launcher built specifically for the
[Assembly Line SMP](https://modrinth.com/server/assembly-line-smp)
modpack on Modrinth. Supports both **cracked (offline)** and **premium
(Microsoft)** accounts side by side, auto-updates the modpack from
Modrinth, and auto-provisions the correct Java runtime — no manual Java
install required.

Built with Python + Qt (PySide6), packaged into standalone executables
with [Nuitka](https://nuitka.net/) via GitHub Actions.

## Features

- **Multi-account**: add any number of cracked and Microsoft accounts,
  switch between them freely.
- **Cracked accounts**: offline-mode login with vanilla-compatible
  deterministic UUIDs (same UUID scheme every mainstream launcher uses).
- **Premium accounts**: real Microsoft sign-in via the OAuth device-code
  flow (no password ever touches this launcher — you sign in through
  Microsoft's own page).
- **Live modpack sync**: fetches the latest (or a chosen) version directly
  from the Modrinth API, downloads only what's missing or changed.
- **Automatic Java provisioning**: downloads the correct Eclipse Temurin
  JRE version for whatever the modpack needs — you never have to install
  Java yourself.
- **Mod loader support**: Fabric, Quilt, NeoForge, and Forge.

## Getting started (development)

```bash
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements-dev.txt
python -m launcher.app
```

Requires Python 3.11+.

## Building a standalone executable

```bash
pip install -r requirements-dev.txt
python packaging/build.py
```

Output goes to `dist/AssemblyLineLauncher-<platform>/`. Set the
`LAUNCHER_BUILD_LTO=1` environment variable to enable link-time
optimization for a smaller/faster binary at the cost of a much longer
build (this is what tagged release builds in CI use).

Pre-built binaries for Windows, macOS, and Linux are published
automatically by [GitHub Actions](.github/workflows/build.yml) on every
push, and attached to [GitHub Releases](../../releases) for tagged
versions (`v*`).

## Project layout

```
src/launcher/
    auth/       Account models, cracked login, Microsoft OAuth device-code
                flow, account persistence (system keyring when available)
    core/       Modrinth API client, .mrpack installer, vanilla Minecraft
                installer, mod loader installers, Java runtime provisioning,
                instance tracking, launch command building
    ui/         PySide6 GUI: main window, account dialog, settings dialog
    app.py      Entry point
packaging/
    build.py    Nuitka build script
docs/
    MICROSOFT_AUTH_SETUP.md   How to register your own Azure AD app
tests/          pytest test suite (runs in CI on every push)
```

## Microsoft sign-in setup

Premium account login needs an Azure AD client ID. See
[`docs/MICROSOFT_AUTH_SETUP.md`](docs/MICROSOFT_AUTH_SETUP.md) for what's
currently configured and how to switch to your own.

## License

MIT — see [LICENSE](LICENSE).
