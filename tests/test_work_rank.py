from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace

from app.broker.moex_candles import MOSCOW, write_candle_csv
from app.broker.port import CandleBar
from app.strategy.abs_mom import AbsMomentum4Strategy
from app.work import desk_state, service
from app.work.exits import entry_day, held_exit

START = date(2026, 8, 1)


def _bars(closes: list[float]) -> list[CandleBar]:
    bars = []
    for index, close in enumerate(closes):
        day = START + timedelta(days=index)
        ts = datetime(day.year, day.month, day.day, tzinfo=UTC) - timedelta(hours=3)
        price = Decimal(str(round(close, 4)))
        bars.append(
            CandleBar(ts=ts, o=price, h=price, low=price, c=price, v=Decimal("1000"))
        )
    return bars


def _write(root, ticker: str, closes: list[float]) -> list[CandleBar]:
    bars = _bars(closes)
    write_candle_csv(root / f"{ticker}.csv", bars)
    return bars


def _row(ticker: str, kind: str, bar: CandleBar):
    return SimpleNamespace(sleeve="abs_momentum_4", kind=kind, ticker=ticker, ts=bar.ts)


def _rising(rate: float, n: int = 50) -> list[float]:
    return [100 * (1 + rate) ** i for i in range(n)]


def test_buys_ranked_by_roc_and_held_names_not_rebought(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CANDLE_DIR", str(tmp_path))
    slow = _write(tmp_path, "SLOW", _rising(0.002))
    fast = _write(tmp_path, "FAST", _rising(0.01))
    mid = _write(tmp_path, "MID", _rising(0.005))
    held = _write(tmp_path, "HELD", _rising(0.02))
    rows = [
        _row("SLOW", "buy", slow[-1]),
        _row("FAST", "buy", fast[-1]),
        _row("MID", "buy", mid[-1]),
        _row("HELD", "buy", held[-1]),
    ]
    state = desk_state.empty_state()
    positions = {"HELD": {"ticker": "HELD", "qty": "10", "avg_price": "100"}}
    plan = service.plan_orders(state, rows, positions)
    assert [(ticker, side) for ticker, side, _day, _roc in plan] == [
        ("FAST", "buy"),
        ("MID", "buy"),
        ("SLOW", "buy"),
    ]
    day = (START + timedelta(days=49)).isoformat()
    assert {item[2] for item in plan} == {day}


def test_held_name_sells_when_strategy_would_exit(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CANDLE_DIR", str(tmp_path))
    closes = _rising(0.01, 40) + [_rising(0.01, 40)[-1] * 0.97**i for i in range(1, 13)]
    bars = _write(tmp_path, "DROP", closes)
    fast = _write(tmp_path, "FAST", _rising(0.01, len(closes)))
    entry_ts = bars[38].ts + timedelta(hours=18)
    state = desk_state.empty_state()
    state["trades"] = [{"ticker": "DROP", "side": "buy", "ts": entry_ts.isoformat()}]
    positions = {"DROP": {"ticker": "DROP", "qty": "10", "avg_price": str(bars[38].c)}}
    rows = [_row("DROP", "flat", bars[-1]), _row("FAST", "buy", fast[-1])]
    plan = service.plan_orders(state, rows, positions)
    # продажа первой: освобождает место рукава под покупку
    assert [(ticker, side) for ticker, side, _day, _roc in plan] == [
        ("DROP", "sell"),
        ("FAST", "buy"),
    ]


def test_held_name_without_fresh_candle_raises_alert(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CANDLE_DIR", str(tmp_path))
    monkeypatch.setenv("WORK_DESK_PATH", str(tmp_path / "work_desk.json"))
    fresh = _write(tmp_path, "SBER", _rising(0.01))
    _write(tmp_path, "HALT", _rising(0.01, 46))
    sent = []
    monkeypatch.setenv("TELEGRAM_ENABLED", "1")
    monkeypatch.setattr("app.ops.telegram.send_telegram", sent.append)
    state = desk_state.empty_state()
    held = {"HALT": {"ticker": "HALT", "qty": "10", "avg_price": "100"}}
    rows = [_row("SBER", "flat", fresh[-1])]
    state = service._note_stale(state, rows, held)
    decision = state["decisions"][-1]
    assert decision["ticker"] == "HALT"
    assert decision["status"] == "stale_data"
    assert decision["days_behind"] == 4
    assert service.plan_orders(state, rows, held) == []
    assert sent and "HALT" in sent[0]


def test_held_name_in_trend_is_kept(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CANDLE_DIR", str(tmp_path))
    bars = _write(tmp_path, "UP", _rising(0.005))
    state = desk_state.empty_state()
    state["trades"] = [
        {
            "ticker": "UP",
            "side": "buy",
            "ts": (bars[40].ts + timedelta(hours=18)).isoformat(),
        }
    ]
    positions = {"UP": {"ticker": "UP", "qty": "10", "avg_price": str(bars[40].c)}}
    assert service.plan_orders(state, [_row("UP", "buy", bars[-1])], positions) == []


def test_partial_sell_keeps_entry_and_ignores_pre_entry_exit() -> None:
    """Остаток после утренней урезки не продаём по выходу, который был до покупки.

    Так 27.10 ушла PMSB: продажа 550 из 610 обнулила день входа, и прогон
    последних 30 баров нашёл выход 10.10 — ещё до реальной покупки 22.10.
    """
    # Прогрев SMA30, потом трейл +30%/−8% ещё до покупки, дальше ровная цена.
    closes = [100.0] * 35 + [130.0, 120.0] + [100.0] * 23
    bars = _bars(closes)
    bought = START + timedelta(days=55)
    bought_at = datetime(bought.year, bought.month, bought.day, 12, tzinfo=MOSCOW)
    trades = [
        {"ticker": "PMSB", "side": "buy", "qty": 610, "ts": bought_at.isoformat()},
        {
            "ticker": "PMSB",
            "side": "sell",
            "qty": 550,
            "ts": (bought_at + timedelta(minutes=7)).isoformat(),
        },
    ]
    assert entry_day(trades, "PMSB", MOSCOW) == bought
    strategy = AbsMomentum4Strategy()
    assert (
        held_exit(
            strategy,
            "PMSB",
            bars,
            entry_price=Decimal("100"),
            entry_day=entry_day(trades, "PMSB", MOSCOW),
        )
        is None
    )
    # Без дня входа тот же ряд продаётся: трейл внутри чужих 30 баров.
    assert (
        held_exit(strategy, "PMSB", bars, entry_price=Decimal("100"), entry_day=None)
        == "exit"
    )
    trades.append(
        {
            "ticker": "PMSB",
            "side": "sell",
            "qty": 60,
            "ts": (bought_at + timedelta(days=5)).isoformat(),
        }
    )
    assert entry_day(trades, "PMSB", MOSCOW) is None
    rebuy = bought_at + timedelta(days=6)
    trades.append({"ticker": "PMSB", "side": "buy", "qty": 60, "ts": rebuy.isoformat()})
    assert entry_day(trades, "PMSB", MOSCOW) == rebuy.date()
