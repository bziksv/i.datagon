"""Локальный запуск API: python -m app. Не source .env."""

from pathlib import Path

import uvicorn

from app.ops.envfile import load_env_file

load_env_file(Path(".env"))

if __name__ == "__main__":
    uvicorn.run(
        "app.main:create_app",
        factory=True,
        host="127.0.0.1",
        port=8000,
        reload=False,
    )
