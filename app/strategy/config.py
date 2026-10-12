"""Параметры рукава из YAML и env, не из промпта."""

from collections.abc import Mapping
from decimal import Decimal
from pathlib import Path

from app.strategy.abs_mom import (
    DEFAULT_BACKTEST_POSITION_SHARE as ABS_MOM_SHARE,
    DEFAULT_LOOKBACK as ABS_MOM_LOOKBACK,
    DEFAULT_MIN_ROC as ABS_MOM_MIN_ROC,
    DEFAULT_SMA_PERIOD as ABS_MOM_SMA,
    DEFAULT_STOP_PCT as ABS_MOM_STOP,
    DEFAULT_TRAIL_PCT as ABS_MOM_TRAIL,
    AbsMomentumStrategy,
)
from app.strategy.donchian import DEFAULT_PERIOD, DonchianBreakoutStrategy
from app.strategy.morning import (
    DEFAULT_MAX_HOLD_BARS as MORNING_MAX_HOLD,
    MorningBounceStrategy,
)
from app.strategy.overnight import (
    DEFAULT_AVERAGE_TRIGGER_PCT,
    DEFAULT_CLOSE_RANGE_MAX,
    DEFAULT_COOLDOWN_BARS,
    DEFAULT_MAX_HOLD_BARS,
    DEFAULT_MAX_LAYERS,
    DEFAULT_MIN_DAY_DROP_PCT,
    DEFAULT_RSI_MAX,
    DEFAULT_RSI_PERIOD,
    DEFAULT_SMA_PERIOD,
    DEFAULT_STOP_PCT as OVERNIGHT_STOP,
    DEFAULT_TAKE_PROFIT_PCT,
    OvernightBounceStrategy,
)
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


def overnight_params(
    env: Mapping[str, str],
    yaml_text: str | None = None,
) -> dict:
    params = {
        "take_profit_pct": DEFAULT_TAKE_PROFIT_PCT,
        "average_trigger_pct": DEFAULT_AVERAGE_TRIGGER_PCT,
        "max_layers": DEFAULT_MAX_LAYERS,
        "stop_pct": OVERNIGHT_STOP,
        "sma_period": DEFAULT_SMA_PERIOD,
        "max_hold_bars": DEFAULT_MAX_HOLD_BARS,
        "cooldown_bars": DEFAULT_COOLDOWN_BARS,
        "min_day_drop_pct": DEFAULT_MIN_DAY_DROP_PCT,
        "rsi_period": DEFAULT_RSI_PERIOD,
        "rsi_max": DEFAULT_RSI_MAX,
        "close_range_max": DEFAULT_CLOSE_RANGE_MAX,
    }
    if yaml_text:
        section = _section(yaml_text, "overnight_bounce")
        params["take_profit_pct"] = _decimal_field(
            section, "take_profit_pct", params["take_profit_pct"]
        )
        params["average_trigger_pct"] = _decimal_field(
            section, "average_trigger_pct", params["average_trigger_pct"]
        )
        params["max_layers"] = _int_field(
            section, "max_layers", params["max_layers"]
        )
        params["stop_pct"] = _decimal_field(section, "stop_pct", params["stop_pct"])
        params["sma_period"] = _int_field(
            section, "sma_period", params["sma_period"]
        )
        params["max_hold_bars"] = _int_field(
            section, "max_hold_bars", params["max_hold_bars"]
        )
        params["cooldown_bars"] = _int_field(
            section, "cooldown_bars", params["cooldown_bars"]
        )
        params["min_day_drop_pct"] = _decimal_field(
            section, "min_day_drop_pct", params["min_day_drop_pct"]
        )
        params["rsi_period"] = _int_field(
            section, "rsi_period", params["rsi_period"]
        )
        params["rsi_max"] = _decimal_field(section, "rsi_max", params["rsi_max"])
        params["close_range_max"] = _decimal_field(
            section, "close_range_max", params["close_range_max"]
        )
    env_map = {
        "OVERNIGHT_TAKE_PROFIT_PCT": ("take_profit_pct", Decimal),
        "OVERNIGHT_AVERAGE_TRIGGER_PCT": ("average_trigger_pct", Decimal),
        "OVERNIGHT_MAX_LAYERS": ("max_layers", int),
        "OVERNIGHT_STOP_PCT": ("stop_pct", Decimal),
        "OVERNIGHT_SMA_PERIOD": ("sma_period", int),
        "OVERNIGHT_MAX_HOLD_BARS": ("max_hold_bars", int),
        "OVERNIGHT_COOLDOWN_BARS": ("cooldown_bars", int),
        "OVERNIGHT_MIN_DAY_DROP_PCT": ("min_day_drop_pct", Decimal),
        "OVERNIGHT_RSI_PERIOD": ("rsi_period", int),
        "OVERNIGHT_RSI_MAX": ("rsi_max", Decimal),
        "OVERNIGHT_CLOSE_RANGE_MAX": ("close_range_max", Decimal),
    }
    for env_key, (name, caster) in env_map.items():
        if env.get(env_key):
            params[name] = caster(env[env_key])
    return params


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


