from app.advisory.score import (
    div_score,
    sane_dividend_yield_pct,
    score_fundamental,
)
from app.advisory.view import fundamental_item
from app.models import Fundamental
from datetime import UTC, datetime


def test_sfin_like_outlier_is_dropped_from_score_and_view() -> None:
    assert sane_dividend_yield_pct(186.98) is None
    assert div_score(186.98) == 0.0
    scored = score_fundamental(
        pe_ratio_ttm=2.32,
        price_to_book_ttm=0.52,
        eps_ttm=237.0,
        raw={"roe": 15.67, "dividend_yield_daily_ttm": 186.98},
    )
    assert scored.div == 0.0
    # 92.5*0.4 + 72.5*0.35 + 0*0.25 ≈ 62.4 — без раздачи веса див. остальным
    assert 61.0 <= scored.total <= 63.5
    assert "выброс" in scored.rationale
    row = Fundamental(
        ticker="SFIN",
        asset_uid="a",
        ts=datetime(2026, 10, 13, tzinfo=UTC),
        pe_ratio_ttm=2.32,
        price_to_book_ttm=0.52,
        eps_ttm=237.0,
        raw={"roe": 15.67, "dividend_yield_daily_ttm": 186.98, "name": "ЭсЭфАй"},
    )
    item = fundamental_item(row)
    assert item["dividend_yield_ttm"] is None
    assert item["dividend_yield_outlier"] is True
    assert item["scores"]["div"] == 0.0
    assert item["scores"]["total"] == scored.total


def test_normal_div_yield_still_scores() -> None:
    assert sane_dividend_yield_pct(0.08) == 8.0
    assert div_score(0.08) == 80.0
