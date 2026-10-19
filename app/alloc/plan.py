"""Прозрачный план: equity → бюджет рукава → лимит на имя → пример лота."""

from __future__ import annotations

import os
from collections.abc import Mapping, Sequence
from decimal import Decimal

from app.alloc.capital import sleeve_capital
from app.alloc.view import ACTIVE_SLEEVES
from app.alloc.weights_store import load_weights
from app.risk.sleeve import DEFAULT_SLEEVE_SHARE
from app.strategy.abs_mom import (
    DEFAULT_EXIT_ROC as ABS_EXIT_ROC,
    DEFAULT_LOOKBACK as ABS_LOOKBACK,
    DEFAULT_MAX_STRETCH as ABS_STRETCH,
    DEFAULT_MIN_ROC as ABS_MIN_ROC,
    DEFAULT_SMA_PERIOD as ABS_SMA,
    DEFAULT_TRAIL_PCT as ABS_TRAIL,
    SLEEVE as ABS_MOM,
    SLEEVE_V2 as ABS_MOM2,
    SLEEVE_V3 as ABS_MOM3,
    SLEEVE_V4 as ABS_MOM4,
)
from app.strategy.donchian import DEFAULT_PERIOD, SLEEVE as DONCHIAN
from app.strategy.morning import (
    DEFAULT_MAX_HOLD_BARS as MORNING_MAX_HOLD,
    SLEEVE as MORNING,
)
from app.strategy.overnight import (
    DEFAULT_AVERAGE_TRIGGER_PCT,
    DEFAULT_COOLDOWN_BARS,
    DEFAULT_MAX_HOLD_BARS,
    DEFAULT_MAX_LAYERS,
    DEFAULT_MIN_DAY_DROP_PCT,
    DEFAULT_RSI_MAX,
    DEFAULT_SMA_PERIOD,
    DEFAULT_STOP_PCT as OVERNIGHT_STOP,
    DEFAULT_TAKE_PROFIT_PCT,
    SLEEVE as OVERNIGHT,
)
from app.strategy.rsi import (
    DEFAULT_OVERBOUGHT,
    DEFAULT_OVERSOLD,
    DEFAULT_PERIOD as RSI_PERIOD,
    SLEEVE as RSI,
)
from app.strategy.scalp import (
    DEFAULT_FAST as SCALP_FAST,
    DEFAULT_SLOW as SCALP_SLOW,
    DEFAULT_STOP_PCT as SCALP_STOP,
    SLEEVE as SCALP,
    TIMEFRAME as SCALP_TF,
)
from app.strategy.size import name_budget, position_qty
from app.strategy.sma import DEFAULT_FAST, DEFAULT_SLOW, SLEEVE as SMA
from app.strategy.stop import DEFAULT_STOP_PCT
from app.strategy.vol_scalp import (
    DEFAULT_AVERAGE_TRIGGER_PCT as VOL_AVG,
    DEFAULT_ATR_EXPAND as VOL_ATR_EXPAND,
    DEFAULT_ATR_PERIOD as VOL_ATR_PERIOD,
    DEFAULT_COOLDOWN_BARS as VOL_COOLDOWN,
    DEFAULT_MAX_HOLD_BARS as VOL_MAX_HOLD,
    DEFAULT_MAX_LAYERS as VOL_MAX_LAYERS,
    DEFAULT_MIN_ATR_PCT as VOL_MIN_ATR,
    DEFAULT_STOP_PCT as VOL_STOP,
    DEFAULT_TAKE_PROFIT_PCT as VOL_TP,
    SLEEVE as VOL_SCALP,
    TIMEFRAME as VOL_TF,
)

