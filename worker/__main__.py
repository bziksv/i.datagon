import asyncio
import logging
import os
from datetime import UTC, date, datetime
from pathlib import Path

from app.logging import setup_logging
from app.ops.envfile import load_env_file
from app.ops.ready import write_beat
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
    fund_interval = int(os.environ.get("FUNDAMENTALS_INTERVAL_SEC", "3600"))
    last_snapshot: datetime | None = None
    last_bar_day: date | None = None
    last_m15_bar: datetime | None = None
    last_fundamentals: datetime | None = None
    day_sleeves = daily_strategies(os.environ)
    scalp_sleeves = scalp_strategies(os.environ)
    while True:
        now = datetime.now(UTC)
        write_beat(now)
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
            except Exception:
                last_fundamentals = now
                log.exception("fundamentals refresh skipped")
        try:
            forward_saved = await refresh_paper_forward(now=now)
            if forward_saved:
                log.info("paper-forward observations saved=%s", forward_saved)
        except Exception:
            log.exception("paper-forward refresh failed")
        await asyncio.sleep(SNAPSHOT_INTERVAL_SEC)


if __name__ == "__main__":
    asyncio.run(run_worker())
