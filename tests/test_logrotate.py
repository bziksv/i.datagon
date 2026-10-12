from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONF = ROOT / "deploy" / "idatagon-logs.logrotate"
WEBROOT = "/var/www/i_datagon_ru_usr/data/www/i.datagon.ru"
LOG_DIR = "/var/www/i_datagon_ru_usr/data/logs"


def test_week_of_rotated_logs_stays_outside_webroot() -> None:
    text = CONF.read_text()
    assert "idatagon-api.log" in text
    assert "idatagon-worker.log" in text
    assert "rotate 7" in text
    assert "daily" in text
    assert "copytruncate" in text
    assert "maxsize 50M" in text
    assert LOG_DIR in text
    assert WEBROOT not in text
    assert not LOG_DIR.startswith(WEBROOT)
