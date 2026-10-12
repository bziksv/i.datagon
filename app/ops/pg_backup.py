"""Дамп и restore-копия: URL не в argv, .env не source."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from app.ops.backup import (
    DEFAULT_BACKUP_DIR,
    DEFAULT_WEBROOT,
    assert_backup_dir,
    copy_db_name,
    parse_database_url,
)
from app.ops.envfile import read_env_value

KEEP_DUMPS = 7


def database_url() -> str:
    env_file = Path(os.environ.get("ENV_FILE", ""))
    if env_file.is_file():
        value = read_env_value(env_file, "DATABASE_URL")
        if value:
            return value
    return os.environ.get("DATABASE_URL", "")


def rotate_dumps(directory: Path, *, keep: int = KEEP_DUMPS) -> None:
    dumps = sorted(directory.glob("idatagon-*.dump"))
    for old in dumps[:-keep] if keep > 0 else dumps:
        old.unlink(missing_ok=True)


def _pg_env(url: str) -> dict[str, str]:
    info = parse_database_url(url)
    env = os.environ.copy()
    env["PGPASSWORD"] = str(info["password"])
    env.pop("DATABASE_URL", None)
    return env


def dump_database() -> Path:
    url = database_url()
    if not url:
        raise SystemExit("DATABASE_URL is required")
    backup_dir = assert_backup_dir(
        os.environ.get("BACKUP_DIR", DEFAULT_BACKUP_DIR),
        os.environ.get("WEBROOT", DEFAULT_WEBROOT),
    )
    backup_dir.mkdir(parents=True, exist_ok=True)
    from datetime import UTC, datetime

    dump = backup_dir / f"idatagon-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}.dump"
    info = parse_database_url(url)
    subprocess.run(
        [
            "pg_dump",
            "-Fc",
            "-h",
            str(info["host"]),
            "-p",
            str(info["port"]),
            "-U",
            str(info["user"]),
            "-d",
            str(info["dbname"]),
            "-f",
            str(dump),
        ],
        check=True,
        env=_pg_env(url),
    )
    rotate_dumps(backup_dir)
    print(dump)
    return dump


def restore_copy(dump: Path | None = None) -> str:
    url = database_url()
    if not url:
        raise SystemExit("DATABASE_URL is required")
    backup_dir = Path(os.environ.get("BACKUP_DIR", DEFAULT_BACKUP_DIR))
    if dump is None:
        found = sorted(backup_dir.glob("idatagon-*.dump"))
        dump = found[-1] if found else None
    if dump is None or not dump.is_file():
        raise SystemExit("dump file required")
    info = parse_database_url(url)
    copy = copy_db_name(str(info["dbname"]))
    if copy == info["dbname"]:
        raise SystemExit("refusing to restore onto the source database")
    env = _pg_env(url)
    admin = [
        "psql",
        "-h",
        str(info["host"]),
        "-p",
        str(info["port"]),
        "-U",
        str(info["user"]),
        "-d",
        "postgres",
        "-v",
        "ON_ERROR_STOP=1",
        "-c",
    ]
    subprocess.run(admin + [f'DROP DATABASE IF EXISTS "{copy}"'], check=True, env=env)
    subprocess.run(admin + [f'CREATE DATABASE "{copy}"'], check=True, env=env)
    subprocess.run(
        [
            "pg_restore",
            "--clean",
            "--if-exists",
            "-h",
            str(info["host"]),
            "-p",
            str(info["port"]),
            "-U",
            str(info["user"]),
            "-d",
            copy,
            str(dump),
        ],
        check=True,
        env=env,
    )
    print(copy)
    return copy


def main(argv: list[str] | None = None) -> None:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] == "dump":
        dump_database()
        return
    if args[0] == "restore":
        path = Path(args[1]) if len(args) > 1 else None
        restore_copy(path)
        return
    raise SystemExit("usage: python -m app.ops.pg_backup dump|restore [dump]")


if __name__ == "__main__":
    main()
