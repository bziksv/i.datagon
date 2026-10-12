from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from app.strategy.paper_forward import (
    new_observation,
    new_paper_forward_run,
    paper_forward_view,
)


def test_campaign_is_preregistered_and_cannot_complete_early() -> None:
    start = datetime(2026, 10, 12, tzinfo=UTC)
    run = new_paper_forward_run(
        sleeve="sma_cross",
        experiment_id=uuid4(),
        minimum_days=30,
        started_at=start,
    )
    rows = [
        new_observation(
            run,
            strategy_equity=Decimal("100"),
            benchmark_equity=Decimal("100"),
            observed_at=start,
        ),
        new_observation(
            run,
            strategy_equity=Decimal("110"),
            benchmark_equity=Decimal("105"),
            observed_at=start + timedelta(days=10),
        ),
    ]
    result = paper_forward_view(
        run,
        rows,
        now=start + timedelta(days=10),
    )
    assert result["status"] == "running"
    assert result["capital_eligible"] is False


def test_positive_excess_after_full_period_can_qualify() -> None:
    start = datetime(2026, 10, 12, tzinfo=UTC)
    run = new_paper_forward_run(
        sleeve="sma_cross",
        experiment_id=uuid4(),
        minimum_days=30,
        started_at=start,
    )
    rows = [
        new_observation(
            run,
            strategy_equity=Decimal("100"),
            benchmark_equity=Decimal("100"),
            observed_at=start,
        ),
        new_observation(
            run,
            strategy_equity=Decimal("110"),
            benchmark_equity=Decimal("105"),
            observed_at=start + timedelta(days=30),
        ),
    ]
    result = paper_forward_view(
        run,
        rows,
        now=start + timedelta(days=30),
    )
    assert result["complete"] is True
    assert result["capital_eligible"] is True
    assert result["excess_return"] == pytest.approx(0.05)


def test_observation_before_start_or_with_invalid_equity_is_rejected() -> None:
    start = datetime(2026, 10, 12, tzinfo=UTC)
    run = new_paper_forward_run(
        sleeve="sma_cross",
        experiment_id=uuid4(),
        started_at=start,
    )
    with pytest.raises(ValueError, match="predates"):
        new_observation(
            run,
            strategy_equity=Decimal("100"),
            benchmark_equity=Decimal("100"),
            observed_at=start - timedelta(seconds=1),
        )
    with pytest.raises(ValueError, match="positive"):
        new_observation(
            run,
            strategy_equity=Decimal("0"),
            benchmark_equity=Decimal("100"),
            observed_at=start,
        )


def test_campaign_reports_stalled_observation_stream() -> None:
    start = datetime(2026, 10, 12, tzinfo=UTC)
    run = new_paper_forward_run(
        sleeve="sma_cross",
        experiment_id=uuid4(),
        started_at=start,
    )
    rows = [
        new_observation(
            run,
            strategy_equity=Decimal("100"),
            benchmark_equity=Decimal("100"),
            observed_at=start,
        )
    ]
    result = paper_forward_view(
        run,
        rows,
        now=start + timedelta(days=4),
    )
    assert result["status"] == "stalled"
    assert result["observation_stale"] is True
    assert result["last_observed_at"] == start.isoformat()
