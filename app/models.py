import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    broker_account_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Instrument(Base):
    __tablename__ = "instruments"
    __table_args__ = (
        UniqueConstraint("ticker", "class_code", name="uq_instruments_ticker_class"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    ticker: Mapped[str] = mapped_column(String(32), nullable=False)
    figi: Mapped[str | None] = mapped_column(String(32), nullable=True)
    uid: Mapped[str | None] = mapped_column(String(64), nullable=True)
    lot: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    currency: Mapped[str] = mapped_column(String(16), nullable=False)
    class_code: Mapped[str] = mapped_column(String(32), nullable=False)


class UniverseMember(Base):
    __tablename__ = "universe_members"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    instrument_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("instruments.id"), nullable=False, unique=True
    )
    reason: Mapped[str] = mapped_column(String(128), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Candle(Base):
    __tablename__ = "candles"
    __table_args__ = (
        UniqueConstraint(
            "instrument_id", "tf", "ts", name="uq_candles_instrument_tf_ts"
        ),
        Index("ix_candles_ts", "ts"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    instrument_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("instruments.id"), nullable=False
    )
    tf: Mapped[str] = mapped_column(String(8), nullable=False)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    o: Mapped[float] = mapped_column(Numeric(18, 6), nullable=False)
    h: Mapped[float] = mapped_column(Numeric(18, 6), nullable=False)
    low: Mapped[float] = mapped_column("l", Numeric(18, 6), nullable=False)
    c: Mapped[float] = mapped_column(Numeric(18, 6), nullable=False)
    v: Mapped[float] = mapped_column(Numeric(20, 4), nullable=False)


class Order(Base):
    __tablename__ = "orders"
    __table_args__ = (Index("ix_orders_status_created_at", "status", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    sleeve: Mapped[str] = mapped_column(String(64), nullable=False)
    ticker: Mapped[str] = mapped_column(String(32), nullable=False)
    side: Mapped[str] = mapped_column(String(8), nullable=False)
    qty: Mapped[int] = mapped_column(Integer, nullable=False)
    type: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    broker_order_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    client_order_id: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True
    )
    raw: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Fill(Base):
    __tablename__ = "fills"
    __table_args__ = (
        UniqueConstraint("execution_id", name="uq_fills_execution_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False
    )
    execution_id: Mapped[str | None] = mapped_column(
        String(128), nullable=True
    )
    qty: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[float] = mapped_column(Numeric(18, 6), nullable=False)
    commission: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False, default=0)
    realized_gross_pnl: Mapped[float | None] = mapped_column(
        Numeric(18, 2), nullable=True
    )
    realized_net_pnl: Mapped[float | None] = mapped_column(
        Numeric(18, 2), nullable=True
    )
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    raw: Mapped[dict] = mapped_column(JSONB, nullable=False)


class Position(Base):
    __tablename__ = "positions"
    __table_args__ = (
        UniqueConstraint(
            "sleeve", "instrument_id", name="uq_positions_sleeve_instrument"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    sleeve: Mapped[str] = mapped_column(String(64), nullable=False)
    instrument_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("instruments.id"), nullable=False
    )
    qty: Mapped[int] = mapped_column(Integer, nullable=False)
    avg_price: Mapped[float] = mapped_column(Numeric(18, 6), nullable=False)
    avg_cost: Mapped[float | None] = mapped_column(Numeric(18, 6), nullable=True)


class LedgerEntry(Base):
    __tablename__ = "ledger_entries"
    __table_args__ = (Index("ix_ledger_entries_ts", "ts"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    account_kind: Mapped[str] = mapped_column(String(32), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    reason: Mapped[str] = mapped_column(String(128), nullable=False)
    ref: Mapped[str | None] = mapped_column(String(64), nullable=True)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class SignalRow(Base):
    __tablename__ = "signals"
    __table_args__ = (Index("ix_signals_sleeve_ts", "sleeve", "ts"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    sleeve: Mapped[str] = mapped_column(String(64), nullable=False)
    ticker: Mapped[str] = mapped_column(String(32), nullable=False)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    kind: Mapped[str] = mapped_column(String(16), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class Flag(Base):
    __tablename__ = "flags"

    key: Mapped[str] = mapped_column(String(32), primary_key=True)
    value: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class Fundamental(Base):
    __tablename__ = "fundamentals"
    __table_args__ = (UniqueConstraint("ticker", name="uq_fundamentals_ticker"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    ticker: Mapped[str] = mapped_column(String(32), nullable=False)
    asset_uid: Mapped[str] = mapped_column(String(64), nullable=False)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    pe_ratio_ttm: Mapped[float | None] = mapped_column(Numeric(18, 6), nullable=True)
    price_to_book_ttm: Mapped[float | None] = mapped_column(
        Numeric(18, 6), nullable=True
    )
    eps_ttm: Mapped[float | None] = mapped_column(Numeric(18, 6), nullable=True)
    market_capitalization: Mapped[float | None] = mapped_column(
        Numeric(20, 4), nullable=True
    )
    raw: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class Report(Base):
    __tablename__ = "reports"
    __table_args__ = (
        UniqueConstraint("kind", "period_start", name="uq_reports_kind_period"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    period_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    period_end: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    equity_start: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    equity_end: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    pnl: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class AgentRun(Base):
    __tablename__ = "agent_runs"
    __table_args__ = (Index("ix_agent_runs_role_ts", "role", "ts"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    role: Mapped[str] = mapped_column(String(64), nullable=False)
    input: Mapped[str] = mapped_column(Text, nullable=False)
    output: Mapped[str] = mapped_column(Text, nullable=False)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class AgentProposal(Base):
    __tablename__ = "agent_proposals"
    __table_args__ = (Index("ix_agent_proposals_status", "status"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(16), nullable=False)


class NewsEvent(Base):
    __tablename__ = "news_events"
    __table_args__ = (
        UniqueConstraint("url", name="uq_news_events_url"),
        UniqueConstraint("source", "source_id", name="uq_news_events_source_id"),
        Index("ix_news_events_ts", "ts"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    source_id: Mapped[str] = mapped_column(String(256), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    url: Mapped[str] = mapped_column(String(1024), nullable=False)
    tickers: Mapped[list[str]] = mapped_column(
        ARRAY(String(32)), nullable=False, default=list
    )
    raw: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class NewsStudy(Base):
    __tablename__ = "news_studies"
    __table_args__ = (
        UniqueConstraint(
            "news_event_id",
            "ticker",
            "horizon_n",
            name="uq_news_studies_event_ticker_n",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    news_event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("news_events.id"), nullable=False
    )
    ticker: Mapped[str] = mapped_column(String(32), nullable=False)
    horizon_n: Mapped[int] = mapped_column(Integer, nullable=False)
    t_minus_ts: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    t_plus_ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ret: Mapped[float] = mapped_column(Numeric(18, 8), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class EarningsDay(Base):
    __tablename__ = "earnings_days"
    __table_args__ = (
        UniqueConstraint("ticker", "day", name="uq_earnings_days_ticker_day"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    ticker: Mapped[str] = mapped_column(String(32), nullable=False)
    day: Mapped[date] = mapped_column(Date, nullable=False)


class EquitySnapshot(Base):
    __tablename__ = "equity_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    trading_cash: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    vault: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    positions_value: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    equity: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
