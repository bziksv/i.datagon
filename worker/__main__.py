import os

os.environ.setdefault("GRPC_DNS_RESOLVER", "native")

import asyncio
import logging
from datetime import UTC, date, datetime
from pathlib import Path

from app.logging import setup_logging
from app.ops.envfile import load_env_file
from app.ops.ready import write_beat
from app.ops.refresh_candles import csv_tickers, refresh_tails
from app.ops.safety import assert_paper_mode
from app.strategy.config import daily_strategies, scalp_strategies

from worker.bars import (
    books_for_day,
    close_all_books,
    close_m15_books,
    close_moment,
    daily_close_due,
    last_closed_day,
    last_closed_m15,
    load_daily_books,
    load_m15_books,
    m15_close_due,
    read_close_day,
    write_close_day,
)
from worker.equity import (
    SNAPSHOT_INTERVAL_SEC,
    persist_valuation_snapshot,
    snapshot_due,
)
from worker.paper_forward import refresh_paper_forward
from worker.persist import persist_signals_async


def candle_tickers(paper_tickers: list[str]) -> list[str]:
    from app.ops.candle_coverage import candle_root

    tickers = csv_tickers(candle_root("1d"))
    for ticker in paper_tickers:
        if ticker not in tickers:
            tickers.append(ticker)
    for tf in ("15m", "10m"):
        for ticker in csv_tickers(candle_root(tf)):
            if ticker not in tickers:
                tickers.append(ticker)
    return tickers


async def run_worker() -> None:
    load_env_file(Path(".env"))
    assert_paper_mode()
    setup_logging()
    log = logging.getLogger("worker")
    from app.ops.prod_sync import enabled as mirror_enabled

    if mirror_enabled():
        # Зеркало прода: свечи и заявки делает воркер на сервере, второй торговал бы тем же счётом.
        log.warning("worker not started: PROD_SYNC is set, this machine mirrors prod")
        return
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
    last_bar_day: date | None = read_close_day()
    log.info("daily close last day=%s", last_bar_day)
    last_m15_bar: datetime | None = None
    last_fundamentals: datetime | None = None
    last_tape: datetime | None = None
    last_candle_refresh: datetime | None = None
    last_daily_pull: datetime | None = None
    empty_alert_day: date | None = None
    candle_workers = int(os.environ.get("CANDLE_REFRESH_THREADS", "4"))
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

            started = datetime.now(UTC)
            tickers = candle_tickers(paper_tickers)
            counts = {}
            for tf, depth in (("1d", 730), ("15m", 180), ("10m", 180)):
                counts[tf] = await asyncio.to_thread(
                    refresh_tails,
                    tickers,
                    tf=tf,
                    root=candle_root(tf),
                    depth_days=depth,
                    workers=candle_workers,
                )
            last_daily_pull = started
            log.info(
                "candle refresh tickers=%s 1d=%s 15m=%s 10m=%s sec=%s",
                len(tickers),
                counts["1d"],
                counts["15m"],
                counts["10m"],
                int((datetime.now(UTC) - started).total_seconds()),
            )
            last_candle_refresh = now
            try:
                from app.ops.candle_refresh import write_stamp

                write_stamp(now)
            except Exception:
                log.exception("candle refresh stamp failed")
        close_now = daily_close_due(last_bar_day, now)
        if close_now and (
            last_daily_pull is None
            or last_daily_pull < close_moment(last_closed_day(now))
        ):
            # Решение дня — только по свежему дневному бару: докачиваем перед ним.
            from app.ops.candle_coverage import candle_root

            started = datetime.now(UTC)
            ok, skip = await asyncio.to_thread(
                refresh_tails,
                candle_tickers(paper_tickers),
                tf="1d",
                root=candle_root("1d"),
                depth_days=730,
                workers=candle_workers,
            )
            last_daily_pull = started
            log.info(
                "pre-close daily pull ok=%s skip=%s sec=%s",
                ok,
                skip,
                int((datetime.now(UTC) - started).total_seconds()),
            )
        from app.ops.candle_coverage import candle_root

        books = load_daily_books(candle_root("1d"))
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
        day = last_closed_day(now)
        day_books, stale = books_for_day(books, day) if close_now else ({}, [])
        if close_now and not day_books and (not books or day.weekday() < 5):
            # День не закрываем: решение примем, как только свечи за него появятся.
            close_now = False
            if empty_alert_day != day:
                empty_alert_day = day
                log.error(
                    "daily close waiting day=%s: no daily bars for the day in %s books=%s",
                    day,
                    candle_root("1d"),
                    len(books),
                )
                from app.ops.telegram import alert_data

                alert_data(
                    f"Решение дня {day:%d.%m.%Y} не принято: нет дневных свечей "
                    f"за этот день (книг {len(books)}). Заявки не выставлены."
                )
        if close_now:
            log.info(
                "daily close coverage day=%s fresh=%s stale=%s sample_stale=%s",
                day,
                len(day_books),
                len(stale),
                stale[:10],
            )
            rows = close_all_books(
                day_sleeves, day_books, last_processed=last_bar_day, now=now
            )
            saved = await persist_signals_async(rows)
            try:
                from app.work.service import place_signals

                placed = await asyncio.to_thread(place_signals, rows)
                log.info("work sandbox orders=%s", placed)
            except Exception:
                log.exception("work sandbox orders failed")
            last_bar_day = last_closed_day(now)
            try:
                write_close_day(last_bar_day)
            except OSError:
                log.exception("daily close stamp failed")
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
