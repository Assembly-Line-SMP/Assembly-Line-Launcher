from launcher.core.downloader import _hash_matches


def test_missing_file_without_hash_is_not_a_cache_hit(tmp_path):
    assert _hash_matches(tmp_path / "missing.jar", None, None) is False


def test_existing_file_without_hash_is_a_cache_hit(tmp_path):
    path = tmp_path / "cached.jar"
    path.write_bytes(b"cached")
    assert _hash_matches(path, None, None) is True