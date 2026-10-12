from datetime import date

from app.book.orders import STATUS_REJECTED, draft_order
from app.broker.port import OrderRequest
from app.models import EarningsDay
from app.risk.calendar import SEED_EARNINGS, calendar_map, seed_earnings
from app.risk.earnings import EARNINGS_DAY, gate_earnings


def test_seed_fills_few_tickers() -> None:
    rows = seed_earnings()
    tickers = {row.ticker for row in rows}
    assert tickers >= {"SBER", "GAZP", "LKOH"}
    assert len(SEED_EARNINGS) >= 3
    assert all(isinstance(row, EarningsDay) for row in rows)
    again = seed_earnings(rows)
    assert len(again) == len(rows)


def test_seeded_calendar_feeds_veto() -> None:
    rows = seed_earnings()
    calendar = calendar_map(rows)
    order = draft_order(
        OrderRequest(
            ticker="SBER",
            side="buy",
            qty=1,
            type="market",
            client_order_id="c-cal-sber",
        ),
        sleeve="sma_cross",
    )
    blocked = gate_earnings(order, calendar, date(2026, 11, 12))
    assert blocked.status == STATUS_REJECTED
    assert blocked.raw["reject_reason"] == EARNINGS_DAY
