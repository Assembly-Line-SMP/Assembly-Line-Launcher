from pathlib import Path

from launcher.core.loader_installer import _run_installer


def test_existing_loader_profile_skips_installer(tmp_path, monkeypatch):
    minecraft_root = tmp_path / "minecraft"
    profile = minecraft_root / "versions" / "neoforge-21.1.248"
    profile.mkdir(parents=True)
    profile_path = profile / "neoforge-21.1.248.json"
    profile_path.write_text("{}", encoding="utf-8")

    def fail_download(*args, **kwargs):
        raise AssertionError("cached loader profile should skip downloading")

    monkeypatch.setattr("launcher.core.loader_installer.download_file", fail_download)

    result = _run_installer(
        "https://example.invalid/installer.jar",
        "neoforge-21.1.248-installer.jar",
        tmp_path,
        Path("java"),
    )

    assert result == profile_path