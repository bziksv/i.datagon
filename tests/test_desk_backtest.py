from pathlib import Path

from app.strategy.backtest import load_bars, replay
from app.strategy.sma import SmaCrossStrategy

FIXTURE = Path(__file__).parent / "fixtures" / "sber_daily.csv"


def test_desk_backtest_one_ticker_without_broker() -> None:
    bars = load_bars(FIXTURE)
    assert len(bars) == 9
    signals = replay(SmaCrossStrategy(fast=2, slow=3), "SBER", bars)
    kinds = [row.kind for row in signals]
    assert "buy" in kinds
    assert "sell" in kinds
    assert {row.ticker for row in signals} == {"SBER"}
    assert {row.sleeve for row in signals} == {"sma_cross"}