SLEEVE_HOWTO = {
    SMA: {
        "title": "Пересечение средних",
        "horizon": "дневки",
        "signal": (
            f"На закрытии дня сравнивает SMA {DEFAULT_FAST} и SMA {DEFAULT_SLOW}. "
            "Пересечение вверх — покупка, вниз — продажа, иначе плоско."
        ),
        "holds": (
            "Держит одну позицию на тикер из вселенной, пока нет сигнала sell/exit "
            "или стопа. Не делит портфель по секторам."
        ),
    },
    DONCHIAN: {
        "title": "Пробой Дончиана",
        "horizon": "дневки",
        "signal": (
            f"Канал по max/min за {DEFAULT_PERIOD} дней. Закрытие выше верха — покупка, "
            "ниже низа — продажа, внутри канала — плоско."
        ),
        "holds": (
            "Та же модель капитала, что у других рукавов: лимит на имя и стоп. "
            "Секторов нет — только тикеры активной вселенной."
        ),
    },
    RSI: {
        "title": "RSI-возврат",
        "horizon": "дневки",
        "signal": (
            f"RSI({RSI_PERIOD}): ≤{DEFAULT_OVERSOLD} — покупка (перепроданность), "
            f"≥{DEFAULT_OVERBOUGHT} — продажа (перекупленность), иначе плоско."
        ),
        "holds": (
            "Mean-reversion: входит против экстремума индикатора, выходит по обратному "
            "сигналу или стопу. Секторов нет."
        ),
    },
    SCALP: {
        "title": "EMA-скальп",
        "horizon": SCALP_TF,
        "signal": (
            f"На {SCALP_TF} сравнивает EMA {SCALP_FAST} и EMA {SCALP_SLOW}. "
            f"Пересечение вверх — покупка, вниз — продажа. Стоп {float(SCALP_STOP)*100:g}%."
        ),
        "holds": (
            "Короткий горизонт: те же лимиты капитала на имя, но быстрее оборачивает "
            "позицию. Нужны свечи M15 (CANDLE_M15_DIR)."
        ),
    },
    VOL_SCALP: {
        "title": "Волатильный скальп",
        "horizon": VOL_TF,
        "signal": (
            f"На {VOL_TF}: выше SMA тренда; ATR({VOL_ATR_PERIOD})/close ≥ "
            f"{float(VOL_MIN_ATR)*100:g}% и ≥ {float(VOL_ATR_EXPAND):g}× нормы; "
            f"импульсный зелёный. В минусе — усреднение каждые "
            f"−{float(VOL_AVG)*100:g}% (до {VOL_MAX_LAYERS} слоёв) только пока ATR живой. "
            f"Выход: тейк +{float(VOL_TP)*100:g}% от средней или возврат к средней "
            f"(стоп {'выкл' if float(VOL_STOP) == 0 else f'{float(VOL_STOP)*100:g}%'})."
        ),
        "holds": (
            "Усредняем в живой волатильности; из мешка выходим от средней или по тейку. "
            "Нужны M10 ~2г (CANDLE_M10_DIR), иначе fallback на M15."
        ),
    },
    OVERNIGHT: {
        "title": "Вечерний докуп",
        "horizon": "дневки",
        "signal": (
            f"Вход на close только после зелёного дня: красный день ≤ "
            f"−{float(DEFAULT_MIN_DAY_DROP_PCT)*100:g}%, close внизу диапазона, "
            f"≤ SMA{DEFAULT_SMA_PERIOD}, RSI≤{float(DEFAULT_RSI_MAX):g}. "
            f"Тейк +{float(DEFAULT_TAKE_PROFIT_PCT)*100:g}%, стоп "
            f"{float(OVERNIGHT_STOP)*100:g}% от первой цены, удержание "
            f"{DEFAULT_MAX_HOLD_BARS} бара, усреднение до {DEFAULT_MAX_LAYERS} слоёв "
            f"при −{float(DEFAULT_AVERAGE_TRIGGER_PCT)*100:g}%, пауза "
            f"{DEFAULT_COOLDOWN_BARS} дней после стопа."
        ),
        "holds": (
            "Защитный overnight: не покупает каждый вечер и не усредняет бесконечно. "
            "На выборке blue chips скорее около нуля, чем «печатный станок». "
            "Модель по дневному OHLC — не тиковый стакан."
        ),
    },
    MORNING: {
        "title": "Утренний докуп",
        "horizon": "дневки",
        "signal": (
            f"После слабого дня (те же фильтры, что у вечернего) покупаем на "
            f"следующем open. Днём тейк +{float(DEFAULT_TAKE_PROFIT_PCT)*100:g}% / "
            f"стоп {float(OVERNIGHT_STOP)*100:g}% от первой цены. Под вечер "
            f"продаём по close; если просадка ≥{float(DEFAULT_AVERAGE_TRIGGER_PCT)*100:g}% — "
            f"держим ночь и утром докупаем (до {DEFAULT_MAX_LAYERS} слоёв). "
            f"Макс. удержание {MORNING_MAX_HOLD} бара, пауза "
            f"{DEFAULT_COOLDOWN_BARS} дней после стопа."
        ),
        "holds": (
            "Зеркало вечернего рукава: вход утром, выход к вечеру. "
            "Усреднение — только если к close всё ещё в минусе. "
            "Модель open/close на днёвках."
        ),
    },
    ABS_MOM: {
        "title": "Абс. моментум",
        "horizon": "дневки",
        "signal": (
            f"Вход: close > SMA{ABS_SMA}, ROC({ABS_LOOKBACK}) ≥ "
            f"{float(ABS_MIN_ROC)*100:g}% и close/SMA ≤ {float(ABS_STRETCH):g} "
            f"(без перегрева). Выход мягче: ROC < {float(ABS_EXIT_ROC)*100:g}% "
            f"или ниже SMA; трейл {float(ABS_TRAIL)*100:g}% от пика. "
            "Иначе кэш. Сетка MOEX+S&P desk 2024–2026."
        ),
        "holds": (
            "Гистерезис + анти-FOMO: не гонится за растяжкой, дольше держит тренд. "
            "Desk-бэктест на полный кэш имени. In-sample — не гарантия вперёд."
        ),
    },
    ABS_MOM2: {
        "title": "Абс. моментум-2",
        "horizon": "дневки",
        "signal": (
            "Вход: close > SMA40, ROC20 ≥ +2%, close/SMA ≤ 1.10, оборот дня "
            "не ниже среднего за 20 дней, день не вырос больше 7% и выше SMA40 "
            "хотя бы 45% списка этого рынка. Для бумаги из файлов S&P широта "
            "считается по ним, не по календарю TQBR. Выход по ROC < −2% два дня "
            "подряд (прокол SMA не продаёт) и по трейлу 4% после +20% от входа. "
            "На TQBR 2024–2026 это +25.2%. Это история, не обещание вперёд."
        ),
        "holds": (
            "Первая версия не трогается. Трейл молчит, пока бумага не дала +20%, "
            "чтобы откат к средней не выбивал тренд. In-sample — не гарантия вперёд."
        ),
    },
    ABS_MOM3: {
        "title": "Абс. моментум-3",
        "horizon": "дневки",
        "signal": (
            "Вход: close > SMA30, ROC15 ≥ 0, close/SMA ≤ 1.10, оборот от 60% "
            "среднего за 20 дней, день не выше +7%, широта этого рынка ≥ 45%. "
            "Для S&P широта по файлам S&P и их датам. Выход после четырёх дней "
            "с ROC < −1% и трейл 4% после +20% от входа. На TQBR 2024–2026 "
            "это около +30.8%. Это история, не обещание вперёд."
        ),
        "holds": (
            "Вторая версия не менялась. Третья короче смотрит тренд и дольше "
            "терпит слабый день. In-sample — не гарантия вперёд."
        ),
    },
    ABS_MOM4: {
        "title": "Абс. моментум-4",
        "horizon": "дневки",
        "signal": (
            "Как абсолютный моментум-3, но вход при широте этого рынка от 42%, "
            "не от 45%. Остальное то же: SMA30, ROC15 ≥ 0, оборот от 60% "
            "среднего, день не выше +7%. Для S&P широта по файлам S&P и их "
            "датам. Выход после четырёх дней с ROC < −1%, трейл 4% после +20%. "
            "На TQBR 2024–2026 около +31.3%. Это история, не обещание вперёд."
        ),
        "holds": (
            "Третья версия осталась на пороге 45% и +30.8%. Сдвиг широты "
            "до 42% — единственное, что обогнало её на обеих половинах выборки. "
            "In-sample — не гарантия вперёд."
        ),
    },
}


