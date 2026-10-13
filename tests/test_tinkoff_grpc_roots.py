from pathlib import Path

from app.broker import tinkoff as tinkoff_mod


def test_packaged_russian_certs_exist() -> None:
    certs = tinkoff_mod._packaged_russian_certs()
    assert len(certs) >= 1
    assert all(path.is_file() for path in certs)
    root = next(path for path in certs if "root" in path.name)
    text = root.read_text(encoding="utf-8")
    assert "BEGIN CERTIFICATE" in text


def test_ensure_grpc_roots_writes_temp_bundle(monkeypatch, tmp_path) -> None:
    monkeypatch.delenv("GRPC_DEFAULT_SSL_ROOTS_FILE_PATH", raising=False)
    monkeypatch.setenv("TMPDIR", str(tmp_path))
    tinkoff_mod._ensure_grpc_roots()
    path = Path(tinkoff_mod.os.environ["GRPC_DEFAULT_SSL_ROOTS_FILE_PATH"])
    assert path.is_file()
    blob = path.read_text(encoding="utf-8")
    assert "BEGIN CERTIFICATE" in blob
    assert tinkoff_mod.os.environ.get("GRPC_DNS_RESOLVER") == "native"
