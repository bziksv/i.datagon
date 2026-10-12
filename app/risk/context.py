"""Полный снимок данных, обязательный для увеличения риска."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal

RISK_CONTEXT_MISSING = "risk_context_missing"
RISK_PRICE_INVALID = "risk_price_invalid"
RISK_EQUITY_INVALID = "risk_equity_invalid"
RISK_PRICE_STALE = "risk_price_stale"
RISK_DAY_START_MISSING = "risk_day_start_missing"
RISK_STOP_INVALID = "risk_stop_invalid"
RISK_BROKER_UNKNOWN = "risk_broker_unknown"


@dataclass(frozen=True)
class RiskContext:
    price: Decimal
    price_as_of: datetime
    equity: Decimal
    start_equity: Decimal
    stop_price: Decimal
    name_existing: Decimal = Decimal("0")
    sleeve_existing: Decimal = Decimal("0")
    gross_existing: Decimal = Decimal("0")
    max_drawdown: Decimal = Decimal("0")
    broker_healthy: bool = True
    observed_at: datetime | None = None
    max_price_age: timedelta = timedelta(hours=36)

    def snapshot(self) -> dict:
        observed_at = self.observed_at or datetime.now(UTC)
        return {
            "price": float(self.price),
            "price_as_of": self.price_as_of.isoformat(),
            "equity": float(self.equity),
            "start_equity": float(self.start_equity),
            "stop_price": float(self.stop_price),
            "name_existing": float(self.name_existing),
            "sleeve_existing": float(self.sleeve_existing),
            "gross_existing": float(self.gross_existing),
            "max_drawdown": float(self.max_drawdown),
            "broker_healthy": self.broker_healthy,
            "observed_at": observed_at.isoformat(),
            "max_price_age_sec": int(self.max_price_age.total_seconds()),
        }

    def error(self) -> str | None:
        if self.price <= 0:
            return RISK_PRICE_INVALID
        if self.equity <= 0:
            return RISK_EQUITY_INVALID
        if self.start_equity <= 0:
            return RISK_DAY_START_MISSING
        if self.stop_price <= 0 or self.stop_price >= self.price:
            return RISK_STOP_INVALID
        if not self.broker_healthy:
            return RISK_BROKER_UNKNOWN
        now = self.observed_at or datetime.now(UTC)
        price_at = (
            self.price_as_of
            if self.price_as_of.tzinfo is not None
            else self.price_as_of.replace(tzinfo=UTC)
        )
        if now - price_at > self.max_price_age:
            return RISK_PRICE_STALE
        return None