def _money(value: Decimal) -> float:
    return float(Decimal(value).quantize(Decimal("0.01")))


def _pct_env(name: str, default: Decimal) -> Decimal:
    raw = os.environ.get(name)
    if not raw:
        return Decimal(default)
    return Decimal(str(raw))


def risk_params() -> dict[str, Decimal]:
    from app.risk.params_store import load_name_share

    return {
        "sleeve_share": _pct_env("SLEEVE_SHARE", DEFAULT_SLEEVE_SHARE),
        "name_share": load_name_share(),
        "stop_pct": _pct_env("STOP_PCT", DEFAULT_STOP_PCT),
    }


def allocation_plan(
    *,
    equity: Decimal,
    sleeves: Sequence[str] = ACTIVE_SLEEVES,
    weights: Mapping[str, Decimal] | None = None,
    example_price: Decimal = Decimal("250"),
    lot: int = 1,
) -> dict:
    params = risk_params()
    sleeve_share = params["sleeve_share"]
    name_share = params["name_share"]
    stop_pct = params["stop_pct"]
    resolved = dict(weights) if weights is not None else load_weights(sleeves)
    pool = Decimal(equity) * sleeve_share
    max_names = int(Decimal("1") // name_share) if name_share > 0 else 0
    items = []
    for name in sleeves:
        weight = Decimal(str(resolved.get(name, "0")))
        capital = sleeve_capital(equity, weight=weight, sleeve_share=sleeve_share)
        per_name = name_budget(capital, name_share)
        qty = position_qty(
            capital=capital,
            price=example_price,
            lot=lot,
            name_share=name_share,
        )
        notional = Decimal(qty) * example_price * Decimal(lot)
        howto = SLEEVE_HOWTO.get(name, {})
        items.append(
            {
                "sleeve": name,
                "title": howto.get("title") or name,
                "horizon": howto.get("horizon") or "дневки",
                "signal": howto.get("signal") or "",
                "holds": howto.get("holds") or "",
                "weight": float(weight),
                "capital": _money(capital),
                "name_budget": _money(per_name),
                "max_concurrent_names": max_names,
                "stop_pct": float(stop_pct),
                "example": {
                    "price": _money(example_price),
                    "lot": lot,
                    "qty": qty,
                    "notional": _money(notional),
                },
            }
        )
    return {
        "equity": _money(equity),
        "trading_pool": _money(pool),
        "sleeve_share": float(sleeve_share),
        "name_share": float(name_share),
        "stop_pct": float(stop_pct),
        "max_concurrent_names": max_names,
        "sectors": None,
        "sectors_note": (
            "Модели секторов в лаборатории нет. Периметр — активная вселенная тикеров "
            "(сито ликвидности/валюты), а не «нефть 20% / банки 30%»."
        ),
        "formula": (
            "бюджет_рукава = equity × потолок_рукава × доля; "
            "лимит_на_имя = бюджет_рукава × доля_имени; "
            "qty = ⌊лимит_на_имя / (цена × лот)⌋"
        ),
        "sleeves": items,
    }
