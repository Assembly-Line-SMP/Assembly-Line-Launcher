import json
import zipfile
from pathlib import Path

import pytest

from launcher.core.mrpack import (
    MrpackError,
    _extract_overrides,
    _file_applies_to_client,
    read_manifest,
)


def _make_mrpack(tmp_path: Path, manifest: dict, overrides: dict[str, str] | None = None) -> Path:
    path = tmp_path / "test.mrpack"
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("modrinth.index.json", json.dumps(manifest))
        for rel, content in (overrides or {}).items():
            zf.writestr(f"overrides/{rel}", content)
    return path


def _base_manifest(**dep_overrides) -> dict:
    deps = {"minecraft": "1.20.1", "neoforge": "20.1.57"}
    deps.update(dep_overrides)
    return {
        "formatVersion": 1,
        "game": "minecraft",
        "versionId": "1.0.0",
        "name": "Test Pack",
        "dependencies": deps,
        "files": [],
    }


def test_read_manifest_parses_neoforge_dependency(tmp_path):
    mrpack = _make_mrpack(tmp_path, _base_manifest())
    manifest = read_manifest(mrpack)
    assert manifest.dependencies.minecraft_version == "1.20.1"
    assert manifest.dependencies.loader_id == "neoforge"
    assert manifest.dependencies.loader_version == "20.1.57"


def test_read_manifest_parses_fabric_dependency(tmp_path):
    manifest_data = _base_manifest()
    manifest_data["dependencies"] = {"minecraft": "1.20.1", "fabric-loader": "0.15.7"}
    mrpack = _make_mrpack(tmp_path, manifest_data)
    manifest = read_manifest(mrpack)
    assert manifest.dependencies.loader_id == "fabric-loader"
    assert manifest.dependencies.loader_version == "0.15.7"


def test_read_manifest_rejects_missing_minecraft_version(tmp_path):
    manifest_data = _base_manifest()
    manifest_data["dependencies"] = {"neoforge": "20.1.57"}
    mrpack = _make_mrpack(tmp_path, manifest_data)
    with pytest.raises(MrpackError):
        read_manifest(mrpack)


def test_read_manifest_rejects_missing_loader(tmp_path):
    manifest_data = _base_manifest()
    manifest_data["dependencies"] = {"minecraft": "1.20.1"}
    mrpack = _make_mrpack(tmp_path, manifest_data)
    with pytest.raises(MrpackError):
        read_manifest(mrpack)


def test_read_manifest_rejects_non_mrpack_zip(tmp_path):
    path = tmp_path / "not_a_pack.mrpack"
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("readme.txt", "hello")
    with pytest.raises(MrpackError):
        read_manifest(path)


def test_client_unsupported_file_is_excluded():
    entry = {"path": "mods/serveronly.jar", "env": {"client": "unsupported", "server": "required"}}
    assert _file_applies_to_client(entry) is False


def test_client_required_file_is_included():
    entry = {"path": "mods/examplemod.jar", "env": {"client": "required", "server": "required"}}
    assert _file_applies_to_client(entry) is True


def test_file_without_env_defaults_to_included():
    entry = {"path": "mods/nofield.jar"}
    assert _file_applies_to_client(entry) is True


def test_extract_overrides_writes_files_stripped_of_prefix(tmp_path):
    mrpack = _make_mrpack(
        tmp_path, _base_manifest(), overrides={"config/test.cfg": "hello=world"}
    )
    dest = tmp_path / "instance"
    _extract_overrides(mrpack, dest)
    extracted = dest / "config" / "test.cfg"
    assert extracted.exists()
    assert extracted.read_text() == "hello=world"


def test_extract_overrides_skips_server_overrides(tmp_path):
    path = tmp_path / "test.mrpack"
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("modrinth.index.json", json.dumps(_base_manifest()))
        zf.writestr("server-overrides/server.properties", "eula=true")
    dest = tmp_path / "instance"
    _extract_overrides(path, dest)
    assert not (dest / "server.properties").exists()
