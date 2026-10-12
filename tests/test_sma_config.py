from pathlib import Path

from app.strategy.config import sma_from_config, sma_params


def test_yaml_changes_periods(tmp_path: Path) -> None:
    path = tmp_path / "sleeves.yaml"
    path.write_text("sma_cross:\n  fast: 3\n  slow: 12\n")
    sleeve = sma_from_config({}, path)
    assert sleeve.fast == 3
    assert sleeve.slow == 12


def test_env_overrides_yaml() -> None:
    yaml_text = "sma_cross:\n  fast: 3\n  slow: 12\n"
    fast, slow = sma_params({"SMA_FAST": "8", "SMA_SLOW": "21"}, yaml_text)
    assert (fast, slow) == (8, 21)