def overnight_from_config(
    env: Mapping[str, str],
    yaml_path: Path | None = DEFAULT_YAML,
) -> OvernightBounceStrategy:
    return OvernightBounceStrategy(**overnight_params(env, _yaml_text(yaml_path)))


def morning_params(
    env: Mapping[str, str],
    yaml_text: str | None = None,
) -> dict:
    params = {
        "take_profit_pct": DEFAULT_TAKE_PROFIT_PCT,
        "average_trigger_pct": DEFAULT_AVERAGE_TRIGGER_PCT,
        "max_layers": DEFAULT_MAX_LAYERS,
        "stop_pct": OVERNIGHT_STOP,
        "sma_period": DEFAULT_SMA_PERIOD,
        "max_hold_bars": MORNING_MAX_HOLD,
        "cooldown_bars": DEFAULT_COOLDOWN_BARS,
        "min_day_drop_pct": DEFAULT_MIN_DAY_DROP_PCT,
        "rsi_period": DEFAULT_RSI_PERIOD,
        "rsi_max": DEFAULT_RSI_MAX,
        "close_range_max": DEFAULT_CLOSE_RANGE_MAX,
    }
    if yaml_text:
        section = _section(yaml_text, "morning_bounce")
        params["take_profit_pct"] = _decimal_field(
            section, "take_profit_pct", params["take_profit_pct"]
        )
        params["average_trigger_pct"] = _decimal_field(
            section, "average_trigger_pct", params["average_trigger_pct"]
        )
        params["max_layers"] = _int_field(
            section, "max_layers", params["max_layers"]
        )
        params["stop_pct"] = _decimal_field(section, "stop_pct", params["stop_pct"])
        params["sma_period"] = _int_field(
            section, "sma_period", params["sma_period"]
        )
        params["max_hold_bars"] = _int_field(
            section, "max_hold_bars", params["max_hold_bars"]
        )
        params["cooldown_bars"] = _int_field(
            section, "cooldown_bars", params["cooldown_bars"]
        )
        params["min_day_drop_pct"] = _decimal_field(
            section, "min_day_drop_pct", params["min_day_drop_pct"]
        )
        params["rsi_period"] = _int_field(
            section, "rsi_period", params["rsi_period"]
        )
        params["rsi_max"] = _decimal_field(section, "rsi_max", params["rsi_max"])
        params["close_range_max"] = _decimal_field(
            section, "close_range_max", params["close_range_max"]
        )
    env_map = {
        "MORNING_TAKE_PROFIT_PCT": ("take_profit_pct", Decimal),
        "MORNING_AVERAGE_TRIGGER_PCT": ("average_trigger_pct", Decimal),
        "MORNING_MAX_LAYERS": ("max_layers", int),
        "MORNING_STOP_PCT": ("stop_pct", Decimal),
        "MORNING_SMA_PERIOD": ("sma_period", int),
        "MORNING_MAX_HOLD_BARS": ("max_hold_bars", int),
        "MORNING_COOLDOWN_BARS": ("cooldown_bars", int),
        "MORNING_MIN_DAY_DROP_PCT": ("min_day_drop_pct", Decimal),
        "MORNING_RSI_PERIOD": ("rsi_period", int),
        "MORNING_RSI_MAX": ("rsi_max", Decimal),
        "MORNING_CLOSE_RANGE_MAX": ("close_range_max", Decimal),
    }
    for env_key, (name, caster) in env_map.items():
        if env.get(env_key):
            params[name] = caster(env[env_key])
    return params


