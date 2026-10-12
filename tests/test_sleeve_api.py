from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from app.main import create_app
from app.models import Position, SignalRow
from app.strategy.view import sleeve_view, sleeves_view
from fastapi.testclient import TestClient


def _signal(kind: str, *, hours: int) -> SignalRow:
    return SignalRow(
        sleeve="sma_cross",
        ticker="SBER",
        ts=datetime(2026, 1, 10, tzinfo=UTC) + timedelta(hours=hours),
        kind=kind,
        payload={},
    )


def test_sleeve_last_signals_and_pnl() -> None:
    older = _signal("flat", hours=0)
    newer = _signal("buy", hours=1)
    other = SignalRow(
        sleeve="flat",
        ticker="SBER",
        ts=datetime(2026, 1, 11, tzinfo=UTC),
        kind="flat",
        payload={},
    )
    instrument_id = uuid4()
    position = Position(
        sleeve="sma_cross",
        instrument_id=instrument_id,
        qty=10,
        avg_price=Decimal("100"),
    )
    view = sleeve_view(
        [older, newer, other],
        [position],
        marks={instrument_id: Decimal("110")},
    )
    assert view["sleeve"] == "sma_cross"
    assert [row["kind"] for row in view["signals"]] == ["buy", "flat"]
    assert view["pnl"]["unrealized"] == 100.0
    assert view["pnl"]["realized"] == 0.0
    assert view["pnl"]["total"] == 100.0
    assert len(view["positions"]) == 1
    assert view["positions"][0]["qty"] == 10
    assert view["positions"][0]["unrealized"] == 100.0


def test_sleeves_compare_pnl() -> None:
    sma_id = uuid4()
    don_id = uuid4()
    view = sleeves_view(
        [],
        [
            Position(
                sleeve="sma_cross",
                instrument_id=sma_id,
                qty=10,
                avg_price=Decimal("100"),
            ),
            Position(
                sleeve="donchian_breakout",
                instrument_id=don_id,
                qty=4,
                avg_price=Decimal("50"),
            ),
        ],
        marks={sma_id: Decimal("110"), don_id: Decimal("40")},
        realized={"sma_cross": Decimal("20")},
    )
    by_name = {row["sleeve"]: row["pnl"] for row in view["sleeves"]}
    assert set(by_name) == {
        "sma_cross",
        "donchian_breakout",
        "rsi_reversion",
        "ema_scalp",
    }
    assert by_name["sma_cross"]["unrealized"] == 100.0
    assert by_name["sma_cross"]["realized"] == 20.0
    assert by_name["sma_cross"]["total"] == 120.0
    assert by_name["donchian_breakout"]["unrealized"] == -40.0
    assert by_name["donchian_breakout"]["total"] == -40.0


def test_sleeves_unauthorized(monkeypatch) -> None:
    monkeypatch.setenv("APP_AUTH_TOKEN", "secret")
    client = TestClient(create_app())
    assert client.get("/sleeves").status_code == 401


def test_sleeve_unauthorized(monkeypatch) -> None:
    monkeypatch.setenv("APP_AUTH_TOKEN", "secret")
    client = TestClient(create_app())
    response = client.get("/sleeves/sma_cross")
    assert response.status_code == 401


def test_sleeve_without_db(monkeypatch) -> None:
    monkeypatch.setenv("APP_AUTH_TOKEN", "secret")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    client = TestClient(create_app())
    response = client.get("/sleeves/sma_cross", headers={"X-App-Token": "secret"})
    assert response.status_code == 503


def test_sleeve_donchian_path_symmetric(monkeypatch) -> None:
    monkeypatch.setenv("APP_AUTH_TOKEN", "secret")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    client = TestClient(create_app())
    headers = {"X-App-Token": "secret"}
    assert client.get("/sleeves/donchian_breakout", headers=headers).status_code == 503
    assert client.get("/sleeves/sma_cross", headers=headers).status_code == 503
    assert client.get("/sleeves/unknown_sleeve", headers=headers).status_code == 404
