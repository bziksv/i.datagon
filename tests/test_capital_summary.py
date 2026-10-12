from collections.abc import AsyncIterator
from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from app.book.accounts import TRADING_CASH
from app.db import get_db
from app.main import create_app
from app.models import Candle, EquitySnapshot, LedgerEntry, Position
from fastapi.testclient import TestClient


class _CapitalSession:
    def __init__(self) -> None:
        instrument_id = uuid4()
        now = datetime.now(UTC)
        self.rows = {
            LedgerEntry: [
                LedgerEntry(
                    account_kind=TRADING_CASH,
                    amount=Decimal("5000"),
                    reason="deposit",
                    ts=now,
                )
            ],
            Position: [
                Position(
                    id=uuid4(),
                    sleeve="sma_cross",
                    instrument_id=instrument_id,
                    qty=10,
                    avg_price=Decimal("100"),
                )
            ],
            Candle: [
                Candle(
                    id=uuid4(),
                    instrument_id=instrument_id,
                    tf="1d",
                    ts=now,
                    o=Decimal("110"),
                    h=Decimal("110"),
                    low=Decimal("110"),
                    c=Decimal("110"),
                    v=Decimal("1000"),
                )
            ],
            EquitySnapshot: [],
        }

    async def scalars(self, stmt):
        entity = stmt.column_descriptions[0].get("entity")
        return self.rows.get(entity, [])


async def _db() -> AsyncIterator[_CapitalSession]:
    yield _CapitalSession()


def test_capital_summary_uses_fresh_market_price(monkeypatch) -> None:
    monkeypatch.setenv("APP_AUTH_TOKEN", "secret")
    app = create_app()
    app.dependency_overrides[get_db] = _db
    response = TestClient(app).get(
        "/capital/summary",
        headers={"X-App-Token": "secret"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "complete"
    assert response.json()["equity"] == 6100.0
    assert response.json()["unrealized_pnl"] == 100.0
