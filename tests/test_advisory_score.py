from datetime import UTC, datetime

from app.advisory.score import score_fundamental
from app.advisory.screener import propose_from_scores, rank_candidates
from app.advisory.view import fundamentals_view, recommendations_view
from app.models import Fundamental


def _row(**kwargs) -> Fundamental:
    base = dict(
        ticker="SBER",
        asset_uid="a",
        ts=datetime(2026, 10, 12, tzinfo=UTC),
        pe_ratio_ttm=5.5,
        price_to_book_ttm=0.8,
        eps_ttm=45.0,
        market_capitalization=1.0,
        raw={"roe": 0.22, "dividend_yield_daily_ttm": 0.09},
    )
    base.update(kwargs)
    return Fundamental(**base)


def test_score_prefers_cheap_quality_div() -> None:
    good = score_fundamental(
        pe_ratio_ttm=5.0,
        price_to_book_ttm=0.7,
        eps_ttm=10.0,
        raw={"roe": 0.2, "dividend_yield_daily_ttm": 0.1},
    )
    weak = score_fundamental(
        pe_ratio_ttm=40.0,
        price_to_book_ttm=5.0,
        eps_ttm=-1.0,
        raw={"roe": -0.05, "dividend_yield_daily_ttm": 0.0},
    )
    assert good.total > weak.total
    assert "P/E" in good.rationale


def test_fundamentals_view_sorted() -> None:
    rows = [
        _row(ticker="WEAK", pe_ratio_ttm=40, price_to_book_ttm=4, raw={"roe": 0.02}),
        _row(ticker="SBER"),
    ]
    view = fundamentals_view(rows)
    assert view["count"] == 2
    assert view["items"][0]["ticker"] == "SBER"
    assert "disclaimer" in view


def test_recommendations_and_propose(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("PROPOSALS_PATH", str(tmp_path / "p.json"))
    rows = [_row(), _row(ticker="LKOH", pe_ratio_ttm=4.0)]
    ranked = rank_candidates(rows, limit=2, min_score=10)
    assert len(ranked) >= 1
    created = propose_from_scores(rows, limit=2, min_score=10)
    assert len(created) == len(ranked)
    assert created[0].payload["sleeve"] == "fund_screener"
    assert created[0].payload["side"] == "buy"
    recs = recommendations_view(rows, limit=5, min_score=10)
    assert recs["count"] >= 1
