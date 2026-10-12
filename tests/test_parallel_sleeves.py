from pathlib import Path
from uuid import uuid4

from app.strategy.backtest import load_bars
from app.strategy.donchian import DonchianBreakoutStrategy
from app.strategy.parallel import run_parallel
from app.strategy.sma import SmaCrossStrategy

FIXTURE = Path(__file__).parent / "fixtures" / "sber_daily.csv"


def test_two_sleeves_share_bars_keep_separate_books() -> None:
    bars = load_bars(FIXTURE)
    instrument_id = uuid4()
    books = run_parallel(
        [
            SmaCrossStrategy(fast=2, slow=3),
            DonchianBreakoutStrategy(period=2),
        ],
        "SBER",
        bars,
        instrument_id=instrument_id,
        qty=1,
    )
    assert set(books) == {"sma_cross", "donchian_breakout"}
    assert books["sma_cross"].instrument_id == instrument_id
    assert books["donchian_breakout"].instrument_id == instrument_id
    assert books["sma_cross"].sleeve == "sma_cross"
    assert books["donchian_breakout"].sleeve == "donchian_breakout"
    assert books["sma_cross"] is not books["donchian_breakout"]
