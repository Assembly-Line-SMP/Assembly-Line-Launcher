from launcher.auth.cracked import InvalidUsernameError, create_cracked_account, validate_username
from launcher.auth.models import Account, AccountType, offline_uuid


def test_offline_uuid_matches_known_reference_value():
    # This is the well-known offline-mode UUID for "Notch" that every
    # offline-mode-compatible launcher (vanilla, PrismLauncher, etc.)
    # produces from the same MD5-based UUID3 derivation.
    assert offline_uuid("Notch") == "b50ad385-829d-3141-a216-7e7d7539ba7f"


def test_offline_uuid_is_deterministic():
    assert offline_uuid("SomePlayer") == offline_uuid("SomePlayer")


def test_offline_uuid_differs_by_username():
    assert offline_uuid("PlayerOne") != offline_uuid("PlayerTwo")


def test_offline_uuid_is_valid_uuid3_variant():
    u = offline_uuid("TestUser")
    # version nibble
    assert u[14] == "3"
    # RFC 4122 variant bits (top two bits of the variant nibble are 10)
    assert u[19] in "89ab"


def test_create_cracked_account_sets_type_and_uuid():
    account = create_cracked_account("Steve")
    assert account.type is AccountType.CRACKED
    assert account.username == "Steve"
    assert account.uuid == offline_uuid("Steve")
    assert account.access_token is None
    assert not account.is_premium


def test_validate_username_accepts_legal_names():
    for name in ("Steve", "Alex_123", "abc", "a" * 16):
        validate_username(name)  # should not raise


def test_validate_username_rejects_too_short():
    import pytest

    with pytest.raises(InvalidUsernameError):
        validate_username("ab")


def test_validate_username_rejects_too_long():
    import pytest

    with pytest.raises(InvalidUsernameError):
        validate_username("a" * 17)


def test_validate_username_rejects_illegal_characters():
    import pytest

    with pytest.raises(InvalidUsernameError):
        validate_username("bad name!")


def test_needs_refresh_false_for_cracked_account():
    account = create_cracked_account("Steve")
    assert account.needs_refresh is False


def test_needs_refresh_true_for_expired_premium_account():
    account = Account.new_premium(
        username="Alex",
        uuid="11111111-1111-1111-1111-111111111111",
        access_token="tok",
        refresh_token="refresh",
        expires_in_seconds=-100,  # already expired
        microsoft_user_id="user-id",
    )
    assert account.needs_refresh is True


def test_needs_refresh_false_for_fresh_premium_account():
    account = Account.new_premium(
        username="Alex",
        uuid="11111111-1111-1111-1111-111111111111",
        access_token="tok",
        refresh_token="refresh",
        expires_in_seconds=3600,
        microsoft_user_id="user-id",
    )
    assert account.needs_refresh is False


def test_account_round_trip_through_dict():
    account = create_cracked_account("Steve")
    restored = Account.from_dict(account.to_dict())
    assert restored.username == account.username
    assert restored.uuid == account.uuid
    assert restored.type == account.type
