import os

os.environ.setdefault("GRPC_DNS_RESOLVER", "native")

import asyncio
import logging
from datetime import UTC, date, datetime
from pathlib import Path

from app.logging import setup_logging
from app.ops.envfile import load_env_file
from app.ops.ready import write_beat
from app.ops.refresh_candles import csv_tickers, refresh as refresh_candles
from app.ops.safety import assert_paper_mode
from app.strategy.config import daily_strategies, scalp_strategies

from worker.bars import (
    close_all_books,
    close_m15_books,
    daily_close_due,
    last_closed_day,
    last_closed_m15,
    load_daily_books,
    load_m15_books,
    m15_close_due,
)
from worker.equity import (
    SNAPSHOT_INTERVAL_SEC,
    persist_valuation_snapshot,
    snapshot_due,
)
from worker.paper_forward import refresh_paper_forward
from worker.persist import persist_signals_async


async def run_worker() -> None:
    load_env_file(Path(".env"))
    assert_paper_mode()
    setup_logging()
    log = logging.getLogger("worker")
    log.info("worker start")
    # Компании / фундамент: по умолчанию раз в час.
    fund_interval = int(os.environ.get("FUNDAMENTALS_INTERVAL_SEC", "3600"))
    from app.ops.candle_refresh import interval_sec as candle_interval_sec

    candle_interval = candle_interval_sec()
    tape_interval = int(os.environ.get("WORK_TAPE_INTERVAL_SEC", "60"))
    paper_tickers = [
        ticker.strip().upper()
        for ticker in os.environ.get("PAPER_FORWARD_TICKERS", "SBER").split(",")
        if ticker.strip()
    ]
    last_snapshot: datetime | None = None
    last_bar_day: date | None = None
    last_m15_bar: datetime | None = None
    last_fundamentals: datetime | None = None
    last_tape: datetime | None = None
    last_candle_refresh: datetime | None = None
    day_sleeves = daily_strategies(os.environ)
    scalp_sleeves = scalp_strategies(os.environ)
    while True:
        now = datetime.now(UTC)
        write_beat(now)
        tape_due = last_tape is None or (now - last_tape).total_seconds() >= tape_interval
        if tape_due:
            try:
                from app.work.service import refresh_tape

                written = await asyncio.to_thread(refresh_tape)
                log.info("work tape tickers_written=%s", written)
            except Exception:
                log.exception("work tape failed")
            finally:
                last_tape = now
        candle_due = (
            candle_interval > 0
            and (
                last_candle_refresh is None
                or (now - last_candle_refresh).total_seconds() >= candle_interval
            )
        )
        if candle_due:
            from app.ops.candle_coverage import candle_root

            daily_root = candle_root("1d")
            m15_root = candle_root("15m")
            m10_root = candle_root("10m")
            tickers = csv_tickers(daily_root)
            for ticker in paper_tickers:
                if ticker not in tickers:
                    tickers.append(ticker)
            for root in (m15_root, m10_root):
                for ticker in csv_tickers(root):
                    if ticker not in tickers:
                        tickers.append(ticker)
            ok_1d = skip_1d = ok_15 = skip_15 = ok_10 = skip_10 = 0
            for ticker in tickers:
                try:
                    await asyncio.to_thread(
                        refresh_candles,
                        [ticker],
                        days=730,
                        tf="1d",
                        root=daily_root,
                    )
                    ok_1d += 1
                except Exception:
                    skip_1d += 1
                    log.exception("daily candle refresh failed ticker=%s", ticker)
                try:
                    await asyncio.to_thread(
                        refresh_candles,
                        [ticker],
                        days=180,
                        tf="15m",
                        root=m15_root,
                    )
                    ok_15 += 1
                except Exception:
                    skip_15 += 1
                    log.exception("m15 candle refresh failed ticker=%s", ticker)
                try:
                    await asyncio.to_thread(
                        refresh_candles,
                        [ticker],
                        days=180,
                        tf="10m",
                        root=m10_root,
                    )
                    ok_10 += 1
                except Exception:
                    skip_10 += 1
                    log.exception("m10 candle refresh failed ticker=%s", ticker)
            log.info(
                "candle refresh tickers=%s 1d ok=%s skip=%s 15m ok=%s skip=%s 10m ok=%s skip=%s",
                len(tickers),
                ok_1d,
                skip_1d,
                ok_15,
                skip_15,
                ok_10,
                skip_10,
            )
            last_candle_refresh = now
            try:
                from app.ops.candle_refresh import write_stamp

                write_stamp(now)
            except Exception:
                log.exception("candle refresh stamp failed")
        books = load_daily_books(os.environ.get("CANDLE_DIR"))
        m15_books = load_m15_books(os.environ.get("CANDLE_M15_DIR", "data/candles_m15"))
        if snapshot_due(last_snapshot, now, SNAPSHOT_INTERVAL_SEC):
            try:
                row = await persist_valuation_snapshot(ts=now)
                last_snapshot = now
                if row is None:
                    log.warning("equity snapshot skipped: incomplete valuation")
                else:
                    log.info(
                        "equity snapshot equity=%s ts=%s",
                        row.equity,
                        row.ts.isoformat(),
                    )
            except Exception:
                last_snapshot = now
                log.exception("equity snapshot persist failed")
        if daily_close_due(last_bar_day, now):
            rows = close_all_books(
                day_sleeves, books, last_processed=last_bar_day, now=now
            )
            saved = await persist_signals_async(rows)
            try:
                from app.work.service import place_signals

                placed = await asyncio.to_thread(place_signals, rows)
                log.info("work sandbox orders=%s", placed)
            except Exception:
                log.exception("work sandbox orders failed")
            last_bar_day = last_closed_day(now)
            log.info(
                "daily close day=%s signals=%s saved=%s books=%s sleeves=%s",
                last_bar_day,
                len(rows),
                saved,
                len(books),
                [s.sleeve for s in day_sleeves],
            )
        if m15_books and m15_close_due(last_m15_bar, now):
            rows = close_m15_books(
                scalp_sleeves, m15_books, last_processed=last_m15_bar, now=now
            )
            saved = await persist_signals_async(rows)
            last_m15_bar = last_closed_m15(now)
            log.info(
                "m15 close bar=%s signals=%s saved=%s books=%s sleeves=%s",
                last_m15_bar.isoformat(),
                len(rows),
                saved,
                len(m15_books),
                [s.sleeve for s in scalp_sleeves],
            )
        fund_due = last_fundamentals is None or (
            (now - last_fundamentals).total_seconds() >= fund_interval
        )
        if fund_due and os.environ.get("TINKOFF_SANDBOX_TOKEN"):
            try:
                from worker.fundamentals import run_fundamentals_refresh

                saved = await run_fundamentals_refresh()
                last_fundamentals = now
                log.info("fundamentals refresh upserted=%s", saved)
                try:
                    from app.ops.fundamentals_refresh import write_stamp

                    write_stamp(now)
                except Exception:
                    log.exception("fundamentals refresh stamp failed")
            except Exception:
                last_fundamentals = now
                log.exception("fundamentals refresh skipped")
        try:
            forward_saved = await refresh_paper_forward(now=now)
            if forward_saved:
                log.info("paper-forward observations saved=%s", forward_saved)
        except Exception:
            log.exception("paper-forward refresh failed")
        await asyncio.sleep(min(tape_interval, 60))


if __name__ == "__main__":
    asyncio.run(run_worker())
