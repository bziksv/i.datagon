"""Временный доступ в кабинет: токен g1.<exp>.<sig> на N часов."""

from __future__ import annotations

import argparse
import hashlib
import hmac
import os
import time
from urllib.parse import quote

PREFIX = "g1"


def _secret() -> str:
    return (
        os.environ.get("APP_GUEST_SECRET")
        or os.environ.get("APP_AUTH_TOKEN")
        or ""
    )


def mint_guest_token(*, hours: float = 24, now: float | None = None) -> str:
    secret = _secret()
    if not secret:
        raise RuntimeError("APP_AUTH_TOKEN or APP_GUEST_SECRET required")
    exp = int((now if now is not None else time.time()) + hours * 3600)
    payload = f"{PREFIX}.{exp}"
    sig = hmac.new(
        secret.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()[:32]
    return f"{payload}.{sig}"


def verify_guest_token(token: str, *, now: float | None = None) -> bool:
    secret = _secret()
    if not secret or not token:
        return False
    parts = token.strip().split(".")
    if len(parts) != 3 or parts[0] != PREFIX:
        return False
    try:
        exp = int(parts[1])
    except ValueError:
        return False
    if exp < int(now if now is not None else time.time()):
        return False
    payload = f"{PREFIX}.{exp}"
    expected = hmac.new(
        secret.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()[:32]
    return hmac.compare_digest(parts[2], expected)


def guest_cabin_url(
    token: str,
    *,
    base: str = "https://i.datagon.ru",
) -> str:
    root = base.rstrip("/")
    return f"{root}/?access={quote(token, safe='')}"


def token_accepted(got: str, expected_main: str) -> bool:
    if expected_main and got:
        try:
            if hmac.compare_digest(got, expected_main):
                return True
        except (TypeError, ValueError):
            pass
    return verify_guest_token(got)


def main() -> None:
    parser = argparse.ArgumentParser(description="Mint 24h cabin guest link")
    parser.add_argument("--hours", type=float, default=24)
    parser.add_argument("--base", default="https://i.datagon.ru")
    args = parser.parse_args()
    from pathlib import Path

    from app.ops.envfile import load_env_file

    load_env_file(Path(".env"))
    token = mint_guest_token(hours=args.hours)
    print(guest_cabin_url(token, base=args.base))
    print(f"# expires_in_hours={args.hours}", flush=True)


if __name__ == "__main__":
    main()
