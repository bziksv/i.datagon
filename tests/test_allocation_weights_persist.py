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
            "sma_cross": 0.25,
            "donchian_breakout": 0.2,
            "rsi_reversion": 0.15,
            "ema_scalp": 0.12,
            "vol_scalp": 0.1,
            "overnight_bounce": 0.08,
            "morning_bounce": 0.05,
            "abs_momentum": 0.05,
            "abs_momentum_2": 0,
            "abs_momentum_3": 0,
            "abs_momentum_4": 0,
        }
    )
    got = load_weights(ACTIVE_SLEEVES)
    assert got["sma_cross"] == Decimal("0.25")
    assert got["donchian_breakout"] == Decimal("0.2")
    assert got["rsi_reversion"] == Decimal("0.15")
    assert got["ema_scalp"] == Decimal("0.12")
    assert got["vol_scalp"] == Decimal("0.1")
    assert got["overnight_bounce"] == Decimal("0.08")
    assert got["morning_bounce"] == Decimal("0.05")
    assert got["abs_momentum"] == Decimal("0.05")
    view = allocation_view(ACTIVE_SLEEVES, equity=Decimal("1000000"))
    by = {row["sleeve"]: row for row in view["sleeves"]}
    assert by["sma_cross"]["weight"] == 0.25
    assert by["sma_cross"]["capital"] == 100000.0  # 1e6 * 0.4 * 0.25


