from pathlib import Path

from app.ops.accesslog import access_line

ROOT = Path(__file__).resolve().parents[1]


def test_header_token_is_not_logged() -> None:
    line = access_line(
        remote="127.0.0.1",
        method="GET",
        uri="/portfolio",
        status=200,
        headers={"X-App-Token": "cabin-secret-token", "Authorization": "Bearer x"},
    )
    assert "cabin-secret-token" not in line
    assert "Bearer" not in line
    assert "/portfolio" in line


def test_nginx_snippet_uses_combined_without_token_var() -> None:
    snippet = (ROOT / "deploy" / "nginx-i.datagon.ru.snippet.conf").read_text()
    fmt = (ROOT / "deploy" / "nginx-idatagon-log-format.conf").read_text()
    assert "access_log" in snippet
    assert "combined" in snippet
    assert "$http_x_app_token" not in snippet
    assert "$http_x_app_token" not in fmt
    assert "без заголовков" in snippet
    assert "$uri" in fmt
    assert "$http_" not in fmt
