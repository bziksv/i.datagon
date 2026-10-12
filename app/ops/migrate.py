"""Alembic upgrade без source .env. Запускать от пользователя сайта."""

import os
import subprocess
from pathlib import Path

from app.ops.envfile import read_env_value


def run_upgrade(site: Path | None = None) -> None:
    root = site or Path(os.environ.get("SITE", ".")).resolve()
    url = read_env_value(root / ".env", "DATABASE_URL") or os.environ.get(
        "DATABASE_URL", ""
    )
    if not url:
        raise SystemExit("DATABASE_URL is required")
    env = os.environ.copy()
    env["DATABASE_URL"] = url
    subprocess.run(
        [str(root / ".venv" / "bin" / "alembic"), "upgrade", "head"],
        check=True,
        cwd=root,
        env=env,
    )


if __name__ == "__main__":
    run_upgrade()