def test_put_allocation_weights_persists(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("APP_AUTH_TOKEN", "secret")
    monkeypatch.setenv("SLEEVE_WEIGHTS_PATH", str(tmp_path / "alloc.json"))
    # без БД endpoint вернёт 503 — проверяем store + view, как кабинет читает после save
    equal = 1 / 8
    save_weights(
        {
            "sma_cross": equal,
            "donchian_breakout": equal,
            "rsi_reversion": equal,
            "ema_scalp": equal,
            "vol_scalp": equal,
            "overnight_bounce": equal,
            "morning_bounce": equal,
            "abs_momentum": equal,
            "abs_momentum_2": 0,
            "abs_momentum_3": 0,
            "abs_momentum_4": 0,
        }
    )
    view = allocation_view(ACTIVE_SLEEVES, equity=Decimal("1000000"))
    by = {row["sleeve"]: row for row in view["sleeves"]}
    assert by["sma_cross"]["weight"] == equal
    assert by["ema_scalp"]["weight"] == equal
    assert by["vol_scalp"]["weight"] == equal
    assert by["overnight_bounce"]["weight"] == equal
    assert by["morning_bounce"]["weight"] == equal
    assert by["abs_momentum"]["weight"] == equal


def test_explicit_cash_reserve_is_not_renormalized(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("SLEEVE_WEIGHTS_PATH", str(tmp_path / "cash.json"))
    save_weights(
        {
            "sma_cross": 0.5,
            "donchian_breakout": 0,
            "rsi_reversion": 0,
            "ema_scalp": 0,
            "vol_scalp": 0,
            "overnight_bounce": 0,
            "morning_bounce": 0,
            "abs_momentum": 0,
            "abs_momentum_2": 0,
            "abs_momentum_3": 0,
            "abs_momentum_4": 0,
            "cash": 0.5,
        }
    )
    got = load_weights(ACTIVE_SLEEVES)
    assert got["sma_cross"] == Decimal("0.5")
    assert sum(got.values()) == Decimal("0.5")


def test_desk_candles_lists_local_csvs(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("APP_AUTH_TOKEN", "secret")
    monkeypatch.setenv("CANDLE_DIR", str(tmp_path))
    monkeypatch.setenv("CANDLE_SP500_DIR", str(tmp_path / "sp500_empty"))
    (tmp_path / "SBER.csv").write_text(
        Path("tests/fixtures/sber_daily.csv").read_text()
    )
    (tmp_path / "GAZP.csv").write_text(
        Path("tests/fixtures/sber_daily.csv").read_text()
    )
    client = TestClient(create_app())
    response = client.get(
        "/desk/candles?tf=1d",
        headers={"X-App-Token": "secret"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["tickers"] == ["GAZP", "SBER"]
    assert body["count"] == 2
    assert body["groups"]["moex"] == ["GAZP", "SBER"]
    assert body["groups"]["sp500"] == []


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


def test_desk_backtest_batch_api(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("APP_AUTH_TOKEN", "secret")
    src = Path("tests/fixtures/sber_daily.csv")
    (tmp_path / "SBER.csv").write_text(src.read_text())
    (tmp_path / "GAZP.csv").write_text(src.read_text())
    monkeypatch.setenv("CANDLE_DIR", str(tmp_path))
    monkeypatch.setenv("CANDLE_SP500_DIR", str(tmp_path / "sp500_empty"))
    m15 = tmp_path / "m15"
    m15.mkdir()
    (m15 / "SBER.csv").write_text(Path("tests/fixtures/sber_m15.csv").read_text())
    monkeypatch.setenv("CANDLE_M15_DIR", str(m15))
    client = TestClient(create_app())
    response = client.post(
        "/desk/backtests/batch",
        headers={"X-App-Token": "secret"},
        json={},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["count"] == 22  # 11 sleeves × 2 daily tickers
    assert body["ok"] == 22
    assert body["skipped"] == 0
    assert len(body["rows"]) == 22
    assert "top" in body
    assert "by_sleeve" in body
    assert len(body["by_sleeve"]) == 11
    sample_sum = body["by_sleeve"][0]
    assert "net_pnl" in sample_sum
    assert "max_drawdown" in sample_sum
    assert "peak_equity" in sample_sum
    assert "equity_curve" in sample_sum
    assert isinstance(sample_sum["equity_curve"], list)
    sleeves = {row["sleeve"] for row in body["rows"]}
    tickers = {row["ticker"] for row in body["rows"]}
    assert sleeves == {
        "sma_cross",
        "donchian_breakout",
        "rsi_reversion",
        "ema_scalp",
        "vol_scalp",
        "overnight_bounce",
        "morning_bounce",
        "abs_momentum",
        "abs_momentum_2",
        "abs_momentum_3",
        "abs_momentum_4",
    }
    assert tickers == {"SBER", "GAZP"}
    # без m15 для GAZP скальп падает на дневки (как одиночный desk_backtest)
    scalp_gazp = next(
        row
        for row in body["rows"]
        if row["sleeve"] == "ema_scalp" and row["ticker"] == "GAZP"
    )
    assert scalp_gazp["status"] == "ok"
    assert scalp_gazp["bars"] == 9
    sample = next(row for row in body["rows"] if row["status"] == "ok")
    assert "trade_rows" in sample
    assert isinstance(sample["trade_rows"], list)
    if sample["trades"]:
        trade = sample["trade_rows"][0]
        assert "qty" in trade
        assert "buy_qty" in trade
        assert "sell_qty" in trade
        assert "averaged" in trade
        assert "entry_price" in trade
        assert "notional" in trade
        assert "net_pnl" in trade
    subset = client.post(
        "/desk/backtests/batch",
        headers={"X-App-Token": "secret"},
        json={
            "sleeves": ["sma_cross", "overnight_bounce"],
            "tickers": ["SBER"],
        },
    )
    assert subset.status_code == 200, subset.text
    picked = subset.json()
    assert picked["count"] == 2
    assert picked["tickers"] == ["SBER"]
    assert set(picked["sleeves"]) == {"sma_cross", "overnight_bounce"}


def test_cabin_strategies_budget_and_desk_ui() -> None:
    js = Path("web/cabin.js").read_text()
    assert "strategies-budgets" in js
    assert "strategies-desk" in js
    assert "strategies-plan" in js
    assert "strategies-whatif" in js
    assert "lastDeskSleeve" in js
    assert 'id === selectedSleeve ? " selected"' in js
    assert 'apiGet("/desk/candles?tf=1d")' in js
    assert 'id="desk-ticker"' in js
    assert "Период файла:" in js
    assert "deskDateLabel" in js
    assert "торг. лет" in js
    assert "Прогон на истории" in js
    assert "Strategy evidence report" not in js
    assert "OOS QUALIFIED" not in js
    assert "next-bar" not in js.split("function renderStrategiesDesk")[1].split(
        "function renderStrategiesCompare"
    )[0]
    assert "/allocation/plan" in js
    assert 'apiPut("/allocation/weights"' in js
    assert 'apiPost("/backtests"' in js
    assert '"/desk/backtests/batch"' in js
    assert "FETCH_TIMEOUT_BATCH_MS" in js
    assert 'id="desk-run-all"' in js
    assert "Прогнать выбранные" in js
    assert "strategies-desk-batch" in js
    assert "strategies-desk-pick" in js
    assert "desk-batch-row" in js
    assert "trade_rows" in js
    assert "сумма покупки" in js
    assert "data-desk-check" in js
    assert "sleeves: sleeves, tickers: tickers" in js
    assert "Сохранить бюджеты" in js
    assert "Прогнать одну пару" in js
    assert "Секторов нет" in js
    assert "data-sleeve-capital" in js
    assert "rsi_reversion" in js
    assert "ema_scalp" in js
    assert "Семь рукавов" in js
    assert "overnight_bounce" in js
    assert "morning_bounce" in js
    assert "abs_momentum" in js
    assert "Абс. моментум" in js
    assert "Вечерний докуп" in js
    assert "Утренний докуп" in js
    assert "renderDeskBatchSummaries" in js
    assert "by_sleeve" in js
    assert "пик капитала" in js
    assert "макс. просадка" in js
    assert "MOEX · ядро" in js or "deskDefaultTickers" in js
    assert "Тикеры S&P 500" in js
    assert "desk-sp500-break" in js
    assert "lastDeskGroups" in js
    assert "data-desk-scope" in js
    assert "sectors" in js
    assert "deskDefaultTickers" in js
