import logging
import os
import time
from contextlib import asynccontextmanager
from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request

from app import __version__
from app.advisory.screener import propose_from_scores
from app.advisory.view import DISCLAIMER, fundamentals_view, recommendations_view
from app.agent.approve import apply_approved
from app.agent.flag import agents_enabled
from app.agent.proposals import new_proposal, reject_proposal
from app.agent.schemas import ProposeOrder, ProposeWeights
from app.agent.store import get_proposal, list_proposals, proposal_view, remember
from app.alloc.plan import allocation_plan
from app.alloc.view import ACTIVE_SLEEVES, allocation_view
from app.alloc.weights_store import save_weights
from app.book.accounts import TRADING_CASH
from app.book.drift import drift_view
from app.book.ledger import ensure_deposit, ledger_balance, ledger_view
from app.book.orders import (
    STATUS_REJECTED,
    order_item,
    orders_view,
    reconcile_order,
    submit_order,
)
from app.book.portfolio import portfolio_from_book
from app.book.valuation import PriceMark, value_portfolio
from app.book.vault import vault_view
from app.broker.fake import FakeBroker
from app.broker.port import OrderRequest
from app.broker.sandbox_payin import DEFAULT_DEPOSIT
from app.broker.tinkoff import BrokerTokenError
from app.db import get_db, get_sessionmaker, ping_session
from app.models import (
    BacktestExperiment,
    Candle,
    EarningsDay,
    EquitySnapshot,
    Fill,
    Flag,
    Fundamental,
    Instrument,
    LedgerEntry,
    NewsEvent,
    NewsStudy,
    Order,
    Position,
    SignalRow,
    UniverseMember,
)
from app.news.view import news_view, studies_view
from app.ops.guest_link import token_accepted
from app.ops.ratelimit import DEFAULT_CABIN_RATE_PER_MIN, IpRateLimit, client_ip
from app.ops.ready import read_beat, ready_view
from app.ops.telegram import alert_kill, send_telegram
from app.risk.calendar import calendar_map
from app.risk.context import RiskContext
from app.risk.kill import apply_kill, is_killed, kill_view
from app.risk.params_store import (
    MAX_NAME_SHARE,
    MIN_NAME_SHARE,
    load_risk_policy,
    load_risk_policy_history,
    save_risk_policy,
)
from app.risk.universe import active_tickers
from app.strategy.desk import desk_backtest
from app.strategy.experiments import (
    experiment_view,
    new_experiment,
    result_is_intact,
)
from app.strategy.view import sleeve_view, sleeves_view
from app.universe.cap import resolve_universe_max
from app.universe.view import universe_view

PUBLIC_PATHS = frozenset(
    {
        "/",
        "/index.html",
        "/cabin.css",
        "/cabin.js",
        "/tour.css",
        "/tour.js",
        "/health",
        "/ready",
    }
)
WEB_DIR = Path(__file__).resolve().parents[1] / "web"
WEB_INDEX = WEB_DIR / "index.html"
log = logging.getLogger("app")


def error_payload(code: str, message: str) -> dict[str, str]:
    return {"code": code, "message": message}


async def bootstrap_book() -> None:
    if not os.environ.get("DATABASE_URL"):
        return
    deposit = Decimal(os.environ.get("SANDBOX_DEPOSIT", str(DEFAULT_DEPOSIT)))
    try:
        maker = get_sessionmaker()
        async with maker() as session:
            balance = await ensure_deposit(session, deposit)
            await session.commit()
        log.info("book deposit ready balance=%s", balance)
    except Exception:
        log.exception("book deposit bootstrap skipped")


