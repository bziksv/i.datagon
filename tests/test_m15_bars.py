from datetime import UTC, datetime

from worker.bars import last_closed_m15, m15_close_due


def test_last_closed_m15_floors_to_boundary() -> None:
    assert last_closed_m15(datetime(2026, 1, 1, 12, 7, tzinfo=UTC)) == datetime(
        2026, 1, 1, 12, 0, tzinfo=UTC
    )
    assert last_closed_m15(datetime(2026, 1, 1, 11, 59, tzinfo=UTC)) == datetime(
        2026, 1, 1, 11, 45, tzinfo=UTC
    )


def test_m15_close_due_advances() -> None:
    now = datetime(2026, 1, 1, 12, 7, tzinfo=UTC)
    assert m15_close_due(None, now)
    assert not m15_close_due(datetime(2026, 1, 1, 12, 0, tzinfo=UTC), now)
    assert m15_close_due(datetime(2026, 1, 1, 11, 45, tzinfo=UTC), now)
