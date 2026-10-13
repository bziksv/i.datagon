from app.advisory.demo_fundamentals import demo_fundamental, demo_fundamentals
from app.advisory.moex_catalog import all_catalog_tickers
from app.advisory.view import fundamentals_view


def test_demo_covers_catalog_universe() -> None:
    rows = demo_fundamentals()
    tickers = [row.ticker for row in rows]
    assert tickers == all_catalog_tickers()
    assert len(rows) >= 70


def test_demo_metrics_are_deterministic() -> None:
    a = demo_fundamental("SBER")
    b = demo_fundamental("SBER")
    assert a.pe_ratio_ttm == b.pe_ratio_ttm
    assert a.raw["demo"] is True
    assert a.raw["name"] == "Сбербанк"


def test_fundamentals_view_groups_by_sector_and_name() -> None:
    view = fundamentals_view(demo_fundamentals())
    assert view["count"] >= 70
    assert view["items"][0]["name"]
    assert view["items"][0]["sector_title"]
    sector_ids = {row["id"] for row in view["sectors"]}
    assert "oil_gas" in sector_ids
    assert "banks" in sector_ids
