from pathlib import Path

from launcher.auth.models import Account
from launcher.auth.store import AccountStore


def _store(tmp_path: Path) -> AccountStore:
    return AccountStore(path=tmp_path / "accounts.json")


def test_add_and_list_accounts(tmp_path):
    store = _store(tmp_path)
    store.add(Account.new_cracked("Steve"))
    store.add(Account.new_cracked("Alex"), make_active=False)

    usernames = sorted(a.username for a in store.list_accounts())
    assert usernames == ["Alex", "Steve"]


def test_first_added_account_becomes_active(tmp_path):
    store = _store(tmp_path)
    account = store.add(Account.new_cracked("Steve"), make_active=False)
    assert store.active_account is not None
    assert store.active_account.id == account.id


def test_persists_across_reload(tmp_path):
    path = tmp_path / "accounts.json"
    store1 = AccountStore(path=path)
    store1.add(Account.new_cracked("Steve"))

    store2 = AccountStore(path=path)
    assert [a.username for a in store2.list_accounts()] == ["Steve"]
    assert store2.active_account.username == "Steve"


def test_readding_same_cracked_username_does_not_duplicate(tmp_path):
    store = _store(tmp_path)
    store.add(Account.new_cracked("Steve"))
    store.add(Account.new_cracked("Steve"), make_active=False)
    assert len(store.list_accounts()) == 1


def test_readding_same_username_different_case_does_not_duplicate(tmp_path):
    store = _store(tmp_path)
    store.add(Account.new_cracked("Steve"))
    store.add(Account.new_cracked("STEVE"), make_active=False)
    assert len(store.list_accounts()) == 1


def test_remove_account(tmp_path):
    store = _store(tmp_path)
    account = store.add(Account.new_cracked("Steve"))
    store.remove(account.id)
    assert store.list_accounts() == []
    assert store.active_account is None


def test_removing_active_account_promotes_another(tmp_path):
    store = _store(tmp_path)
    a1 = store.add(Account.new_cracked("Steve"))
    store.add(Account.new_cracked("Alex"), make_active=False)
    store.remove(a1.id)
    assert store.active_account is not None
    assert store.active_account.username == "Alex"


def test_set_active_switches_selection(tmp_path):
    store = _store(tmp_path)
    store.add(Account.new_cracked("Steve"))
    a2 = store.add(Account.new_cracked("Alex"), make_active=False)
    store.set_active(a2.id)
    assert store.active_account.id == a2.id
