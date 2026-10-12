import logging
from decimal import Decimal

from app.book.drift import drift_alert_line, report_cash_drift
from worker.drift import check_sandbox_drift


def test_no_alert_within_threshold() -> None:
    assert (
        drift_alert_line(Decimal("1000000"), Decimal("1000000.50")) is None
    )


def test_alert_when_drift_over_threshold(caplog) -> None:
    caplog.set_level(logging.WARNING)
    log = logging.getLogger("test.drift")
    got = report_cash_drift(
        log,
        Decimal("1000000"),
        Decimal("998000"),
        threshold=Decimal("1"),
    )
    assert got["alert"] is True
    assert got["drift"] == Decimal("2000")
    assert "ALERT drift ledger vs sandbox" in (got["message"] or "")
    assert any("ALERT drift ledger vs sandbox" in rec.message for rec in caplog.records)


def test_worker_logs_alert(caplog) -> None:
    caplog.set_level(logging.WARNING)
    log = logging.getLogger("worker")
    got = check_sandbox_drift(log, Decimal("500"), Decimal("1000"))
    assert got["alert"] is True
    assert any("ALERT drift" in rec.message for rec in caplog.records)
