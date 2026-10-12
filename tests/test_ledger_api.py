from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.book.accounts import TRADING_CASH
from app.book.ledger import apply_deposit, ledger_view
from app.main import create_app
from app.models import LedgerEntry
from fastapi.testclient import TestClient


def test_ledger_feed_newest_first() -> None:
    first, _ = apply_deposit([], ts=datetime(2026, 10, 12, 10, 0, tzinfo=UTC))
    assert first is not None
    later = LedgerEntry(
        account_kind=TRADING_CASH,
        amount=Decimal("-1000"),
        reason="fill",
        ref="c-1",
        ts=datetime(2026, 10, 12, 11, 0, tzinfo=UTC),
    )
    feed = ledger_view([first, later])
    assert [row["reason"] for row in feed["entries"]] == ["fill", "deposit"]
    assert feed["entries"][0]["amount"] == -1000.0
    assert feed["entries"][1]["amount"] == 1000000.0
    assert feed["entries"][0]["ts"] > feed["entries"][1]["ts"]
    assert later.ts == first.ts + timedelta(hours=1)


def test_ledger_unauthorized(monkeypatch) -> None:
    monkeypatch.setenv("APP_AUTH_TOKEN", "secret")
    client = TestClient(create_app())
    response = client.get("/ledger")
    assert response.status_code == 401


def test_ledger_without_db(monkeypatch) -> None:
    monkeypatch.setenv("APP_AUTH_TOKEN", "secret")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    client = TestClient(create_app())
    response = client.get("/ledger", headers={"X-App-Token": "secret"})
    assert response.status_code == 503
