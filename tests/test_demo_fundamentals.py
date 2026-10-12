from app.advisory.demo_fundamentals import demo_fundamental, demo_fundamentals
from app.strategy.moex_groups import all_moex_desk_tickers


def test_demo_covers_desk_universe() -> None:
    rows = demo_fundamentals()
    tickers = [row.ticker for row in rows]
    assert tickers == all_moex_desk_tickers()
    assert len(rows) >= 40


def test_demo_metrics_are_deterministic() -> None:
    a = demo_fundamental("SBER")
    b = demo_fundamental("SBER")
    assert a.pe_ratio_ttm == b.pe_ratio_ttm
    assert a.raw["demo"] is True
