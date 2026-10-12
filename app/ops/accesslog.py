"""Строка access-лога без заголовка X-App-Token."""

from collections.abc import Mapping

SKIP_HEADERS = ("x-app-token", "authorization")


def access_line(
    *,
    remote: str,
    method: str,
    uri: str,
    status: int,
    headers: Mapping[str, str] | None = None,
) -> str:
    _ = {
        key: value
        for key, value in (headers or {}).items()
        if key.lower() not in SKIP_HEADERS
    }
    return f'{remote} - - "{method} {uri} HTTP/1.1" {status}'
