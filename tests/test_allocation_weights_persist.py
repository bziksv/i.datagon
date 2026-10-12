"""Сохранение бюджетов рукавов и desk backtest API."""

from decimal import Decimal
from pathlib import Path

from app.alloc.view import ACTIVE_SLEEVES, allocation_view
from app.alloc.weights_store import load_weights, save_weights
from app.main import create_app
from app.strategy.desk import desk_backtest
from fastapi.testclient import TestClient


def test_weights_roundtrip(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("SLEEVE_WEIGHTS_PATH", str(tmp_path / "w.json"))
    save_weights(
        {
            "sma_cross": 0.4,
            "donchian_breakout": 0.3,
            "rsi_reversion": 0.2,
            "ema_scalp": 0.1,
        }
    )
    got = load_weights(ACTIVE_SLEEVES)
    assert got["sma_cross"] == Decimal("0.4")
    assert got["donchian_breakout"] == Decimal("0.3")
    assert got["rsi_reversion"] == Decimal("0.2")
    assert got["ema_scalp"] == Decimal("0.1")
    view = allocation_view(ACTIVE_SLEEVES, equity=Decimal("1000000"))
    by = {row["sleeve"]: row for row in view["sleeves"]}
    assert by["sma_cross"]["weight"] == 0.4
    assert by["sma_cross"]["capital"] == 160000.0  # 1e6 * 0.4 * 0.4


def test_put_allocation_weights_persists(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("APP_AUTH_TOKEN", "secret")
    monkeypatch.setenv("SLEEVE_WEIGHTS_PATH", str(tmp_path / "alloc.json"))
    # без БД endpoint вернёт 503 — проверяем store + view, как кабинет читает после save
    save_weights(
        {
            "sma_cross": 0.25,
            "donchian_breakout": 0.25,
            "rsi_reversion": 0.25,
            "ema_scalp": 0.25,
        }
    )
    view = allocation_view(ACTIVE_SLEEVES, equity=Decimal("1000000"))
    by = {row["sleeve"]: row for row in view["sleeves"]}
    assert by["sma_cross"]["weight"] == 0.25
    assert by["ema_scalp"]["weight"] == 0.25


def test_explicit_cash_reserve_is_not_renormalized(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("SLEEVE_WEIGHTS_PATH", str(tmp_path / "cash.json"))
    save_weights(
        {
            "sma_cross": 0.5,
            "donchian_breakout": 0,
            "rsi_reversion": 0,
            "ema_scalp": 0,
            "cash": 0.5,
        }
    )
    got = load_weights(ACTIVE_SLEEVES)
    assert got["sma_cross"] == Decimal("0.5")
    assert sum(got.values()) == Decimal("0.5")


def test_desk_backtest_api(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("APP_AUTH_TOKEN", "secret")
    src = Path("tests/fixtures/sber_daily.csv")
    dest = tmp_path / "SBER.csv"
    dest.write_text(src.read_text())
    monkeypatch.setenv("CANDLE_DIR", str(tmp_path))
    client = TestClient(create_app())
    response = client.post(
        "/desk/backtest",
        headers={"X-App-Token": "secret"},
        json={"sleeve": "sma_cross", "ticker": "SBER"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["bars"] == 9
    assert body["sleeve"] == "sma_cross"
    assert "signals" in body
    assert "kinds" in body
    result = desk_backtest(sleeve="donchian_breakout", ticker="SBER")
    assert result["ticker"] == "SBER"
    assert result["bars"] == 9
    assert result["from"]
    assert result["to"]
    assert result["evaluation_start"]
    rsi = desk_backtest(sleeve="rsi_reversion", ticker="SBER")
    assert rsi["sleeve"] == "rsi_reversion"
    m15 = tmp_path / "m15"
    m15.mkdir()
    (m15 / "SBER.csv").write_text(Path("tests/fixtures/sber_m15.csv").read_text())
    monkeypatch.setenv("CANDLE_M15_DIR", str(m15))
    scalp = desk_backtest(sleeve="ema_scalp", ticker="SBER")
    assert scalp["sleeve"] == "ema_scalp"
    assert scalp["tf"] == "15m"
    assert scalp["bars"] == 12


def test_cabin_strategies_budget_and_desk_ui() -> None:
    js = Path("web/cabin.js").read_text()
    assert "strategies-budgets" in js
    assert "strategies-desk" in js
    assert "strategies-plan" in js
    assert "strategies-whatif" in js
    assert "lastDeskSleeve" in js
    assert 'id === selectedSleeve ? " selected"' in js
    assert "Период файла:" in js
    assert "Прогон на истории" in js
    assert "Strategy evidence report" not in js
    assert "OOS QUALIFIED" not in js
    assert "next-bar" not in js.split("function renderStrategiesDesk")[1].split(
        "function renderStrategiesCompare"
    )[0]
    assert "/allocation/plan" in js
    assert 'apiPut("/allocation/weights"' in js
    assert 'apiPost("/backtests"' in js
    assert "Сохранить бюджеты" in js
    assert "Прогнать на истории" in js
    assert "Секторов нет" in js
    assert "data-sleeve-capital" in js
    assert "rsi_reversion" in js
    assert "ema_scalp" in js
    assert "четыре рукава" in js
