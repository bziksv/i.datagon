"""Pre-registered paper-forward qualification on genuinely new observations."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID, uuid4

from app.models import PaperForwardObservation, PaperForwardRun


def new_paper_forward_run(
    *,
    sleeve: str,
    experiment_id: UUID,
    minimum_days: int = 30,
    started_at: datetime | None = None,
) -> PaperForwardRun:
    if minimum_days < 7:
        raise ValueError("minimum_days must be >= 7")
    start = started_at or datetime.now(UTC)
    return PaperForwardRun(
        id=uuid4(),
        sleeve=sleeve,
        experiment_id=experiment_id,
        minimum_days=minimum_days,
        started_at=start,
        ends_at=start + timedelta(days=minimum_days),
    )


def new_observation(
    run: PaperForwardRun,
    *,
    strategy_equity: Decimal,
    benchmark_equity: Decimal,
    observed_at: datetime | None = None,
) -> PaperForwardObservation:
    at = observed_at or datetime.now(UTC)
    if at < run.started_at:
        raise ValueError("observation predates campaign")
    if strategy_equity <= 0 or benchmark_equity <= 0:
        raise ValueError("equity must be positive")
    return PaperForwardObservation(
        id=uuid4(),
        run_id=run.id,
        observed_at=at,
        strategy_equity=strategy_equity,
        benchmark_equity=benchmark_equity,
    )


def paper_forward_view(
    run: PaperForwardRun,
    observations: Sequence[PaperForwardObservation],
    *,
    now: datetime | None = None,
    stale_after: timedelta = timedelta(hours=72),
) -> dict:
    observed = sorted(observations, key=lambda row: row.observed_at)
    current = now or datetime.now(UTC)
    last_observed_at = observed[-1].observed_at if observed else None
    observation_stale = bool(
        last_observed_at is None
        or current - last_observed_at > stale_after
    )
    matured = current >= run.ends_at
    covers_period = bool(
        len(observed) >= 2
        and observed[0].observed_at >= run.started_at
        and observed[-1].observed_at >= run.ends_at
    )
    strategy_return = None
    benchmark_return = None
    excess_return = None
    if covers_period:
        first = observed[0]
        last = observed[-1]
        strategy_return = (
            Decimal(str(last.strategy_equity))
            / Decimal(str(first.strategy_equity))
            - Decimal("1")
        )
        benchmark_return = (
            Decimal(str(last.benchmark_equity))
            / Decimal(str(first.benchmark_equity))
            - Decimal("1")
        )
        excess_return = strategy_return - benchmark_return
    complete = matured and covers_period
    status = (
        "complete"
        if complete
        else "incomplete"
        if matured
        else "stalled"
        if observation_stale
        else "running"
    )
    return {
        "id": str(run.id),
        "sleeve": run.sleeve,
        "experiment_id": str(run.experiment_id),
        "minimum_days": run.minimum_days,
        "started_at": run.started_at.isoformat(),
        "ends_at": run.ends_at.isoformat(),
        "observations": len(observed),
        "status": status,
        "complete": complete,
        "observation_stale": observation_stale,
        "stale_after_sec": int(stale_after.total_seconds()),
        "last_observed_at": (
            last_observed_at.isoformat() if last_observed_at else None
        ),
        "next_observation_due": (
            (last_observed_at + stale_after).isoformat()
            if last_observed_at
            else run.started_at.isoformat()
        ),
        "capital_eligible": bool(complete and excess_return and excess_return > 0),
        "strategy_return": (
            float(strategy_return) if strategy_return is not None else None
        ),
        "benchmark_return": (
            float(benchmark_return) if benchmark_return is not None else None
        ),
        "excess_return": (
            float(excess_return) if excess_return is not None else None
        ),
    }