def create_app() -> FastAPI:
    prod = os.environ.get("APP_ENV", "dev") == "prod"

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        await bootstrap_book()
        yield

    app = FastAPI(
        title="i.datagon",
        version=__version__,
        docs_url=None if prod else "/docs",
        redoc_url=None if prod else "/redoc",
        openapi_url=None if prod else "/openapi.json",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["https://i.datagon.ru", "http://i.datagon.ru"],
        allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization", "Content-Type", "X-App-Token"],
    )
    limiter = IpRateLimit(
        int(os.environ.get("CABIN_RATE_PER_MIN", DEFAULT_CABIN_RATE_PER_MIN))
    )

    @app.middleware("http")
    async def require_app_token(request: Request, call_next):
        if request.method == "OPTIONS" or request.url.path in PUBLIC_PATHS:
            return await call_next(request)
        expected = os.environ.get("APP_AUTH_TOKEN", "")
        got = request.headers.get("X-App-Token", "")
        if not expected or not token_accepted(got, expected):
            return JSONResponse(
                status_code=401, content=error_payload("401", "unauthorized")
            )
        return await call_next(request)

    @app.middleware("http")
    async def cabin_rate_limit(request: Request, call_next):
        if request.method == "OPTIONS" or request.url.path in PUBLIC_PATHS:
            return await call_next(request)
        remote = request.client.host if request.client else None
        ip = client_ip(dict(request.headers), remote)
        if not limiter.allow(ip, time.time()):
            return JSONResponse(
                status_code=429, content=error_payload("429", "rate_limited")
            )
        return await call_next(request)

    @app.exception_handler(StarletteHTTPException)
    async def http_error(
        _request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        message = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
        return JSONResponse(
            status_code=exc.status_code,
            content=error_payload(str(exc.status_code), message),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=error_payload("422", str(exc.errors())),
        )

    @app.exception_handler(BrokerTokenError)
    async def broker_token_error(
        _request: Request, exc: BrokerTokenError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=503,
            content=error_payload("broker_token", str(exc)),
        )

    @app.get("/")
    def cabin() -> FileResponse:
        return FileResponse(WEB_INDEX, media_type="text/html")

    @app.get("/index.html")
    def cabin_index() -> FileResponse:
        return FileResponse(WEB_INDEX, media_type="text/html")

    @app.get("/cabin.css")
    def cabin_css() -> FileResponse:
        return FileResponse(WEB_DIR / "cabin.css", media_type="text/css")

    @app.get("/cabin.js")
    def cabin_js() -> FileResponse:
        return FileResponse(
            WEB_DIR / "cabin.js", media_type="application/javascript"
        )

    @app.get("/tour.css")
    def tour_css() -> FileResponse:
        return FileResponse(WEB_DIR / "tour.css", media_type="text/css")

    @app.get("/tour.js")
    def tour_js() -> FileResponse:
        return FileResponse(
            WEB_DIR / "tour.js", media_type="application/javascript"
        )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/version")
    def version() -> dict[str, str]:
        return {"version": __version__}

    @app.get("/ready")
    async def ready(session: AsyncSession = Depends(get_db)) -> dict:
        await ping_session(session)
        orders = await session.scalar(select(func.count()).select_from(Order))
        return ready_view(int(orders or 0), read_beat(), datetime.now(UTC))

    @app.get("/status")
    async def status(session: AsyncSession = Depends(get_db)) -> dict:
        await ping_session(session)
        now = datetime.now(UTC)
        orders = await session.scalar(select(func.count()).select_from(Order))
        entries = list(await session.scalars(select(LedgerEntry)))
        positions = list(await session.scalars(select(Position)))
        flags = list(await session.scalars(select(Flag)))
        members = list(
            await session.scalars(
                select(UniverseMember).where(UniverseMember.active.is_(True))
            )
        )
        book = portfolio_from_book(entries, positions)
        ready = ready_view(int(orders or 0), read_beat(), now)
        agents_on = os.environ.get("AGENTS_ENABLED", "0").lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
        return {
            **ready,
            "killed": is_killed(flags),
            "agents_enabled": agents_on or agents_enabled(),
            "universe_size": len(members),
            "portfolio": book,
            "vault": vault_view(entries),
            "version": __version__,
            "env": os.environ.get("APP_ENV", "dev"),
        }

    @app.get("/kill")
    async def kill_status(session: AsyncSession = Depends(get_db)) -> dict:
        flags = list(await session.scalars(select(Flag)))
        return kill_view(flags)

    @app.get("/portfolio")
    async def portfolio(session: AsyncSession = Depends(get_db)) -> dict:
        entries = list(await session.scalars(select(LedgerEntry)))
        positions = list(await session.scalars(select(Position)))
        return portfolio_from_book(entries, positions)

    @app.get("/capital/summary")
    async def capital_summary(session: AsyncSession = Depends(get_db)) -> dict:
        entries = list(await session.scalars(select(LedgerEntry)))
        positions = list(await session.scalars(select(Position)))
        fills = list(await session.scalars(select(Fill)))
        snapshots = list(await session.scalars(select(EquitySnapshot)))
        instrument_ids = {row.instrument_id for row in positions}
        candles = (
            list(
                await session.scalars(
                    select(Candle).where(Candle.instrument_id.in_(instrument_ids))
                )
            )
            if instrument_ids
            else []
        )
        latest: dict[UUID, Candle] = {}
        for candle in candles:
            previous = latest.get(candle.instrument_id)
            if previous is None or candle.ts > previous.ts:
                latest[candle.instrument_id] = candle
        marks = {
            instrument_id: PriceMark(
                instrument_id=instrument_id,
                price=Decimal(str(candle.c)),
                as_of=candle.ts,
                source=f"candle:{candle.tf}",
            )
            for instrument_id, candle in latest.items()
        }
        stale_hours = int(os.environ.get("VALUATION_STALE_HOURS", "36"))
        return value_portfolio(
            entries,
            positions,
            marks,
            fills=fills,
            snapshots=snapshots,
            stale_after=timedelta(hours=stale_hours),
        )

    @app.get("/orders")
    async def orders(
        status: str | None = None,
        session: AsyncSession = Depends(get_db),
    ) -> dict:
        stmt = select(Order)
        if status:
            stmt = stmt.where(Order.status == status)
        rows = list(await session.scalars(stmt))
        return orders_view(rows, status=status)

    class ReconcileOrderBody(BaseModel):
        broker_status: str = Field(..., min_length=1)
        filled_qty: int = Field(..., ge=0)
        reconciliation_id: str = Field(..., min_length=1)
        source: str = Field(default="broker", min_length=1)

    @app.post("/orders/{order_id}/reconcile")
    async def reconcile_order_route(
        order_id: UUID,
        body: ReconcileOrderBody,
        session: AsyncSession = Depends(get_db),
    ) -> dict:
        row = await session.get(Order, order_id)
        if row is None:
            raise HTTPException(status_code=404, detail="not found")
        try:
            row, changed = reconcile_order(
                row,
                broker_status=body.broker_status,
                filled_qty=body.filled_qty,
                reconciliation_id=body.reconciliation_id,
                source=body.source,
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        if changed:
            await session.commit()
        return {**order_item(row), "reconciled": changed}

    @app.get("/ledger")
    async def ledger(session: AsyncSession = Depends(get_db)) -> dict:
        stmt = select(LedgerEntry).order_by(LedgerEntry.ts.desc())
        rows = list(await session.scalars(stmt))
        return ledger_view(rows)

    class DepositBody(BaseModel):
        amount: float = Field(..., gt=0)

    @app.post("/ledger/deposit")
    async def ledger_deposit(
        body: DepositBody,
        session: AsyncSession = Depends(get_db),
    ) -> dict:
        """Дотягивает trading_cash до целевой суммы (не уменьшает)."""
        target = Decimal(str(body.amount)).quantize(Decimal("0.01"))
        before = ledger_balance(
            list(
                await session.scalars(
                    select(LedgerEntry).where(LedgerEntry.account_kind == TRADING_CASH)
                )
            ),
            TRADING_CASH,
        )
        await ensure_deposit(session, target)
        await session.commit()
        positions = list(await session.scalars(select(Position)))
        entries = list(await session.scalars(select(LedgerEntry)))
        book = portfolio_from_book(entries, positions)
        return {
            "target": float(target),
            "before": float(Decimal(before).quantize(Decimal("0.01"))),
            "cash": float(Decimal(str(book["cash"])).quantize(Decimal("0.01"))),
            "equity": float(Decimal(str(book["equity"])).quantize(Decimal("0.01"))),
            "topped_up": float(
                (Decimal(str(book["cash"])) - Decimal(before)).quantize(Decimal("0.01"))
            ),
        }

    @app.get("/admin/drift")
    async def admin_drift(
        sandbox_cash: Decimal = Decimal("0"),
        session: AsyncSession = Depends(get_db),
    ) -> dict:
        entries = list(await session.scalars(select(LedgerEntry)))
        return drift_view(ledger_balance(entries), sandbox_cash)

    @app.get("/vault")
    async def vault(session: AsyncSession = Depends(get_db)) -> dict:
        rows = list(await session.scalars(select(LedgerEntry)))
        return vault_view(rows)

    @app.get("/universe")
    async def universe(session: AsyncSession = Depends(get_db)) -> dict:
        members = list(await session.scalars(select(UniverseMember)))
        instruments = list(await session.scalars(select(Instrument)))
        limit = resolve_universe_max(
            int(os.environ["UNIVERSE_MAX"])
            if os.environ.get("UNIVERSE_MAX")
            else None
        )
        return universe_view(members, instruments, limit=limit)

    class DeskBacktestBody(BaseModel):
        sleeve: str = Field(..., min_length=1)
        ticker: str = Field(default="SBER", min_length=1)

    async def _book_equity(session: AsyncSession) -> Decimal:
        entries = list(await session.scalars(select(LedgerEntry)))
        positions = list(await session.scalars(select(Position)))
        book = portfolio_from_book(entries, positions)
        equity = Decimal(str(book["equity"]))
        if equity <= 0:
            return Decimal(str(DEFAULT_DEPOSIT))
        return equity

    @app.get("/allocation")
    async def allocation(session: AsyncSession = Depends(get_db)) -> dict:
        equity = await _book_equity(session)
        return allocation_view(ACTIVE_SLEEVES, equity=equity)

    @app.get("/allocation/plan")
    async def allocation_plan_endpoint(
        session: AsyncSession = Depends(get_db),
        example_price: float = 250,
        lot: int = 1,
    ) -> dict:
        if example_price <= 0:
            raise HTTPException(status_code=422, detail="example_price must be > 0")
        if lot < 1:
            raise HTTPException(status_code=422, detail="lot must be >= 1")
        equity = await _book_equity(session)
        members = list(await session.scalars(select(UniverseMember)))
        instruments = list(await session.scalars(select(Instrument)))
        limit = resolve_universe_max(
            int(os.environ["UNIVERSE_MAX"])
            if os.environ.get("UNIVERSE_MAX")
            else None
        )
        uni = universe_view(members, instruments, limit=limit)
        tickers = [
            row["ticker"]
            for row in uni.get("members") or []
            if row.get("active") and row.get("ticker")
        ]
        plan = allocation_plan(
            equity=equity,
            example_price=Decimal(str(example_price)),
            lot=lot,
        )
        plan["universe_size"] = int(uni.get("count") or len(tickers))
        plan["universe_tickers"] = tickers[:40]
        return plan

    @app.put("/allocation/weights")
    async def put_allocation_weights(
        body: ProposeWeights,
        session: AsyncSession = Depends(get_db),
    ) -> dict:
        unknown = [
            row.sleeve
            for row in body.weights
            if row.sleeve not in ACTIVE_SLEEVES
        ]
        if unknown:
            raise HTTPException(
                status_code=422,
                detail="unknown sleeve: " + ", ".join(unknown),
            )
        missing = [
            name
            for name in ACTIVE_SLEEVES
            if name not in {r.sleeve for r in body.weights}
        ]
        if missing:
            raise HTTPException(
                status_code=422,
                detail="missing sleeve: " + ", ".join(missing),
            )
        weights = {row.sleeve: Decimal(str(row.weight)) for row in body.weights}
        save_weights(weights)
        equity = await _book_equity(session)
        return allocation_view(ACTIVE_SLEEVES, equity=equity, weights=weights)

    class RiskParamsBody(BaseModel):
        name_share: float | None = Field(default=None, gt=0, le=0.5)
        trade_risk_share: float | None = Field(default=None, gt=0, le=1)
        gross_limit: float | None = Field(default=None, gt=0, le=1)
        max_drawdown: float | None = Field(default=None, gt=0, le=1)
        daily_loss: float | None = Field(default=None, gt=0, le=1)
        expected_version: int | None = Field(default=None, ge=1)

    @app.get("/allocation/risk")
    def get_allocation_risk() -> dict:
        policy = load_risk_policy()
        share = policy.name_share
        return {
            **policy.snapshot(),
            "history": load_risk_policy_history(),
            "min_name_share": float(MIN_NAME_SHARE),
            "max_name_share": float(MAX_NAME_SHARE),
            "max_concurrent_names": int(Decimal("1") // share) if share > 0 else 0,
        }

    @app.put("/allocation/risk")
    def put_allocation_risk(body: RiskParamsBody) -> dict:
        current = load_risk_policy()
        share = (
            Decimal(str(body.name_share))
            if body.name_share is not None
            else current.name_share
        )
        if share < MIN_NAME_SHARE or share > MAX_NAME_SHARE:
            raise HTTPException(
                status_code=422,
                detail=(
                    f"name_share must be between {MIN_NAME_SHARE} and {MAX_NAME_SHARE}"
                ),
            )
        candidate = replace(
            current,
            name_share=share,
            trade_risk_share=(
                Decimal(str(body.trade_risk_share))
                if body.trade_risk_share is not None
                else current.trade_risk_share
            ),
            gross_limit=(
                Decimal(str(body.gross_limit))
                if body.gross_limit is not None
                else current.gross_limit
            ),
            max_drawdown=(
                Decimal(str(body.max_drawdown))
                if body.max_drawdown is not None
                else current.max_drawdown
            ),
            daily_loss=(
                Decimal(str(body.daily_loss))
                if body.daily_loss is not None
                else current.daily_loss
            ),
        )
        try:
            save_risk_policy(
                candidate,
                expected_version=body.expected_version,
            )
        except ValueError as exc:
            status = 409 if str(exc) == "risk_policy_version_conflict" else 422
            raise HTTPException(status_code=status, detail=str(exc)) from exc
        return get_allocation_risk()

    def _run_desk_backtest(body: DeskBacktestBody) -> dict:
        try:
            return desk_backtest(sleeve=body.sleeve, ticker=body.ticker)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except FileNotFoundError as exc:
            raise HTTPException(
                status_code=404,
                detail=(
                    f"Нет файла свечей для {body.ticker.upper()}. "
                    "Положите CSV в CANDLE_DIR (например data/candles/SBER.csv)."
                ),
            ) from exc

    @app.post("/desk/backtest")
    def run_desk_backtest(body: DeskBacktestBody) -> dict:
        return _run_desk_backtest(body)

    @app.post("/backtests")
    async def create_backtest(
        body: DeskBacktestBody,
        session: AsyncSession = Depends(get_db),
    ) -> dict:
        candidate = new_experiment(_run_desk_backtest(body))
        existing = await session.scalar(
            select(BacktestExperiment).where(
                BacktestExperiment.data_hash == candidate.data_hash,
                BacktestExperiment.config_hash == candidate.config_hash,
                BacktestExperiment.code_hash == candidate.code_hash,
            )
        )
        if existing is not None:
            return {**experiment_view(existing), "deduplicated": True}
        session.add(candidate)
        await session.commit()
        await session.refresh(candidate)
        return {**experiment_view(candidate), "deduplicated": False}

    @app.get("/backtests/{experiment_id}")
    async def get_backtest(
        experiment_id: UUID,
        session: AsyncSession = Depends(get_db),
    ) -> dict:
        row = await session.get(BacktestExperiment, experiment_id)
        if row is None:
            raise HTTPException(status_code=404, detail="not found")
        if not result_is_intact(row):
            raise HTTPException(status_code=409, detail="result hash mismatch")
        return experiment_view(row)

    @app.get("/backtests/{experiment_id}/trades")
    async def get_backtest_trades(
        experiment_id: UUID,
        session: AsyncSession = Depends(get_db),
    ) -> dict:
        row = await session.get(BacktestExperiment, experiment_id)
        if row is None:
            raise HTTPException(status_code=404, detail="not found")
        if not result_is_intact(row):
            raise HTTPException(status_code=409, detail="result hash mismatch")
        return {
            "id": str(row.id),
            "trades": (row.result.get("backtest") or {}).get("trades", []),
        }

    @app.get("/fundamentals")
    async def fundamentals(session: AsyncSession = Depends(get_db)) -> dict:
        rows = list(await session.scalars(select(Fundamental)))
        return fundamentals_view(rows)

    @app.get("/recommendations")
    async def recommendations(
        limit: int = 10,
        min_score: float = 40.0,
        session: AsyncSession = Depends(get_db),
    ) -> dict:
        rows = list(await session.scalars(select(Fundamental)))
        return recommendations_view(rows, limit=limit, min_score=min_score)

    class ProposeRecsBody(BaseModel):
        limit: int = Field(default=5, ge=1, le=20)
        min_score: float = Field(default=40.0, ge=0, le=100)
        qty: int = Field(default=1, ge=1)
        stop: float = Field(default=250.0, gt=0)

    @app.post("/recommendations/propose")
    async def recommendations_propose(
        body: ProposeRecsBody,
        session: AsyncSession = Depends(get_db),
    ) -> dict:
        rows = list(await session.scalars(select(Fundamental)))
        created = propose_from_scores(
            rows,
            limit=body.limit,
            min_score=body.min_score,
            qty=body.qty,
            stop=body.stop,
        )
        return {
            "proposals": [proposal_view(row) for row in created],
            "count": len(created),
            "disclaimer": DISCLAIMER,
        }

    @app.post("/fundamentals/refresh")
    async def fundamentals_refresh() -> dict:
        from worker.fundamentals import run_fundamentals_refresh

        try:
            saved = await run_fundamentals_refresh()
        except BrokerTokenError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(
                status_code=503,
                detail=f"Не удалось обновить фундамент: {exc}",
            ) from exc
        return {"upserted": saved, "disclaimer": DISCLAIMER}

    @app.post("/fundamentals/demo")
    async def fundamentals_demo(session: AsyncSession = Depends(get_db)) -> dict:
        """Локальные демо-снимки без брокера — чтобы кабинет не был пустым."""
        samples = [
            Fundamental(
                ticker="SBER",
                asset_uid="demo-sber",
                ts=datetime.now(UTC),
                pe_ratio_ttm=5.5,
                price_to_book_ttm=0.8,
                eps_ttm=45.0,
                market_capitalization=6_000_000_000_000.0,
                raw={
                    "roe": 0.22,
                    "free_float": 0.48,
                    "dividend_yield_daily_ttm": 0.09,
                },
            ),
            Fundamental(
                ticker="LKOH",
                asset_uid="demo-lkoh",
                ts=datetime.now(UTC),
                pe_ratio_ttm=4.2,
                price_to_book_ttm=0.7,
                eps_ttm=120.0,
                market_capitalization=4_000_000_000_000.0,
                raw={
                    "roe": 0.18,
                    "free_float": 0.40,
                    "dividend_yield_daily_ttm": 0.11,
                },
            ),
            Fundamental(
                ticker="GAZP",
                asset_uid="demo-gazp",
                ts=datetime.now(UTC),
                pe_ratio_ttm=28.0,
                price_to_book_ttm=0.4,
                eps_ttm=8.0,
                market_capitalization=3_000_000_000_000.0,
                raw={
                    "roe": 0.06,
                    "free_float": 0.50,
                    "dividend_yield_daily_ttm": 0.03,
                },
            ),
        ]
        existing = {
            row.ticker: row for row in await session.scalars(select(Fundamental))
        }
        for snap in samples:
            found = existing.get(snap.ticker)
            if found is None:
                session.add(snap)
            else:
                found.ts = snap.ts
                found.pe_ratio_ttm = snap.pe_ratio_ttm
                found.price_to_book_ttm = snap.price_to_book_ttm
                found.eps_ttm = snap.eps_ttm
                found.market_capitalization = snap.market_capitalization
                found.raw = snap.raw
                found.asset_uid = snap.asset_uid
        await session.commit()
        rows = list(await session.scalars(select(Fundamental)))
        return fundamentals_view(rows)

    @app.get("/news")
    async def news(session: AsyncSession = Depends(get_db)) -> dict:
        rows = list(await session.scalars(select(NewsEvent)))
        return news_view(rows)

    @app.get("/news/studies")
    async def news_studies(session: AsyncSession = Depends(get_db)) -> dict:
        studies = list(await session.scalars(select(NewsStudy)))
        events = list(await session.scalars(select(NewsEvent)))
        return studies_view(studies, events)

    @app.get("/sleeves")
    async def sleeves(session: AsyncSession = Depends(get_db)) -> dict:
        signals = list(await session.scalars(select(SignalRow)))
        positions = list(await session.scalars(select(Position)))
        return sleeves_view(signals, positions)

    @app.get("/sleeves/{name}")
    async def sleeves_one(name: str) -> dict:
        if name not in ACTIVE_SLEEVES:
            raise HTTPException(status_code=404, detail="unknown sleeve")
        maker = get_sessionmaker()
        async with maker() as session:
            signals = list(
                await session.scalars(
                    select(SignalRow).where(SignalRow.sleeve == name)
                )
            )
            positions = list(
                await session.scalars(
                    select(Position).where(Position.sleeve == name)
                )
            )
            instruments = list(await session.scalars(select(Instrument)))
            tickers = {row.id: row.ticker for row in instruments}
            return sleeve_view(
                signals,
                positions,
                sleeve=name,
                tickers=tickers,
            )

    async def _set_kill(session: AsyncSession, killed: bool) -> dict:
        flags = list(await session.scalars(select(Flag)))
        row = apply_kill(flags, killed)
        if row not in session:
            session.add(row)
        await session.commit()
        alert_kill(killed, send=send_telegram)
        return kill_view(flags)

    @app.get("/proposals")
    def proposals() -> dict:
        return {"proposals": [proposal_view(row) for row in list_proposals()]}

    @app.post("/proposals/order")
    def propose_order(body: ProposeOrder) -> dict:
        row = remember(new_proposal("order", body.model_dump()))
        return proposal_view(row)

    @app.post("/proposals/weights")
    def propose_weights(body: ProposeWeights) -> dict:
        row = remember(new_proposal("weights", body.model_dump()))
        return proposal_view(row)

    @app.post("/proposals/{proposal_id}/approve")
    async def approve_proposal(
        proposal_id: UUID,
        session: AsyncSession = Depends(get_db),
    ) -> dict:
        row = get_proposal(proposal_id)
        if row is None:
            raise HTTPException(status_code=404, detail="not found")
        members = list(
            await session.scalars(
                select(UniverseMember).where(UniverseMember.active.is_(True))
            )
        )
        instruments = list(await session.scalars(select(Instrument)))
        flags = list(await session.scalars(select(Flag)))
        earnings = list(await session.scalars(select(EarningsDay)))
        entries = list(await session.scalars(select(LedgerEntry)))
        positions = list(await session.scalars(select(Position)))
        orders = list(await session.scalars(select(Order)))
        fills = list(await session.scalars(select(Fill)))
        candles = list(await session.scalars(select(Candle)))
        snapshots = list(await session.scalars(select(EquitySnapshot)))
        now = datetime.now(UTC)
        latest: dict[UUID, Candle] = {}
        for candle in candles:
            previous = latest.get(candle.instrument_id)
            if previous is None or candle.ts > previous.ts:
                latest[candle.instrument_id] = candle
        marks = {
            instrument_id: PriceMark(
                instrument_id=instrument_id,
                price=Decimal(str(candle.c)),
                as_of=candle.ts,
                source=f"candle:{candle.tf}",
            )
            for instrument_id, candle in latest.items()
        }
        valuation = value_portfolio(
            entries,
            positions,
            marks,
            snapshots=snapshots,
            now=now,
            stale_after=timedelta(
                hours=int(os.environ.get("VALUATION_STALE_HOURS", "36"))
            ),
        )
        payload = row.payload or {}
        ticker = str(payload.get("ticker") or "").upper()
        sleeve = str(payload.get("sleeve") or "")
        instrument_by_ticker = {item.ticker: item for item in instruments}
        instrument = instrument_by_ticker.get(ticker)
        mark = marks.get(instrument.id) if instrument is not None else None
        today_snapshots = sorted(
            (
                snapshot
                for snapshot in snapshots
                if snapshot.ts.astimezone(UTC).date() == now.date()
            ),
            key=lambda snapshot: snapshot.ts,
        )
        risk_context = None
        if (
            mark is not None
            and valuation["status"] == "complete"
            and valuation["equity"] is not None
            and today_snapshots
        ):
            active_statuses = {
                "new",
                "submitted",
                "acknowledged",
                "partially_filled",
                "cancel_pending",
                "unknown",
            }
            filled_by_order: dict[UUID, int] = {}
            for fill in fills:
                filled_by_order[fill.order_id] = (
                    filled_by_order.get(fill.order_id, 0) + fill.qty
                )

            def remaining(order: Order) -> Decimal:
                return Decimal(max(order.qty - filled_by_order.get(order.id, 0), 0))

            name_existing = sum(
                (
                    Decimal(str(position.qty)) * mark.price
                    for position in positions
                    if position.instrument_id == instrument.id
                ),
                Decimal("0"),
            )
            name_existing += sum(
                (
                    remaining(order) * mark.price
                    for order in orders
                    if order.ticker == ticker
                    and order.side == "buy"
                    and order.status in active_statuses
                ),
                Decimal("0"),
            )
            sleeve_existing = sum(
                (
                    Decimal(str(position.qty))
                    * marks[position.instrument_id].price
                    for position in positions
                    if position.sleeve == sleeve
                    and position.instrument_id in marks
                ),
                Decimal("0"),
            )
            sleeve_existing += sum(
                (
                    remaining(order)
                    * marks[instrument_by_ticker[order.ticker].id].price
                    for order in orders
                    if order.sleeve == sleeve
                    and order.side == "buy"
                    and order.status in active_statuses
                    and order.ticker in instrument_by_ticker
                    and instrument_by_ticker[order.ticker].id in marks
                ),
                Decimal("0"),
            )
            gross_existing = sum(
                (
                    abs(Decimal(str(position.qty)))
                    * marks[position.instrument_id].price
                    for position in positions
                    if position.instrument_id in marks
                ),
                Decimal("0"),
            )
            gross_existing += sum(
                (
                    remaining(order)
                    * marks[instrument_by_ticker[order.ticker].id].price
                    for order in orders
                    if order.status in active_statuses
                    and order.ticker in instrument_by_ticker
                    and instrument_by_ticker[order.ticker].id in marks
                ),
                Decimal("0"),
            )
            risk_context = RiskContext(
                price=mark.price,
                price_as_of=mark.as_of,
                equity=Decimal(str(valuation["equity"])),
                start_equity=Decimal(str(today_snapshots[0].equity)),
                stop_price=Decimal(str(payload.get("stop") or 0)),
                name_existing=name_existing,
                sleeve_existing=sleeve_existing,
                gross_existing=gross_existing,
                max_drawdown=Decimal(
                    str(valuation["max_drawdown"] or 0)
                ),
                broker_healthy=not any(
                    order.status == "unknown" for order in orders
                ),
                observed_at=now,
                max_price_age=timedelta(
                    hours=int(os.environ.get("VALUATION_STALE_HOURS", "36"))
                ),
            )
        row, order, weights = apply_approved(
            row,
            tickers=active_tickers(members, instruments),
            port=None,
            flags=flags,
            calendar=calendar_map(earnings),
            day=date.today(),
            context=risk_context,
            defer_submit=True,
        )
        if order is not None:
            session.add(order)
            await session.commit()
            if order.status != STATUS_REJECTED:
                request = OrderRequest(
                    ticker=order.ticker,
                    side=order.side,
                    qty=order.qty,
                    type=order.type,
                    client_order_id=order.client_order_id,
                )
                submit_order(order, FakeBroker(), request)
                raw = dict(order.raw or {})
                checks = list(raw.get("risk_checks") or [])
                checks.append(
                    {
                        "code": "broker_submit",
                        "outcome": (
                            "deny"
                            if order.status == STATUS_REJECTED
                            else "allow"
                        ),
                        "reason": raw.get("reject_reason")
                        or raw.get("broker_error"),
                        "explanation": raw.get("reject_reason")
                        or raw.get("broker_error")
                        or "broker_acknowledged",
                        "inputs": {
                            "client_order_id": order.client_order_id,
                        },
                    }
                )
                raw["risk_checks"] = checks
                order.raw = raw
                await session.commit()
        # веса уже сохранены в apply_approved → save_weights
        return proposal_view(
            row,
            order=order_item(order) if order is not None else None,
            weights=(
                {name: float(value) for name, value in weights.items()}
                if weights is not None
                else None
            ),
        )

    @app.post("/proposals/{proposal_id}/reject")
    def reject_proposal_route(proposal_id: UUID) -> dict:
        row = get_proposal(proposal_id)
        if row is None:
            raise HTTPException(status_code=404, detail="not found")
        return proposal_view(remember(reject_proposal(row)))

    @app.post("/kill")
    async def kill(session: AsyncSession = Depends(get_db)) -> dict:
        return await _set_kill(session, True)

    @app.post("/unkill")
    async def unkill(session: AsyncSession = Depends(get_db)) -> dict:
        return await _set_kill(session, False)

    return app
