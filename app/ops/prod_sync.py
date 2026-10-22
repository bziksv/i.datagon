"""Локаль — зеркало прода: свечи, песочницы и таблицы воркера забираем с сервера.

Прод — источник правды. С сервера только читаем (rsync и COPY TO STDOUT),
на нём ничего не меняется. Локально таблицы заменяются целиком одной
транзакцией, файлы свечей — зеркалом каталога.

Включается в локальном .env: PROD_SYNC=root@host:/path/to/app
"""

from __future__ import annotations

import json
import logging
import os
import shlex
import subprocess
import tempfile
import threading
import time
from datetime import UTC, datetime
from pathlib import Path

log = logging.getLogger(__name__)

DEFAULT_INTERVAL_SEC = 900
STATE_PATH = Path("data/logs/prod-sync.json")

# Каталоги, которые пишет прод. candles_m1 / candles_h1 живут только локально.
MIRROR_DIRS = ("candles", "candles_m15", "candles_m10", "candles_sp500")
# Отдельные файлы: песочницы и отметки последнего обновления свечей и фундаментала.
MIRROR_FILES = (
    "work_desk.json",
    "logs/candle-refresh.beat",
    "logs/fundamentals-refresh.beat",
)
MIRROR_TREES = ("work_desks",)
# Порядок важен: родители раньше детей (внешние ключи).
TABLES = (
    "instruments",
    "universe_members",
    "candles",
    "positions",
    "fundamentals",
    "earnings_days",
    "signals",
    "equity_snapshots",
    "backtest_experiments",
    "paper_forward_runs",
    "paper_forward_observations",
)
SSH_OPTS = (
    "-o",
    "BatchMode=yes",
    "-o",
    "ConnectTimeout=15",
    "-o",
    "ControlMaster=auto",
    "-o",
    "ControlPath=/tmp/idatagon-sync-%r@%h",
    "-o",
    "ControlPersist=120",
)

_lock = threading.Lock()


def source() -> str:
    return os.environ.get("PROD_SYNC", "").strip()


def enabled() -> bool:
    return bool(source())


MIRROR_BLOCKED_PREFIXES = ("/work/", "/desk/candles/", "/fundamentals/refresh")
MIRROR_ALLOWED = frozenset({"/work/probe"})


def blocks_write(path: str) -> bool:
    """В зеркале локаль не качает данные и не трогает песочницы (общий счёт с продом)."""
    if not enabled() or path in MIRROR_ALLOWED:
        return False
    return path.startswith(MIRROR_BLOCKED_PREFIXES)


def interval_sec() -> int:
    try:
        return max(
            60, int(os.environ.get("PROD_SYNC_INTERVAL_SEC", DEFAULT_INTERVAL_SEC))
        )
    except ValueError:
        return DEFAULT_INTERVAL_SEC


def _split(src: str) -> tuple[str, str]:
    host, _, root = src.partition(":")
    if not host or not root:
        raise ValueError("PROD_SYNC: нужно user@host:/путь/к/приложению")
    return host, root.rstrip("/")


def _local_db_url() -> str:
    url = os.environ.get("DATABASE_URL", "")
    return url.replace("+asyncpg", "")


