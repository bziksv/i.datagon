import os
from pathlib import Path

import pytest
from app.ops.backup import (
    DEFAULT_BACKUP_DIR,
    DEFAULT_WEBROOT,
    BackupDirError,
    assert_backup_dir,
    backup_dir_ok,
    copy_db_name,
    parse_database_url,
)
from app.ops.envfile import load_env_file, read_env_value
from app.ops.pg_backup import rotate_dumps

ROOT = Path(__file__).resolve().parents[1]


def test_backup_dir_outside_webroot() -> None:
    assert backup_dir_ok(DEFAULT_BACKUP_DIR, DEFAULT_WEBROOT)
    assert not DEFAULT_BACKUP_DIR.startswith(DEFAULT_WEBROOT)
    assert not backup_dir_ok(f"{DEFAULT_WEBROOT}/dumps", DEFAULT_WEBROOT)
    with pytest.raises(BackupDirError):
        assert_backup_dir(DEFAULT_WEBROOT, DEFAULT_WEBROOT)
    assert copy_db_name("idatagon") == "idatagon_copy"
    info = parse_database_url(
        "postgresql+asyncpg://idatagon:secret@localhost:5432/idatagon"
    )
    assert info["dbname"] == "idatagon"
    assert "secret" not in DEFAULT_BACKUP_DIR


def test_scripts_do_not_source_env_or_pass_url_argv() -> None:
    backup = (ROOT / "deploy" / "backup-postgres.sh").read_text()
    restore = (ROOT / "deploy" / "restore-postgres-copy.sh").read_text()
    cron = (ROOT / "deploy" / "backup-postgres.cron").read_text()
    release = (ROOT / "deploy" / "release.sh").read_text()
    assert "source \"" not in backup
    assert "source \"" not in restore
    assert "source \"" not in release
    assert "source $" not in release
    assert "python3 -m app.ops.pg_backup" in backup
    assert "python3 -m app.ops.pg_backup" in restore
    assert "app.ops.migrate" in release
    assert "runuser" in release
    assert cron.splitlines()[-1].startswith("15 3 * * * i_datagon_ru_usr ")
    assert "DATABASE_URL" not in backup.split("python3")[-1] or "-m app.ops" in backup


def test_envfile_does_not_execute_shell(tmp_path: Path, monkeypatch) -> None:
    env = tmp_path / ".env"
    env.write_text('DATABASE_URL=postgresql://u:p@localhost/db\nEVIL=$(echo hacked)\n')
    assert read_env_value(env, "DATABASE_URL") == "postgresql://u:p@localhost/db"
    assert read_env_value(env, "EVIL") == "$(echo hacked)"
    monkeypatch.delenv("EVIL", raising=False)
    monkeypatch.setenv("DATABASE_URL", "already-set")
    load_env_file(env)
    assert os.environ["DATABASE_URL"] == "already-set"
    assert os.environ["EVIL"] == "$(echo hacked)"


def test_rotate_dumps_keeps_last_seven(tmp_path: Path) -> None:
    for i in range(9):
        (tmp_path / f"idatagon-2026010{i}.dump").write_text("x")
    rotate_dumps(tmp_path, keep=7)
    left = sorted(p.name for p in tmp_path.glob("*.dump"))
    assert len(left) == 7
    assert "idatagon-20260100.dump" not in left
    assert "idatagon-20260108.dump" in left
