"""Воркер пишет алерт, если книга и sandbox разъехались."""

from decimal import Decimal
from logging import Logger

from app.book.drift import DEFAULT_DRIFT_THRESHOLD, report_cash_drift


def check_sandbox_drift(
    log: Logger,
    ledger_cash: Decimal,
    sandbox_cash: Decimal,
    threshold: Decimal = DEFAULT_DRIFT_THRESHOLD,
) -> dict:
    return report_cash_drift(log, ledger_cash, sandbox_cash, threshold)
