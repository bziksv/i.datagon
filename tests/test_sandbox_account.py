import inspect

from app.broker.sandbox_account import resolve_sandbox_account
from app.broker.tinkoff import open_sandbox_account_id
from app.models import Account


def test_reuses_existing_broker_account_id() -> None:
    calls = {"n": 0}

    def opener() -> str:
        calls["n"] += 1
        return "sbx-new"

    existing = Account(kind="sandbox", broker_account_id="sbx-1")
    got, created = resolve_sandbox_account(existing, opener)
    assert created is False
    assert got is existing
    assert got.broker_account_id == "sbx-1"
    assert calls["n"] == 0


def test_opens_once_when_missing() -> None:
    calls = {"n": 0}

    def opener() -> str:
        calls["n"] += 1
        return "sbx-opened"

    first, created = resolve_sandbox_account(None, opener)
    assert created is True
    assert first.kind == "sandbox"
    assert first.broker_account_id == "sbx-opened"
    again, created_again = resolve_sandbox_account(first, opener)
    assert created_again is False
    assert again.broker_account_id == "sbx-opened"
    assert calls["n"] == 1


def test_sdk_open_uses_sandbox_service() -> None:
    source = inspect.getsource(open_sandbox_account_id)
    assert "open_sandbox_account" in source
    assert "make_client()" in source