def _run(cmd: list[str], *, timeout: int = 600, stdout=None, what: str = "") -> str:
    done = subprocess.run(
        cmd,
        check=False,
        timeout=timeout,
        stdout=stdout if stdout is not None else subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if done.returncode != 0:
        lines = (done.stderr or "").strip().splitlines()
        tail = " | ".join(lines[:3]) or f"exit {done.returncode}"
        raise RuntimeError(f"{cmd[0]} {what}: {tail}".replace("  ", " "))
    return done.stdout or ""


def rsync_filters() -> list[str]:
    """Зеркалим только перечисленное; чего нет на проде — удаляется и локально.

    Всё остальное в data/ (candles_m1, certs, локальные логи) исключено и потому
    не удаляется: --delete не трогает исключённые пути без --delete-excluded.
    """
    rules = ["--exclude=*.tmp"]
    rules += [f"--include=/{name}/***" for name in MIRROR_DIRS + MIRROR_TREES]
    parents = sorted({str(Path(name).parent) for name in MIRROR_FILES} - {"."})
    rules += [f"--include=/{parent}/" for parent in parents]
    rules += [f"--include=/{name}" for name in MIRROR_FILES]
    rules.append("--exclude=*")
    return rules


def sync_files(host: str, root: str, local: Path) -> int:
    local.mkdir(parents=True, exist_ok=True)
    out = _run(
        [
            "rsync",
            "-a",
            "--delete",
            *rsync_filters(),
            "--stats",
            "-e",
            "ssh " + " ".join(SSH_OPTS),
            f"{host}:{root}/data/",
            f"{local}/",
        ],
        what="files",
    )
    for line in out.splitlines():
        if line.startswith("Number of regular files transferred:"):
            return int(line.split(":", 1)[1].strip().replace(",", ""))
    return 0


def _columns(local_url: str, table: str) -> list[str]:
    out = _run(
        [
            "psql",
            local_url,
            "-Atc",
            "select column_name from information_schema.columns "
            f"where table_schema='public' and table_name='{table}' order by ordinal_position",
        ]
    )
    return [line for line in out.splitlines() if line]


def sync_tables(host: str, root: str) -> dict[str, int]:
    """COPY каждой таблицы с прода во временный файл, потом замена одной транзакцией."""
    local_url = _local_db_url()
    if not local_url:
        raise RuntimeError("нет DATABASE_URL для локальной базы")
    remote_url = f"$(grep ^DATABASE_URL= {shlex.quote(root)}/.env | cut -d= -f2- | sed 's/+asyncpg//')"
    counts: dict[str, int] = {}
    with tempfile.TemporaryDirectory(prefix="idatagon-sync-") as tmp:
        script = ["\\set ON_ERROR_STOP on", "BEGIN;", f"TRUNCATE {', '.join(TABLES)};"]
        for table in TABLES:
            cols = _columns(local_url, table)
            if not cols:
                raise RuntimeError(f"локально нет таблицы {table}")
            quoted = ", ".join(f'"{col}"' for col in cols)
            select = f"COPY (SELECT {quoted} FROM {table}) TO STDOUT"
            dump = Path(tmp) / f"{table}.copy"
            with dump.open("w", encoding="utf-8") as fh:
                _run(
                    [
                        "ssh",
                        *SSH_OPTS,
                        host,
                        f'psql "{remote_url}" -v ON_ERROR_STOP=1 -c {shlex.quote(select)}',
                    ],
                    stdout=fh,
                    what=table,
                )
            counts[table] = sum(1 for _ in dump.open(encoding="utf-8"))
            script.append(f"\\copy {table} ({quoted}) FROM '{dump}'")
        script.append("COMMIT;")
        sql = Path(tmp) / "apply.sql"
        sql.write_text("\n".join(script) + "\n", encoding="utf-8")
        _run(["psql", local_url, "-q", "-f", str(sql)], what="apply")
    return counts


def _reset_caches() -> None:
    try:
        from app.strategy import abs_mom

        abs_mom._BREADTH = None
        abs_mom._SP_BREADTH = None
    except Exception:  # noqa: BLE001
        log.exception("prod sync: cache reset failed")


def write_state(state: dict, path: Path | None = None) -> None:
    target = path or STATE_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")


def read_state(path: Path | None = None) -> dict:
    target = path or STATE_PATH
    try:
        return json.loads(target.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def sync_once(local: Path | None = None) -> dict:
    host, root = _split(source())
    local = local or Path("data")
    started = datetime.now(UTC)
    prev = read_state()
    with _lock:
        try:
            files = sync_files(host, root, local)
            rows = sync_tables(host, root)
        except Exception as exc:  # noqa: BLE001 — локаль живёт и без свежей синхры
            state = {
                **prev,
                "ok": False,
                "error": str(exc)[:300],
                "tried_at": started.isoformat(),
            }
            write_state(state)
            log.warning("prod sync failed: %s", exc)
            return state
    _reset_caches()
    state = {
        "ok": True,
        "error": "",
        "last_at": started.isoformat(),
        "tried_at": started.isoformat(),
        "sec": round((datetime.now(UTC) - started).total_seconds(), 1),
        "files": files,
        "rows": rows,
    }
    write_state(state)
    log.info("prod sync ok sec=%s rows=%s", state["sec"], sum(rows.values()))
    return state


def view() -> dict:
    state = read_state()
    return {
        "enabled": enabled(),
        "source": _split(source())[0] if enabled() else "",
        "interval_sec": interval_sec(),
        **{
            key: state.get(key) for key in ("ok", "error", "last_at", "tried_at", "sec")
        },
    }


def start_background() -> threading.Thread | None:
    """Синхра раз в interval_sec в фоне API. Только когда задан PROD_SYNC."""
    if not enabled():
        return None

    def loop() -> None:
        while True:
            sync_once()
            time.sleep(interval_sec())

    thread = threading.Thread(target=loop, name="prod-sync", daemon=True)
    thread.start()
    return thread


def main() -> None:
    from app.ops.envfile import load_env_file

    load_env_file(Path(".env"))
    if not enabled():
        raise SystemExit("PROD_SYNC не задан в .env")
    print(json.dumps(sync_once(), ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
