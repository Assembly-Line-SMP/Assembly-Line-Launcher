from launcher.core.java_manager import required_java_major


def test_java_major_for_modern_minecraft():
    assert required_java_major("1.20.4") == 21
    assert required_java_major("1.21") == 21


def test_java_major_for_1_18_through_1_19():
    assert required_java_major("1.18.2") == 17
    assert required_java_major("1.19.4") == 17


def test_java_major_for_1_17():
    assert required_java_major("1.17.1") == 16


def test_java_major_for_legacy_minecraft():
    assert required_java_major("1.12.2") == 8
    assert required_java_major("1.8.9") == 8


def test_java_major_for_unparseable_version_defaults_to_latest():
    assert required_java_major("weird-snapshot-string") == 21
