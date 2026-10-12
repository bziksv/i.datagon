"""Сверка нашей книги и sandbox portfolio. Расхождение не молчим."""

from decimal import Decimal
from logging import Logger

from app.ops.telegram import alert_drift, send_telegram

DEFAULT_DRIFT_THRESHOLD = Decimal("1")


def cash_drift(ledger_cash: Decimal, sandbox_cash: Decimal) -> Decimal:
    return ledger_cash - sandbox_cash


def drift_alert_line(
    ledger_cash: Decimal,
    sandbox_cash: Decimal,
    threshold: Decimal = DEFAULT_DRIFT_THRESHOLD,
) -> str | None:
    drift = cash_drift(ledger_cash, sandbox_cash)
    if abs(drift) <= threshold:
        return None
    return (
        f"ALERT drift ledger vs sandbox cash={drift} "
        f"ledger={ledger_cash} sandbox={sandbox_cash} threshold={threshold}"
    )


def report_cash_drift(
    log: Logger,
    ledger_cash: Decimal,
    sandbox_cash: Decimal,
    threshold: Decimal = DEFAULT_DRIFT_THRESHOLD,
) -> dict:
    drift = cash_drift(ledger_cash, sandbox_cash)
    line = drift_alert_line(ledger_cash, sandbox_cash, threshold)
    if line:
        log.warning(line)
        alert_drift(line, send=send_telegram)
    return {
        "drift": drift,
        "ledger_cash": ledger_cash,
        "sandbox_cash": sandbox_cash,
        "threshold": threshold,
        "alert": line is not None,
        "message": line,
    }


def drift_view(
    ledger_cash: Decimal,
    sandbox_cash: Decimal,
    threshold: Decimal = DEFAULT_DRIFT_THRESHOLD,
) -> dict:
    drift = cash_drift(ledger_cash, sandbox_cash)
    return {
        "ledger_cash": float(ledger_cash),
        "sandbox_cash": float(sandbox_cash),
        "drift": float(drift),
        "threshold": float(threshold),
        "alert": abs(drift) > threshold,
    }
