"""Фоновая докачка свечей на сервере — вкладка не нужна."""

from __future__ import annotations

import json
import logging
import os
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

log = logging.getLogger(__name__)

DEFAULT_STATE = "data/logs/candle-fill.job.json"

_lock = threading.Lock()
_thread: threading.Thread | None = None
_cancel = threading.Event()


def state_path() -> Path:
    return Path(os.environ.get("CANDLE_FILL_JOB_PATH", DEFAULT_STATE))


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _empty() -> dict[str, Any]:
    return {
        "status": "idle",
        "tf": "1d",
        "total": 0,
        "index": 0,
        "ticker": "",
        "done": {},
        "fail": {},
        "started_at": None,
        "finished_at": None,
        "message": "",
        "tickers": [],
    }


def read_state(path: Path | None = None) -> dict[str, Any]:
    target = path or state_path()
    if not target.is_file():
        return _empty()
    try:
        raw = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return _empty()
    if not isinstance(raw, dict):
        return _empty()
    base = _empty()
    base.update(raw)
    if not isinstance(base.get("done"), dict):
        base["done"] = {}
    if not isinstance(base.get("fail"), dict):
        base["fail"] = {}
    if not isinstance(base.get("tickers"), list):
        base["tickers"] = []
    return base


def write_state(state: dict[str, Any], path: Path | None = None) -> dict[str, Any]:
    target = path or state_path()
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_suffix(target.suffix + ".tmp")
        tmp.write_text(
            json.dumps(state, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        tmp.replace(target)
    except OSError:
        log.exception("candle fill state write failed path=%s", target)
    return state


def status_view(path: Path | None = None) -> dict[str, Any]:
    state = read_state(path)
    running = state.get("status") == "running" and _thread is not None and _thread.is_alive()
    if state.get("status") == "running" and not running:
        # Процесс API перезапустили посреди джобы.
        state["status"] = "error"
        state["finished_at"] = state.get("finished_at") or _now()
        state["message"] = state.get("message") or "докачка оборвалась (перезапуск API)"
        write_state(state, path)
    return {
        "status": state.get("status") or "idle",
        "tf": state.get("tf") or "1d",
        "total": int(state.get("total") or 0),
        "index": int(state.get("index") or 0),
        "ticker": str(state.get("ticker") or ""),
        "done": state.get("done") or {},
        "fail": state.get("fail") or {},
        "started_at": state.get("started_at"),
        "finished_at": state.get("finished_at"),
        "message": state.get("message") or "",
        "running": bool(state.get("status") == "running"),
    }


def pull_one(ticker: str, *, tf: str, days: int) -> int:
    """Один тикер → CSV. Та же логика, что POST /desk/candles/pull."""
    from app.ops.broker_daily import pull_daily
    from app.ops.candle_coverage import STRATEGY_TFS, candle_root
    from app.ops.refresh_candles import refresh

    symbol = ticker.strip().upper()
    frame = (tf or "1d").strip().lower()
    if frame not in STRATEGY_TFS:
        raise ValueError("unsupported tf")
    span = int(days)
    if frame in {"15m", "10m"} and span > 180:
        span = 180
    if frame == "1d":
        return pull_daily(symbol, days=span)
    path = refresh([symbol], days=span, tf=frame, root=candle_root(frame))[0]
    return max(0, len(path.read_text(encoding="utf-8").splitlines()) - 1)


def gap_tickers_from_coverage(coverage: dict[str, Any]) -> list[str]:
    out: list[str] = []
    for row in coverage.get("items") or []:
        if not isinstance(row, dict):
            continue
        if row.get("status") == "ready":
            continue
        ticker = str(row.get("ticker") or "").strip().upper()
        if ticker:
            out.append(ticker)
    return out


def _run(
    tickers: list[str],
    *,
    tf: str,
    days: int,
    pull: Callable[..., int],
    path: Path,
) -> None:
    state = read_state(path)
    try:
        for i, ticker in enumerate(tickers):
            if _cancel.is_set():
                state["status"] = "cancelled"
                state["message"] = "остановлено"
                state["finished_at"] = _now()
                write_state(state, path)
                return
            state["index"] = i
            state["ticker"] = ticker
            state["message"] = f"качаю {ticker}"
            write_state(state, path)
            try:
                bars = pull(ticker, tf=tf, days=days)
                state["done"][ticker] = {"bars": int(bars)}
            except Exception as exc:  # noqa: BLE001 — копим ошибки по тикерам
                state["fail"][ticker] = str(exc) or "ошибка"
                log.exception("candle fill failed ticker=%s tf=%s", ticker, tf)
            write_state(state, path)
        state["index"] = len(tickers)
        state["ticker"] = ""
        state["status"] = "done"
        state["finished_at"] = _now()
        failed = len(state.get("fail") or {})
        ok = len(state.get("done") or {})
        state["message"] = f"готово: {ok} ок" + (f", {failed} с ошибкой" if failed else "")
        write_state(state, path)
    except Exception as exc:  # noqa: BLE001
        log.exception("candle fill crashed")
        state["status"] = "error"
        state["message"] = str(exc) or "сломалось"
        state["finished_at"] = _now()
        write_state(state, path)
    finally:
        global _thread
        with _lock:
            _thread = None


def start_fill(
    tickers: list[str],
    *,
    tf: str = "1d",
    days: int | None = None,
    path: Path | None = None,
    pull: Callable[..., int] | None = None,
) -> dict[str, Any]:
    """Запустить докачку в фоне. Если уже running — вернуть текущий статус."""
    global _thread
    target = path or state_path()
    symbols = [str(t).strip().upper() for t in tickers if str(t).strip()]
    # уникальные, порядок сохранить
    seen: set[str] = set()
    ordered: list[str] = []
    for t in symbols:
        if t in seen:
            continue
        seen.add(t)
        ordered.append(t)
    frame = (tf or "1d").strip().lower()
    span = int(days if days is not None else (730 if frame == "1d" else 180))

    with _lock:
        current = read_state(target)
        if current.get("status") == "running" and _thread is not None and _thread.is_alive():
            return status_view(target)
        if not ordered:
            state = _empty()
            state["status"] = "done"
            state["tf"] = frame
            state["message"] = "качать нечего"
            state["started_at"] = _now()
            state["finished_at"] = _now()
            write_state(state, target)
            return status_view(target)
        _cancel.clear()
        state = {
            "status": "running",
            "tf": frame,
            "total": len(ordered),
            "index": 0,
            "ticker": ordered[0],
            "done": {},
            "fail": {},
            "started_at": _now(),
            "finished_at": None,
            "message": "стартовала",
            "tickers": ordered,
        }
        write_state(state, target)
        worker = pull or pull_one
        _thread = threading.Thread(
            target=_run,
            kwargs={
                "tickers": ordered,
                "tf": frame,
                "days": span,
                "pull": worker,
                "path": target,
            },
            name="candle-fill",
            daemon=True,
        )
        _thread.start()
    return status_view(target)


def request_cancel(path: Path | None = None) -> dict[str, Any]:
    target = path or state_path()
    with _lock:
        state = read_state(target)
        if state.get("status") == "running":
            _cancel.set()
            state["message"] = "останавливаю…"
            write_state(state, target)
    return status_view(target)
