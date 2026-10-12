from datetime import UTC, datetime
from decimal import Decimal

from app.book.accounts import TRADING_CASH
from app.book.vault import deposit_cap, vault_entries, vault_view
from app.main import create_app
from app.models import LedgerEntry
from fastapi.testclient import TestClient


def test_vault_json_is_complete() -> None:
    empty = vault_view([])
    assert empty == {
        "deposit": 1000000.0,
        "accumulated": 0.0,
        "phase": "50",
        "remaining": 1000000.0,
    }

    mid = vault_view(vault_entries(Decimal("35000"), ts=datetime(2026, 1, 1, tzinfo=UTC)))
    assert mid["accumulated"] == 35000.0
    assert mid["phase"] == "50"
    assert mid["remaining"] == 965000.0

    covered = vault_view(
        vault_entries(Decimal("1000000"), ts=datetime(2026, 1, 2, tzinfo=UTC))
    )
    assert covered["phase"] == "20"
    assert covered["remaining"] == 0.0
    assert set(covered) == {"deposit", "accumulated", "phase", "remaining"}


def test_vault_deposit_follows_ledger_top_ups() -> None:
    rows = [
        LedgerEntry(
            account_kind=TRADING_CASH,
            amount=Decimal("1000000"),
            reason="deposit",
            ref="initial",
            ts=datetime(2026, 1, 1, tzinfo=UTC),
        ),
        LedgerEntry(
            account_kind=TRADING_CASH,
            amount=Decimal("1000000"),
            reason="deposit",
            ref="top-up",
            ts=datetime(2026, 1, 2, tzinfo=UTC),
        ),
        *vault_entries(Decimal("35000"), ts=datetime(2026, 1, 3, tzinfo=UTC)),
    ]
    assert deposit_cap(rows) == Decimal("2000000")
    view = vault_view(rows)
    assert view["deposit"] == 2000000.0
    assert view["accumulated"] == 35000.0
    assert view["remaining"] == 1965000.0
    assert view["phase"] == "50"


def test_vault_unauthorized(monkeypatch) -> None:
    monkeypatch.setenv("APP_AUTH_TOKEN", "secret")
    client = TestClient(create_app())
    assert client.get("/vault").status_code == 401


def test_vault_without_db(monkeypatch) -> None:
    monkeypatch.setenv("APP_AUTH_TOKEN", "secret")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    client = TestClient(create_app())
    response = client.get("/vault", headers={"X-App-Token": "secret"})
    assert response.status_code == 503