def morning_from_config(
    env: Mapping[str, str],
    yaml_path: Path | None = DEFAULT_YAML,
) -> MorningBounceStrategy:
    return MorningBounceStrategy(**morning_params(env, _yaml_text(yaml_path)))


def abs_mom_params(
    env: Mapping[str, str],
    yaml_text: str | None = None,
) -> dict:
    params = {
        "lookback": ABS_MOM_LOOKBACK,
        "sma_period": ABS_MOM_SMA,
        "min_roc": ABS_MOM_MIN_ROC,
        "stop_pct": ABS_MOM_STOP,
        "trail_pct": ABS_MOM_TRAIL,
        "backtest_position_share": ABS_MOM_SHARE,
    }
    if yaml_text:
        section = _section(yaml_text, "abs_momentum")
        params["lookback"] = _int_field(section, "lookback", params["lookback"])
        params["sma_period"] = _int_field(
            section, "sma_period", params["sma_period"]
        )
        params["min_roc"] = _decimal_field(section, "min_roc", params["min_roc"])
        params["stop_pct"] = _decimal_field(section, "stop_pct", params["stop_pct"])
        params["trail_pct"] = _decimal_field(
            section, "trail_pct", params["trail_pct"]
        )
        params["backtest_position_share"] = _decimal_field(
            section,
            "backtest_position_share",
            params["backtest_position_share"],
        )
    env_map = {
        "ABS_MOM_LOOKBACK": ("lookback", int),
        "ABS_MOM_SMA_PERIOD": ("sma_period", int),
        "ABS_MOM_MIN_ROC": ("min_roc", Decimal),
        "ABS_MOM_STOP_PCT": ("stop_pct", Decimal),
        "ABS_MOM_TRAIL_PCT": ("trail_pct", Decimal),
        "ABS_MOM_POSITION_SHARE": ("backtest_position_share", Decimal),
    }
    for env_key, (name, caster) in env_map.items():
        if env.get(env_key):
            params[name] = caster(env[env_key])
    return params


def abs_mom_from_config(
    env: Mapping[str, str],
    yaml_path: Path | None = DEFAULT_YAML,
) -> AbsMomentumStrategy:
    return AbsMomentumStrategy(**abs_mom_params(env, _yaml_text(yaml_path)))


def active_strategies(env: Mapping[str, str], yaml_path: Path | None = DEFAULT_YAML):
    return [
        sma_from_config(env, yaml_path),
        donchian_from_config(env, yaml_path),
        rsi_from_config(env, yaml_path),
        scalp_from_config(env, yaml_path),
        overnight_from_config(env, yaml_path),
        morning_from_config(env, yaml_path),
        abs_mom_from_config(env, yaml_path),
    ]


def daily_strategies(env: Mapping[str, str], yaml_path: Path | None = DEFAULT_YAML):
    return [
        sma_from_config(env, yaml_path),
        donchian_from_config(env, yaml_path),
        rsi_from_config(env, yaml_path),
        overnight_from_config(env, yaml_path),
        morning_from_config(env, yaml_path),
        abs_mom_from_config(env, yaml_path),
    ]


def scalp_strategies(env: Mapping[str, str], yaml_path: Path | None = DEFAULT_YAML):
    return [scalp_from_config(env, yaml_path)]
