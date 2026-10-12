from decimal import Decimal

from app.alloc.plan import allocation_plan
from app.alloc.view import ACTIVE_SLEEVES
from app.main import create_app
from fastapi.testclient import TestClient


def test_allocation_plan_one_million_sleeve(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("SLEEVE_WEIGHTS_PATH", str(tmp_path / "w.json"))
    equal = Decimal("1") / Decimal(len(ACTIVE_SLEEVES))
    plan = allocation_plan(
        equity=Decimal("5000000"),
        weights={name: equal for name in ACTIVE_SLEEVES},
        example_price=Decimal("250"),
        lot=1,
    )
    assert plan["equity"] == 5000000.0
    assert plan["trading_pool"] == 2000000.0
    assert plan["sleeve_share"] == 0.4
    assert plan["name_share"] == 0.1
    assert plan["max_concurrent_names"] == 10
    assert plan["sectors"] is None
    assert "сектор" in plan["sectors_note"].lower()
    by = {row["sleeve"]: row for row in plan["sleeves"]}
    assert set(by) == {
        "sma_cross",
        "donchian_breakout",
        "rsi_reversion",
        "ema_scalp",
        "overnight_bounce",
    }
    sma = by["sma_cross"]
    assert sma["capital"] == 400000.0
    assert sma["name_budget"] == 40000.0
    assert sma["example"]["qty"] == 160
    assert sma["example"]["notional"] == 40000.0
    assert sma["signal"]
    assert sma["holds"]
    assert by["ema_scalp"]["horizon"] == "15m"
    assert by["overnight_bounce"]["title"] == "Вечерний докуп"
    assert by["rsi_reversion"]["title"]


def test_allocation_plan_unauthorized(monkeypatch) -> None:
    monkeypatch.setenv("APP_AUTH_TOKEN", "secret")
    client = TestClient(create_app())
    assert client.get("/allocation/plan").status_code == 401


def test_allocation_plan_without_db(monkeypatch) -> None:
    monkeypatch.setenv("APP_AUTH_TOKEN", "secret")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    client = TestClient(create_app())
    response = client.get("/allocation/plan", headers={"X-App-Token": "secret"})
    assert response.status_code == 503
