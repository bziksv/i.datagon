from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_nginx_rejects_trace_and_extra_methods() -> None:
    snippet = (ROOT / "deploy" / "nginx-i.datagon.ru.snippet.conf").read_text()
    note = (ROOT / "deploy" / "NGINX-METHODS.md").read_text()
    assert "TRACE" in snippet or "request_method" in snippet
    assert "405" in snippet
    assert "GET|POST|HEAD|OPTIONS" in snippet
    assert "TRACE" in note
    assert "405" in note
    assert "FastPanel" in note
