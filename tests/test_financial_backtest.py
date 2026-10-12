from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.broker.port import CandleBar
from app.strategy.backtest import BacktestConfig, run_backtest, run_walk_forward
from app.strategy.base import BarContext, Signal, Strategy


class BuyThenSell(Strategy):
    def on_bar(self, ctx: BarContext) -> Signal | None:
        if len(ctx.bars) == 1:
            return Signal("test", ctx.ticker, "buy", ctx.bars[-1].ts)
        if len(ctx.bars) == 3:
            return Signal("test", ctx.ticker, "sell", ctx.bars[-1].ts)
        return None


def _bars() -> list[CandleBar]:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    prices = ("10", "11", "12", "13")
    return [
        CandleBar(
            ts=start + timedelta(days=index),
            o=Decimal(price),
            h=Decimal(price),
            low=Decimal(price),
            c=Decimal(price),
            v=Decimal("100000"),
        )
        for index, price in enumerate(prices)
    ]


def test_signals_execute_on_next_bar_without_lookahead() -> None:
    result = run_backtest(
        BuyThenSell(),
        "TEST",
        _bars(),
        config=BacktestConfig(
            initial_cash=Decimal("1000"),
            position_share=Decimal("1"),
            commission_bps=Decimal("0"),
            slippage_bps=Decimal("0"),
        ),
    )
    assert result["fills"][0]["ts"] == _bars()[1].ts.isoformat()
    assert result["fills"][0]["price"] == 11.0
    assert result["fills"][1]["ts"] == _bars()[3].ts.isoformat()
    assert result["fills"][1]["price"] == 13.0
    assert result["summary"]["net_pnl"] == 180.0
    assert result["summary"]["trades"] == 1


def test_costs_reduce_result_and_run_is_deterministic() -> None:
    free = BacktestConfig(
        initial_cash=Decimal("1000"),
        position_share=Decimal("1"),
        commission_bps=Decimal("0"),
        slippage_bps=Decimal("0"),
    )
    costly = BacktestConfig(
        initial_cash=Decimal("1000"),
        position_share=Decimal("1"),
        commission_bps=Decimal("10"),
        slippage_bps=Decimal("10"),
    )
    baseline = run_backtest(BuyThenSell(), "TEST", _bars(), config=free)
    first = run_backtest(BuyThenSell(), "TEST", _bars(), config=costly)
    second = run_backtest(BuyThenSell(), "TEST", _bars(), config=costly)
    assert first == second
    assert first["summary"]["net_pnl"] < baseline["summary"]["net_pnl"]
    assert first["summary"]["costs"] > 0
    assert first["summary"]["max_drawdown"] >= 0
    assert first["summary"]["benchmark_return"] > 0


def test_open_position_is_marked_to_market() -> None:
    class BuyOnly(Strategy):
        def on_bar(self, ctx: BarContext) -> Signal | None:
            if len(ctx.bars) == 1:
                return Signal("test", ctx.ticker, "buy", ctx.bars[-1].ts)
            return None

    result = run_backtest(
        BuyOnly(),
        "TEST",
        _bars(),
        config=BacktestConfig(
            initial_cash=Decimal("1000"),
            position_share=Decimal("1"),
            commission_bps=Decimal("0"),
            slippage_bps=Decimal("0"),
        ),
    )
    assert result["summary"]["open_qty"] == 90
    assert result["summary"]["final_equity"] == 1180.0
    assert result["summary"]["closed_trade_pnl"] == 0.0


def test_walk_forward_executes_only_in_oos_and_does_not_read_future() -> None:
    class BuyAtBoundary(Strategy):
        def on_bar(self, ctx: BarContext) -> Signal | None:
            if len(ctx.bars) == 2:
                return Signal("test", ctx.ticker, "buy", ctx.bars[-1].ts)
            return None

    config = BacktestConfig(
        initial_cash=Decimal("1000"),
        position_share=Decimal("1"),
        commission_bps=Decimal("0"),
        slippage_bps=Decimal("0"),
    )
    baseline = run_walk_forward(
        BuyAtBoundary,
        "TEST",
        _bars(),
        train_bars=2,
        test_bars=1,
        config=config,
    )
    changed_future = list(_bars())
    changed_future[-1] = CandleBar(
        ts=changed_future[-1].ts,
        o=Decimal("999"),
        h=Decimal("999"),
        low=Decimal("999"),
        c=Decimal("999"),
        v=changed_future[-1].v,
    )
    changed = run_walk_forward(
        BuyAtBoundary,
        "TEST",
        changed_future,
        train_bars=2,
        test_bars=1,
        config=config,
    )
    first = baseline["folds"][0]["result"]
    assert first["fills"][0]["ts"] == _bars()[2].ts.isoformat()
    assert first["config"]["warmup_bars"] == 2
    assert first == changed["folds"][0]["result"]
