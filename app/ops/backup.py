"""Бэкап Postgres: каталог только вне webroot."""

from pathlib import Path
from urllib.parse import urlparse

DEFAULT_WEBROOT = "/var/www/i_datagon_ru_usr/data/www/i.datagon.ru"
DEFAULT_BACKUP_DIR = "/var/www/i_datagon_ru_usr/data/backups"
COPY_DB_SUFFIX = "_copy"


class BackupDirError(ValueError):
    pass


def parse_database_url(url: str) -> dict[str, str | int]:
    raw = url.replace("postgresql+asyncpg://", "postgresql://", 1)
    parsed = urlparse(raw)
    return {
        "user": parsed.username or "",
        "password": parsed.password or "",
        "host": parsed.hostname or "localhost",
        "port": parsed.port or 5432,
        "dbname": (parsed.path or "").lstrip("/"),
    }


def backup_dir_ok(backup_dir: str, webroot: str = DEFAULT_WEBROOT) -> bool:
    target = Path(backup_dir).expanduser().resolve()
    root = Path(webroot).expanduser().resolve()
    return root not in target.parents and target != root


def assert_backup_dir(backup_dir: str, webroot: str = DEFAULT_WEBROOT) -> Path:
    if not backup_dir_ok(backup_dir, webroot):
        raise BackupDirError(f"backup dir must be outside webroot: {webroot}")
    return Path(backup_dir).expanduser().resolve()


def copy_db_name(dbname: str) -> str:
    return f"{dbname}{COPY_DB_SUFFIX}"
