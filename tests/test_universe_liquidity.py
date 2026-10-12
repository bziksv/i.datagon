from decimal import Decimal
from uuid import uuid4

from app.models import UniverseMember
from app.universe.liquidity import DEFAULT_MAX_SPREAD_BPS, DEFAULT_MIN_TURNOVER, LiquidityQuote
from worker.universe import mark_liquid


def test_illiquid_is_inactive_universe_is_finite() -> None:
    liquid_id = uuid4()
    thin_id = uuid4()
    wide_id = uuid4()
    liquid = UniverseMember(instrument_id=liquid_id, reason="dump", active=True)
    thin = UniverseMember(instrument_id=thin_id, reason="dump", active=True)
    wide = UniverseMember(instrument_id=wide_id, reason="dump", active=True)
    mark_liquid(
        [liquid, thin, wide],
        {
            liquid_id: LiquidityQuote(
                turnover=Decimal("50000000"), spread_bps=Decimal("10")
            ),
            thin_id: LiquidityQuote(
                turnover=Decimal("1000"), spread_bps=Decimal("10")
            ),
            wide_id: LiquidityQuote(
                turnover=Decimal("50000000"), spread_bps=Decimal("200")
            ),
        },
        min_turnover=DEFAULT_MIN_TURNOVER,
        max_spread_bps=DEFAULT_MAX_SPREAD_BPS,
    )
    active = [row for row in (liquid, thin, wide) if row.active]
    assert liquid.active is True
    assert thin.active is False
    assert wide.active is False
    assert len(active) == 1
