"""Параметры рукава из YAML и env, не из промпта."""

from collections.abc import Mapping
from decimal import Decimal
from pathlib import Path

from app.strategy.donchian import DEFAULT_PERIOD, DonchianBreakoutStrategy
from app.strategy.rsi import (
    DEFAULT_OVERBOUGHT,
    DEFAULT_OVERSOLD,
    DEFAULT_PERIOD as RSI_PERIOD,
    RsiReversionStrategy,
)
from app.strategy.scalp import (
    DEFAULT_FAST as SCALP_FAST,
    DEFAULT_SLOW as SCALP_SLOW,
    DEFAULT_STOP_PCT as SCALP_STOP,
    EmaScalpStrategy,
)
from app.strategy.sma import DEFAULT_FAST, DEFAULT_SLOW, SmaCrossStrategy

DEFAULT_YAML = Path("config/sleeves.yaml")


def _section(text: str, sleeve: str) -> str:
    lines = text.splitlines()
    out: list[str] = []
    in_section = False
    for line in lines:
        if line.startswith(sleeve + ":"):
            in_section = True
            continue
        if in_section:
            if line and not line[0].isspace() and ":" in line:
                break
            out.append(line)
    return "\n".join(out)


def _int_field(section: str, key: str, default: int) -> int:
    for line in section.splitlines():
        stripped = line.strip()
        if stripped.startswith(key + ":"):
            return int(stripped.split(":", 1)[1].strip())
    return default


def _decimal_field(section: str, key: str, default: Decimal) -> Decimal:
    for line in section.splitlines():
        stripped = line.strip()
        if stripped.startswith(key + ":"):
            return Decimal(stripped.split(":", 1)[1].strip())
    return default


def parse_sleeve_yaml(text: str) -> dict[str, int]:
    """Совместимость со старыми тестами SMA: fast/slow из всего файла."""
    parsed: dict[str, int] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("fast:"):
            parsed["fast"] = int(stripped.split(":", 1)[1])
        elif stripped.startswith("slow:"):
            parsed["slow"] = int(stripped.split(":", 1)[1])
    return parsed


def sma_params(
    env: Mapping[str, str],
    yaml_text: str | None = None,
) -> tuple[int, int]:
    fast, slow = DEFAULT_FAST, DEFAULT_SLOW
    if yaml_text:
        section = _section(yaml_text, "sma_cross") or yaml_text
        fast = _int_field(section, "fast", fast)
        slow = _int_field(section, "slow", slow)
    if env.get("SMA_FAST"):
        fast = int(env["SMA_FAST"])
    if env.get("SMA_SLOW"):
        slow = int(env["SMA_SLOW"])
    return fast, slow


def donchian_params(
    env: Mapping[str, str],
    yaml_text: str | None = None,
) -> int:
    period = DEFAULT_PERIOD
    if yaml_text:
        section = _section(yaml_text, "donchian_breakout") or yaml_text
        period = _int_field(section, "period", period)
    if env.get("DONCHIAN_PERIOD"):
        period = int(env["DONCHIAN_PERIOD"])
    return period


def rsi_params(
    env: Mapping[str, str],
    yaml_text: str | None = None,
) -> tuple[int, Decimal, Decimal]:
    period = RSI_PERIOD
    oversold = DEFAULT_OVERSOLD
    overbought = DEFAULT_OVERBOUGHT
    if yaml_text:
        section = _section(yaml_text, "rsi_reversion")
        period = _int_field(section, "period", period)
        oversold = _decimal_field(section, "oversold", oversold)
        overbought = _decimal_field(section, "overbought", overbought)
    if env.get("RSI_PERIOD"):
        period = int(env["RSI_PERIOD"])
    if env.get("RSI_OVERSOLD"):
        oversold = Decimal(env["RSI_OVERSOLD"])
    if env.get("RSI_OVERBOUGHT"):
        overbought = Decimal(env["RSI_OVERBOUGHT"])
    return period, oversold, overbought


def scalp_params(
    env: Mapping[str, str],
    yaml_text: str | None = None,
) -> tuple[int, int, Decimal]:
    fast, slow, stop = SCALP_FAST, SCALP_SLOW, SCALP_STOP
    if yaml_text:
        section = _section(yaml_text, "ema_scalp")
        fast = _int_field(section, "fast", fast)
        slow = _int_field(section, "slow", slow)
        stop = _decimal_field(section, "stop_pct", stop)
    if env.get("SCALP_FAST"):
        fast = int(env["SCALP_FAST"])
    if env.get("SCALP_SLOW"):
        slow = int(env["SCALP_SLOW"])
    if env.get("SCALP_STOP_PCT"):
        stop = Decimal(env["SCALP_STOP_PCT"])
    return fast, slow, stop


def _yaml_text(yaml_path: Path | None) -> str | None:
    if yaml_path is not None and yaml_path.exists():
        return yaml_path.read_text()
    return None


def donchian_from_config(
    env: Mapping[str, str],
    yaml_path: Path | None = DEFAULT_YAML,
) -> DonchianBreakoutStrategy:
    return DonchianBreakoutStrategy(period=donchian_params(env, _yaml_text(yaml_path)))


def sma_from_config(
    env: Mapping[str, str],
    yaml_path: Path | None = DEFAULT_YAML,
) -> SmaCrossStrategy:
    fast, slow = sma_params(env, _yaml_text(yaml_path))
    return SmaCrossStrategy(fast=fast, slow=slow)


def rsi_from_config(
    env: Mapping[str, str],
    yaml_path: Path | None = DEFAULT_YAML,
) -> RsiReversionStrategy:
    period, oversold, overbought = rsi_params(env, _yaml_text(yaml_path))
    return RsiReversionStrategy(
        period=period, oversold=oversold, overbought=overbought
    )


def scalp_from_config(
    env: Mapping[str, str],
    yaml_path: Path | None = DEFAULT_YAML,
) -> EmaScalpStrategy:
    fast, slow, stop = scalp_params(env, _yaml_text(yaml_path))
    return EmaScalpStrategy(fast=fast, slow=slow, stop_pct=stop)


def active_strategies(env: Mapping[str, str], yaml_path: Path | None = DEFAULT_YAML):
    return [
        sma_from_config(env, yaml_path),
        donchian_from_config(env, yaml_path),
        rsi_from_config(env, yaml_path),
        scalp_from_config(env, yaml_path),
    ]


def daily_strategies(env: Mapping[str, str], yaml_path: Path | None = DEFAULT_YAML):
    return [
        sma_from_config(env, yaml_path),
        donchian_from_config(env, yaml_path),
        rsi_from_config(env, yaml_path),
    ]


def scalp_strategies(env: Mapping[str, str], yaml_path: Path | None = DEFAULT_YAML):
    return [scalp_from_config(env, yaml_path)]
