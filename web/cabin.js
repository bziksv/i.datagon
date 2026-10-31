(function () {
  "use strict";

  /** Версия UI кабинета (этап 30+). Не путать с version API. */
  var CABIN_UI_VERSION = "v3.3.31";

  var ROUTES = [
    {
      id: "home",
      title: "Среды",
      group: "fork",
      hint: "Тест или работа",
      intro: "Слева проверка стратегий. Справа счёт у брокера.",
    },
    {
      id: "candles",
      title: "Свечи",
      group: "test",
      hint: "Форматы под стратегии",
      intro: "Дневки, 15 минут и 10 минут — те файлы, на которых гоняют рукава.",
    },
    {
      id: "overview",
      title: "Обзор",
      group: "start",
      step: "1",
      hint: "Контур жив",
      intro:
        "Сводка лаборатории: живость системы, деньги, решения, которые ждут вас, и состояние рукавов.",
    },
    {
      id: "portfolio",
      title: "Портфель",
      group: "start",
      step: "5",
      hint: "Книга после решений",
      intro:
        "Тестовая книга лаборатории: где лежат деньги и какие позиции открыты. Это не экран приложения брокера.",
    },
    {
      id: "strategies",
      title: "Стратегии",
      group: "start",
      step: "3",
      hint: "Прогон рукава",
      intro: "",
    },
    {
      id: "companies",
      title: "Компании",
      group: "aside",
      hint: "По отраслям",
      intro:
        "Кого показатели выделяют внутри отрасли. Скор ≥70 — рекомендуем смотреть; это аналитика лаборатории, не сигнал брокера.",
    },
    {
      id: "whatif",
      title: "Если бы",
      group: "test",
      hint: "Купил и держал",
      intro:
        "Бюджет и дата покупки → что было бы сегодня, если просто купить выбранные бумаги. Заявка не ставится.",
    },
    {
      id: "recommendations",
      title: "Рекомендации",
      group: "aside",
      hint: "Скор, не рукав",
      intro:
        "Топ имён по фундаментальному скору → paper-план по свежей цене и лоту → вы решаете в Агентах. Аналитика лаборатории, не ИК.",
    },
    {
      id: "agents",
      title: "Агенты",
      group: "start",
      step: "4",
      hint: "Принять или отклонить",
      intro:
        "Очередь решений: агент или Рекомендации предлагают план → вы принимаете или отклоняете → paper в Журнале. В T‑Invest ничего не уходит.",
    },
    {
      id: "news",
      title: "Новости",
      group: "aside",
      hint: "Сделки не открывает",
      intro:
        "Внешний информационный контур. Новости не открывают сделки сами. Research считается offline.",
    },
    {
      id: "market",
      title: "Рынок",
      group: "aside",
      hint: "Периметр и стоп-правила",
      intro:
        "Периметр торговли: какие бумаги допущены и какие правила режут ордера.",
    },
    {
      id: "journal",
      title: "Журнал",
      group: "start",
      step: "6",
      hint: "Что записала книга",
      intro: "Факт лабораторной истории: ордера и проводки книги.",
    },
    {
      id: "work",
      title: "Песочница T-Invest",
      group: "work",
      hint: "Песочница T-Invest",
      intro:
        "Песочницы T-Invest: игровые деньги брокера, у каждой свой счёт и одна дневная стратегия. Боевой счёт не подключён.",
    },
    {
      id: "settings",
      title: "Настройки",
      group: "start",
      step: "2",
      hint: "Депозит и лимит",
      intro:
        "Капитал лаборатории: депозит (торговый кэш) и максимум на одну бумагу. Бюджеты рукавов — в Стратегиях.",
    },
    {
      id: "help",
      title: "Помощь",
      group: "aside",
      hint: "Справочник",
      intro:
        "Карта кабинета, легенда статусов, словарь терминов и управление обучением.",
    },
  ];

  /** Основные вкладки на мобиле; остальное — в «Ещё» (G3). */
  var MOBILE_PRIMARY_IDS = [
    "overview",
    "settings",
    "strategies",
    "agents",
  ];
  var MOBILE_MORE_IDS = [
    "portfolio",
    "journal",
    "companies",
    "recommendations",
    "market",
    "news",
    "help",
  ];
  var lastFundamentals = null;
  var lastCompaniesNote = "";
  var lastCandlesCoverage = null;
  var lastCompaniesSector = "all";
  var lastFundMode = "all";
  var lastFundLens = "strong";
  var lastCompaniesQuery = "";
  var lastCandleFilter = "gaps";
  var lastCandleQuery = "";
  var lastCandleTf = "1d";
  var candlePullNote = "";
  var candleLog = [];
  var candleJob = null;
  var candleFillPollTimer = null;
  var CANDLE_TF_HINT = {
    "1d": "Пересечение средних, Дончиан, RSI, докупы, моментум",
    "15m": "EMA-скальп",
    "10m": "Волатильный скальп",
  };
  var companiesPollTimer = null;
  var COMPANIES_POLL_MS = 10 * 60 * 1000;
  var lastRecommendations = null;
  var SETTINGS_TOUR_KEY = "settings";

  var TOKEN_KEY = "app_token";
  var REMEMBER_KEY = "cabin_remember_token";
  var MENU_TOUR_KEY = "menu";
  var GATE_TOUR_KEY = "gate";
  var HELP_TOUR_KEY = "help-demo";
  var OVERVIEW_TOUR_KEY = "overview";
  var PORTFOLIO_TOUR_KEY = "portfolio";
  var STRATEGIES_TOUR_KEY = "strategies";
  var AGENTS_TOUR_KEY = "agents";
  var NEWS_TOUR_KEY = "news";
  var MARKET_TOUR_KEY = "market";
  var JOURNAL_TOUR_KEY = "journal";
  var portfolioTab = "capital";
  var newsTab = "feed";
  var marketTab = "universe";
  var journalTab = "orders";
  var newsFilterTicker = "";
  var newsSearch = "";
  var orderFilterStatus = "";
  var orderFilterSleeve = "";
  var orderFilterTicker = "";
  var lastNews = [];
  var lastStudies = [];
  var lastUniverse = null;
  var lastOrders = [];
  var lastLedger = [];
  var agentsFocusProposed = false;
  var lastAgentsFlash = null;
  var lastDeskBacktest = null;
  var lastDeskBatch = null;
  var lastDeskBatchOpen = null;
  var lastDeskBatchSleeves = null;
  var lastDeskBatchTickers = null;
  var lastDeskSleeve = "sma_cross";
  var lastDeskTicker = "SBER";
  var lastDeskTickers = [];
  var lastDeskGroups = { moex: [], sp500: [], sectors: [], default_tickers: [] };

  function applyDeskCandleUniverse(data) {
    lastDeskTickers = (data && data.tickers) || [];
    var groups = (data && data.groups) || {};
    lastDeskGroups = {
      moex: groups.moex || [],
      sp500: groups.sp500 || [],
      sectors: groups.sectors || [],
      default_tickers: groups.default_tickers || [],
    };
    if (
      lastDeskTickers.length &&
      lastDeskTickers.indexOf(lastDeskTicker) < 0
    ) {
      lastDeskTicker = lastDeskTickers[0];
    }
  }
  var deskListTried = false;
  var lastWhatIfCapital = 1000000;
  var lastWhatIfStart = "";
  var lastWhatIfTickers = null;
  var lastWhatIfAmounts = null;
  var lastWhatIfEqual = true;
  var lastWhatIfResult = null;
  var lastWhatIfBusy = false;
  var whatifListTried = false;
  var loadErrors = {};
  var blockLoading = {};
  var routeLoading = false;
  var refreshBusy = false;
  var FETCH_TIMEOUT_MS = 12000;
  // Полный TQBR × M10 не укладывался в 10 минут: страница обрывала уже идущий расчёт.
  var FETCH_TIMEOUT_BATCH_MS = 1800000;
  var confirmResolver = null;
  var confirmReturnFocus = null;
  var mobileMoreOpen = false;
  var LEDGER_ACCOUNT_RU = {
    trading_cash: "торговый кэш",
    vault: "сейф прибыли",
  };
  var LEDGER_REASON_RU = {
    deposit: "депозит",
    commission: "комиссия",
    fill: "сделка",
    vault: "отчисление в сейф",
  };
  var ORDER_STATUS_RU = {
    new: "новый",
    rejected: "отклонён",
    filled: "исполнен",
    partially_filled: "частично исполнен",
    cancelled: "отменён",
    unknown: "статус неизвестен",
    reconciled: "сверен",
    cancel_pending: "отмена ожидается",
  };
  var MARK_QUALITY_RU = {
    fresh: "актуальная",
    good: "актуальная",
    stale: "устарела",
    missing: "нет цены",
  };
  var ORDER_REJECT_RU = {
    killed: "Отклонено: включён стоп торговли",
    outside_universe: "Отклонено: тикера нет в активной вселенной",
    not_in_universe: "Отклонено: тикера нет в активной вселенной",
    name_weight: "Отклонено: слишком большая доля одной бумаги",
    sleeve_weight: "Отклонено: превышен лимит капитала рукава",
    daily_loss: "Отклонено: сработал дневной лимит убытка",
    already_entered: "Отклонено: повторный вход в тот же бар",
    once_per_bar: "Отклонено: повторный вход в тот же бар",
    earnings_day: "Отклонено: день отчёта эмитента (veto)",
    earnings_window: "Отклонено: день отчёта эмитента (veto)",
    broker_unavailable: "Отклонено: брокер недоступен",
    kill_switch: "Отклонено: включён стоп торговли",
  };
  var UNIVERSE_REASON_RU = {
    "tradable,rub,lot,liquid": "прошла сито: торгуемая, рубль, лот, ликвидность",
    not_tradable: "не торгуется сейчас",
    not_rub_or_lot: "не рубль или нет лота",
    illiquid: "слабая ликвидность",
    weak_fundamental: "слабый фундамент (сито включено)",
    over_universe_max: "не влезла в лимит вселенной",
  };
  var ACTIVE_SLEEVE_IDS = [
    "sma_cross",
    "donchian_breakout",
    "rsi_reversion",
    "ema_scalp",
    "vol_scalp",
    "overnight_bounce",
    "morning_bounce",
    "abs_momentum",
    "abs_momentum_2",
    "abs_momentum_3",
    "abs_momentum_4",
    "abs_momentum_5",
  ];
  var SLEEVE_GROUPS = [
    { title: "Дневные", ids: ["sma_cross", "donchian_breakout", "rsi_reversion"] },
    { title: "Скальп", ids: ["ema_scalp", "vol_scalp"] },
    { title: "Докуп", ids: ["overnight_bounce", "morning_bounce"] },
    { title: "Моментум", ids: ["abs_momentum", "abs_momentum_2", "abs_momentum_3", "abs_momentum_4", "abs_momentum_5"] },
  ];
  var SLEEVE_LINE = {
    sma_cross: "Дневки. Быстрая средняя пересекла медленную.",
    donchian_breakout: "Дневки. Цена вышла из канала.",
    rsi_reversion: "Дневки. Покупка, когда бумага слишком упала, продажа — когда слишком выросла.",
    ema_scalp: "Свечи 15 минут. Короткие пересечения средних.",
    vol_scalp: "Свечи 10 минут. Вход, когда рынок разгоняется.",
    overnight_bounce: "Дневки. Покупка вечером после слабого дня.",
    morning_bounce: "Дневки. Покупка утром после слабого дня.",
    abs_momentum: "Дневки. Покупка в силе, без перегрева.",
    abs_momentum_2: "Как моментум, плюс фильтр: рынок в целом должен быть сильным.",
    abs_momentum_3: "Короче окно и мягче выход.",
    abs_momentum_4: "Как моментум-3, порог широты чуть ниже. Эта стратегия стоит в рабочей среде.",
    abs_momentum_5: "Как моментум-4, плюс шорты слабых бумаг при узком рынке.",
  };
  var SLEEVE_NAMES = {
    sma_cross: "Пересечение средних",
    donchian_breakout: "Пробой Дончиана",
    rsi_reversion: "RSI-возврат",
    ema_scalp: "EMA-скальп",
    vol_scalp: "Волатильный скальп",
    overnight_bounce: "Вечерний докуп",
    morning_bounce: "Утренний докуп",
    abs_momentum: "Абс. моментум",
    abs_momentum_2: "Абс. моментум-2",
    abs_momentum_3: "Абс. моментум-3",
    abs_momentum_4: "Абс. моментум-4",
    abs_momentum_5: "Абс. моментум-5",
    fund_screener: "Фундамент-скринер",
  };
  var authed = false;
  var lastStatus = null;
  var lastStatusAt = null;
  var lastCapital = null;
  var lastWeeklyReport = null;
  var lastAudit = null;
  var lastAdmission = null;
  var lastUnknownOrders = [];
  var lastProposals = [];
  var lastSleeves = [];
  var lastVault = null;
  var lastAllocation = null;
  var lastAllocPlan = null;
  var lastDrift = null;
  var lastSleeveDetail = null;
  var sleeveDetailLoading = false;
  var sandboxCashKnown = null;
  var signalFilterTicker = "";
  var signalFilterKind = "";
  var planExamplePrice = 250;
  var planWhatIfCapital = "";
  var currentRoute = "overview";
  var SLEEVE_HOWTO = {
    sma_cross:
      "На дневках сравнивает быструю и медленную скользящие средние. Пересечение вверх — покупка, вниз — продажа; иначе рукав остаётся в плоскости.",
    donchian_breakout:
      "Строит канал по максимумам и минимумам за период. Закрытие выше верхней границы — покупка, ниже нижней — продажа; внутри канала — плоско.",
    rsi_reversion:
      "Дневной RSI(14): ниже 30 — покупка (перепроданность), выше 70 — продажа (перекупленность); иначе плоско. Mean-reversion.",
    ema_scalp:
      "Скальп на M15: пересечение EMA 3/8. Короткий стоп 1.5%. Нужны свечи в CANDLE_M15_DIR (data/candles_m15).",
    vol_scalp:
      "M10 (~2г): вход выше SMA100 + ATR↑ + импульс. В минусе усредняем каждые −0.5% (до 6 слоёв) только пока рынок волатильный; тейк +1% или выход от средней. Нужны M10.",
    overnight_bounce:
      "Защитный overnight: вход только после зелёного дня, на красном ≤−1%, close внизу диапазона, ≤SMA5 и RSI≤40. Тейк +3.5%, стоп 3.5% от первой цены, удержание 2 бара, редкое усреднение 2-м слоем, пауза 5 дней после стопа.",
    morning_bounce:
      "Зеркало вечернего: после слабого дня покупаем на следующем open, днём тейк/стоп 3.5%, под вечер продаём по close; если в минусе — утром докупаем 2-м слоем. Пауза 5 дней после стопа.",
    abs_momentum:
      "Вход только в силе без перегрева: close > SMA40, ROC20 ≥ +2% и close/SMA ≤ 1.10. Выход мягче (ROC < −1% или ниже SMA) + трейл 10% от пика. Гистерезис и анти-FOMO — сетка MOEX+S&P 2024–2026; desk на полный кэш имени.",
    abs_momentum_2:
      "Вход как у абсолютного моментума, плюс оборот, день не выше +7% и фильтр широты: покупаем, только если выше SMA40 хотя бы 45% списка этого рынка. Для S&P список — файлы S&P, не календарь TQBR. Слабый ROC один день ещё держим, выход со второго. Трейл 4% после +20% от входа. На TQBR 2024–2026 это +25.2%. Это история, не обещание вперёд.",
    abs_momentum_3:
      "SMA30 и ROC15 ≥ 0, оборот от 60% среднего, день не выше +7%, широта этого рынка ≥ 45%. Для S&P широта по файлам S&P и их датам. Слабый ROC держим три дня, выход с четвёртого (порог −1%). Трейл 4% после +20%. На TQBR 2024–2026 около +30.8%. Это история, не обещание вперёд.",
    abs_momentum_4:
      "Как абсолютный моментум-3, но широта этого рынка от 42%, не от 45%. Для S&P широта по файлам S&P и их датам. На TQBR 2024–2026 около +31.3%. Это история, не обещание вперёд.",
    abs_momentum_5:
      "Длинная сторона как у моментума-4. Шорты — зеркало слабой бумаги при широте рынка не выше 35%, стоп 5% выше входа, не больше четверти счёта. За ночь — плата Т-Банка по ступеням. На ядре с 2023 шорты с этой платой дают около +15.9% против +30.2% у четвёртой. Это история, не обещание вперёд.",
  };
  var SIGNAL_KIND_RU = {
    buy: "покупка",
    sell: "продажа",
    flat: "плоско",
    exit: "выход",
  };

  function byId(id) {
    return document.getElementById(id);
  }

  function escapeHtml(value) {
    return String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function formatNow() {
    return new Date().toLocaleString("ru-RU", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  }

  function dateTimeLabel(iso) {
    if (!iso) return "—";
    var value = new Date(iso);
    if (isNaN(value.getTime())) return String(iso);
    return value.toLocaleString("ru-RU", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  function humanBeat(iso) {
    if (!iso) return "ещё не откликался";
    var beat = new Date(iso);
    if (isNaN(beat.getTime())) return "время неизвестно";
    var sec = Math.max(0, Math.round((Date.now() - beat.getTime()) / 1000));
    if (sec < 60) return sec + " с назад";
    var min = Math.round(sec / 60);
    if (min < 60) return min + " мин назад";
    var hours = Math.round(min / 60);
    return hours + " ч назад";
  }

  function whatis(title, text) {
    return (
      '<span class="whatis" tabindex="0" data-tip="' +
      escapeHtml(text) +
      '" aria-label="' +
      escapeHtml(title + ": " + text) +
      '">?</span>'
    );
  }

  function pillHtml(label, value, tone, tip) {
    return (
      '<div class="status-pill">' +
      '<div class="k">' +
      "<span>" +
      escapeHtml(label) +
      "</span>" +
      (tip ? whatis(label, tip) : "") +
      "</div>" +
      '<div class="v"><span class="dot ' +
      tone +
      '"></span><span>' +
      escapeHtml(value) +
      "</span></div></div>"
    );
  }

  function intervalRu(sec) {
    var n = Number(sec) || 0;
    if (n < 1) return "";
    if (n === 3600) return "час";
    if (n === 86400) return "сутки";
    if (n < 60) return n + " с";
    if (n < 3600) return Math.round(n / 60) + " мин";
    if (n % 86400 === 0) return n / 86400 + " сут";
    if (n % 3600 === 0) return n / 3600 + " ч";
    return (n / 3600).toLocaleString("ru-RU", { maximumFractionDigits: 1 }) + " ч";
  }

  function humanUntil(iso) {
    if (!iso) return "";
    var at = new Date(iso);
    if (isNaN(at.getTime())) return "";
    var sec = Math.max(0, Math.round((at.getTime() - Date.now()) / 1000));
    if (sec < 60) return "через " + sec + " с";
    var min = Math.round(sec / 60);
    if (min < 60) return "через " + min + " мин";
    return "через " + Math.round(min / 60) + " ч";
  }

  function rememberRefresh(kind, refresh) {
    if (!refresh) return;
    lastStatus = lastStatus || {};
    lastStatus.refresh = lastStatus.refresh || {};
    lastStatus.refresh[kind] = refresh;
    if (authed) renderStatus(lastStatus, {});
  }

  function refreshModTone(mod) {
    if (!mod || !mod.enabled) return "warn";
    if (!mod.last_at) return "warn";
    if (mod.next_at) return "ok";
    return "warn";
  }

  function refreshPillHtml(label, mod, tipLead, manual) {
    var enabled = !!(mod && mod.enabled);
    var pace = enabled
      ? "раз в " + (intervalRu(mod.interval_sec) || "—")
      : "выкл.";
    var last = mod && mod.last_at ? humanBeat(mod.last_at) : "ещё не было";
    var next = !enabled
      ? "только вручную"
      : mod.next_at
        ? humanUntil(mod.next_at)
        : "в очереди у воркера";
    var tip =
      tipLead +
      " Последний прогон — " +
      last +
      ". Следующий — " +
      next +
      ". Вручную: «" +
      manual +
      "».";
    return pillHtml(label, pace + " · " + last, refreshModTone(mod), tip);
  }

  function mirrorPillHtml(mod) {
    var last = mod.last_at ? humanBeat(mod.last_at) : "ещё не было";
    var failed = mod.ok === false;
    var text = failed ? "ошибка · последняя " + last : "раз в " + (intervalRu(mod.interval_sec) || "—") + " · " + last;
    var tip =
      "Локаль — зеркало прода: свечи, песочницы, сигналы, фундаментал и отметки счёта забираются с сервера " +
      (mod.source ? "(" + mod.source + ") " : "") +
      "автоматически, на сервере ничего не меняется. Сама локаль ничего не качает и не торгует." +
      (failed && mod.error ? " Ошибка последней попытки: " + mod.error : "");
    return pillHtml("С прода", text, failed ? "bad" : mod.last_at ? "ok" : "warn", tip);
  }

  function renderStatus(data, meta) {
    var strip = byId("status-strip");
    if (!strip) return;
    var alive = !!(data && data.worker_alive);
    var killed = !!(data && data.killed);
    var agents = !!(data && data.agents_enabled);
    var refresh = (data && data.refresh) || {};
    var systemTone = meta && meta.error ? "bad" : "ok";
    var systemText =
      meta && meta.error
        ? meta.error
        : data && data.status === "ok"
          ? "связь есть"
          : "нет ответа";
    var mirror = refresh.mirror || {};
    var workerTone = alive || mirror.enabled ? "ok" : "warn";
    var workerText = mirror.enabled
      ? "на проде · здесь выключен"
      : alive
        ? "на связи · " + humanBeat(data.worker_beat)
        : "нет связи · " + humanBeat(data && data.worker_beat);
    var tradeTone = killed ? "bad" : "ok";
    var tradeText = killed
      ? "стоп включён · новые ордера нельзя"
      : "можно выставлять";
    var agentsTone = agents ? "ok" : "warn";
    var agentsText = agents ? "включены" : "выключены";

    strip.innerHTML = [
      pillHtml(
        "Система",
        systemText,
        systemTone,
        "Ответ API кабинета. Если связи нет — страница не получает свежие данные."
      ),
      pillHtml(
        "Воркер",
        workerText,
        workerTone,
        "Фоновый процесс: свечи, цифры компаний, сигналы. Время — когда последний раз отозвался."
      ),
      pillHtml(
        "Торговля",
        tradeText,
        tradeTone,
        "Стоп-кран лаборатории. При стопе новые ордера отклоняются; уже открытые позиции сами не закрываются."
      ),
      pillHtml(
        "Агенты",
        agentsText,
        agentsTone,
        "Фоновые агенты могут класть предложения в очередь. Принимаете или отклоняете вы."
      ),
      refreshPillHtml(
        "Свечи",
        refresh.candles || {},
        "Воркер сам докачивает дневки, 15 минут и 10 минут по всем бумагам.",
        "Докачать"
      ),
      refreshPillHtml(
        "Компании",
        refresh.fundamentals || {},
        "Воркер тянет P/E, P/B, EPS, ROE, дивиденд и капитализацию с брокера.",
        "Обновить с брокера"
      ),
    ].concat(mirror.enabled ? [mirrorPillHtml(mirror)] : []).join("");
    strip.classList.toggle("has-mirror", !!mirror.enabled);

    var env = (data && data.env) || "dev";
    byId("env-badge").textContent = env === "prod" ? "бой" : "песочница";
    syncKillControls(killed);
    var footer = byId("app-footer");
    if (meta && meta.error) {
      footer.textContent =
        "Данные paper-книги · статус не обновлён · " + meta.error + " · " + formatNow();
      strip.classList.add("is-stale");
    } else {
      footer.textContent =
        "Данные paper-книги лаборатории · статус обновлён " +
        formatNow() +
        " · кабинет " +
        CABIN_UI_VERSION +
        (data && data.version ? " · API v" + data.version : "");
      strip.classList.remove("is-stale");
    }
  }

  function syncKillControls(killed) {
    var killBtn = byId("btn-kill");
    var unkillBtn = byId("btn-unkill");
    var banner = byId("kill-banner");
    if (!killBtn || !unkillBtn || !banner) return;
    killBtn.hidden = !!killed;
    unkillBtn.hidden = !killed;
    banner.hidden = !killed;
  }

  function closeConfirm(result) {
    var modal = byId("confirm-modal");
    modal.hidden = true;
    var resolve = confirmResolver;
    confirmResolver = null;
    var returnTo = confirmReturnFocus;
    confirmReturnFocus = null;
    if (resolve) resolve(result);
    if (returnTo && typeof returnTo.focus === "function") {
      window.setTimeout(function () {
        try {
          returnTo.focus();
        } catch (e) {}
      }, 0);
    }
  }

  function askConfirm(options) {
    return new Promise(function (resolve) {
      confirmResolver = resolve;
      confirmReturnFocus = document.activeElement;
      byId("confirm-title").textContent = options.title;
      byId("confirm-text").textContent = options.text;
      var ok = byId("confirm-ok");
      ok.textContent = options.okLabel || "Подтвердить";
      ok.className = options.danger === false ? "primary" : "danger";
      byId("confirm-modal").hidden = false;
      ok.focus();
    });
  }

  function wrapTableScroll(html, stickyFirst) {
    if (!html || html.indexOf("<table") === -1) return html || "";
    return (
      '<div class="table-scroll' +
      (stickyFirst ? " is-sticky-first" : "") +
      '" tabindex="0" role="region" aria-label="Таблица, прокрутка вбок">' +
      html +
      "</div>"
    );
  }

  function routeById(id) {
    for (var i = 0; i < ROUTES.length; i++) {
      if (ROUTES[i].id === id) return ROUTES[i];
    }
    return null;
  }

  function closeMobileMore() {
    var panel = byId("mobile-more");
    if (!panel) return;
    panel.hidden = true;
    mobileMoreOpen = false;
    var btn = byId("mobile-more-btn");
    if (btn) btn.setAttribute("aria-expanded", "false");
  }

  function openMobileMore() {
    var panel = byId("mobile-more");
    if (!panel) return;
    panel.hidden = false;
    mobileMoreOpen = true;
    var btn = byId("mobile-more-btn");
    if (btn) btn.setAttribute("aria-expanded", "true");
    var closeBtn = byId("mobile-more-close");
    if (closeBtn) closeBtn.focus();
  }

  function toggleMobileMore() {
    if (mobileMoreOpen) closeMobileMore();
    else openMobileMore();
  }

  function syncNavActive(routeId) {
    document
      .querySelectorAll(".nav a, .mobile-nav a[data-route], .mobile-more-links a")
      .forEach(function (el) {
        var active = el.dataset.route === routeId;
        el.classList.toggle("active", active);
        if (active) el.setAttribute("aria-current", "page");
        else el.removeAttribute("aria-current");
      });
    var moreBtn = byId("mobile-more-btn");
    if (moreBtn) {
      var inMore = MOBILE_MORE_IDS.indexOf(routeId) !== -1;
      moreBtn.classList.toggle("active", inMore);
      var moreRoute = routeById(routeId);
      moreBtn.setAttribute(
        "aria-label",
        inMore && moreRoute ? "Ещё, текущий раздел: " + moreRoute.title : "Ещё"
      );
    }
  }

  function apiPost(path, body, options) {
    options = options || {};
    return fetchJson(path, {
      method: "POST",
      body: body === undefined ? undefined : body,
      timeoutMs: options.timeoutMs,
    });
  }

  function apiPut(path, body) {
    return fetchJson(path, { method: "PUT", body: body });
  }

  function requestKill(enable) {
    // Приёмочные J7: тур не должен перекрывать аварийный стоп (§D1).
    if (window.CabinTour && CabinTour.isActive()) {
      CabinTour.stop(true);
    }
    var path = enable ? "/kill" : "/unkill";
    var prompt = enable
      ? {
          title: "Остановить торговлю?",
          text: "Новые ордера будут отклоняться правилами риска. Уже открытые позиции этим действием автоматически не закрываются.",
          okLabel: "Остановить",
          danger: true,
        }
      : {
          title: "Снять стоп?",
          text: "Снова разрешить новые ордера? Риск-правила (вселенная, доли, дневной лимит) продолжат действовать.",
          okLabel: "Снять стоп",
          danger: false,
        };
    return askConfirm(prompt).then(function (ok) {
      if (!ok) return null;
      return apiPost(path).then(function (data) {
        lastStatus = Object.assign({}, lastStatus || {}, { killed: !!data.killed });
        syncKillControls(!!data.killed);
        return refreshStatus();
      });
    });
  }

  function humanizeHttpError(status) {
    if (status === 401) {
      return "Сессия или токен не приняты. Смените токен кабины и войдите снова.";
    }
    if (status === 429) {
      return "Слишком частые запросы — подождите немного и обновите.";
    }
    if (status === 503) {
      return "API недоступен или не готов. Проверьте, что сервер и база запущены локально.";
    }
    if (status === 502) {
      return "Брокер не отдал свечи. Повторите позже или проверьте токен песочницы.";
    }
    if (status === "timeout" || status === 408) {
      return "Превышено время ожидания ответа API. Обновите ещё раз или проверьте сервер.";
    }
    if (status === 0 || status == null) {
      return "Нет связи с API. Проверьте, что кабинет открыт с того же хоста, что и сервер.";
    }
    return "Ошибка загрузки (код " + status + ").";
  }

  function fetchJson(path, options) {
    options = options || {};
    var ctrl =
      typeof AbortController !== "undefined" ? new AbortController() : null;
    var timer = null;
    var timeoutMs =
      options.timeoutMs != null ? options.timeoutMs : FETCH_TIMEOUT_MS;
    if (ctrl) {
      timer = window.setTimeout(function () {
        try {
          ctrl.abort();
        } catch (e) {}
      }, timeoutMs);
    }
    var headers = Object.assign(
      { "X-App-Token": options.token || activeToken() },
      options.headers || {}
    );
    var opts = {
      method: options.method || "GET",
      headers: headers,
    };
    if (options.body != null) {
      headers["Content-Type"] = "application/json";
      opts.body =
        typeof options.body === "string"
          ? options.body
          : JSON.stringify(options.body);
    }
    if (ctrl) opts.signal = ctrl.signal;
    return fetch(path, opts)
      .then(function (res) {
        if (!res.ok) {
          return res
            .json()
            .catch(function () {
              return null;
            })
            .then(function (payload) {
              var detail = "";
              if (payload) {
                if (typeof payload.message === "string" && payload.message) {
                  detail = payload.message;
                } else if (typeof payload.detail === "string") {
                  detail = payload.detail;
                } else if (payload.detail && payload.detail.message) {
                  detail = payload.detail.message;
                }
              }
              var err = new Error(detail || humanizeHttpError(res.status));
              err.status = res.status;
              err.detail = detail || "";
              throw err;
            });
        }
        return res.json();
      })
      .catch(function (err) {
        if (err && err.status != null) throw err;
        if (
          err &&
          (err.name === "AbortError" ||
            String(err.message || "").toLowerCase().indexOf("abort") !== -1)
        ) {
          var timed = new Error(humanizeHttpError("timeout"));
          timed.status = "timeout";
          throw timed;
        }
        var net = new Error(humanizeHttpError(0));
        net.status = 0;
        throw net;
      })
      .finally(function () {
        if (timer) window.clearTimeout(timer);
      });
  }

  function apiGet(path) {
    return fetchJson(path);
  }

  function setBlockLoading(key, on) {
    if (on) blockLoading[key] = true;
    else delete blockLoading[key];
  }

  function isBlockLoading(key) {
    return !!blockLoading[key];
  }

  function setLoadError(key, err) {
    if (!err) {
      delete loadErrors[key];
      return;
    }
    loadErrors[key] = {
      status: err.status,
      message: err.message || humanizeHttpError(err.status),
    };
  }

  function clearLoadError(key) {
    delete loadErrors[key];
  }

  function blockErrorHtml(key, fallback) {
    var err = loadErrors[key];
    if (!err) return "";
    return (
      '<div class="attention warn" data-tour="block-error-' +
      escapeHtml(key) +
      '" role="alert">' +
      "<span><strong>Блок не загрузился.</strong> " +
      escapeHtml(err.message || fallback || "Ошибка загрузки.") +
      " Цифры ниже не подставляются нулями «как будто всё ок».</span>" +
      "</div>"
    );
  }

  function skeletonHtml(rows) {
    var n = rows || 3;
    var lines = "";
    for (var i = 0; i < n; i++) {
      lines += '<div class="skeleton-line" style="width:' + (70 - i * 12) + '%"></div>';
    }
    return (
      '<div class="skeleton" data-tour="page-skeleton" aria-busy="true" aria-label="Загрузка">' +
      lines +
      "</div>"
    );
  }

  function money(value) {
    if (value === null || value === undefined || value === "") return "—";
    return (
      Number(value).toLocaleString("ru-RU", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      }) + " ₽"
    );
  }

  function rubles(value) {
    if (value === null || value === undefined || value === "") return "—";
    var n = Number(value);
    if (!isFinite(n)) return "—";
    var whole = Math.abs(n - Math.round(n)) < 0.005;
    return (
      n.toLocaleString("ru-RU", {
        minimumFractionDigits: whole ? 0 : 2,
        maximumFractionDigits: whole ? 0 : 2,
      }) + " ₽"
    );
  }

  /** Отображение суммы в инпуте: 1000000 → «1 000 000». */
  function formatRubGrouped(value) {
    var n = Math.round(Number(value));
    if (!isFinite(n)) return "";
    var sign = n < 0 ? "-" : "";
    var digits = String(Math.abs(n));
    return sign + digits.replace(/\B(?=(\d{3})+(?!\d))/g, " ");
  }

  /** Разбор «1 000 000», «1\u00a0000», «1000000» → number. */
  function parseRubInput(raw) {
    var s = String(raw == null ? "" : raw)
      .replace(/[\s\u00a0\u202f]/g, "")
      .replace(/,/g, ".")
      .replace(/[^\d.-]/g, "");
    if (!s || s === "-" || s === "." || s === "-.") return NaN;
    var n = Number(s);
    return isFinite(n) ? n : NaN;
  }

  function bindRubInput(el, onCommit) {
    if (!el || el.getAttribute("data-rub-bound") === "1") return;
    el.setAttribute("data-rub-bound", "1");
    el.addEventListener("blur", function () {
      var n = parseRubInput(el.value);
      if (!isFinite(n) || n < 0) n = 0;
      el.value = formatRubGrouped(n);
      if (typeof onCommit === "function") onCommit(n, el);
    });
    el.addEventListener("keydown", function (ev) {
      if (ev.key === "Enter") {
        el.blur();
      }
    });
  }

  function wireRubInputs(root, onCommit) {
    var scope = root && root.querySelectorAll ? root : document;
    scope.querySelectorAll("[data-rub-input]").forEach(function (el) {
      bindRubInput(el, onCommit);
    });
  }

  function plainNumber(value) {
    var n = Number(value);
    if (!isFinite(n)) return "—";
    var whole = Math.abs(n - Math.round(n)) < 0.000001;
    return n.toLocaleString("ru-RU", {
      minimumFractionDigits: whole ? 0 : 2,
      maximumFractionDigits: whole ? 0 : 2,
    });
  }

  function shareToPercent(raw) {
    var n = Number(raw);
    if (!isFinite(n)) return "";
    return String(Math.round(n * 100));
  }

  function readPercent(input, label) {
    var raw = String(input.value || "").trim().replace(",", ".");
    if (!/^\d{1,2}$/.test(raw)) {
      throw new Error(label + ": целое число от 1 до 99");
    }
    var n = Number(raw);
    if (n < 1 || n > 99) throw new Error(label + ": от 1 до 99");
    return (n / 100).toFixed(2);
  }

  function refreshStatus() {
    if (!authed) return Promise.resolve(null);
    if (refreshBusy) return Promise.resolve(lastStatus);
    refreshBusy = true;
    var btn = byId("btn-refresh");
    if (btn) {
      btn.disabled = true;
      btn.setAttribute("aria-busy", "true");
    }
    return verifyToken(activeToken())
      .then(function (data) {
        lastStatus = data;
        lastStatusAt = new Date();
        renderStatus(data, {});
        if (currentRoute === "overview") return loadOverviewData(true);
        if (currentRoute === "portfolio") {
          return refreshPortfolioBook().then(function () {
            return refreshProposals().then(function () {
              return data;
            });
          });
        }
        if (currentRoute === "news") {
          return refreshNews().then(function () {
            return refreshProposals().then(function () {
              return data;
            });
          });
        }
        return refreshProposals().then(function () {
          return data;
        });
      })
      .catch(function (err) {
        if (err && err.status === 401) {
          logoutToGate(false);
          showGateError(humanizeHttpError(401));
          return null;
        }
        renderStatus(lastStatus || {}, {
          error: humanizeHttpError(err && err.status),
        });
        return null;
      })
      .finally(function () {
        refreshBusy = false;
        if (btn) {
          btn.disabled = false;
          btn.removeAttribute("aria-busy");
        }
      });
  }

  function cabinToken() {
    return (localStorage.getItem(TOKEN_KEY) || "").trim();
  }

  function rememberEnabled() {
    var box = byId("remember-token");
    if (box) return box.checked;
    return localStorage.getItem(REMEMBER_KEY) !== "0";
  }

  function setToken(value, remember) {
    var token = (value || "").trim();
    if (remember) {
      localStorage.setItem(TOKEN_KEY, token);
      localStorage.setItem(REMEMBER_KEY, "1");
    } else {
      localStorage.removeItem(TOKEN_KEY);
      localStorage.setItem(REMEMBER_KEY, "0");
      sessionStorage.setItem(TOKEN_KEY, token);
    }
  }

  function readStoredToken() {
    if (localStorage.getItem(REMEMBER_KEY) === "0") {
      return (sessionStorage.getItem(TOKEN_KEY) || "").trim();
    }
    return cabinToken();
  }

  function activeToken() {
    if (localStorage.getItem(REMEMBER_KEY) === "0") {
      return (sessionStorage.getItem(TOKEN_KEY) || "").trim();
    }
    return cabinToken();
  }

  function showGateError(text) {
    var el = byId("gate-error");
    if (!text) {
      el.hidden = true;
      el.textContent = "";
      return;
    }
    el.hidden = false;
    el.textContent = text;
  }

  function setAuthed(ok) {
    authed = ok;
    byId("gate").hidden = ok;
    byId("app").hidden = !ok;
    var skip = document.querySelector(".skip-link");
    if (skip) skip.setAttribute("href", ok ? "#page-body" : "#gate-form");
    if (ok) {
      document.title = "i.datagon · Обзор";
      renderNav();
      syncFromHash();
      refreshStatus().then(function () {
        renderQueueBadge();
        if (currentRoute === "overview") maybeStartOverviewTour();
        else maybeStartMenuTour();
      });
    } else {
      document.title = "i.datagon · Вход";
      lastStatus = null;
      lastProposals = [];
      renderQueueBadge();
      if (window.CabinTour) CabinTour.stop(false);
    }
  }

  function verifyToken(token) {
    return fetchJson("/status", { token: token });
  }

  function loginWithToken(token, remember) {
    var value = (token || "").trim();
    if (!value) {
      showGateError("Вставьте токен кабины");
      return Promise.resolve(false);
    }
    byId("gate-submit").disabled = true;
    showGateError("");
    return verifyToken(value)
      .then(function () {
        setToken(value, remember);
        setAuthed(true);
        return true;
      })
      .catch(function (err) {
        if (err && err.status === 401) {
          showGateError(
            "Токен не принят. Проверьте APP_AUTH_TOKEN в .env и что API запущен."
          );
        } else if (err && err.status === 429) {
          showGateError(
            "Сервер временно ограничил частоту запросов с вашего IP. Подождите ~30 секунд и войдите снова — это не из‑за «лишних» кликов."
          );
        } else if (err && err.status >= 500) {
          showGateError("API недоступен или не готов. Проверьте, что сервер запущен.");
        } else {
          showGateError("Нет связи с API на этом адресе. Проверьте, что кабинет открыт с того же хоста, что и API.");
        }
        return false;
      })
      .finally(function () {
        byId("gate-submit").disabled = false;
      });
  }

  function logoutToGate(clearStored) {
    if (clearStored) {
      localStorage.removeItem(TOKEN_KEY);
      sessionStorage.removeItem(TOKEN_KEY);
    }
    byId("app-token").value = readStoredToken();
    showGateError("");
    setAuthed(false);
    maybeStartGateTour();
  }

  function hashPath() {
    return (location.hash || "").replace(/^#\/?/, "").split("?")[0];
  }

  function routeFromHash() {
    var raw = hashPath();
    if (!raw || raw === "home") return raw === "home" ? "home" : "home";
    if (raw === "candles") return "candles";
    if (raw === "work" || raw.indexOf("work/") === 0) return "work";
    if (raw === "strategies" || raw.indexOf("strategies/") === 0) {
      return "strategies";
    }
    for (var i = 0; i < ROUTES.length; i++) {
      if (ROUTES[i].id === raw) return raw;
    }
    return "home";
  }

  function deskMode() {
    var id = routeFromHash();
    if (id === "work") return "work";
    if (id === "home") return "home";
    return "test";
  }

  function strategiesSleeveFromHash() {
    var raw = hashPath();
    if (raw.indexOf("strategies/") !== 0) return null;
    var id = decodeURIComponent(raw.slice("strategies/".length).split("/")[0] || "");
    return id || null;
  }

  function setHash(id) {
    if (location.hash !== "#/" + id) {
      location.hash = "#/" + id;
    }
  }

  function setRouteTab(routeId, tabId) {
    var next = "#/" + routeId + "?tab=" + encodeURIComponent(tabId);
    if (location.hash !== next) location.hash = next;
    else showRoute(routeId);
  }

  function appendNavLabel(nav, text) {
    var label = document.createElement("div");
    label.className = "nav-label";
    label.textContent = text;
    nav.appendChild(label);
  }

  function appendNavLink(nav, id, title, hint) {
    var a = document.createElement("a");
    a.href = "#/" + id;
    a.dataset.route = id;
    a.innerHTML =
      '<span class="nav-copy"><span>' +
      title +
      '</span><span class="nav-hint">' +
      hint +
      "</span></span>";
    nav.appendChild(a);
  }

  function appendMobileLink(mobile, id, title) {
    var m = document.createElement("a");
    m.href = "#/" + id;
    m.dataset.route = id;
    m.textContent = title;
    mobile.appendChild(m);
  }

  function markDeskSwitch() {
    var mode = deskMode();
    document.body.dataset.desk = mode;
    ["home", "test", "work"].forEach(function (name) {
      var link = byId("desk-link-" + name);
      if (!link) return;
      if (name === mode) link.setAttribute("aria-current", "page");
      else link.removeAttribute("aria-current");
    });
    var badge = byId("env-badge");
    if (badge) {
      badge.textContent = mode === "work" ? "работа" : mode === "test" ? "тест" : "выбор";
    }
  }

  function renderNav() {
    var nav = byId("nav");
    var mobile = byId("mobile-nav");
    var moreLinks = byId("mobile-more-links");
    nav.innerHTML = "";
    mobile.innerHTML = "";
    if (moreLinks) moreLinks.innerHTML = "";
    markDeskSwitch();
    if (deskMode() === "work") {
      var desks = (workDesks && workDesks.desks) || [];
      appendNavLabel(nav, "Работа · брокер");
      appendNavLink(nav, "work", "Все песочницы", "Сравнение и итоги");
      appendMobileLink(mobile, "work", "Все");
      if (desks.length) appendNavLabel(nav, "Песочницы");
      desks.forEach(function (d) {
        var id = "work/" + encodeURIComponent(d.id);
        appendNavLink(
          nav,
          id,
          escapeHtml(d.name),
          escapeHtml((d.strategy && d.strategy.title) || "") + (d.enabled ? " · заявки" : d.ready ? " · выкл" : " · настройка")
        );
        appendMobileLink(mobile, id, d.name);
      });
      appendNavLink(nav, "work/new", "+ Новая песочница", "Свой счёт и стратегия");
      appendMobileLink(mobile, "work/new", "+ Новая");
      return;
    }
    if (deskMode() === "home") {
      appendNavLabel(nav, "Выбор");
      appendNavLink(nav, "candles", "Тест", "Свечи и прогон");
      appendNavLink(nav, "work", "Работа", "Счёт песочницы");
      appendMobileLink(mobile, "candles", "Тест");
      appendMobileLink(mobile, "work", "Работа");
      return;
    }
    if (deskMode() === "test") {
      appendNavLabel(nav, "Тест");
      appendNavLink(nav, "candles", "Свечи", "Дневки, 15м, 10м");
      appendNavLink(nav, "strategies", "Стратегии", "Проверка на истории");
      appendNavLink(nav, "companies", "Компании", "По отраслям");
      appendNavLink(nav, "whatif", "Если бы", "Купил и держал");
      appendMobileLink(mobile, "candles", "Свечи");
      appendMobileLink(mobile, "strategies", "Стратегии");
      appendMobileLink(mobile, "companies", "Компании");
      appendMobileLink(mobile, "whatif", "Если бы");
      return;
    }
    MOBILE_PRIMARY_IDS.forEach(function (id) {
      var route = routeById(id);
      if (!route) return;
      var m = document.createElement("a");
      m.href = "#/" + route.id;
      m.dataset.route = route.id;
      m.dataset.tour = "mobile-nav-" + route.id;
      m.textContent = route.title;
      mobile.appendChild(m);
    });
    var moreBtn = document.createElement("button");
    moreBtn.type = "button";
    moreBtn.id = "mobile-more-btn";
    moreBtn.className = "mobile-more-btn";
    moreBtn.setAttribute("aria-haspopup", "dialog");
    moreBtn.setAttribute("aria-expanded", "false");
    moreBtn.setAttribute("aria-controls", "mobile-more");
    moreBtn.dataset.tour = "mobile-nav-more";
    moreBtn.textContent = "Ещё";
    moreBtn.addEventListener("click", function () {
      toggleMobileMore();
    });
    mobile.appendChild(moreBtn);
    MOBILE_MORE_IDS.forEach(function (id) {
      var route = routeById(id);
      if (!route || !moreLinks) return;
      var link = document.createElement("a");
      link.href = "#/" + route.id;
      link.dataset.route = route.id;
      link.dataset.tour = "mobile-more-" + route.id;
      link.innerHTML =
        "<span>" +
        route.title +
        '</span><span class="nav-hint">' +
        route.hint +
        "</span>";
      link.addEventListener("click", function () {
        closeMobileMore();
      });
      moreLinks.appendChild(link);
    });
  }

  function proposalKindLabel(kind) {
    if (kind === "order") return "Предложение ордера";
    if (kind === "weights") return "Предложение весов";
    return kind || "Предложение";
  }

  function proposalStatusLabel(status) {
    if (status === "proposed") return "ждёт решения";
    if (status === "approved") return "принято";
    if (status === "rejected") return "отклонено";
    if (status === "expired") return "истекло";
    return status || "—";
  }

  function proposalExpiredReasonLabel(row) {
    var reason = row && row.payload && row.payload.expired_reason;
    if (reason === "recommendation_plan_incomplete") {
      return "не хватало цены или лота";
    }
    if (reason === "recommendation_lot_invalid") {
      return "объём не кратен лоту";
    }
    if (reason === "recommendation_stop_invalid") {
      return "стоп некорректен";
    }
    if (reason === "recommendation_price_stale") {
      return "цена устарела";
    }
    if (reason === "recommendation_price_invalid") {
      return "цена некорректна";
    }
    return reason || "";
  }

  function proposalSummary(row) {
    var payload = row.payload || {};
    if (row.kind === "order") {
      var side =
        payload.side === "buy"
          ? "покупка"
          : payload.side === "sell"
            ? "продажа"
            : payload.side || "сделка";
      var parts = [
        side,
        payload.ticker || "—",
        "× " + (payload.qty != null ? payload.qty : "—"),
      ];
      if (payload.sleeve) {
        parts.push(SLEEVE_NAMES[payload.sleeve] || payload.sleeve);
      }
      if (payload.stop != null && payload.stop !== "") {
        parts.push("стоп " + payload.stop);
      }
      if (payload.reason) {
        parts.push(String(payload.reason).slice(0, 80));
      }
      return parts.join(" · ");
    }
    if (row.kind === "weights") {
      var weights = payload.weights || payload;
      if (Array.isArray(weights)) {
        return weights
          .map(function (item) {
            return (
              (SLEEVE_NAMES[item.sleeve] || item.sleeve || "рукав") +
              " " +
              pctLabel(item.weight)
            );
          })
          .join(", ");
      }
      if (weights && typeof weights === "object" && !Array.isArray(weights)) {
        return Object.keys(weights)
          .filter(function (name) {
            return name !== "reason";
          })
          .map(function (name) {
            return (
              (SLEEVE_NAMES[name] || name) +
              " " +
              Math.round(Number(weights[name]) * 100) +
              "%"
            );
          })
          .join(", ");
      }
    }
    return "Нет краткого описания — раскройте «Подробнее»";
  }

  function proposalWillDo(row) {
    if (row.kind === "order") {
      return "После одобрения план пройдёт риск-ворота и сохранится как внутренняя paper-заявка в Журнале. В T‑Invest sandbox и на биржу ничего не отправляется.";
    }
    if (row.kind === "weights") {
      return "После «Принять веса» новые веса рукавов применятся в аллокаторе. Сами сделки от смены весов не откроются.";
    }
    return "После подтверждения предложение перестанет ждать решения.";
  }

  function proposedList(rows) {
    return (rows || []).filter(function (row) {
      return row.status === "proposed";
    });
  }

  function recentProposals(rows) {
    return (rows || []).filter(function (row) {
      return row.status && row.status !== "proposed";
    });
  }

  function hashQuery() {
    var hash = location.hash || "";
    var q = hash.indexOf("?");
    if (q < 0) return {};
    var out = {};
    String(hash.slice(q + 1))
      .split("&")
      .forEach(function (pair) {
        if (!pair) return;
        var parts = pair.split("=");
        out[decodeURIComponent(parts[0])] = decodeURIComponent(parts[1] || "");
      });
    return out;
  }

  function sortProposalsProposedFirst(rows) {
    return (rows || []).slice().sort(function (a, b) {
      var ap = a.status === "proposed" ? 0 : 1;
      var bp = b.status === "proposed" ? 0 : 1;
      if (ap !== bp) return ap - bp;
      return String(b.id || "").localeCompare(String(a.id || ""));
    });
  }

  function queueBadgeLabel(count) {
    var mod10 = count % 10;
    var mod100 = count % 100;
    var word = "ждут решения";
    if (mod10 === 1 && mod100 !== 11) word = "ждёт решения";
    return count + " " + word;
  }

  function renderQueueBadge() {
    var badge = byId("queue-badge");
    if (!badge) return;
    var count = proposedList(lastProposals).length;
    if (count <= 0) {
      badge.hidden = true;
      badge.innerHTML = "";
      badge.setAttribute("aria-label", "Нет предложений, которые ждут решения");
      return;
    }
    badge.hidden = false;
    badge.href = "#/agents?tab=proposed";
    badge.innerHTML =
      '<span class="count">' +
      count +
      "</span><span>" +
      escapeHtml(queueBadgeLabel(count).replace(/^\d+\s/, "")) +
      "</span>";
    badge.setAttribute("aria-label", queueBadgeLabel(count) + ", открыть агентов");
  }

  function refreshProposals() {
    return apiGet("/proposals")
      .then(function (data) {
        clearLoadError("proposals");
        lastProposals = sortProposalsProposedFirst(
          (data && data.proposals) || []
        );
        renderQueueBadge();
        if (currentRoute === "overview") renderOverview();
        if (currentRoute === "agents") renderAgents();
        return lastProposals;
      })
      .catch(function (err) {
        setLoadError("proposals", err);
        renderQueueBadge();
        if (currentRoute === "overview") renderOverview();
        if (currentRoute === "agents") renderAgents();
        return lastProposals;
      });
  }

  function loadOverviewData(silent) {
    // Параллельно: proposals, sleeves, капитал и сигналы наблюдаемости.
    // Чужие endpoint (лента новостей и т.п.) сюда не входят и Обзор не роняют.
    if (!silent) {
      setBlockLoading("proposals", true);
      setBlockLoading("sleeves", true);
      setBlockLoading("capital", true);
      setBlockLoading("observability", true);
      if (currentRoute === "overview") renderOverview();
    }
    return Promise.all([
      refreshProposals().finally(function () {
        setBlockLoading("proposals", false);
      }),
      apiGet("/sleeves")
        .then(function (data) {
          clearLoadError("sleeves");
          return data;
        })
        .catch(function (err) {
          setLoadError("sleeves", err);
          return { sleeves: lastSleeves };
        })
        .finally(function () {
          setBlockLoading("sleeves", false);
        }),
      apiGet("/capital/summary")
        .then(function (data) {
          clearLoadError("capital");
          return data;
        })
        .catch(function (err) {
          setLoadError("capital", err);
          return lastCapital;
        })
        .finally(function () {
          setBlockLoading("capital", false);
        }),
      apiGet("/reports/weekly").catch(function () {
        return lastWeeklyReport;
      }),
      apiGet("/audit/timeline").catch(function () {
        return lastAudit;
      }),
      apiGet("/orders?status=unknown").catch(function () {
        return { orders: lastUnknownOrders };
      }),
      apiGet("/admission").catch(function () {
        return lastAdmission;
      }),
      refreshDrift(),
    ]).then(function (parts) {
      lastSleeves = (parts[1] && parts[1].sleeves) || lastSleeves;
      lastCapital = parts[2] || lastCapital;
      lastWeeklyReport = parts[3] || lastWeeklyReport;
      lastAudit = parts[4] || lastAudit;
      lastUnknownOrders =
        (parts[5] && parts[5].orders) || lastUnknownOrders;
      lastAdmission = parts[6] || lastAdmission;
      setBlockLoading("observability", false);
      if (currentRoute === "overview") renderOverview();
      return parts;
    });
  }

  function renderOverview() {
    var body = byId("page-body");
    var vault = (lastStatus && lastStatus.vault) || {};
    var waiting = proposedList(lastProposals).slice(0, 3);
    var agentsOn = !!(lastStatus && lastStatus.agents_enabled);
    var killed = !!(lastStatus && lastStatus.killed);

    var attention = "";
    if (killed) {
      attention +=
        '<div class="attention warn" data-tour="overview-attention">' +
        "<span><strong>Торговля остановлена.</strong> Новые ордера будут отклоняться.</span>" +
        '<div class="actions"><button type="button" class="ghost" id="overview-unkill">Снять стоп…</button></div></div>';
    }
    if (waiting.length) {
      attention +=
        '<div class="attention info" data-tour="overview-attention">' +
        "<span><strong>Есть предложения, которые ждут решения</strong> — " +
        waiting.length +
        ".</span>" +
        '<div class="actions"><a class="panel-link" href="#/agents" id="overview-to-agents">Открыть агентов</a></div></div>';
    }
    if (!attention) {
      attention =
        '<div class="attention calm" data-tour="overview-attention">' +
        "<span><strong>Срочных действий нет.</strong> Торговый стоп выключен, критических событий не обнаружено.</span>" +
        "</div>";
    }

    var queueHtml = "";
    if (isBlockLoading("proposals")) {
      queueHtml = skeletonHtml(2);
    } else if (loadErrors.proposals && !(lastProposals || []).length) {
      queueHtml =
        blockErrorHtml("proposals") ||
        '<p class="empty">Очередь не загрузилась — не считаем это «0 предложений».</p>';
    } else if (waiting.length) {
      queueHtml =
        '<div class="proposal-cards">' +
        waiting
          .map(function (row) {
            return (
              '<div class="proposal-card">' +
              '<div class="meta"><div class="kind">' +
              escapeHtml(proposalKindLabel(row.kind)) +
              '</div><div class="summary">' +
              escapeHtml(proposalSummary(row)) +
              "</div></div>" +
              '<a class="panel-link" href="#/agents">Открыть</a></div>'
            );
          })
          .join("") +
        "</div>";
    } else if (!agentsOn) {
      queueHtml =
        '<p class="empty">Очередь пуста: агенты выключены. Это ожидаемо. Когда включите агентов в настройках сервера, предложения появятся здесь.</p>';
    } else {
      queueHtml =
        '<p class="empty">Новых предложений нет. Когда агент что-то предложит, вы увидите карточку здесь и сможете перейти в «Агенты».</p>';
    }

    var sleevesBlock = "";
    if (isBlockLoading("sleeves")) {
      sleevesBlock = skeletonHtml(2);
    } else if (loadErrors.sleeves && !(lastSleeves || []).length) {
      sleevesBlock =
        blockErrorHtml("sleeves") ||
        '<p class="empty">Сводка рукавов не загрузилась.</p>';
    } else {
      var sleevesRows = normalizeSleeves(lastSleeves)
        .map(function (row) {
          var pnl = row.pnl || {};
          var name = SLEEVE_NAMES[row.sleeve] || row.sleeve || "—";
          var total = Number(pnl.total || 0);
          return (
            '<a class="strategy-tile" href="#/strategies/' +
            encodeURIComponent(row.sleeve) +
            '">' +
            '<span class="strategy-tile__eyebrow">' +
            escapeHtml(row.sleeve || "") +
            "</span>" +
            '<strong class="strategy-tile__name">' +
            escapeHtml(name) +
            "</strong>" +
            '<span class="strategy-tile__pnl ' +
            (total > 0 ? "is-positive" : total < 0 ? "is-negative" : "") +
            '">' +
            money(total) +
            "</span>" +
            '<span class="strategy-tile__split">зафиксировано ' +
            money(pnl.realized) +
            " · открытый результат " +
            money(pnl.unrealized) +
            "</span></a>"
          );
        })
        .join("");
      sleevesBlock = sleevesRows
        ? '<div class="strategy-grid">' + sleevesRows + "</div>"
        : '<p class="empty">Пока нет сводки рукавов.</p>';
    }

    var capital = lastCapital;
    var quality = (capital && capital.data_quality) || {};
    var weekly = lastWeeklyReport || {};
    var audit = lastAudit || {};
    var admission = lastAdmission || {};
    var admissionGates = admission.gates || {};
    var qualityTotal = Number(quality.positions || 0);
    var qualityFresh = Number(quality.fresh_marks || 0);
    var qualityPct = qualityTotal
      ? Math.round((qualityFresh / qualityTotal) * 100)
      : 100;
    var alertItems = [];
    if (killed) alertItems.push(["critical", "Торговля остановлена", "Новые заявки будут отклонены"]);
    if (!(lastStatus && lastStatus.worker_alive)) {
      alertItems.push(["warning", "Нет связи с воркером", "Фоновые данные могут не обновляться"]);
    }
    if (capital && capital.status !== "complete") {
      alertItems.push(["critical", "Не хватает рыночных цен", "Точная стоимость счёта временно скрыта"]);
    } else if (Number(quality.stale_marks || 0) || Number(quality.missing_marks || 0)) {
      alertItems.push([
        "warning",
        "Качество данных",
        String(quality.stale_marks || 0) +
          " устарело · " +
          String(quality.missing_marks || 0) +
          " отсутствует",
      ]);
    }
    if (lastDrift && lastDrift.alert) {
      alertItems.push([
        "critical",
        "Расхождение с брокером",
        "Расхождение " + money(lastDrift.drift),
      ]);
    }
    if (lastUnknownOrders.length) {
      alertItems.push([
        "critical",
        "Неясный статус заявок",
        String(lastUnknownOrders.length) + " заявок требуют сверки",
      ]);
    }
    var forwardGate = admissionGates.G3 || {};
    if (
      forwardGate.status === "stalled" ||
      forwardGate.status === "incomplete"
    ) {
      alertItems.push([
        "critical",
        "Проверка на новых данных",
        forwardGate.status === "stalled"
          ? "Новые наблюдения не поступают"
          : "Период завершён без полного покрытия",
      ]);
    }
    if (!alertItems.length) {
      alertItems.push(["ok", "Система работает штатно", "Критических событий нет"]);
    }
    var alertsHtml = alertItems
      .map(function (item) {
        return (
          '<div class="ops-alert is-' +
          item[0] +
          '"><span class="ops-alert__dot"></span><div><strong>' +
          escapeHtml(item[1]) +
          "</strong><span>" +
          escapeHtml(item[2]) +
          "</span></div></div>"
        );
      })
      .join("");
    var gatesHtml = ["G1", "G2", "G3", "G4", "G5"]
      .map(function (key) {
        var gate = admissionGates[key] || {};
        var state = gate.status || "unknown";
        var gateNames = {
          G1: "Учёт",
          G2: "Бэктест",
          G3: "Наблюдение",
          G4: "Сбои",
          G5: "Боевой контур",
        };
        var gateStates = {
          passed: "пройден",
          running: "идёт",
          blocked: "закрыт",
          stalled: "остановлен",
          incomplete: "не завершён",
          unknown: "нет данных",
        };
        return (
          '<div class="admission-gate is-' +
          escapeHtml(state) +
          '"><span>' +
          escapeHtml(gateNames[key] || key) +
          "</span><strong>" +
          escapeHtml(gateStates[state] || state) +
          "</strong></div>"
        );
      })
      .join("");
    var capitalBlock = isBlockLoading("capital") && !capital
      ? skeletonHtml(2)
      : !capital
      ? '<p class="empty" data-tour="overview-capital-empty">Рыночная оценка ещё не пришла. Это не «0 ₽» — обновите статус.</p>'
      : '<div class="overview-balance"><span>Стоимость счёта</span><strong>' +
        money(capital.equity) +
        '</strong><small>Оценка всех денег и открытых позиций</small></div>' +
        '<div class="overview-money-grid">' +
        '<div><span>Свободный кэш</span><strong>' +
        money(capital.cash) +
        "</strong><small>доступен для новых решений</small></div>" +
        '<div><span>Сейф прибыли</span><strong>' +
        money(capital.vault != null ? capital.vault : vault.accumulated) +
        "</strong><small>отложено отдельно</small></div>" +
        '<div><span>Зафиксированный результат</span><strong>' +
        money(capital.realized_net_pnl) +
        "</strong><small>после расходов</small></div>" +
        '<div><span>Открытый результат</span><strong>' +
        money(capital.unrealized_pnl) +
        "</strong><small>по текущим позициям</small></div>" +
        '<div><span>Максимальная просадка</span><strong>' +
        (capital.max_drawdown == null
          ? "—"
          : escapeHtml((Number(capital.max_drawdown) * 100).toFixed(2) + "%")) +
        "</strong><small>от исторического пика</small></div>" +
        '<div><span>Доходность без пополнений</span><strong>' +
        (capital.twr == null
          ? "—"
          : escapeHtml((Number(capital.twr) * 100).toFixed(2) + "%")) +
        "</strong><small>метод TWR</small></div></div>" +
        (capital.status !== "complete"
          ? '<p class="warning-text">Точная стоимость счёта скрыта: есть устаревшие или отсутствующие цены (' +
            escapeHtml(
              String(quality.stale_marks || 0) +
                " устарело, " +
                String(quality.missing_marks || 0) +
                " отсутствует"
            ) +
            ").</p>"
          : '<p class="source-line">Оценка ' +
            escapeHtml(capital.version || "") +
            " · " +
            escapeHtml(formatSignalTime(capital.as_of)) +
            "</p>");

    body.innerHTML =
      blockErrorHtml("proposals") +
      blockErrorHtml("sleeves") +
      blockErrorHtml("capital") +
      '<div class="overview-home">' +
      '<section class="activation"><h3>Запуск кабинета</h3><ol class="activation-steps">' +
      '<li><a href="#/overview"><strong>Обзор.</strong> Контур жив, воркер на связи.</a></li>' +
      '<li><a href="#/settings"><strong>Настройки.</strong> Депозит и потолок на одну бумагу.</a></li>' +
      '<li><a href="#/strategies"><strong>Стратегии.</strong> Рукав и прогон по файлу свечей.</a></li>' +
      '<li><a href="#/agents"><strong>Агенты.</strong> Принять или отклонить план. В Тинькофф заявка не уходит.</a></li>' +
      '<li><a href="#/portfolio"><strong>Портфель.</strong> Книга: кэш, сейф, позиции.</a></li>' +
      '<li><a href="#/journal"><strong>Журнал.</strong> Что лаборатория записала.</a></li>' +
      "</ol></section>" +
      '<section class="overview-welcome"><div><span class="overview-eyebrow">Главная · тестовый контур</span>' +
      "<h3>" +
      (killed ? "Торговля остановлена" : waiting.length ? "Есть решения, которые ждут вас" : "Капитал под контролем") +
      "</h3><p>Здесь только главное: состояние денег, задачи на сейчас и здоровье системы.</p></div>" +
      '<div class="overview-welcome__state ' +
      (killed ? "is-critical" : "is-ok") +
      '"><span class="overview-state-dot"></span><div><strong>' +
      (killed ? "Новые заявки запрещены" : "Система работает") +
      "</strong><small>" +
      (lastStatusAt ? "Обновлено " + escapeHtml(formatSignalTime(lastStatusAt)) : "Ожидаем первое обновление") +
      "</small></div></div></section>" +
      '<section class="overview-capital-card" data-tour="overview-capital">' +
      '<div class="overview-section-head"><div><span class="overview-eyebrow">Ваш капитал</span><h3>Деньги и результат</h3></div>' +
      '<div class="overview-quality"><strong>' +
      escapeHtml(String(qualityPct)) +
      '%</strong><span>актуальных цен</span></div></div>' +
      capitalBlock +
      '<div class="overview-card-footer"><span>За неделю <strong>' +
      (weekly.available === false ? "нет данных" : money(weekly.pnl)) +
      '</strong></span><span>На начало дня <strong>' +
      money(capital && capital.day_start_equity) +
      '</strong></span><a href="#/portfolio">Подробнее в Портфеле</a></div></section>' +
      '<aside class="overview-now" data-tour="overview-attention"><div class="overview-section-head"><div><span class="overview-eyebrow">Ваше внимание</span><h3>Что сделать сейчас</h3></div>' +
      (waiting.length ? '<span class="overview-count">' + waiting.length + "</span>" : "") +
      "</div>" +
      attention +
      '<div class="overview-now__queue" data-tour="overview-queue">' +
      queueHtml +
      "</div></aside>" +
      '<section class="overview-strategies" data-tour="overview-sleeves"><div class="overview-section-head"><div><span class="overview-eyebrow">Результат по направлениям</span><h3>Стратегии</h3></div><a href="#/strategies">Открыть все</a></div>' +
      sleevesBlock +
      "</section>" +
      '<section class="overview-system"><div class="overview-section-head"><div><span class="overview-eyebrow">Надёжность</span><h3>Состояние системы</h3></div><a href="#/journal">Открыть журнал</a></div>' +
      '<div class="overview-system-grid"><div class="overview-alerts">' +
      alertsHtml +
      '</div><div class="overview-readiness"><div class="overview-readiness__head"><div><strong>Готовность контуров</strong><small>Live остаётся закрыт до независимых проверок</small></div><span>' +
      (audit.chain_valid === false ? "Цепочка нарушена" : "Журнал цел") +
      "</span></div><div class=\"admission-strip\">" +
      gatesHtml +
      "</div></div></div></section></div>";

    var unkill = byId("overview-unkill");
    if (unkill) {
      unkill.addEventListener("click", function () {
        requestKill(false);
      });
    }
  }

  function renderHelpPanel() {
    var body = byId("page-body");
    var mapRows = ROUTES.map(function (route) {
      return (
        "<tr><td><a class=\"panel-link\" href=\"#/" +
        route.id +
        '">' +
        escapeHtml(route.title) +
        "</a></td><td>" +
        escapeHtml(route.hint) +
        "</td><td>" +
        escapeHtml(route.intro) +
        "</td></tr>"
      );
    }).join("");
    body.innerHTML =
      '<section class="panel" data-tour="help-map">' +
      '<h3 data-tour="help-title">Карта кабинета</h3>' +
      "<p>" +
      escapeHtml(String(ROUTES.length)) +
      " разделов — зачем каждый. Порядок меню = порядок обучения новичка. " +
      "Депозит и лимит на бумагу — в «Настройках».</p>" +
      wrapTableScroll(
        '<table class="data-table"><thead><tr><th>раздел</th><th>кратко</th><th>зачем</th></tr></thead><tbody>' +
          mapRows +
          "</tbody></table>"
      ) +
      "</section>" +
      '<section class="panel" data-tour="help-legend">' +
      "<h3>Легенда пиллов статуса</h3>" +
      "<ul class=\"help-list\">" +
      "<li><strong>Система</strong> — связь с API есть или нет.</li>" +
      "<li><strong>Воркер</strong> — пульс фонового процесса (свечи, сигналы, сито).</li>" +
      "<li><strong>Торговля</strong> — стоп выключен или включён (новые ордера нельзя).</li>" +
      "<li><strong>Агенты</strong> — включены или выключены; выключены — это нормально, не авария.</li>" +
      "</ul></section>" +
      '<section class="panel" data-tour="help-glossary">' +
      "<h3>Словарь</h3>" +
      "<p data-tour=\"help-vault\">Ключевое про сейф: пока накоплено меньше депозита, в сейф уходит 50% зафиксированной прибыли; после перекрытия депозита — 20%. Нереализованная переоценка в сейф не идёт.</p>" +
      wrapTableScroll(
        '<table class="data-table"><thead><tr><th>термин</th><th>смысл</th></tr></thead><tbody>' +
          "<tr><td>стоимость счёта</td><td>кэш + сейф + оценка позиций в paper-книге</td></tr>" +
          "<tr><td>свободный кэш</td><td>деньги на торговом счёте, ещё не в позициях и не в сейфе</td></tr>" +
          "<tr><td>сейф прибыли</td><td>доля зафиксированной прибыли, которую лаборатория откладывает</td></tr>" +
          "<tr><td>рукав</td><td>отдельная стратегия со своими сигналами и PnL</td></tr>" +
          "<tr><td>вселенная</td><td>список бумаг, по которым разрешён вход</td></tr>" +
          "<tr><td>ждут решения</td><td>агент предложил — без вас ордер/веса не применятся</td></tr>" +
          "<tr><td>стоп включён</td><td>риск режет новые ордера</td></tr>" +
          "</tbody></table>"
      ) +
      "</section>" +
      '<section class="panel" data-tour="help-security">' +
      "<h3>Безопасность</h3>" +
      "<ul class=\"help-list\">" +
      "<li>В браузер вводится только <code>APP_AUTH_TOKEN</code> кабины — токен Тинькоффа / брокера никогда.</li>" +
      "<li>Это paper-лаборатория: цифры из книги, не экран приложения Инвестиций.</li>" +
      "<li>Боевой торговый интерфейс и ввод боевого токена вне рамок кабинета.</li>" +
      "</ul></section>" +
      '<section class="panel" data-tour="help-learn">' +
      '<h3 data-tour="help-engine">Управление обучением</h3>' +
      '<p>Движок туров: подсветка якоря, «Назад / Далее / Закрыть», Esc, прогресс «шаг N из M». Первый визит в раздел может запустить тур сам; кнопка «Обучение» — вручную.</p>' +
      '<div class="help-actions" data-tour="help-actions">' +
      '<button type="button" class="primary" id="help-overview-tour">Пройти тур Обзора</button>' +
      '<button type="button" class="ghost" id="help-demo-tour">Демо-тур (5 шагов)</button>' +
      '<button type="button" class="ghost" id="help-reset-tours">Сбросить все туры</button>' +
      "</div>" +
      '<p class="source-line" id="help-learn-status" data-tour="help-learn-status">Туры хранятся в localStorage ключами cabin_tour_v1:*.</p>' +
      "</section>" +
      '<section class="panel" data-tour="help-version">' +
      "<h3>Версия</h3>" +
      '<p data-tour="help-cabin-version">Кабинет <strong>' +
      escapeHtml(CABIN_UI_VERSION) +
      "</strong> — операторский интерфейс тестовой лаборатории (paper/sandbox). " +
      "Источник истины по экранам: TZ-CABIN.md (этапы 01–30). " +
      "Приёмка оператора: CABIN-ACCEPTANCE.md · фиксация: CABIN-FINAL.md.</p>" +
      "</section>" +
      '<section class="panel" data-tour="help-limits">' +
      "<h3>Ограничения продукта</h3>" +
      "<p data-tour=\"help-known-limits\">Известные границы (не баги «потом допилим»):</p>" +
      "<ul class=\"help-list\">" +
      "<li>Нет боевого торгового интерфейса и ввода боевого токена.</li>" +
      "<li>Нет стакана и графического терминала (TradingView / DOM).</li>" +
      "<li>Нет чата с языковой моделью в кабинете.</li>" +
      "<li>Нет мультиаккаунта, RBAC и SSO.</li>" +
      "<li>Нет маркетингового лендинга.</li>" +
      "<li>Кабинет не заменяет бэкенд-ТЗ 001–156 — это операторский экран поверх уже сделанного контура.</li>" +
      "<li>Цифры — paper-книга лаборатории, не баланс экрана брокера.</li>" +
      "</ul></section>";

    byId("help-demo-tour").addEventListener("click", startHelpDemoTour);
    byId("help-overview-tour").addEventListener("click", function () {
      if (window.CabinTour) CabinTour.reset(OVERVIEW_TOUR_KEY);
      startOverviewTour();
    });
    byId("help-reset-tours").addEventListener("click", function () {
      var n = window.CabinTour ? CabinTour.resetAll() : 0;
      byId("help-learn-status").textContent =
        "Сброшено туров: " + n + ". Можно снова пройти Обзор или демо.";
    });
  }

  function renderPlaceholder(route) {
    byId("page-body").innerHTML =
      '<section class="panel">' +
      "<h3>Раздел готовится</h3>" +
      "<p>Вы вошли по токену кабины. Содержимое «" +
      escapeHtml(route.title) +
      "» появится в следующих этапах.</p>" +
      '<p class="soon">Домашний экран уже в «Обзоре». Откройте его, чтобы видеть капитал, очередь решений и рукава.</p>' +
      "</section>";
  }

  function agentsBannerHtml() {
    var on = !!(lastStatus && lastStatus.agents_enabled);
    if (on) {
      return (
        '<div class="attention info" data-tour="agents-banner">' +
        "<span><strong>Очередь решений.</strong> Сейчас планы появляются только из Рекомендаций → «В очередь». Фоновые агенты ордера сами не кладут. В брокер ничего не уходит.</span>" +
        "</div>"
      );
    }
    return (
      '<div class="attention calm" data-tour="agents-banner">' +
      "<span><strong>Фоновые агенты выключены.</strong> Планы всё равно можно добавить из Рекомендаций → «В очередь».</span>" +
      "</div>"
    );
  }

  function agentsHowHtml() {
    return (
      '<div class="agents-how" data-tour="agents-how">' +
      '<div class="agents-how-step"><span>1</span><strong>Предложение</strong><p>Рекомендации → «В очередь»</p></div>' +
      '<div class="agents-how-step"><span>2</span><strong>Ваше решение</strong><p>Принять или отклонить</p></div>' +
      '<div class="agents-how-step"><span>3</span><strong>Paper</strong><p>Только внутренняя книга</p></div>' +
      "</div>"
    );
  }

  function agentsStatsHtml(waitingCount, recentCount, agentsOn) {
    return (
      '<div class="metrics agents-stats" data-tour="agents-stats">' +
      '<div class="metric hero"><div class="k">статус</div><div class="v">' +
      (agentsOn ? "вкл" : "выкл") +
      "</div></div>" +
      '<div class="metric hero"><div class="k">ждут решения</div><div class="v">' +
      escapeHtml(String(waitingCount)) +
      "</div></div>" +
      '<div class="metric"><div class="k">недавние</div><div class="v">' +
      escapeHtml(String(recentCount)) +
      "</div></div>" +
      "</div>"
    );
  }

  function proposalStatusChipClass(status) {
    if (status === "proposed") return "is-wait";
    if (status === "approved") return "is-ok";
    if (status === "rejected") return "is-bad";
    if (status === "expired") return "is-muted";
    return "";
  }

  function orderRejectLabel(code) {
    var key = String(code || "");
    if (!key) return "—";
    if (ORDER_REJECT_RU[key]) return ORDER_REJECT_RU[key];
    return "Отклонено: " + key;
  }

  function riskReasonLabel(code) {
    var full = ORDER_REJECT_RU[String(code || "")];
    if (full) return full.replace(/^Отклонено:\s*/i, "");
    return String(code || "") || "риск";
  }

  function orderStatusLabel(status) {
    var key = String(status || "");
    return ORDER_STATUS_RU[key] || key || "—";
  }

  function orderSideLabel(side) {
    if (side === "buy") return "покупка";
    if (side === "sell") return "продажа";
    return side || "—";
  }

  function agentsFlashHtml() {
    if (!lastAgentsFlash) return "";
    var tone = lastAgentsFlash.tone || "info";
    var cls =
      tone === "warn" ? "warn" : tone === "ok" ? "info" : tone === "bad" ? "warn" : "calm";
    return (
      '<div class="attention ' +
      cls +
      '" data-tour="agents-flash" role="status">' +
      "<span>" +
      escapeHtml(lastAgentsFlash.text) +
      "</span>" +
      '<div class="actions"><button type="button" class="ghost" id="agents-flash-dismiss">Скрыть</button></div>' +
      "</div>"
    );
  }

  function explainApproveResult(data) {
    var order = data && data.order;
    if (order && order.status === "rejected") {
      var reason =
        (order.raw && (order.raw.reject_reason || order.raw.reason)) || "risk";
      return {
        tone: "warn",
        text:
          "Принято вами, но риск отклонил ордер: " +
          riskReasonLabel(reason) +
          ". Предложение остаётся в очереди — исправьте условия или отклоните.",
      };
    }
    if (data && data.status === "approved") {
      if (data.weights) {
        return {
          tone: "ok",
          text: "Принято. Новые веса рукавов применены. Сделки сами не открылись.",
        };
      }
      return {
        tone: "ok",
        text:
          "Одобрено. Paper-заявка прошла риск и сохранена только во внутреннем Журнале" +
          (order && order.ticker ? " (" + order.ticker + ")" : "") +
          ". В брокер она не отправлена.",
      };
    }
    return {
      tone: "info",
      text: "Ответ сервера получен, но итог неочевиден — обновите список предложений.",
    };
  }

  function upsertProposalLocal(data) {
    if (!data || !data.id) return;
    var found = false;
    lastProposals = (lastProposals || []).map(function (row) {
      if (row.id === data.id) {
        found = true;
        return data;
      }
      return row;
    });
    if (!found) lastProposals = [data].concat(lastProposals || []);
    lastProposals = sortProposalsProposedFirst(lastProposals);
    renderQueueBadge();
  }

  function proposalCardHtml(row, opts) {
    var waiting = row.status === "proposed";
    var payload = row.payload || {};
    var payloadJson = JSON.stringify(row.payload || {}, null, 2);
    var isOrder = row.kind === "order" || !!payload.ticker;
    var thesis = payload.reason || proposalSummary(row);
    var title = isOrder
      ? String(payload.ticker || "—")
      : proposalKindLabel(row.kind);
    var subtitle = isOrder
      ? orderSideLabel(payload.side) +
        " · " +
        String(payload.qty || "—") +
        " шт." +
        (payload.lot ? " · лот " + String(payload.lot) : "") +
        (payload.sleeve
          ? " · " + (SLEEVE_NAMES[payload.sleeve] || payload.sleeve)
          : "")
      : proposalSummary(row);
    var facts = "";
    if (isOrder) {
      facts =
        '<div class="proposal-facts">' +
        '<div><span>цена</span><strong>' +
        escapeHtml(payload.entry_price != null ? money(payload.entry_price) : "—") +
        "</strong></div>" +
        '<div><span>стоп</span><strong>' +
        escapeHtml(payload.stop != null ? money(payload.stop) : "—") +
        "</strong></div>" +
        '<div><span>цена на</span><strong>' +
        escapeHtml(
          payload.price_as_of ? dateTimeLabel(payload.price_as_of) : "—"
        ) +
        "</strong></div></div>";
    }
    var actions = "";
    if (waiting) {
      actions =
        '<div class="proposal-actions" data-tour="agents-actions">' +
        '<button type="button" class="primary" data-approve="' +
        escapeHtml(row.id) +
        '">' +
        (isOrder ? "Одобрить paper-план" : "Принять веса") +
        "</button>" +
        '<button type="button" class="ghost" data-reject="' +
        escapeHtml(row.id) +
        '">Отклонить</button>' +
        "</div>";
    }
    return (
      '<article class="proposal-card large' +
      (waiting ? " is-waiting" : "") +
      '" data-proposal-id="' +
      escapeHtml(row.id) +
      '" data-tour="' +
      (opts && opts.tour ? opts.tour : "agents-card") +
      '">' +
      '<div class="proposal-head">' +
      '<div class="proposal-title-block">' +
      '<div class="kind">' +
      escapeHtml(proposalKindLabel(row.kind)) +
      "</div>" +
      "<h4>" +
      escapeHtml(title) +
      "</h4>" +
      '<p class="summary">' +
      escapeHtml(subtitle) +
      "</p></div>" +
      '<span class="status-chip ' +
      proposalStatusChipClass(row.status) +
      '">' +
      escapeHtml(proposalStatusLabel(row.status)) +
      "</span></div>" +
      '<p class="proposal-thesis">' +
      escapeHtml(thesis) +
      "</p>" +
      facts +
      (waiting
        ? '<p class="will-do" data-tour="agents-will-do"><strong>После одобрения:</strong> ' +
          escapeHtml(proposalWillDo(row)) +
          "</p>"
        : "") +
      actions +
      '<details class="fold tight"><summary>Подробнее</summary><pre class="payload">' +
      escapeHtml(payloadJson) +
      "</pre></details></article>"
    );
  }

  function bindAgentsActions() {
    var dismiss = byId("agents-flash-dismiss");
    if (dismiss) {
      dismiss.addEventListener("click", function () {
        lastAgentsFlash = null;
        renderAgents();
      });
    }
    document.querySelectorAll("[data-approve]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var id = btn.getAttribute("data-approve");
        var row = (lastProposals || []).filter(function (item) {
          return item.id === id;
        })[0];
        askConfirm({
          title:
            row && row.kind === "weights"
              ? "Принять новые веса?"
              : "Одобрить paper-план?",
          text:
            (row ? proposalSummary(row) + ". " : "") +
            (row && row.kind === "weights"
              ? "Веса применятся в аллокаторе; сделки автоматически не откроются."
              : "После риск-проверки заявка сохранится только во внутренней paper-книге. В T‑Invest sandbox и на биржу ничего не отправляется."),
          okLabel:
            row && row.kind === "weights" ? "Принять веса" : "Одобрить paper-план",
          danger: false,
        }).then(function (ok) {
          if (!ok) return;
          btn.disabled = true;
          apiPost("/proposals/" + encodeURIComponent(id) + "/approve")
            .then(function (data) {
              lastAgentsFlash = explainApproveResult(data);
              if (data && data.status === "approved") {
                upsertProposalLocal(data);
              }
              return refreshProposals();
            })
            .catch(function (err) {
              lastAgentsFlash = {
                tone: "bad",
                text:
                  "Не удалось принять предложение" +
                  (err && err.status ? " (HTTP " + err.status + ")" : "") +
                  ".",
              };
              renderAgents();
            });
        });
      });
    });
    document.querySelectorAll("[data-reject]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var id = btn.getAttribute("data-reject");
        var row = (lastProposals || []).filter(function (item) {
          return item.id === id;
        })[0];
        askConfirm({
          title: "Отклонить предложение?",
          text:
            (row ? proposalSummary(row) + ". " : "") +
            "Предложение уйдёт из очереди без сделки и без смены весов.",
          okLabel: "Отклонить",
          danger: true,
        }).then(function (ok) {
          if (!ok) return;
          btn.disabled = true;
          apiPost("/proposals/" + encodeURIComponent(id) + "/reject")
            .then(function (data) {
              lastAgentsFlash = {
                tone: "ok",
                text: "Отклонено вами. Сделка не отправлялась.",
              };
              upsertProposalLocal(data);
              return refreshProposals();
            })
            .catch(function (err) {
              lastAgentsFlash = {
                tone: "bad",
                text:
                  "Не удалось отклонить" +
                  (err && err.status ? " (HTTP " + err.status + ")" : "") +
                  ".",
              };
              renderAgents();
            });
        });
      });
    });
  }

  function renderAgents() {
    var body = byId("page-body");
    var waiting = proposedList(lastProposals);
    var recent = recentProposals(lastProposals);
    var agentsOn = !!(lastStatus && lastStatus.agents_enabled);
    var waitingHtml = "";
    if (waiting.length) {
      waitingHtml =
        '<div class="proposal-cards">' +
        waiting
          .map(function (row, i) {
            return proposalCardHtml(row, {
              tour: i === 0 ? "agents-card" : "agents-card-more",
            });
          })
          .join("") +
        "</div>";
    } else if (loadErrors.proposals) {
      waitingHtml =
        blockErrorHtml("proposals") ||
        '<p class="empty" data-tour="agents-waiting-empty">Очередь не загрузилась.</p>';
    } else if (!agentsOn) {
      waitingHtml =
        '<div class="agents-empty" data-tour="agents-waiting-empty">' +
        "<strong>Очередь пуста.</strong>" +
        "<p>Добавьте план из Рекомендаций → «В очередь».</p>" +
        '<a class="panel-link" href="#/recommendations">Открыть Рекомендации</a></div>';
    } else {
      waitingHtml =
        '<div class="agents-empty" data-tour="agents-waiting-empty">' +
        "<strong>Сейчас нечего решать.</strong>" +
        "<p>Когда появится предложение — карточка будет здесь.</p>" +
        '<a class="panel-link" href="#/recommendations">Открыть Рекомендации → В очередь</a></div>';
    }
    var recentHtml = "";
    if (recent.length) {
      recentHtml = wrapTableScroll(
        '<table class="data-table" data-tour="agents-recent">' +
          "<thead><tr><th>тип</th><th>статус</th><th>кратко</th></tr></thead><tbody>" +
          recent
            .map(function (row) {
              var expired = proposalExpiredReasonLabel(row);
              return (
                "<tr><td>" +
                escapeHtml(proposalKindLabel(row.kind)) +
                '</td><td><span class="status-chip ' +
                proposalStatusChipClass(row.status) +
                '">' +
                escapeHtml(proposalStatusLabel(row.status)) +
                "</span></td><td>" +
                escapeHtml(
                  proposalSummary(row) + (expired ? " · " + expired : "")
                ) +
                "</td></tr>"
              );
            })
            .join("") +
          "</tbody></table>"
      );
    } else {
      recentHtml =
        '<p class="empty">Пока пусто. После принятия или отклонения строки появятся здесь.</p>';
    }
    body.innerHTML =
      '<section class="panel agents-panel" data-tour="agents-panel">' +
      "<h3>Агенты</h3>" +
      '<p class="muted-note">Это очередь решений, не лента «умных агентов». Paper — не брокер.</p>' +
      agentsBannerHtml() +
      agentsHowHtml() +
      agentsStatsHtml(waiting.length, recent.length, agentsOn) +
      agentsFlashHtml() +
      "</section>" +
      '<section class="panel" id="agents-waiting" data-tour="agents-waiting">' +
      "<h3>Ждут решения · " +
      escapeHtml(String(waiting.length)) +
      "</h3>" +
      waitingHtml +
      "</section>" +
      '<section class="panel" data-tour="agents-recent-panel">' +
      "<h3>Недавние</h3>" +
      recentHtml +
      "</section>";
    bindAgentsActions();
    if (agentsFocusProposed || hashQuery().tab === "proposed") {
      agentsFocusProposed = false;
      var el = byId("agents-waiting");
      if (el && el.scrollIntoView) {
        window.setTimeout(function () {
          el.scrollIntoView({
            behavior: "smooth",
            block: "start",
            inline: "nearest",
          });
        }, 40);
      }
    }
  }

  function normalizeSleeves(list) {
    var byIdMap = {};
    (list || []).forEach(function (row) {
      if (row && row.sleeve) byIdMap[row.sleeve] = row;
    });
    return ACTIVE_SLEEVE_IDS.map(function (id) {
      var row = byIdMap[id];
      if (row) return row;
      return {
        sleeve: id,
        pnl: { realized: 0, unrealized: 0, total: 0 },
      };
    });
  }

  function allocBySleeve() {
    var map = {};
    var rows = (lastAllocation && lastAllocation.sleeves) || [];
    rows.forEach(function (row) {
      if (row && row.sleeve) map[row.sleeve] = row;
    });
    return map;
  }

  function planBySleeve() {
    var map = {};
    var rows = (lastAllocPlan && lastAllocPlan.sleeves) || [];
    rows.forEach(function (row) {
      if (row && row.sleeve) map[row.sleeve] = row;
    });
    return map;
  }

  function tradingPoolRub() {
    var plan = lastAllocPlan;
    if (plan && plan.trading_pool != null) return Number(plan.trading_pool);
    var alloc = lastAllocation || {};
    var equity = Number(alloc.equity);
    var share = Number(alloc.sleeve_share != null ? alloc.sleeve_share : 0.4);
    if (!isFinite(equity) || equity <= 0) return 0;
    return equity * share;
  }

  function nameShareValue() {
    var plan = lastAllocPlan;
    if (plan && plan.name_share != null) return Number(plan.name_share);
    return 0.1;
  }

  function stopPctValue() {
    var plan = lastAllocPlan;
    if (plan && plan.stop_pct != null) return Number(plan.stop_pct);
    return 0.05;
  }

  function whatIfForCapital(capitalRub) {
    var capital = parseRubInput(capitalRub);
    if (!isFinite(capital) || capital <= 0) return null;
    var nameShare = nameShareValue();
    var price = Number(planExamplePrice) || 250;
    var lot = 1;
    var nameBudget = capital * nameShare;
    var lotCost = price * lot;
    var qty = lotCost > 0 ? Math.floor(nameBudget / lotCost) : 0;
    var maxNames = nameShare > 0 ? Math.floor(1 / nameShare) : 0;
    return {
      capital: capital,
      nameBudget: nameBudget,
      qty: qty,
      notional: qty * lotCost,
      maxNames: maxNames,
      stopPct: stopPctValue(),
      price: price,
    };
  }

  function capitalSetupValues() {
    var plan = lastAllocPlan || {};
    var book = (lastStatus && lastStatus.portfolio) || {};
    var cash = book.cash != null ? book.cash : plan.equity;
    var namePct =
      plan.name_share != null
        ? Math.round(Number(plan.name_share) * 1000) / 10
        : 10;
    var depositDefault =
      cash != null && isFinite(Number(cash))
        ? Math.round(Number(cash))
        : 1000000;
    return {
      plan: plan,
      cash: cash,
      namePct: namePct,
      depositDefault: depositDefault,
    };
  }

  function renderCapitalSettingsForm(prefix) {
    var vals = capitalSetupValues();
    var idDeposit = prefix + "-deposit-amount";
    var idDepositBtn = prefix + "-deposit-save";
    var idName = prefix + "-name-share";
    var idNameBtn = prefix + "-name-share-save";
    var idStatus = prefix + "-capital-status";
    return (
      '<div class="filters" data-tour="' +
      prefix +
      '-capital-form">' +
      '<label class="field compact">депозит (торговый кэш), ₽' +
      '<input type="text" inputmode="decimal" data-rub-input id="' +
      idDeposit +
      '" value="' +
      escapeHtml(formatRubGrouped(vals.depositDefault)) +
      '"></label>' +
      '<button type="button" class="primary" id="' +
      idDepositBtn +
      '">Применить депозит</button>' +
      '<label class="field compact">макс. на одну бумагу, %' +
      '<input type="number" min="1" max="50" step="0.5" id="' +
      idName +
      '" value="' +
      escapeHtml(String(vals.namePct)) +
      '"></label>' +
      '<button type="button" class="primary" id="' +
      idNameBtn +
      '">Сохранить лимит</button>' +
      "</div>" +
      '<p class="source-line" id="' +
      idStatus +
      '">' +
      "Сейчас кэш " +
      money(vals.cash) +
      ", лимит на бумагу " +
      escapeHtml(pctLabel(vals.plan.name_share != null ? vals.plan.name_share : 0.1)) +
      " → до ≤" +
      escapeHtml(
        String(
          vals.plan.max_concurrent_names != null
            ? vals.plan.max_concurrent_names
            : 10
        )
      ) +
      " имён в рукаве." +
      "</p>"
    );
  }

  function renderSettings() {
    var body = byId("page-body");
    var vals = capitalSetupValues();
    body.innerHTML =
      '<section class="panel" data-tour="settings-capital">' +
      '<h3 data-tour="settings-title">Депозит и лимит на бумагу</h3>' +
      '<div class="callout warn" data-tour="settings-disclaimer">' +
      "<strong>Рамка.</strong> Аналитика тестовой лаборатории. Не индивидуальная инвестиционная рекомендация и не услуга ИК. " +
      'Кандидаты по фундаменту — в <a class="panel-link" href="#/recommendations">Рекомендациях</a>.' +
      "</div>" +
      "<p data-tour=\"settings-intro\">" +
      "Здесь задаётся капитал лаборатории. Депозит <strong>дотягивает</strong> торговый кэш до суммы и не уменьшает его. " +
      "«Макс. на одну бумагу» — доля бюджета рукава на тикер (1–50%): влияет на план, размер позиции и risk-gate." +
      "</p>" +
      renderCapitalSettingsForm("settings") +
      "</section>" +
      '<section class="panel" data-tour="settings-sleeves">' +
      "<h3>Бюджеты рукавов</h3>" +
      "<p>Доли стратегий (SMA, Дончиан, RSI, скальп) настраиваются в разделе " +
      '<a class="panel-link" href="#/strategies">Стратегии</a> — блок «Бюджеты рукавов».</p>' +
      '<div class="metrics tight">' +
      '<div class="metric"><div class="k">кэш сейчас</div><div class="v">' +
      money(vals.cash) +
      "</div></div>" +
      '<div class="metric"><div class="k">лимит на бумагу</div><div class="v">' +
      escapeHtml(pctLabel(vals.plan.name_share != null ? vals.plan.name_share : 0.1)) +
      "</div></div>" +
      '<div class="metric"><div class="k">имён сразу</div><div class="v">≤ ' +
      escapeHtml(
        String(
          vals.plan.max_concurrent_names != null
            ? vals.plan.max_concurrent_names
            : "—"
        )
      ) +
      "</div></div></div></section>";
    wireRubInputs(byId("page-body"));
    bindCapitalSettingsActions("settings", function () {
      refreshSettings();
    });
  }

  function refreshSettings() {
    return Promise.all([
      apiGet("/status")
        .then(function (data) {
          lastStatus = data;
          lastStatusAt = new Date();
          return data;
        })
        .catch(function () {
          return null;
        }),
      apiGet("/allocation/plan")
        .then(function (plan) {
          lastAllocPlan = plan;
          return plan;
        })
        .catch(function () {
          return null;
        }),
      apiGet("/allocation")
        .then(function (data) {
          lastAllocation = data;
          return data;
        })
        .catch(function () {
          return null;
        }),
    ]).then(function () {
      if (currentRoute === "settings") renderSettings();
    });
  }

  function fundScoreTone(score) {
    var n = Number(score);
    if (!isFinite(n)) return "fund-tone--muted";
    if (n >= 70) return "fund-tone--good";
    if (n >= 45) return "fund-tone--mid";
    return "fund-tone--bad";
  }

  function fundScoreLabel(score) {
    var n = Number(score);
    if (!isFinite(n)) return "нет данных";
    if (n >= 70) return "сильно";
    if (n >= 45) return "средне";
    return "слабо";
  }

  function fundPctLabel(value) {
    if (value == null || value === "") return "—";
    var n = Number(value);
    if (!isFinite(n)) return "—";
    var pct = Math.abs(n) <= 1.5 ? n * 100 : n;
    return (Math.round(pct * 10) / 10).toFixed(1) + "%";
  }

  function fundDivLabel(row) {
    if (row && row.dividend_yield_outlier && row.dividend_yield_ttm == null) {
      return "н/д";
    }
    return fundPctLabel(row && row.dividend_yield_ttm);
  }

  function fundToneCell(score, text) {
    return (
      '<td class="' +
      fundScoreTone(score) +
      '"><span class="fund-pill">' +
      escapeHtml(text) +
      "</span></td>"
    );
  }

  function fundCompanyRow(row, idx, opts) {
    opts = opts || {};
    var showSector = opts.showSector !== false;
    var scores = row.scores || {};
    var total = scores.total;
    var isTop = opts.ranked && idx < 5 && Number(total) >= 45;
    return (
      '<tr class="' +
      (isTop ? "fund-row--top " : "") +
      fundScoreTone(total) +
      '-row">' +
      '<td class="fund-company"><div class="fund-name-cell"><strong>' +
      escapeHtml(row.ticker || "—") +
      "</strong><span>" +
      escapeHtml(row.name || row.ticker || "—") +
      "</span></div></td>" +
      (showSector
        ? "<td>" + escapeHtml(row.sector_title || "Прочее") + "</td>"
        : "") +
      fundToneCell(
        total,
        String(total != null ? total : "—") + " · " + fundScoreLabel(total)
      ) +
      fundToneCell(
        scores.value,
        String(scores.value != null ? scores.value : "—")
      ) +
      fundToneCell(
        scores.quality,
        String(scores.quality != null ? scores.quality : "—")
      ) +
      fundToneCell(
        scores.div,
        String(scores.div != null ? scores.div : "—")
      ) +
      "<td>" +
      escapeHtml(row.pe_ratio_ttm != null ? String(row.pe_ratio_ttm) : "—") +
      "</td><td>" +
      escapeHtml(
        row.price_to_book_ttm != null ? String(row.price_to_book_ttm) : "—"
      ) +
      "</td><td>" +
      escapeHtml(fundPctLabel(row.roe)) +
      "</td><td>" +
      escapeHtml(fundDivLabel(row)) +
      "</td><td class=\"fund-verdict " +
      fundScoreTone(total) +
      '">' +
      escapeHtml(
        Number(total) >= 70
          ? "интереснее к покупке"
          : Number(total) >= 45
            ? "нейтрально"
            : "слабее / дороже"
      ) +
      "</td></tr>"
    );
  }

  function fundTableHtml(rows, opts) {
    opts = opts || {};
    var showSector = opts.showSector !== false;
    return (
      '<table class="data-table fund-table"' +
      (opts.tour ? ' data-tour="' + escapeHtml(opts.tour) + '"' : "") +
      ">" +
      "<thead><tr>" +
      "<th>компания</th>" +
      (showSector ? "<th>сектор</th>" : "") +
      "<th>скор</th><th>оценка</th><th>качество</th><th>дивиденды</th>" +
      "<th>P/E</th><th>P/B</th><th>ROE</th><th>див.</th><th>вердикт</th>" +
      "</tr></thead><tbody>" +
      rows
        .map(function (row, idx) {
          return fundCompanyRow(row, idx, {
            ranked: opts.ranked,
            showSector: showSector,
          });
        })
        .join("") +
      "</tbody></table>"
    );
  }

  function fundCompanyMatches(row, query) {
    var q = String(query || "").trim().toLowerCase();
    if (!q) return true;
    var ticker = String(row.ticker || "").toLowerCase();
    var name = String(row.name || "").toLowerCase();
    return ticker.indexOf(q) >= 0 || name.indexOf(q) >= 0;
  }

  function renderCompanies(opts) {
    if (deskMode() === "test") {
      renderTestCompanies();
      return;
    }
    opts = opts || {};
    var body = byId("page-body");
    var data = lastFundamentals || { items: [], disclaimer: "", sectors: [] };
    var items = (data.items || []).slice().sort(function (a, b) {
      var sa = Number((a.scores || {}).total);
      var sb = Number((b.scores || {}).total);
      if (!isFinite(sa)) sa = -1;
      if (!isFinite(sb)) sb = -1;
      return sb - sa;
    });
    var sectors = data.sectors && data.sectors.length
      ? data.sectors
      : [];
    var activeSector = lastCompaniesSector || "all";
    var query = lastCompaniesQuery || "";
    if (/демо/i.test(String(lastCompaniesNote || ""))) {
      lastCompaniesNote = "";
    }
    var matched = items.filter(function (row) {
      return fundCompanyMatches(row, query);
    });
    var visible =
      activeSector === "all"
        ? matched
        : matched.filter(function (row) {
            return row.sector === activeSector;
          });
    var top = visible.filter(function (row) {
      return Number((row.scores || {}).total) >= 70;
    }).slice(0, 5);
    if (!top.length) top = visible.slice(0, 5);
    var sectorCounts = {};
    matched.forEach(function (row) {
      var id = row.sector || "other";
      sectorCounts[id] = (sectorCounts[id] || 0) + 1;
    });
    var searchBar =
      '<div class="fund-search-bar">' +
      '<label class="field compact">поиск' +
      '<input type="search" id="companies-search" placeholder="тикер или название (IRAO, Интер)" value="' +
      escapeHtml(query) +
      '" autocomplete="off" spellcheck="false">' +
      "</label>" +
      (query
        ? '<button type="button" class="ghost" id="companies-search-clear">Сбросить</button>'
        : "") +
      (query
        ? '<span class="fund-search-count">' +
          escapeHtml(String(visible.length)) +
          " из " +
          escapeHtml(String(items.length)) +
          "</span>"
        : "") +
      "</div>";
    var sectorChips =
      '<div class="fund-sector-chips" data-tour="companies-sectors">' +
      '<button type="button" class="fund-chip' +
      (activeSector === "all" ? " is-active" : "") +
      '" data-fund-sector="all">Все (' +
      matched.length +
      ")</button>" +
      sectors
        .map(function (sector) {
          var count = query
            ? sectorCounts[sector.id] || 0
            : sector.count || 0;
          return (
            '<button type="button" class="fund-chip' +
            (activeSector === sector.id ? " is-active" : "") +
            '" data-fund-sector="' +
            escapeHtml(sector.id) +
            '">' +
            escapeHtml(sector.title || sector.id) +
            " (" +
            escapeHtml(String(count)) +
            ")</button>"
          );
        })
        .join("") +
      "</div>";
    var topCards = top.length
      ? '<div class="fund-top" data-tour="companies-top">' +
        "<h4>Топ к покупке" +
        (activeSector === "all"
          ? ""
          : " · " + escapeHtml((top[0] && top[0].sector_title) || "")) +
        "</h4>" +
        '<p class="fund-top-note">Зелёный ≥70 — сильнее по оценке/качеству/дивидендам внутри выбранного среза. Не сигнал брокера.</p>' +
        '<div class="fund-top-grid">' +
        top
          .map(function (row, idx) {
            var scores = row.scores || {};
            return (
              '<article class="fund-top-card ' +
              fundScoreTone(scores.total) +
              '">' +
              '<div class="fund-top-rank">#' +
              (idx + 1) +
              " · " +
              escapeHtml(row.sector_title || "") +
              "</div>" +
              "<h5>" +
              escapeHtml(row.ticker || "—") +
              "</h5><p class=\"fund-top-name\">" +
              escapeHtml(row.name || row.ticker || "—") +
              '</p><div class="fund-top-score">' +
              escapeHtml(String(scores.total != null ? scores.total : "—")) +
              " <small>" +
              escapeHtml(fundScoreLabel(scores.total)) +
              "</small></div>" +
              '<div class="fund-top-meta">оценка ' +
              escapeHtml(String(scores.value != null ? scores.value : "—")) +
              " · качество " +
              escapeHtml(String(scores.quality != null ? scores.quality : "—")) +
              " · див. " +
              escapeHtml(String(scores.div != null ? scores.div : "—")) +
              "</div></article>"
            );
          })
          .join("") +
        "</div></div>"
      : "";
    var sectorBlocks =
      activeSector === "all" && sectors.length
        ? sectors
            .map(function (sector) {
              var rows = (sector.items || []).filter(function (row) {
                return fundCompanyMatches(row, query);
              });
              if (!rows.length) return "";
              return (
                '<section class="fund-sector-block" data-fund-sector-block="' +
                escapeHtml(sector.id) +
                '">' +
                "<h4>" +
                escapeHtml(sector.title || sector.id) +
                " · " +
                escapeHtml(String(rows.length)) +
                " · лучший скор " +
                escapeHtml(
                  String(
                    rows[0] && rows[0].scores && rows[0].scores.total != null
                      ? rows[0].scores.total
                      : sector.top_score != null
                        ? sector.top_score
                        : "—"
                  )
                ) +
                "</h4>" +
                wrapTableScroll(
                  fundTableHtml(rows, { ranked: true, showSector: false }),
                  true
                ) +
                "</section>"
              );
            })
            .join("") ||
          (query
            ? '<p class="empty" data-tour="companies-empty">Ничего не найдено по «' +
              escapeHtml(query) +
              '».</p>'
            : "")
        : visible.length
          ? wrapTableScroll(
              fundTableHtml(visible, {
                ranked: true,
                showSector: activeSector === "all",
                tour: "companies-table",
              }),
              true
            )
          : '<p class="empty" data-tour="companies-empty">' +
            (query
              ? "Ничего не найдено по «" + escapeHtml(query) + "»."
              : "В этом секторе пока нет снимков.") +
            "</p>";
    var empty = !items.length
      ? '<p class="empty" data-tour="companies-empty">Снимков ещё нет. Нажмите «Обновить с брокера» — подтянем TQBR и фундамент с Тинькофф.</p>'
      : "";
    body.innerHTML =
      '<section class="panel" data-tour="companies-panel">' +
      "<h3>Компании</h3>" +
      '<div class="callout" data-tour="companies-explain">' +
      "<strong>Что смотреть.</strong> Все акции РФ с Тинькофф (MOEX TQBR): " +
      escapeHtml(String(items.length || data.count || 0)) +
      " шт. Название, отрасль и скор. Сверху — топ; ниже — сектора. " +
      'Дальше — <a class="panel-link" href="#/recommendations">Рекомендации</a>. ' +
      "<br>Источник: живой фундамент с брокера Тинькофф. " +
      "Воркер обновляет снимки каждые 6 часов; кнопка — вне очереди." +
      "</div>" +
      '<div class="panel-actions">' +
      '<button type="button" class="primary" id="companies-refresh">Обновить с брокера</button>' +
      "</div>" +
      '<p class="source-line" id="companies-status">' +
      escapeHtml(
        lastCompaniesNote ||
          "Всего с брокера: " +
            String(items.length || data.count || 0) +
            ". Автообновление каждые 6 часов. " +
            (data.disclaimer || "")
      ) +
      "</p>" +
      (lastCandlesCoverage
        ? '<p class="source-line" id="companies-candles">' +
          escapeHtml(
            "Дневные свечи ~2г: " +
              String(lastCandlesCoverage.ready || 0) +
              "/" +
              String(lastCandlesCoverage.total || items.length || 0) +
              " · нет файла: " +
              String(lastCandlesCoverage.missing || 0) +
              " · коротких: " +
              String(lastCandlesCoverage.short || 0)
          ) +
          "</p>"
        : "") +
      (items.length ? searchBar + sectorChips + topCards + sectorBlocks : empty) +
      "</section>";
    var refreshBtn = byId("companies-refresh");
    var searchInput = byId("companies-search");
    var clearSearch = byId("companies-search-clear");
    document.querySelectorAll("[data-fund-sector]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        lastCompaniesSector = btn.getAttribute("data-fund-sector") || "all";
        renderCompanies();
      });
    });
    if (searchInput) {
      searchInput.addEventListener("input", function () {
        lastCompaniesQuery = searchInput.value || "";
        var caret = searchInput.selectionStart;
        renderCompanies({ keepSearchFocus: true, caret: caret });
      });
      if (opts.keepSearchFocus) {
        searchInput.focus();
        var pos =
          opts.caret != null ? opts.caret : searchInput.value.length;
        try {
          searchInput.setSelectionRange(pos, pos);
        } catch (err) {
          /* ignore */
        }
      }
    }
    if (clearSearch) {
      clearSearch.addEventListener("click", function () {
        lastCompaniesQuery = "";
        renderCompanies({ keepSearchFocus: true, caret: 0 });
      });
    }
    if (refreshBtn) {
      refreshBtn.addEventListener("click", function () {
        refreshBtn.disabled = true;
        lastCompaniesNote =
          "Обновляю все акции РФ TQBR с брокера (может занять минуту)…";
        renderCompanies();
        var busy = byId("companies-refresh");
        if (busy) busy.disabled = true;
        apiPost("/fundamentals/refresh", {}, { timeoutMs: FETCH_TIMEOUT_BATCH_MS })
          .then(function (payload) {
            lastCompaniesNote =
              "С брокера обновлено: " + (payload.upserted || 0) + " записей";
            lastCompaniesSector = "all";
            return refreshCompanies();
          })
          .catch(function (err) {
            lastCompaniesNote =
              "Брокер: " + (err.message || "ошибка обновления");
            renderCompanies();
          })
          .finally(function () {
            var btn = byId("companies-refresh");
            if (btn) btn.disabled = false;
          });
      });
    }
  }

  function refreshCompanies() {
    return Promise.all([
      apiGet("/fundamentals"),
      apiGet("/candles/coverage").catch(function () {
        return null;
      }),
    ])
      .then(function (pair) {
        lastFundamentals = pair[0];
        lastCandlesCoverage = pair[1];
        rememberRefresh("fundamentals", pair[0] && pair[0].refresh);
        rememberRefresh("candles", pair[1] && pair[1].refresh);
        if (currentRoute === "companies") renderCompanies();
        return pair[0];
      })
      .catch(function (err) {
        lastFundamentals = { items: [], disclaimer: err.message || "" };
        if (currentRoute === "companies") renderCompanies();
        return null;
      });
  }

  function stopCompaniesPoll() {
    if (companiesPollTimer) {
      clearInterval(companiesPollTimer);
      companiesPollTimer = null;
    }
  }

  function startCompaniesPoll() {
    stopCompaniesPoll();
    companiesPollTimer = setInterval(function () {
      if (currentRoute !== "companies") {
        stopCompaniesPoll();
        return;
      }
      refreshCompanies();
    }, COMPANIES_POLL_MS);
  }

  function recsSkipReasonLabel(code) {
    var key = String(code || "");
    if (key === "not_in_active_universe") return "вне вселенной";
    if (key === "market_price_missing") return "нет цены";
    if (key === "market_price_stale") return "цена устарела";
    if (key === "market_price_invalid") return "цена битая";
    return key || "пропуск";
  }

  function formatRecsProposeStatus(payload) {
    var count = (payload && payload.count) || 0;
    var skipped = (payload && payload.skipped) || [];
    if (count > 0) {
      return (
        "В очереди: " +
        count +
        " paper-планов" +
        (skipped.length ? "; пропущено: " + skipped.length : "") +
        ". Открываю Агенты…"
      );
    }
    if (!skipped.length) {
      return "Нечего ставить в очередь — нет подходящих кандидатов.";
    }
    var tallies = {};
    skipped.forEach(function (row) {
      var label = recsSkipReasonLabel(row.reason);
      tallies[label] = (tallies[label] || 0) + 1;
    });
    var parts = Object.keys(tallies).map(function (label) {
      return label + " · " + tallies[label];
    });
    return (
      "В очередь не попало ничего. Причины: " +
      parts.join("; ") +
      ". Нужны тикер во вселенной и свежая цена (свечи)."
    );
  }

  function renderRecommendations() {
    var body = byId("page-body");
    var data = lastRecommendations || { candidates: [], disclaimer: "" };
    var picks = data.candidates || [];
    var cards = picks.length
      ? picks
          .map(function (row) {
            var scores = row.scores || {};
            return (
              '<article class="plan-sleeve" data-tour="rec-card-' +
              escapeHtml(row.ticker || "") +
              '">' +
              "<h4>" +
              escapeHtml(row.ticker || "—") +
              " · buy</h4>" +
              (row.name
                ? '<p class="fund-top-name">' +
                  escapeHtml(row.name) +
                  (row.sector_title
                    ? " · " + escapeHtml(row.sector_title)
                    : "") +
                  "</p>"
                : "") +
              '<div class="metrics tight">' +
              '<div class="metric hero"><div class="k">скор</div><div class="v">' +
              escapeHtml(String(scores.total != null ? scores.total : "—")) +
              "</div></div>" +
              '<div class="metric"><div class="k">оценка</div><div class="v">' +
              escapeHtml(String(scores.value != null ? scores.value : "—")) +
              "</div></div>" +
              '<div class="metric"><div class="k">качество</div><div class="v">' +
              escapeHtml(String(scores.quality != null ? scores.quality : "—")) +
              "</div></div>" +
              '<div class="metric"><div class="k">дивиденды</div><div class="v">' +
              escapeHtml(String(scores.div != null ? scores.div : "—")) +
              "</div></div></div>" +
              "<p>" +
              escapeHtml(row.rationale || "") +
              "</p></article>"
            );
          })
          .join("")
      : '<p class="empty" data-tour="recs-empty">Кандидатов нет. Сначала загрузите фундамент в «Компании» (демо или брокер).</p>';
    body.innerHTML =
      '<section class="panel" data-tour="recs-panel">' +
      "<h3>Рекомендации</h3>" +
      '<div class="callout warn" data-tour="recs-disclaimer">' +
      "<strong>Важно.</strong> " +
      escapeHtml(
        data.disclaimer ||
          "Аналитика лаборатории, не индивидуальная инвестиционная рекомендация."
      ) +
      "</div>" +
      "<p>«В очередь» создаёт paper-план только для активного инструмента со свежей рыночной ценой: объём равен одному биржевому лоту, стоп считается от зафиксированной цены. Одобрение в Агентах не отправляет заявку брокеру.</p>" +
      '<div class="panel-actions">' +
      '<button type="button" class="primary" id="recs-propose">В очередь (топ)</button>' +
      '<a class="panel-link" href="#/companies">Открыть Компании</a>' +
      '<a class="panel-link" href="#/agents">Очередь агентов</a>' +
      "</div>" +
      '<p class="source-line" id="recs-status">Готово кандидатов: ' +
      escapeHtml(String(picks.length)) +
      "</p>" +
      '<div class="plan-grid" data-tour="recs-grid">' +
      cards +
      "</div></section>";
    var proposeBtn = byId("recs-propose");
    var status = byId("recs-status");
    if (proposeBtn) {
      proposeBtn.addEventListener("click", function () {
        if (!picks.length) {
          if (status) status.textContent = "Нечего ставить в очередь — нет кандидатов.";
          return;
        }
        proposeBtn.disabled = true;
        apiPost("/recommendations/propose", { limit: 5, min_score: 40 })
          .then(function (payload) {
            if (status) {
              status.textContent = formatRecsProposeStatus(payload);
            }
            return refreshProposals().then(function () {
              if ((payload.count || 0) > 0) {
                setHash("agents");
              }
            });
          })
          .catch(function (err) {
            if (status) {
              status.textContent =
                "Не удалось поставить в очередь: " + (err.message || "ошибка");
            }
          })
          .finally(function () {
            proposeBtn.disabled = false;
          });
      });
    }
  }

  function refreshRecommendations() {
    return apiGet("/recommendations?limit=10&min_score=40")
      .then(function (data) {
        lastRecommendations = data;
        if (currentRoute === "recommendations") renderRecommendations();
        return data;
      })
      .catch(function (err) {
        lastRecommendations = {
          candidates: [],
          disclaimer: err.message || "",
        };
        if (currentRoute === "recommendations") renderRecommendations();
        return null;
      });
  }

  function bindCapitalSettingsActions(prefix, afterSave) {
    var depositBtn = byId(prefix + "-deposit-save");
    var nameShareBtn = byId(prefix + "-name-share-save");
    var capitalStatus = byId(prefix + "-capital-status");
    if (depositBtn) {
      depositBtn.addEventListener("click", function () {
        var input = byId(prefix + "-deposit-amount");
        var amount = parseRubInput(input && input.value);
        if (!isFinite(amount) || amount <= 0) {
          if (capitalStatus) {
            capitalStatus.textContent = "Укажите депозит больше нуля.";
          }
          return;
        }
        if (input) input.value = formatRubGrouped(amount);
        depositBtn.disabled = true;
        apiPost("/ledger/deposit", { amount: amount })
          .then(function (data) {
            if (capitalStatus) {
              capitalStatus.textContent =
                "Депозит: кэш " +
                money(data.cash) +
                (Number(data.topped_up) > 0
                  ? " (доложено " + money(data.topped_up) + ")"
                  : " (уже был ≥ цели)");
            }
            return typeof afterSave === "function"
              ? afterSave()
              : reloadStrategiesPlanAndStatus();
          })
          .catch(function (err) {
            if (capitalStatus) {
              capitalStatus.textContent =
                "Не удалось применить депозит: " + (err.message || "ошибка");
            }
          })
          .finally(function () {
            depositBtn.disabled = false;
          });
      });
    }
    if (nameShareBtn) {
      nameShareBtn.addEventListener("click", function () {
        var input = byId(prefix + "-name-share");
        var pct = Number(input && input.value);
        if (!isFinite(pct) || pct < 1 || pct > 50) {
          if (capitalStatus) {
            capitalStatus.textContent = "Лимит на бумагу: от 1% до 50%.";
          }
          return;
        }
        nameShareBtn.disabled = true;
        apiPut("/allocation/risk", { name_share: Math.round(pct * 10) / 1000 })
          .then(function (data) {
            if (lastAllocPlan) {
              lastAllocPlan.name_share = data.name_share;
              lastAllocPlan.max_concurrent_names = data.max_concurrent_names;
            }
            if (capitalStatus) {
              capitalStatus.textContent =
                "Лимит на бумагу сохранён: " +
                pctLabel(data.name_share) +
                " (≤" +
                String(data.max_concurrent_names) +
                " имён).";
            }
            return typeof afterSave === "function"
              ? afterSave()
              : reloadStrategiesPlanAndStatus();
          })
          .catch(function (err) {
            if (capitalStatus) {
              capitalStatus.textContent =
                "Не удалось сохранить лимит: " + (err.message || "ошибка");
            }
          })
          .finally(function () {
            nameShareBtn.disabled = false;
          });
      });
    }
  }

  function renderStrategiesCapitalSetup() {
    var vals = capitalSetupValues();
    return (
      '<section class="panel" data-tour="strategies-capital-setup">' +
      "<h3>Депозит и лимит на бумагу</h3>" +
      "<p>" +
      "Сейчас кэш " +
      money(vals.cash) +
      ", макс. на бумагу " +
      escapeHtml(pctLabel(vals.plan.name_share != null ? vals.plan.name_share : 0.1)) +
      ". Меняется в разделе " +
      '<a class="panel-link" href="#/settings">Настройки</a>.' +
      "</p></section>"
    );
  }

  function renderStrategiesPlan() {
    var plan = lastAllocPlan;
    if (!plan) {
      return (
        renderStrategiesCapitalSetup() +
        '<section class="panel" data-tour="strategies-plan">' +
        "<h3>Как рукав держит портфель</h3>" +
        '<p class="empty">План аллокации ещё не загрузился.</p></section>'
      );
    }
    var byPlan = planBySleeve();
    var tickers = plan.universe_tickers || [];
    var tickerLine = tickers.length
      ? tickers.slice(0, 12).join(", ") +
        (tickers.length > 12 ? "…" : "")
      : "пока пусто — воркер ещё не собрал вселенную";
    var whatIfNum = parseRubInput(
      planWhatIfCapital !== ""
        ? planWhatIfCapital
        : Math.round(
            Number(
              (byPlan[ACTIVE_SLEEVE_IDS[0]] &&
                byPlan[ACTIVE_SLEEVE_IDS[0]].capital) ||
                1000000
            )
          )
    );
    if (!isFinite(whatIfNum) || whatIfNum < 0) whatIfNum = 1000000;
    var whatIfInput = formatRubGrouped(whatIfNum);
    var whatIf = whatIfForCapital(whatIfNum);
    var sleeveCards = ACTIVE_SLEEVE_IDS.map(function (id) {
      var row = byPlan[id] || {};
      var ex = row.example || {};
      return (
        '<article class="plan-sleeve" data-tour="strategies-plan-' +
        escapeHtml(id) +
        '">' +
        "<h4>" +
        escapeHtml(row.title || SLEEVE_NAMES[id] || id) +
        "</h4>" +
        '<p class="source-line">горизонт: ' +
        escapeHtml(row.horizon || "дневки") +
        " · код <code>" +
        escapeHtml(id) +
        "</code></p>" +
        '<div class="metrics tight">' +
        '<div class="metric"><div class="k">бюджет рукава</div><div class="v">' +
        money(row.capital) +
        "</div></div>" +
        '<div class="metric"><div class="k">лимит на имя</div><div class="v">' +
        money(row.name_budget) +
        "</div></div>" +
        '<div class="metric"><div class="k">имён сразу</div><div class="v">≤ ' +
        escapeHtml(String(row.max_concurrent_names != null ? row.max_concurrent_names : "—")) +
        "</div></div>" +
        '<div class="metric"><div class="k">стоп</div><div class="v">' +
        escapeHtml(pctLabel(row.stop_pct)) +
        "</div></div></div>" +
        "<p><strong>Сигнал.</strong> " +
        escapeHtml(row.signal || SLEEVE_HOWTO[id] || "") +
        "</p>" +
        "<p><strong>Как держит.</strong> " +
        escapeHtml(row.holds || "") +
        "</p>" +
        '<p class="source-line">пример лота при цене ' +
        money(ex.price) +
        ": qty " +
        escapeHtml(String(ex.qty != null ? ex.qty : "—")) +
        " ≈ " +
        money(ex.notional) +
        "</p></article>"
      );
    }).join("");
    var whatIfHtml = whatIf
      ? '<div class="metrics tight" data-tour="strategies-whatif-result">' +
        '<div class="metric"><div class="k">лимит на одно имя</div><div class="v">' +
        money(whatIf.nameBudget) +
        "</div></div>" +
        '<div class="metric"><div class="k">акций (лот 1)</div><div class="v">' +
        escapeHtml(String(whatIf.qty)) +
        "</div></div>" +
        '<div class="metric"><div class="k">номинал позиции</div><div class="v">' +
        money(whatIf.notional) +
        "</div></div>" +
        '<div class="metric"><div class="k">имён параллельно</div><div class="v">≤ ' +
        escapeHtml(String(whatIf.maxNames)) +
        "</div></div>" +
        '<div class="metric"><div class="k">стоп от входа</div><div class="v">' +
        escapeHtml(pctLabel(whatIf.stopPct)) +
        "</div></div></div>" +
        '<p class="source-line">При цене ' +
        money(whatIf.price) +
        " рукав купит не больше qty = ⌊лимит / цена⌋ на тикер. " +
        "Секторов нет: деление только по тикерам вселенной и лимиту на имя.</p>"
      : "";
    return (
      renderStrategiesCapitalSetup() +
      '<section class="panel" data-tour="strategies-plan">' +
      "<h3>Как рукав держит портфель</h3>" +
      "<p>" +
      "Если на рукав выделено, например, 1&nbsp;000&nbsp;000&nbsp;₽ — это не «разложи по секторам». " +
      "Это бюджет: из него на каждое имя уходит не больше доли имени, остальное ждёт следующий сигнал." +
      "</p>" +
      '<div class="metrics" data-tour="strategies-plan-pool">' +
      '<div class="metric"><div class="k">стоимость счёта</div><div class="v">' +
      money(plan.equity) +
      "</div></div>" +
      '<div class="metric"><div class="k">торговый потолок</div><div class="v">' +
      money(plan.trading_pool) +
      ' <span class="muted-note">(' +
      escapeHtml(pctLabel(plan.sleeve_share)) +
      ")</span></div></div>" +
      '<div class="metric"><div class="k">доля на имя</div><div class="v">' +
      escapeHtml(pctLabel(plan.name_share)) +
      "</div></div>" +
      '<div class="metric"><div class="k">вселенная</div><div class="v">' +
      escapeHtml(String(plan.universe_size != null ? plan.universe_size : "—")) +
      " тик.</div></div></div>" +
      '<p class="formula" data-tour="strategies-plan-formula"><code>' +
      escapeHtml(plan.formula || "") +
      "</code></p>" +
      '<div class="callout warn" data-tour="strategies-plan-sectors">' +
      "<strong>Секторов нет.</strong> " +
      escapeHtml(plan.sectors_note || "") +
      " Сейчас в периметре: " +
      escapeHtml(tickerLine) +
      ".</div>" +
      '<div class="plan-grid">' +
      sleeveCards +
      "</div>" +
      '<div class="whatif" data-tour="strategies-whatif">' +
      "<h4>Что будет, если выделить сумму на рукав</h4>" +
      '<div class="filters">' +
      '<label class="field compact">бюджет рукава, ₽' +
      '<input type="text" inputmode="decimal" data-rub-input id="plan-whatif-capital" value="' +
      escapeHtml(whatIfInput) +
      '"></label>' +
      '<label class="field compact">пример цены акции' +
      '<input type="number" min="0.01" step="1" id="plan-example-price" value="' +
      escapeHtml(String(planExamplePrice)) +
      '"></label>' +
      "</div>" +
      whatIfHtml +
      "</div></section>"
    );
  }

  function renderStrategiesBudgets() {
    var alloc = lastAllocation || { sleeve_share: 0.4, equity: null, sleeves: [] };
    var bySleeve = allocBySleeve();
    var pool = tradingPoolRub();
    var inputs = ACTIVE_SLEEVE_IDS.map(function (id) {
      var row = bySleeve[id] || {};
      var pct =
        row.weight != null
          ? Math.round(Number(row.weight) * 1000) / 10
          : Math.round(1000 / ACTIVE_SLEEVE_IDS.length) / 10;
      var capital =
        row.capital != null
          ? Math.round(Number(row.capital))
          : Math.round((pool * pct) / 100);
      return (
        '<div class="budget-row" data-tour="strategies-budget-' +
        escapeHtml(id) +
        '">' +
        "<strong>" +
        escapeHtml(SLEEVE_NAMES[id] || id) +
        "</strong>" +
        '<label class="field compact">доля %' +
        '<input type="number" min="0" max="100" step="0.1" data-sleeve-weight="' +
        escapeHtml(id) +
        '" value="' +
        escapeHtml(String(pct)) +
        '"></label>' +
        '<label class="field compact">бюджет, ₽' +
        '<input type="text" inputmode="decimal" data-rub-input data-sleeve-capital="' +
        escapeHtml(id) +
        '" value="' +
        escapeHtml(formatRubGrouped(capital)) +
        '"></label>' +
        "</div>"
      );
    }).join("");
    return (
      '<section class="panel" data-tour="strategies-budgets">' +
      "<h3>Бюджеты рукавов</h3>" +
      "<p>" +
      "Задайте долю или сумму в рублях от торгового потолка (" +
      money(pool) +
      " = стоимость счёта × " +
      escapeHtml(pctLabel(alloc.sleeve_share)) +
      "). Сумма долей — 100%. Рубли считаются от потолка: бюджет = потолок × доля." +
      "</p>" +
      '<div class="budget-form" data-tour="strategies-budget-form">' +
      inputs +
      '<button type="button" class="primary" id="strategies-budget-save">Сохранить бюджеты</button>' +
      "</div>" +
      '<p class="source-line" id="strategies-budget-status">Изменения сразу идут в аллокацию (не через агента).</p>' +
      "</section>"
    );
  }

  function renderStrategiesGuide() {
    return (
      '<section class="panel" data-tour="strategies-guide">' +
      '<h3 data-tour="strategies-intro">Что смотреть на этой странице</h3>' +
      "<ol class=\"help-list\">" +
      "<li><strong>Деньги и лимит на бумагу</strong> — раздел " +
      '<a class="panel-link" href="#/settings">Настройки</a> ' +
      "(депозит и макс. % на одну акцию).</li>" +
      "<li><strong>Таблица рукавов</strong> — кто сколько заработал и какой бюджет.</li>" +
      "<li><strong>Бюджеты</strong> — раздайте % / ₽ между четырьмя стратегиями.</li>" +
      "<li><strong>Как держит портфель</strong> — формула: сколько акций купит при вашем бюджете.</li>" +
      "<li><strong>Прогон на истории</strong> — модель по файлу свечей: даты берутся из всего файла, сделки на следующем баре, расходы и просадка. " +
      "<em>Это модель, не обещание результата и не рекомендация.</em></li>" +
      "</ol></section>"
    );
  }

  function deskDateLabel(iso) {
    if (!iso) return "—";
    var value = new Date(iso);
    if (isNaN(value.getTime())) return String(iso);
    return value.toLocaleDateString("ru-RU", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
    });
  }

  function deskExitReasonLabel(reason) {
    var raw = String(reason || "").trim();
    if (!raw) return "—";
    if (raw === "take_profit") return "тейк";
    if (raw === "stop") return "стоп";
    if (raw === "signal:exit") return "выход (soft/время)";
    if (raw.indexOf("signal:") === 0) return raw.slice("signal:".length);
    return raw;
  }

  function deskBatchSleeveSelection() {
    if (lastDeskBatchSleeves == null) {
      return ACTIVE_SLEEVE_IDS.slice();
    }
    return lastDeskBatchSleeves.filter(function (id) {
      return ACTIVE_SLEEVE_IDS.indexOf(id) >= 0;
    });
  }

  function deskDefaultTickers(pool) {
    var defaults = ((lastDeskGroups && lastDeskGroups.default_tickers) || []).slice();
    if (!defaults.length) {
      var sectors = (lastDeskGroups && lastDeskGroups.sectors) || [];
      sectors.forEach(function (sector) {
        if (!sector || !sector.default_on) return;
        (sector.tickers || []).forEach(function (ticker) {
          if (defaults.indexOf(ticker) < 0) defaults.push(ticker);
        });
      });
    }
    if (!defaults.length) {
      defaults = (lastDeskGroups && lastDeskGroups.moex) || [];
    }
    return defaults.filter(function (ticker) {
      return pool.indexOf(ticker) >= 0;
    });
  }

  function deskBatchTickerSelection(available) {
    var pool = available && available.length ? available : [];
    if (lastDeskBatchTickers == null) {
      // По умолчанию — ядро MOEX; отрасли и S&P включаете отдельно.
      var defaults = deskDefaultTickers(pool);
      if (defaults.length) return defaults;
      return pool.slice();
    }
    return lastDeskBatchTickers.filter(function (ticker) {
      return pool.indexOf(ticker) >= 0;
    });
  }

  function renderDeskCheckGroup(kind, title, items, selected, labelFn) {
    var scope = items.join(",");
    var boxes = items
      .map(function (item) {
        var checked = selected.indexOf(item) >= 0;
        return (
          '<label class="desk-check">' +
          '<input type="checkbox" data-desk-check="' +
          escapeHtml(kind) +
          '" value="' +
          escapeHtml(item) +
          '"' +
          (checked ? " checked" : "") +
          "> " +
          escapeHtml(labelFn ? labelFn(item) : item) +
          "</label>"
        );
      })
      .join("");
    return (
      '<div class="desk-check-group" data-desk-group="' +
      escapeHtml(kind) +
      '">' +
      '<div class="desk-check-head">' +
      '<span class="desk-check-title">' +
      escapeHtml(title) +
      "</span>" +
      '<span class="desk-check-actions">' +
      '<button type="button" class="ghost compact" data-desk-check-all="' +
      escapeHtml(kind) +
      '" data-desk-scope="' +
      escapeHtml(scope) +
      '">все</button>' +
      '<button type="button" class="ghost compact" data-desk-check-none="' +
      escapeHtml(kind) +
      '" data-desk-scope="' +
      escapeHtml(scope) +
      '">сбросить</button>' +
      "</span></div>" +
      '<div class="desk-check-list">' +
      (boxes || '<span class="empty">нет файлов свечей</span>') +
      "</div></div>"
    );
  }

  function deskPeriodLabel(fromIso, toIso, bars, tf) {
    var from = deskDateLabel(fromIso);
    var to = deskDateLabel(toIso);
    var tfLabel =
      tf === "10m" ? "10 минут" : tf === "15m" ? "15 минут" : "дневки";
    var count = bars != null ? String(bars) : "—";
    var years =
      bars != null && tf !== "15m" && tf !== "10m"
        ? " (~" + (Math.round((Number(bars) / 252) * 10) / 10) + " торг. лет)"
        : "";
    return (
      "Период файла: " +
      from +
      " — " +
      to +
      " · " +
      count +
      " баров" +
      years +
      " · " +
      tfLabel
    );
  }

  function pctSigned(value) {
    var n = Number(value);
    if (!isFinite(n)) return "—";
    var sign = n > 0 ? "+" : "";
    return sign + (n * 100).toFixed(1) + "%";
  }

  function toneClass(value) {
    var n = Number(value);
    if (!isFinite(n) || n === 0) return "";
    return n > 0 ? " is-up" : " is-down";
  }

  function renderDeskBatchEquityChart(curve, initialCash) {
    if (!curve || curve.length < 2) {
      return '<p class="empty">Кривой капитала нет — мало точек по истории.</p>';
    }
    var values = curve.map(function (point) {
      return Number(point.equity);
    });
    var initial = Number(initialCash);
    if (!isFinite(initial) || initial <= 0) initial = values[0];
    var minV = Math.min.apply(null, values.concat([initial]));
    var maxV = Math.max.apply(null, values.concat([initial]));
    var pad = (maxV - minV) * 0.08 || Math.abs(initial) * 0.01 || 1;
    minV -= pad;
    maxV += pad;
    var span = maxV - minV || 1;
    var w = 640;
    var h = 180;
    var left = 8;
    var right = 8;
    var top = 14;
    var bottom = 22;
    var iw = w - left - right;
    var ih = h - top - bottom;
    function xAt(index) {
      return left + (index / (values.length - 1)) * iw;
    }
    function yAt(value) {
      return top + (1 - (value - minV) / span) * ih;
    }
    var path = values
      .map(function (value, index) {
        return (
          (index ? "L" : "M") +
          xAt(index).toFixed(1) +
          "," +
          yAt(value).toFixed(1)
        );
      })
      .join(" ");
    var baseY = yAt(initial);
    var peak = Math.max.apply(null, values);
    var peakIdx = values.indexOf(peak);
    var final = values[values.length - 1];
    var stroke = final >= initial ? "#1f6b45" : "#b33333";
    var area =
      path +
      " L" +
      xAt(values.length - 1).toFixed(1) +
      "," +
      baseY.toFixed(1) +
      " L" +
      xAt(0).toFixed(1) +
      "," +
      baseY.toFixed(1) +
      " Z";
    var firstTs = deskDateLabel(curve[0].ts);
    var lastTs = deskDateLabel(curve[curve.length - 1].ts);
    return (
      '<div class="desk-batch-chart" role="img" aria-label="Кривая капитала портфеля">' +
      '<svg viewBox="0 0 ' +
      w +
      " " +
      h +
      '" preserveAspectRatio="none">' +
      '<line class="desk-batch-chart__base" x1="' +
      left +
      '" y1="' +
      baseY.toFixed(1) +
      '" x2="' +
      (w - right) +
      '" y2="' +
      baseY.toFixed(1) +
      '" />' +
      '<path class="desk-batch-chart__area" d="' +
      area +
      '" fill="' +
      stroke +
      '" />' +
      '<path class="desk-batch-chart__line" d="' +
      path +
      '" stroke="' +
      stroke +
      '" />' +
      '<circle class="desk-batch-chart__peak" cx="' +
      xAt(peakIdx).toFixed(1) +
      '" cy="' +
      yAt(peak).toFixed(1) +
      '" r="3.5" />' +
      "</svg>" +
      '<div class="desk-batch-chart__meta">' +
      "<span>" +
      escapeHtml(firstTs) +
      "</span>" +
      "<span>пик " +
      escapeHtml(money(peak)) +
      "</span>" +
      "<span>" +
      escapeHtml(lastTs) +
      "</span>" +
      "</div></div>"
    );
  }

  function renderDeskBatchBarsChart(names) {
    var rows = (names || [])
      .slice()
      .filter(function (row) {
        return row && row.total_return != null;
      })
      .sort(function (a, b) {
        return Number(b.total_return) - Number(a.total_return);
      });
    if (!rows.length) {
      return '<p class="empty">Нет доходностей по тикерам для графика.</p>';
    }
    var maxAbs = 0;
    rows.forEach(function (row) {
      maxAbs = Math.max(maxAbs, Math.abs(Number(row.total_return) || 0));
    });
    if (!maxAbs) maxAbs = 0.01;
    var bars = rows
      .map(function (row) {
        var ret = Number(row.total_return) || 0;
        var width = Math.max(2, Math.round((Math.abs(ret) / maxAbs) * 100));
        return (
          '<div class="desk-batch-bar' +
          toneClass(ret) +
          '">' +
          '<span class="desk-batch-bar__name">' +
          escapeHtml(row.ticker || "—") +
          "</span>" +
          '<span class="desk-batch-bar__track"><span class="desk-batch-bar__fill" style="width:' +
          width +
          '%"></span></span>' +
          '<span class="desk-batch-bar__val">' +
          escapeHtml(pctSigned(ret)) +
          "</span></div>"
        );
      })
      .join("");
    return '<div class="desk-batch-bars">' + bars + "</div>";
  }

  function renderDeskBatchSummaries(bySleeve) {
    if (!bySleeve || !bySleeve.length) return "";
    return bySleeve
      .map(function (summary) {
        var name = SLEEVE_NAMES[summary.sleeve] || summary.sleeve || "рукав";
        var ret = summary.total_return;
        var pnl = summary.net_pnl;
        var verdict =
          ret == null && pnl == null
            ? "Итога нет — нет успешных прогонов."
            : Number(pnl) > 0 || Number(ret) > 0
              ? "В плюсе на корзине тикеров"
              : Number(pnl) < 0 || Number(ret) < 0
                ? "В минусе на корзине тикеров"
                : "Около нуля на корзине тикеров";
        return (
          '<article class="desk-batch-summary">' +
          "<h4>" +
          escapeHtml(name) +
          " · итог по всем тикерам</h4>" +
          '<p class="desk-batch-summary__verdict' +
          toneClass(ret != null ? ret : pnl) +
          '">' +
          escapeHtml(verdict) +
          ": " +
          '<strong>' +
          escapeHtml(money(pnl)) +
          "</strong> · " +
          '<strong>' +
          escapeHtml(pctSigned(ret)) +
          "</strong>" +
          " (равный кэш на каждый тикер, сумма кривых).</p>" +
          '<div class="desk-batch-kpis">' +
          '<div class="metric"><div class="k">стартовый кэш</div><div class="v">' +
          escapeHtml(money(summary.initial_cash)) +
          "</div></div>" +
          '<div class="metric"><div class="k">финал</div><div class="v' +
          toneClass(ret) +
          '">' +
          escapeHtml(money(summary.final_equity)) +
          "</div></div>" +
          '<div class="metric"><div class="k">пик капитала</div><div class="v">' +
          escapeHtml(money(summary.peak_equity)) +
          " · " +
          escapeHtml(pctSigned(summary.peak_return)) +
          "</div></div>" +
          '<div class="metric"><div class="k">макс. просадка</div><div class="v is-down">' +
          escapeHtml(
            summary.max_drawdown == null
              ? "—"
              : "−" + (Number(summary.max_drawdown) * 100).toFixed(1) + "%"
          ) +
          "</div></div>" +
          '<div class="metric"><div class="k">плюсовых тикеров</div><div class="v">' +
          escapeHtml(
            String(summary.win_tickers != null ? summary.win_tickers : "—")
          ) +
          " / " +
          escapeHtml(
            String(summary.ticker_count != null ? summary.ticker_count : "—")
          ) +
          "</div></div>" +
          '<div class="metric"><div class="k">сделок</div><div class="v">' +
          escapeHtml(String(summary.trades != null ? summary.trades : "—")) +
          "</div></div>" +
          "</div>" +
          '<div class="desk-batch-visuals">' +
          '<div><h5>Капитал корзины</h5>' +
          renderDeskBatchEquityChart(
            summary.equity_curve,
            summary.initial_cash
          ) +
          "</div>" +
          "<div><h5>Доходность по тикерам</h5>" +
          renderDeskBatchBarsChart(summary.names) +
          "</div></div></article>"
        );
      })
      .join("");
  }

  function renderStrategiesDesk() {
    var result = lastDeskBacktest;
    var selectedSleeve = lastDeskSleeve || "sma_cross";
    var selectedTicker = lastDeskTicker || "SBER";
    var resultHtml = "";
    if (result && result.error) {
      resultHtml =
        '<p class="empty" data-tour="strategies-desk-error">Прогон не удался: ' +
        escapeHtml(result.error) +
        "</p>";
    } else if (result) {
      var kinds = result.kinds || {};
      var backtest = result.backtest || {};
      var summary = backtest.summary || {};
      var walkForward = result.walk_forward || {};
      var oos = walkForward.oos_summary || {};
      var evidence = result.evidence || null;
      var buys = Number(kinds.buy || 0);
      var sells = Number(kinds.sell || 0);
      var flats = Number(kinds.flat || 0);
      var exits = Number(kinds.exit || 0);
      var trades = buys + sells + exits;
      var qualified = evidence
        ? evidence.capital_eligible === true
        : !oos.insufficient_statistics &&
          Number(oos.trades || 0) >= 5 &&
          Number(oos.excess_return || 0) > 0;
      var evidenceNames = {
        oos_edge: "Преимущество вне выборки",
        sample: "Объём выборки",
        drawdown: "Просадка",
        cost_resilience: "Устойчивость к расходам",
        paper_forward: "Проверка на новых данных",
        walk_forward_coverage: "Покрытие скользящих окон",
      };
      var evidenceHtml = evidence
        ? '<div class="evidence-score"><div class="evidence-score__total"><span>Доказательность</span><strong>' +
          escapeHtml(String(evidence.score)) +
          '<small>/ 100</small><em>' +
          escapeHtml(evidence.rating || "") +
          "</em></strong></div><div class=\"evidence-score__components\">" +
          Object.keys(evidence.components || {})
            .map(function (key) {
              var item = evidence.components[key] || {};
              var width = item.max
                ? Math.round((Number(item.points || 0) / Number(item.max)) * 100)
                : 0;
              return (
                '<div class="evidence-component"><div><span>' +
                escapeHtml(evidenceNames[key] || key) +
                "</span><strong>" +
                escapeHtml(String(item.points || 0)) +
                " / " +
                escapeHtml(String(item.max || 0)) +
                '</strong></div><i><b style="width:' +
                escapeHtml(String(width)) +
                '%"></b></i></div>'
              );
            })
            .join("") +
          "</div></div>" +
          ((evidence.blockers || []).length
            ? '<p class="warning-text">Блокирует капитал: ' +
              escapeHtml((evidence.blockers || []).join(" · ")) +
              ".</p>"
            : "")
        : "";
      var verdict =
        trades === 0
          ? "На этом отрезке торговых сигналов нет — стратегия всё время в плоскости."
          : "Итого торговых решений: " +
            trades +
            " (покупка " +
            buys +
            ", продажа " +
            sells +
            (exits ? ", выход " + exits : "") +
            "). «Плоско» (" +
            flats +
            ") — дни без действия, в таблицу их не кладём.";
      var actionRows = (result.last || []).filter(function (row) {
        return row && row.kind && row.kind !== "flat";
      });
      var lastRows = actionRows
        .map(function (row) {
          return (
            "<tr><td>" +
            formatSignalTime(row.ts) +
            "</td><td>" +
            escapeHtml(signalKindLabel(row.kind)) +
            "</td></tr>"
          );
        })
        .join("");
      var periodLine = deskPeriodLabel(
        result.from,
        result.to,
        result.bars,
        result.tf
      );
      var evalStart = deskDateLabel(result.evaluation_start);
      resultHtml =
        '<div class="experiment-report">' +
        '<div class="experiment-report__head"><div><span class="section-kicker">Прогон ' +
        escapeHtml(shortId(result.experiment_id)) +
        "</span><h4>Отчёт по стратегии</h4></div>" +
        '<span class="qualification ' +
        (qualified ? "is-qualified" : "is-rejected") +
        '">' +
        (qualified ? "Допущена к капиталу" : "Только кэш") +
        "</span></div>" +
        '<p class="source-line" data-tour="strategies-desk-period">' +
        escapeHtml(periodLine) +
        ". Торговля считается с " +
        escapeHtml(evalStart) +
        " (после прогрева индикаторов).</p>" +
        '<div class="callout" data-tour="strategies-desk-verdict"><strong>Исторический прогон.</strong> ' +
        escapeHtml(verdict) +
        " Сигнал исполняется не раньше открытия следующего бара; учтены комиссия и проскальзывание." +
        "</div>" +
        '<div class="metrics" data-tour="strategies-desk-result">' +
        '<div class="metric hero"><div class="k">чистый результат</div><div class="v">' +
        escapeHtml(money(summary.net_pnl)) +
        "</div></div>" +
        '<div class="metric"><div class="k">итоговый капитал</div><div class="v">' +
        escapeHtml(money(summary.final_equity)) +
        "</div></div>" +
        '<div class="metric"><div class="k">макс. просадка</div><div class="v">' +
        escapeHtml(
          summary.max_drawdown === null || summary.max_drawdown === undefined
            ? "—"
            : (Number(summary.max_drawdown) * 100).toFixed(2) + "%"
        ) +
        "</div></div>" +
        '<div class="metric"><div class="k">сделки / расходы</div><div class="v">' +
        escapeHtml(String(summary.trades || 0) + " / " + money(summary.costs)) +
        "</div></div>" +
        '<div class="metric"><div class="k">комиссия / плата за шорт</div><div class="v">' +
        escapeHtml(
          money(summary.commissions == null ? summary.costs : summary.commissions) +
            " / " +
            money(summary.short_carry || 0)
        ) +
        "</div></div>" +
        '<div class="metric"><div class="k">доходность стратегии</div><div class="v">' +
        escapeHtml(
          summary.total_return === null || summary.total_return === undefined
            ? "—"
            : (Number(summary.total_return) * 100).toFixed(2) + "%"
        ) +
        "</div></div>" +
        '<div class="metric"><div class="k">против «купить и держать»</div><div class="v">' +
        escapeHtml(
          summary.excess_return === null || summary.excess_return === undefined
            ? "—"
            : (Number(summary.excess_return) * 100).toFixed(2) + " п.п."
        ) +
        "</div></div></div>" +
        '<div class="callout"><strong>Проверка на хвосте данных.</strong> ' +
        escapeHtml(
          oos.folds
            ? String(oos.folds) +
                " окон, доходность " +
                (Number(oos.total_return) * 100).toFixed(2) +
                "%, преимущество к «купить и держать» " +
                (Number(oos.excess_return) * 100).toFixed(2) +
                " п.п."
            : "Недостаточно данных для окна вне выборки."
        ) +
        "</div>" +
        '<div class="evidence-lanes">' +
        "<div><span>На обучающем отрезке</span><strong>" +
        escapeHtml(String(summary.trades || 0)) +
        " сделок</strong><small>доходность " +
        escapeHtml(pctLabel(summary.total_return)) +
        "</small></div>" +
        "<div><span>Вне выборки</span><strong>" +
        escapeHtml(String(oos.trades || 0)) +
        " сделок / " +
        escapeHtml(String(oos.folds || 0)) +
        " окон</strong><small>преимущество " +
        escapeHtml(pctLabel(oos.excess_return)) +
        "</small></div>" +
        "<div><span>Решение по капиталу</span><strong>" +
        (qualified ? "можно выделять" : "только кэш") +
        "</strong><small>" +
        (qualified
          ? "≥5 сделок вне выборки и положительное преимущество"
          : "порог допуска не пройден") +
        "</small></div></div>" +
        evidenceHtml +
        (summary.insufficient_statistics
          ? '<p class="warning-text">Сделок мало: статистики недостаточно для вывода о преимуществе стратегии.</p>'
          : "") +
        (oos.insufficient_statistics
          ? '<p class="warning-text">Сделок вне выборки мало: стратегия пока не допущена к выделению капитала.</p>'
          : "") +
        (Number(summary.open_qty) > 0
          ? '<p class="warning-text">В конце ряда ещё открыта позиция (' +
            escapeHtml(String(summary.open_qty)) +
            " шт.) — её переоценка уже сидит в итоговом капитале и может сильно тянуть результат вниз.</p>"
          : "") +
        '<p class="source-line">файл ' +
        escapeHtml(result.path || "") +
        (result.experiment_id
          ? " · номер прогона " + escapeHtml(result.experiment_id)
          : "") +
        "</p>" +
        (lastRows
          ? "<h4>Последние покупки / продажи</h4>" +
            wrapTableScroll(
              '<table class="data-table"><thead><tr><th>время</th><th>действие</th></tr></thead><tbody>' +
                lastRows +
                "</tbody></table>"
            )
          : '<p class="empty">В хвосте файла нет покупок/продаж — одни «плоско». Смотрите счётчики выше.</p>') +
        "</div>";
    } else {
      resultHtml =
        '<p class="empty">Выберите рукав и тикер, затем «Прогнать» — или сразу «Прогнать все». Ордера не ставятся — только модель по локальному файлу свечей. Диапазон = весь CSV: дневки ~2 года, vol_scalp — M10 ~2 года (fallback M15).</p>';
    }
    var batchHtml = "";
    if (lastDeskBatch && lastDeskBatch.error) {
      batchHtml =
        '<div class="desk-batch" data-tour="strategies-desk-batch">' +
        '<p class="empty">Пакетный прогон не удался: ' +
        escapeHtml(lastDeskBatch.error) +
        "</p></div>";
    } else if (lastDeskBatch && lastDeskBatch.rows) {
      var batchRows = (lastDeskBatch.rows || []).slice().sort(function (a, b) {
        var aq = a.capital_eligible ? 0 : 1;
        var bq = b.capital_eligible ? 0 : 1;
        if (aq !== bq) return aq - bq;
        return (Number(b.oos_excess_return) || -999) - (Number(a.oos_excess_return) || -999);
      });
      var batchBody = batchRows
        .map(function (row) {
          var key = String(row.sleeve || "") + "|" + String(row.ticker || "");
          var open = lastDeskBatchOpen === key;
          var statusLabel =
            row.status === "ok"
              ? row.capital_eligible
                ? "можно капитал"
                : "только кэш"
              : row.status === "skipped"
                ? "нет данных"
                : "ошибка";
          var tradeRows = row.trade_rows || [];
          var detail =
            '<tr class="desk-batch-detail' +
            (open ? " is-open" : "") +
            '" data-batch-detail="' +
            escapeHtml(key) +
            '"><td colspan="8">' +
            (tradeRows.length
              ? '<div class="desk-batch-trades">' +
                '<p class="muted-note">Куплено / продано — штуки по сделке. «Усреднение» = докуп (2-й слой), цена входа — средняя. Колонка «выход» — почему закрыли: тейк / стоп / soft / время.</p>' +
                '<table class="data-table compact"><thead><tr>' +
                "<th>вход</th><th>выход</th><th>тип</th><th>причина</th>" +
                "<th>куплено</th><th>продано</th>" +
                "<th>цена входа</th><th>сумма покупки</th>" +
                "<th>цена выхода</th><th>сумма продажи</th><th>PnL</th>" +
                "</tr></thead><tbody>" +
                tradeRows
                  .map(function (trade) {
                    var averaged = !!trade.averaged || Number(trade.layers || 1) > 1;
                    var added = Number(trade.added_qty || 0);
                    var typeLabel = averaged
                      ? "усреднение · +" +
                        (added || "?") +
                        " шт · слоёв " +
                        String(trade.layers || 2)
                      : "обычная";
                    var reason = deskExitReasonLabel(trade.exit_reason);
                    var buyQty =
                      trade.buy_qty != null
                        ? trade.buy_qty
                        : trade.qty != null
                          ? trade.qty
                          : "—";
                    var sellQty =
                      trade.sell_qty != null
                        ? trade.sell_qty
                        : trade.qty != null
                          ? trade.qty
                          : "—";
                    return (
                      '<tr class="' +
                      (averaged ? "is-averaged" : "") +
                      '"><td>' +
                      deskDateLabel(trade.entry_ts) +
                      "</td><td>" +
                      deskDateLabel(trade.exit_ts) +
                      "</td><td>" +
                      escapeHtml(typeLabel) +
                      "</td><td>" +
                      escapeHtml(reason) +
                      "</td><td>" +
                      escapeHtml(String(buyQty)) +
                      "</td><td>" +
                      escapeHtml(String(sellQty)) +
                      "</td><td>" +
                      money(trade.entry_price) +
                      "</td><td>" +
                      money(
                        trade.buy_notional != null
                          ? trade.buy_notional
                          : trade.notional
                      ) +
                      "</td><td>" +
                      money(trade.exit_price) +
                      "</td><td>" +
                      money(trade.sell_notional) +
                      "</td><td>" +
                      money(trade.net_pnl) +
                      "</td></tr>"
                    );
                  })
                  .join("") +
                "</tbody></table></div>"
              : '<p class="empty">Закрытых сделок нет — разворачивать нечего.</p>') +
            "</td></tr>";
          return (
            '<tr class="desk-batch-row' +
            (open ? " is-open" : "") +
            '" data-batch-key="' +
            escapeHtml(key) +
            '" tabindex="0" role="button" aria-expanded="' +
            (open ? "true" : "false") +
            '">' +
            '<td><span class="desk-batch-caret" aria-hidden="true"></span>' +
            escapeHtml(SLEEVE_NAMES[row.sleeve] || row.sleeve || "—") +
            "</td><td>" +
            escapeHtml(row.ticker || "—") +
            "</td><td>" +
            escapeHtml(String(row.trades != null ? row.trades : "—")) +
            '</td><td class="' +
            toneClass(row.net_pnl).trim() +
            '">' +
            money(row.net_pnl) +
            '</td><td class="' +
            toneClass(row.total_return).trim() +
            '">' +
            escapeHtml(
              row.total_return == null ? "—" : pctSigned(row.total_return)
            ) +
            '</td><td class="is-down">' +
            escapeHtml(
              row.max_drawdown == null
                ? "—"
                : "−" + (Number(row.max_drawdown) * 100).toFixed(1) + "%"
            ) +
            "</td><td>" +
            escapeHtml(
              row.oos_excess_return == null
                ? "—"
                : (Number(row.oos_excess_return) * 100).toFixed(1) + " п.п."
            ) +
            "</td><td>" +
            escapeHtml(statusLabel) +
            (row.error ? " · " + escapeHtml(row.error) : "") +
            "</td></tr>" +
            detail
          );
        })
        .join("");
      batchHtml =
        '<div class="desk-batch" data-tour="strategies-desk-batch">' +
        renderDeskBatchSummaries(lastDeskBatch.by_sleeve) +
        "<h4>Сводка по всем прогонам</h4>" +
        "<p>" +
        escapeHtml(String(lastDeskBatch.ok || 0)) +
        " успешно · " +
        escapeHtml(String(lastDeskBatch.skipped || 0)) +
        " без данных · " +
        escapeHtml(String(lastDeskBatch.errors || 0)) +
        " ошибок · всего " +
        escapeHtml(String(lastDeskBatch.count || 0)) +
        " (рукава × тикеры). Сверху — итог корзины, пик и макс. просадка; клик по строке — сделки: штуки, сумма покупки, PnL.</p>" +
        wrapTableScroll(
          '<table class="data-table"><thead><tr>' +
            "<th>рукав</th><th>тикер</th><th>сделки</th><th>PnL</th><th>доходность</th>" +
            "<th>просадка</th><th>вне выборки</th><th>статус</th>" +
            "</tr></thead><tbody>" +
            batchBody +
            "</tbody></table>"
        ) +
        "</div>";
    }
    var tickers = lastDeskTickers && lastDeskTickers.length
      ? lastDeskTickers.slice()
      : [selectedTicker || "SBER"];
    if (tickers.indexOf(selectedTicker) < 0 && selectedTicker) {
      tickers = [selectedTicker].concat(tickers);
    }
    var sectors =
      lastDeskGroups && lastDeskGroups.sectors && lastDeskGroups.sectors.length
        ? lastDeskGroups.sectors
        : [
            {
              id: "moex",
              title: "MOEX",
              default_on: true,
              tickers: tickers.slice(),
            },
          ];
    var batchSleeves = deskBatchSleeveSelection();
    var batchTickers = deskBatchTickerSelection(tickers);
    var batchCount = batchSleeves.length * batchTickers.length;
    var sleeveChecks = renderDeskCheckGroup(
      "sleeve",
      "Рукава для пакета (" + batchSleeves.length + "/" + ACTIVE_SLEEVE_IDS.length + ")",
      ACTIVE_SLEEVE_IDS,
      batchSleeves,
      function (id) {
        return SLEEVE_NAMES[id] || id;
      }
    );
    var moexTickers =
      (lastDeskGroups && lastDeskGroups.moex && lastDeskGroups.moex.length
        ? lastDeskGroups.moex
        : tickers
      ).slice();
    var sp500Tickers =
      (lastDeskGroups && lastDeskGroups.sp500
        ? lastDeskGroups.sp500
        : []
      ).slice();
    var moexSectors = sectors.filter(function (sector) {
      return sector && sector.id !== "sp500";
    });
    var spSector =
      sectors.filter(function (sector) {
        return sector && sector.id === "sp500";
      })[0] ||
      (sp500Tickers.length
        ? {
            id: "sp500",
            title: "S&P 500",
            default_on: false,
            tickers: sp500Tickers,
          }
        : null);
    function sectorChecksHtml(sector, titleOverride) {
      var items = (sector && sector.tickers) || [];
      var selected = batchTickers.filter(function (ticker) {
        return items.indexOf(ticker) >= 0;
      });
      return renderDeskCheckGroup(
        "ticker",
        (titleOverride || sector.title || "Тикеры") +
          " (" +
          selected.length +
          "/" +
          items.length +
          ")",
        items,
        selected
      );
    }
    var marketPick =
      '<div class="desk-market-actions" role="group" aria-label="Рынок">' +
      '<button type="button" class="ghost compact" data-desk-market="moex"' +
      (moexTickers.length ? "" : " disabled") +
      ">РФ акции (" +
      escapeHtml(String(moexTickers.length)) +
      ")</button>" +
      '<button type="button" class="ghost compact" data-desk-market="sp500"' +
      (sp500Tickers.length ? "" : " disabled") +
      ">Западные (" +
      escapeHtml(String(sp500Tickers.length)) +
      ")</button>" +
      '<button type="button" class="ghost compact" data-desk-market="none">сбросить тикеры</button>' +
      "</div>";
    var tickerChecks =
      marketPick +
      '<div class="desk-market-break">Россия · MOEX</div>' +
      moexSectors.map(function (sector) {
        return sectorChecksHtml(sector);
      }).join("") +
      (spSector
        ? '<div class="desk-market-break" data-tour="desk-sp500-break">Запад · S&P 500</div>' +
          sectorChecksHtml(spSector)
        : "");
    return (
      '<section class="panel" data-tour="strategies-desk">' +
      "<h3>Прогон на истории</h3>" +
      '<p class="source-line">' +
      escapeHtml(String(moexTickers.length)) +
      " РФ · " +
      escapeHtml(String(sp500Tickers.length)) +
      " Запад · весь CSV · заявка не ставится" +
      "</p>" +
      '<div class="desk-batch-pick" data-tour="strategies-desk-pick">' +
      sleeveChecks +
      tickerChecks +
      '<div class="filters desk-batch-actions">' +
      '<button type="button" class="primary" id="desk-run-all"' +
      (batchCount ? "" : " disabled") +
      ">Прогнать выбранные (" +
      escapeHtml(String(batchCount)) +
      ")</button>" +
      '<span class="source-line" id="desk-batch-pick-hint">' +
      (batchCount
        ? escapeHtml(String(batchSleeves.length)) +
          " рукав(а) × " +
          escapeHtml(String(batchTickers.length)) +
          " тикер(ов)"
        : "Отметьте хотя бы один рукав и один тикер") +
      "</span></div></div>" +
      batchHtml +
      resultHtml +
      "</section>"
    );
  }

  function renderStrategiesCompare() {
    var rows = normalizeSleeves(lastSleeves);
    var bySleeve = allocBySleeve();
    var table = wrapTableScroll(
      '<table class="data-table" data-tour="strategies-table">' +
        "<thead><tr>" +
        "<th>название</th><th>доля</th><th>бюджет</th>" +
        "<th>зафиксировано</th><th>на бумаге</th><th>итог</th><th></th>" +
        "</tr></thead><tbody>" +
        rows
          .map(function (row) {
            var pnl = row.pnl || {};
            var name = SLEEVE_NAMES[row.sleeve] || row.sleeve || "—";
            var href = "#/strategies/" + encodeURIComponent(row.sleeve);
            var alloc = bySleeve[row.sleeve] || {};
            return (
              '<tr data-href="' +
              href +
              '" data-tour="strategies-row-' +
              escapeHtml(row.sleeve) +
              '">' +
              "<td>" +
              escapeHtml(name) +
              "</td><td>" +
              escapeHtml(pctLabel(alloc.weight)) +
              "</td><td>" +
              money(alloc.capital) +
              "</td><td>" +
              money(pnl.realized) +
              "</td><td>" +
              money(pnl.unrealized) +
              "</td><td>" +
              money(pnl.total) +
              '</td><td><a class="panel-link" href="' +
              href +
              '">открыть</a></td></tr>'
            );
          })
          .join("") +
        "</tbody></table>"
    );
    return (
      renderStrategiesGuide() +
      '<section class="panel" data-tour="strategies-compare">' +
      "<h3>Семь рукавов</h3>" +
      "<p>" +
      "SMA и Дончиан (дневки), RSI-возврат, EMA-скальп (M15), " +
      "Вечерний/Утренний докуп и Абс. моментум (long только в силе). " +
      "Клик по строке — правила и сигналы рукава." +
      "</p>" +
      table +
      '<p class="source-line" data-tour="strategies-pnl-hint">' +
      "«Зафиксировано» — закрытые сделки. «На бумаге» — переоценка. «Бюджет» — лимит из аллокации." +
      "</p></section>" +
      renderStrategiesBudgets() +
      renderStrategiesPlan() +
      renderStrategiesDesk()
    );
  }

  function formatSignalTime(iso) {
    if (!iso) return "—";
    var d = new Date(iso);
    if (isNaN(d.getTime())) return escapeHtml(String(iso));
    return escapeHtml(
      d.toLocaleString("ru-RU", {
        day: "2-digit",
        month: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
      })
    );
  }

  function signalKindLabel(kind) {
    var key = String(kind || "");
    return SIGNAL_KIND_RU[key] || key || "—";
  }

  function filterSignals(signals) {
    var ticker = String(signalFilterTicker || "")
      .trim()
      .toUpperCase();
    var kind = String(signalFilterKind || "");
    return (signals || []).filter(function (row) {
      if (ticker && String(row.ticker || "").toUpperCase().indexOf(ticker) < 0) {
        return false;
      }
      if (kind && String(row.kind || "") !== kind) return false;
      return true;
    });
  }

  function signalsEmptyHtml(totalCount, filteredCount) {
    var alive = !!(lastStatus && lastStatus.worker_alive);
    if (totalCount === 0) {
      if (!alive) {
        return (
          '<p class="empty" data-tour="strategies-signals-empty">' +
          "Нет пульса воркера — сигналы могут не обновляться. Проверьте, что воркер запущен." +
          "</p>"
        );
      }
      return (
        '<p class="empty" data-tour="strategies-signals-empty">' +
        "За выбранный период решений не было." +
        "</p>"
      );
    }
    if (filteredCount === 0) {
      return (
        '<p class="empty" data-tour="strategies-signals-filtered">' +
        "Нет сигналов по выбранным фильтрам. Сбросьте тикер или тип действия." +
        "</p>"
      );
    }
    return "";
  }

  function signalFiltersHtml(signals) {
    var tickers = [];
    var seen = {};
    (signals || []).forEach(function (row) {
      var t = String(row.ticker || "").toUpperCase();
      if (t && !seen[t]) {
        seen[t] = true;
        tickers.push(t);
      }
    });
    var kinds = ["buy", "sell", "flat", "exit"];
    return (
      '<div class="filters" data-tour="strategies-filters">' +
      '<label class="field compact">тикер' +
      '<input type="text" id="signal-filter-ticker" list="signal-ticker-list" placeholder="например SBER" value="' +
      escapeHtml(signalFilterTicker) +
      '">' +
      '<datalist id="signal-ticker-list">' +
      tickers
        .map(function (t) {
          return '<option value="' + escapeHtml(t) + '">';
        })
        .join("") +
      "</datalist></label>" +
      '<label class="field compact">действие' +
      '<select id="signal-filter-kind">' +
      '<option value="">все</option>' +
      kinds
        .map(function (k) {
          return (
            '<option value="' +
            k +
            '"' +
            (signalFilterKind === k ? " selected" : "") +
            ">" +
            escapeHtml(SIGNAL_KIND_RU[k]) +
            "</option>"
          );
        })
        .join("") +
      "</select></label>" +
      '<button type="button" class="ghost" id="signal-filter-reset">Сбросить</button>' +
      "</div>"
    );
  }

  function renderStrategiesSleeveCard(sleeveId) {
    var name = SLEEVE_NAMES[sleeveId] || sleeveId;
    var known = ACTIVE_SLEEVE_IDS.indexOf(sleeveId) >= 0;
    if (!known) {
      return (
        '<section class="panel" data-tour="strategies-card">' +
        '<p><a class="panel-link" href="#/strategies" data-tour="strategies-back">← ко сравнению</a></p>' +
        '<p class="empty">Неизвестный рукав. Вернитесь к сравнению и выберите один из четырёх активных.</p>' +
        "</section>"
      );
    }
    if (
      sleeveDetailLoading &&
      (!lastSleeveDetail || lastSleeveDetail.sleeve !== sleeveId)
    ) {
      return (
        '<section class="panel" data-tour="strategies-card">' +
        '<p><a class="panel-link" href="#/strategies" data-tour="strategies-back">← ко сравнению</a></p>' +
        "<h3>" +
        escapeHtml(name) +
        "</h3>" +
        '<p class="source-line">Загружаем результат, позиции и сигналы рукава…</p>' +
        skeletonHtml(4) +
        "</section>"
      );
    }
    var detail =
      lastSleeveDetail && lastSleeveDetail.sleeve === sleeveId
        ? lastSleeveDetail
        : null;
    var pnl = (detail && detail.pnl) || { realized: 0, unrealized: 0, total: 0 };
    var signals = (detail && detail.signals) || [];
    var positions = (detail && detail.positions) || [];
    var filtered = filterSignals(signals);
    var planRow = planBySleeve()[sleeveId] || {};
    var howto =
      planRow.signal || SLEEVE_HOWTO[sleeveId] || "Описание рукава появится здесь.";
    var holds = planRow.holds || "";
    var signalBody = "";
    if (filtered.length) {
      signalBody = wrapTableScroll(
        '<table class="data-table" data-tour="strategies-signals">' +
          "<thead><tr><th>тикер</th><th>время</th><th>действие</th><th></th></tr></thead><tbody>" +
          filtered
            .map(function (row) {
              var payload =
                row.payload && Object.keys(row.payload).length
                  ? JSON.stringify(row.payload)
                  : "";
              return (
                "<tr>" +
                "<td>" +
                escapeHtml(row.ticker || "—") +
                "</td><td>" +
                formatSignalTime(row.ts) +
                "</td><td>" +
                escapeHtml(signalKindLabel(row.kind)) +
                "</td><td>" +
                (payload
                  ? '<details class="fold tight"><summary>подробнее</summary><pre class="payload">' +
                    escapeHtml(payload) +
                    "</pre></details>"
                  : "—") +
                "</td></tr>"
              );
            })
            .join("") +
          "</tbody></table>",
        true
      );
    } else {
      signalBody = signalsEmptyHtml(signals.length, filtered.length);
    }
    var positionsBody = positions.length
      ? wrapTableScroll(
          '<table class="data-table" data-tour="strategies-positions">' +
            "<thead><tr><th>тикер</th><th>кол-во</th><th>средняя</th><th>на бумаге</th></tr></thead><tbody>" +
            positions
              .map(function (row) {
                return (
                  "<tr><td>" +
                  escapeHtml(row.ticker || row.instrument_id || "—") +
                  "</td><td>" +
                  escapeHtml(String(row.qty)) +
                  "</td><td>" +
                  money(row.avg_price) +
                  "</td><td>" +
                  money(row.unrealized) +
                  "</td></tr>"
                );
              })
              .join("") +
            "</tbody></table>"
        )
      : '<p class="empty" data-tour="strategies-positions-empty">Открытых позиций у рукава нет. После buy появится строка с qty и средней.</p>';
    var capital = planRow.capital;
    var nameBudget = planRow.name_budget;
    var ex = planRow.example || {};
    return (
      '<section class="panel" data-tour="strategies-card">' +
      '<p><a class="panel-link" href="#/strategies" data-tour="strategies-back">← ко сравнению</a></p>' +
      "<h3 data-tour=\"strategies-card-title\">" +
      escapeHtml(name) +
      "</h3>" +
      '<p class="source-line">код: <code>' +
      escapeHtml(sleeveId) +
      "</code> · горизонт: " +
      escapeHtml(planRow.horizon || "дневки") +
      "</p>" +
      '<div class="metrics" data-tour="strategies-card-pnl">' +
      '<div class="metric"><div class="k">бюджет рукава</div><div class="v">' +
      money(capital) +
      "</div></div>" +
      '<div class="metric"><div class="k">лимит на имя</div><div class="v">' +
      money(nameBudget) +
      "</div></div>" +
      '<div class="metric"><div class="k">зафиксировано</div><div class="v">' +
      money(pnl.realized) +
      "</div></div>" +
      '<div class="metric"><div class="k">на бумаге</div><div class="v">' +
      money(pnl.unrealized) +
      "</div></div>" +
      '<div class="metric hero"><div class="k">итог</div><div class="v">' +
      money(pnl.total) +
      "</div></div></div>" +
      '<div class="howto" data-tour="strategies-howto"><h4>Как устроен сигнал</h4><p>' +
      escapeHtml(howto) +
      "</p></div>" +
      (holds
        ? '<div class="howto" data-tour="strategies-holds"><h4>Как держит портфель</h4><p>' +
          escapeHtml(holds) +
          " Лимит на имя " +
          money(nameBudget) +
          "; при цене " +
          money(ex.price) +
          " пример qty " +
          escapeHtml(String(ex.qty != null ? ex.qty : "—")) +
          ". Секторов нет — только тикеры вселенной.</p></div>"
        : "") +
      "<h4 data-tour=\"strategies-positions-title\">Открытые позиции</h4>" +
      positionsBody +
      "<h4 data-tour=\"strategies-signals-title\">Сигналы</h4>" +
      "<p>Последние решения рукава на дневном закрытии: покупка, продажа, плоско, выход.</p>" +
      signalFiltersHtml(signals) +
      signalBody +
      "</section>"
    );
  }

  function bindSignalFilters() {
    var tickerInput = byId("signal-filter-ticker");
    var kindSelect = byId("signal-filter-kind");
    var resetBtn = byId("signal-filter-reset");
    function apply() {
      signalFilterTicker = tickerInput ? tickerInput.value : "";
      signalFilterKind = kindSelect ? kindSelect.value : "";
      renderStrategies();
    }
    if (tickerInput) {
      tickerInput.addEventListener("input", apply);
      tickerInput.addEventListener("change", apply);
    }
    if (kindSelect) kindSelect.addEventListener("change", apply);
    if (resetBtn) {
      resetBtn.addEventListener("click", function () {
        signalFilterTicker = "";
        signalFilterKind = "";
        renderStrategies();
      });
    }
  }

  function candlePullHtml() {
    return (
      '<section class="candle-pull">' +
      "<h3>Свечи с брокера</h3>" +
      "<p>Дневки пишутся в файл лаборатории. Это тест: заявка не ставится.</p>" +
      '<label>Тикер <input id="candle-ticker" value="SBER" maxlength="12"></label>' +
      '<button type="button" id="candle-pull">Скачать с брокера</button>' +
      '<p id="candle-pull-note" class="muted"></p>' +
      "</section>"
    );
  }

  function bindCandlePull() {
    var button = byId("candle-pull");
    if (!button) return;
    button.onclick = function () {
      var ticker = (byId("candle-ticker").value || "").trim();
      var note = byId("candle-pull-note");
      button.disabled = true;
      if (note) note.textContent = "Качаю " + ticker + "…";
      apiPost("/desk/candles/pull", { ticker: ticker, days: 730 })
        .then(function (row) {
          if (note) note.textContent = row.ticker + ": " + row.bars + " дневных баров в файле.";
        })
        .catch(function (err) {
          if (note) note.textContent = err.message || "не скачалось";
        })
        .finally(function () {
          button.disabled = false;
        });
    };
  }

  function ruDay(iso) {
    var raw = String(iso || "").trim();
    if (!raw) return "—";
    var ms = Date.parse(raw.length === 10 ? raw + "T00:00:00Z" : raw);
    if (!isFinite(ms)) return "—";
    var shifted = new Date(ms + 3 * 60 * 60 * 1000);
    function pad(n) { return (n < 10 ? "0" : "") + n; }
    return pad(shifted.getUTCDate()) + "." + pad(shifted.getUTCMonth() + 1) + "." + shifted.getUTCFullYear();
  }

  function gapText(row) {
    return (row && row.gaps || []).map(function (gap) {
      var from = ruDay(gap.from);
      var to = ruDay(gap.to);
      return from === to ? from : from + " — " + to;
    }).join(", ");
  }

  function candleCount(row) {
    if (!row || row.status === "missing") return "файла нет";
    var session = (lastCandlesCoverage && lastCandlesCoverage.session) || "";
    var need = Number((lastCandlesCoverage && lastCandlesCoverage.min_bars) || 300);
    var reached = session && row.session_day && row.session_day >= session;
    if (row.status === "ready" && reached) return plainNumber(row.bars);
    var holes = gapText(row);
    if (holes) return "нет " + holes;
    if (row.status === "short") {
      if (!reached) return plainNumber(row.bars) + ", не доходит до закрытого дня";
      return plainNumber(row.bars) + " из " + plainNumber(need) + ", в этих датах дыр нет";
    }
    return plainNumber(row.bars);
  }

  function setCandleNote(text) {
    candlePullNote = text || "";
    var note = byId("candle-board-note");
    if (note) note.textContent = candlePullNote;
  }

  function pushCandleLog(text) {
    if (!text) return;
    candleLog.push(text);
    if (candleLog.length > 40) candleLog.shift();
  }

  function candleWho(row) {
    var ticker = String(row.ticker || "");
    var name = String(row.name || "").trim();
    if (name && name.toUpperCase() !== ticker.toUpperCase()) return name + " (" + ticker + ")";
    return ticker;
  }

  function candlesWord(n) {
    var x = Math.abs(Number(n) || 0) % 100;
    var d = x % 10;
    if (x > 10 && x < 20) return "свечей";
    if (d === 1) return "свеча";
    if (d > 1 && d < 5) return "свечи";
    return "свечей";
  }

  function candleFillRunning() {
    return !!(candleJob && candleJob.status === "running");
  }

  function applyCandleFillStatus(data) {
    if (!data) return;
    var status = data.status || "idle";
    if (status === "running") {
      candleJob = {
        status: "running",
        total: Number(data.total) || 0,
        index: Number(data.index) || 0,
        ticker: data.ticker || "",
        done: data.done || {},
        fail: data.fail || {},
        message: data.message || "",
      };
      if (data.message) candlePullNote = data.message;
    } else if (status === "done" || status === "cancelled" || status === "error") {
      var wasRunning = candleFillRunning();
      candleJob = null;
      if (data.message) {
        candlePullNote = data.message;
        if (wasRunning || status !== "idle") pushCandleLog(data.message);
      }
    } else {
      candleJob = null;
    }
  }

  function stopCandleFillPoll() {
    if (candleFillPollTimer) {
      clearInterval(candleFillPollTimer);
      candleFillPollTimer = null;
    }
  }

  function pollCandleFillOnce() {
    return apiGet("/desk/candles/fill")
      .then(function (data) {
        var wasRunning = candleFillRunning();
        applyCandleFillStatus(data);
        if (candleFillRunning()) {
          if (currentRoute === "candles") renderCandles();
        } else {
          stopCandleFillPoll();
          if (wasRunning || (data && data.status === "done")) {
            return refreshCandles().then(function () {
              if (currentRoute === "candles") renderCandles();
            });
          }
          if (currentRoute === "candles") renderCandles();
        }
        return data;
      })
      .catch(function () {
        return null;
      });
  }

  function startCandleFillPoll() {
    stopCandleFillPoll();
    candleFillPollTimer = setInterval(function () {
      pollCandleFillOnce();
    }, 2000);
  }

  function pullLine() {
    if (!candleJob || candleJob.status !== "running") {
      return '<p id="candle-board-note" class="tape-note">' + escapeHtml(candlePullNote) + "</p>";
    }
    var items = (lastCandlesCoverage && lastCandlesCoverage.items) || [];
    var current = null;
    for (var i = 0; i < items.length; i++) {
      if (items[i].ticker === candleJob.ticker) current = items[i];
    }
    var name = current ? candleWho(current) : candleJob.ticker;
    var pct = candleJob.total ? Math.round((candleJob.index / candleJob.total) * 100) : 0;
    var idx = Math.min(candleJob.index + 1, candleJob.total || 0);
    return '<div class="pull-line" id="candle-board-note">' +
      '<div class="pull-meter" role="progressbar" aria-valuemin="0" aria-valuemax="' + candleJob.total + '" aria-valuenow="' + candleJob.index + '"><span style="width:' + pct + '%"></span></div>' +
      "<p>" + escapeHtml(idx + " из " + candleJob.total + " · " + name) +
      " · на сервере, вкладку можно закрыть</p></div>";
  }

  function candleJournal(data) {
    var session = data.session || "";
    var sessionLabel = session ? ruDay(session) : "";
    var head = session
      ? "До закрытого дня " + sessionLabel + " доходят " + plainNumber(data.on_session != null ? data.on_session : 0) + " из " + plainNumber(data.total || 0) + ". Сегодня " + ruDay(new Date().toISOString()) + ", дневная свеча этого дня ещё не закрыта."
      : "";
    var run = candleLog.map(function (line) {
      return "<li>" + escapeHtml(line) + "</li>";
    }).join("");
    if (!head && !run) return "";
    return '<section class="tape-log">' +
      (head ? "<p>" + escapeHtml(head) + "</p>" : "") +
      (run ? "<p>Ход докачки</p><ol>" + run + "</ol>" : "") +
      "</section>";
  }

  function refreshCandles() {
    var tf = candleTf();
    return apiGet("/candles/coverage?tf=" + encodeURIComponent(tf)).then(function (data) {
      lastCandlesCoverage = data;
      if (data && data.tf) lastCandleTf = data.tf;
      rememberRefresh("candles", data && data.refresh);
      if (currentRoute === "candles") renderCandles();
    }).catch(function (err) {
      var note = byId("candle-board-note");
      if (note) note.textContent = err.message || "список не загрузился";
    });
  }

  function candleTf() {
    return lastCandleTf === "15m" || lastCandleTf === "10m" ? lastCandleTf : "1d";
  }

  function candleGapKey(row) {
    var base = candleTf() + "|";
    if (!row || row.status === "missing" || !row.last) return base + "missing";
    return base + (row.gaps || []).map(function (gap) {
      return (gap.from || "") + ":" + (gap.to || "");
    }).join("|") + "|" + String(row.bars || 0) + "|" + String(row.session_day || "");
  }

  function readCandleOk() {
    try {
      var raw = JSON.parse(localStorage.getItem("cabin_candle_ok") || "{}");
      return raw && typeof raw === "object" ? raw : {};
    } catch (err) {
      return {};
    }
  }

  function candleAcked(row) {
    var ticker = String((row && row.ticker) || "");
    if (!ticker) return false;
    return readCandleOk()[ticker] === candleGapKey(row);
  }

  function setCandleAck(row, on) {
    var all = readCandleOk();
    var ticker = String(row.ticker || "");
    if (!ticker) return;
    if (on) all[ticker] = candleGapKey(row);
    else delete all[ticker];
    localStorage.setItem("cabin_candle_ok", JSON.stringify(all));
  }

  function companyCell(row) {
    var ticker = String(row.ticker || "");
    var name = String(row.name || "")
      .trim()
      .replace(/\s*[—–-]\s*привилегированные акции/i, " прив.")
      .replace(/\s+привилегированные$/i, " прив.");
    var titled = name && name.toUpperCase() !== ticker.toUpperCase();
    var label = titled ? name : ticker;
    return (
      '<td class="co-name" title="' +
      escapeHtml(titled ? name + " · " + ticker : ticker) +
      '"><span class="co-name__line"><strong>' +
      escapeHtml(label) +
      "</strong>" +
      (titled ? "<small>" + escapeHtml(ticker) + "</small>" : "") +
      "</span></td>"
    );
  }

  function renderCandles() {
    var data = lastCandlesCoverage || { items: [], ready: 0, short: 0, missing: 0, total: 0 };
    var items = data.items || [];
    var query = (lastCandleQuery || "").trim().toUpperCase();
    var filter = lastCandleFilter || "gaps";
    var tf = candleTf();
    var need = Number(data.min_bars || 300);
    var openGaps = items.filter(function (row) {
      return row.status !== "ready" && !candleAcked(row);
    });
    var hiddenGaps = items.filter(function (row) {
      return row.status !== "ready" && candleAcked(row);
    }).length;
    var shown = items.filter(function (row) {
      var blob = ((row.name || "") + " " + (row.ticker || "")).toUpperCase();
      if (query && blob.indexOf(query) === -1) return false;
      if (filter === "ready") return row.status === "ready";
      if (filter === "gaps") return row.status !== "ready" && !candleAcked(row);
      return true;
    });
    var loaded = !!lastCandlesCoverage;
    var gaps = openGaps.length;
    var rows = shown.map(function (row) {
      var period = row.first && row.last ? ruDay(row.first) + " — " + ruDay(row.last) : "—";
      var ticker = String(row.ticker || "");
      var action = row.status === "ready" ? "Обновить" : "Докачать";
      var mark = "";
      if (candleJob && candleJob.fail && candleJob.fail[ticker]) {
        action = "Ошибка";
        mark = "is-fail";
      } else if (candleJob && candleJob.done && candleJob.done[ticker]) {
        action = "Скачано";
        mark = "is-done";
      } else if (candleJob && candleJob.ticker === ticker) {
        action = "Качаю";
        mark = "is-pull";
      } else if (candleFillRunning()) {
        action = "Ждёт";
      }
      var acked = candleAcked(row);
      var okBtn = row.status === "ready" ? "" : '<button type="button" data-candle-ok="' + escapeHtml(ticker) + '">' + (acked ? "Вернуть" : "Ок") + "</button>";
      return "<tr" + (mark ? ' class="' + mark + '"' : "") + ">" + companyCell(row) + "<td class=\"candle-" + escapeHtml(row.status || "missing") + "\">" + candleCount(row) + "</td><td>" + escapeHtml(period) + "</td><td><span class=\"row-actions\"><button type=\"button\" data-pull=\"" + escapeHtml(ticker) + "\"" + (candleFillRunning() ? " disabled" : "") + ">" + action + "</button>" + okBtn + "</span></td></tr>";
    }).join("");
    var fillLabel = candleFillRunning()
      ? (Math.min(candleJob.index + 1, candleJob.total) + " из " + candleJob.total)
      : (loaded && gaps ? "Докачать эти " + plainNumber(gaps) : "Докачать");
    var formats = data.formats || [
      { id: "1d", title: "Дневки", sleeves: CANDLE_TF_HINT["1d"] },
      { id: "15m", title: "15 минут", sleeves: CANDLE_TF_HINT["15m"] },
      { id: "10m", title: "10 минут", sleeves: CANDLE_TF_HINT["10m"] },
    ];
    var tfButtons = formats.map(function (fmt) {
      return '<button type="button" data-candle-tf="' + escapeHtml(fmt.id) + '"' + (fmt.id === tf ? ' aria-pressed="true"' : "") + "><span>" + escapeHtml(fmt.title) + "</span></button>";
    }).join("");
    var sleeveHint = (data.sleeves || CANDLE_TF_HINT[tf] || "") + ". Полный ряд — от " + plainNumber(need) + " свечей.";
    byId("page-body").innerHTML =
      '<section class="tape">' +
      '<div class="tape-bar">' +
      '<div class="tape-filters" role="group" aria-label="Формат свечей">' + tfButtons + "</div>" +
      "</div>" +
      '<div class="tape-head"><p class="tape-lead">' +
      (loaded
        ? (gaps
          ? "Не хватает у " + plainNumber(gaps) + " компаний. " + sleeveHint
          : (hiddenGaps ? "Скрыто " + plainNumber(hiddenGaps) + ". " : "") + "По этому формату хватает у всех " + plainNumber(data.total || items.length) + ". " + sleeveHint)
        : "Считаю файлы…") +
      '</p><button type="button" class="primary" id="candle-fill"' + (loaded && gaps && !candleFillRunning() ? "" : " disabled") + ">" +
      fillLabel +
      "</button>" +
      (candleFillRunning()
        ? '<button type="button" class="ghost" id="candle-fill-cancel">Стоп</button>'
        : "") +
      "</div>" +
      pullLine() +
      '<div class="tape-bar">' +
      '<div class="tape-filters" role="group" aria-label="Какие компании показать">' +
      '<button type="button" data-candle-filter="gaps"' + (filter === "gaps" ? ' aria-pressed="true"' : "") + "><span>Не хватает</span><strong>" + plainNumber(gaps) + "</strong></button>" +
      '<button type="button" data-candle-filter="ready"' + (filter === "ready" ? ' aria-pressed="true"' : "") + "><span>Хватает</span><strong>" + plainNumber(data.ready || 0) + "</strong></button>" +
      '<button type="button" data-candle-filter="all"' + (filter === "all" ? ' aria-pressed="true"' : "") + "><span>Все</span><strong>" + plainNumber(data.total || items.length) + "</strong></button>" +
      "</div>" +
      '<input id="candle-find" class="tape-find" type="search" placeholder="Тикер или имя" value="' + escapeHtml(lastCandleQuery || "") + '" aria-label="Найти компанию">' +
      "</div>" +
      '<div class="table-scroll"><table class="data-table"><thead><tr><th>Компания</th><th>Свечей</th><th>Даты</th><th>Действие</th></tr></thead><tbody>' +
      (rows || '<tr><td colspan="4">' + (query ? "Такого тикера нет" : (filter === "gaps" && hiddenGaps ? "Скрыты кнопкой Ок" : "Таких компаний нет")) + "</td></tr>") +
      "</tbody></table></div>" +
      candleJournal(data) +
      "</section>";
    bindCandles();
  }

  function pullTicker(ticker) {
    var tf = candleTf();
    var days = tf === "1d" ? 730 : 180;
    return apiPost("/desk/candles/pull", { ticker: ticker, days: days, tf: tf }, { timeoutMs: 180000 });
  }

  function bindCandles() {
    document.querySelectorAll("[data-candle-tf]").forEach(function (btn) {
      btn.onclick = function () {
        if (candleFillRunning()) return;
        var next = btn.getAttribute("data-candle-tf") || "1d";
        if (next === candleTf()) return;
        lastCandleTf = next;
        lastCandlesCoverage = null;
        renderCandles();
        refreshCandles();
      };
    });
    document.querySelectorAll("[data-candle-filter]").forEach(function (btn) {
      btn.onclick = function () {
        lastCandleFilter = btn.getAttribute("data-candle-filter") || "all";
        renderCandles();
      };
    });
    var find = byId("candle-find");
    if (find) find.oninput = function () {
      lastCandleQuery = find.value || "";
      var pos = find.selectionStart;
      renderCandles();
      var again = byId("candle-find");
      if (again) {
        again.focus();
        again.selectionStart = again.selectionEnd = pos;
      }
    };
    document.querySelectorAll("[data-candle-ok]").forEach(function (btn) {
      btn.onclick = function () {
        var ticker = btn.getAttribute("data-candle-ok");
        var row = null;
        ((lastCandlesCoverage || {}).items || []).forEach(function (item) {
          if (item.ticker === ticker) row = item;
        });
        if (!row) return;
        setCandleAck(row, !candleAcked(row));
        renderCandles();
      };
    });
    document.querySelectorAll("[data-pull]").forEach(function (btn) {
      btn.onclick = function () {
        if (candleFillRunning()) return;
        var ticker = btn.getAttribute("data-pull");
        btn.disabled = true;
        setCandleNote("Качаю " + ticker + "…");
        pullTicker(ticker).then(function (row) {
          var line = (row.ticker || ticker) + ": в файле " + plainNumber(row.bars) + " свечей.";
          pushCandleLog(line);
          setCandleNote(line);
          return refreshCandles();
        }).catch(function (err) {
          var line = (ticker || "") + ": " + (err.message || "не скачалось");
          pushCandleLog(line);
          setCandleNote(line);
        });
      };
    });
    var fill = byId("candle-fill");
    if (fill) {
      fill.onclick = function () {
        if (candleFillRunning()) return;
        var gaps = ((lastCandlesCoverage || {}).items || []).filter(function (row) {
          return row.status !== "ready" && !candleAcked(row);
        });
        if (!gaps.length) {
          setCandleNote("Качать нечего.");
          return;
        }
        var tickers = gaps.map(function (row) {
          return row.ticker;
        });
        fill.disabled = true;
        setCandleNote("Запускаю докачку на сервере…");
        apiPost("/desk/candles/fill", { tf: candleTf(), tickers: tickers })
          .then(function (data) {
            applyCandleFillStatus(data);
            pushCandleLog(
              "Докачка на сервере: " +
                plainNumber((data && data.total) || tickers.length) +
                " бумаг · вкладку можно закрыть"
            );
            setCandleNote(
              "Докачка идёт на сервере · вкладку можно закрыть"
            );
            renderCandles();
            startCandleFillPoll();
          })
          .catch(function (err) {
            setCandleNote(err.message || "не удалось запустить докачку");
            fill.disabled = false;
          });
      };
    }
    var cancel = byId("candle-fill-cancel");
    if (cancel) {
      cancel.onclick = function () {
        cancel.disabled = true;
        apiPost("/desk/candles/fill/cancel", {})
          .then(function (data) {
            applyCandleFillStatus(data);
            renderCandles();
          })
          .catch(function () {
            cancel.disabled = false;
          });
      };
    }
  }

  function capLabel(value) {
    var n = Number(value);
    if (!isFinite(n)) return "—";
    var abs = Math.abs(n);
    var scaled = n;
    var unit = "";
    if (abs >= 1e12) {
      scaled = n / 1e12;
      unit = "\u00a0трлн";
    } else if (abs >= 1e9) {
      scaled = n / 1e9;
      unit = "\u00a0млрд";
    } else if (abs >= 1e6) {
      scaled = n / 1e6;
      unit = "\u00a0млн";
    } else {
      return Math.round(n).toLocaleString("ru-RU");
    }
    return (
      scaled.toLocaleString("ru-RU", {
        minimumFractionDigits: 1,
        maximumFractionDigits: 1,
      }) + unit
    );
  }

  function fundFields(row) {
    return [
      ["P/E", row.pe_ratio_ttm],
      ["P/B", row.price_to_book_ttm],
      ["EPS", row.eps_ttm],
      ["ROE", row.roe],
      ["Дивиденд", row.dividend_yield_ttm],
      ["Капитализация", row.market_capitalization],
    ];
  }

  function asPercentPoints(value) {
    var n = Number(value);
    if (!isFinite(n)) return null;
    return Math.abs(n) <= 1.5 ? n * 100 : n;
  }

  function epsLabel(value) {
    var n = Number(value);
    if (!isFinite(n)) return null;
    var digits = Math.abs(n) >= 100 ? 0 : 2;
    return n.toLocaleString("ru-RU", {
      minimumFractionDigits: digits,
      maximumFractionDigits: digits,
    });
  }

  function fundPoint(row, key) {
    if (key === "score") {
      var total = Number((row.scores || {}).total);
      return isFinite(total) ? total : null;
    }
    if (key === "roe") {
      if (row.roe === null || row.roe === undefined || row.roe === "") return null;
      return asPercentPoints(row.roe);
    }
    var raw = row[key];
    if (raw === null || raw === undefined || raw === "") return null;
    var n = Number(raw);
    return isFinite(n) ? n : null;
  }

  function fundPercentile(sorted, p) {
    if (!sorted.length) return null;
    var i = (sorted.length - 1) * p;
    var lo = Math.floor(i);
    var hi = Math.ceil(i);
    if (lo === hi) return sorted[lo];
    return sorted[lo] + (sorted[hi] - sorted[lo]) * (i - lo);
  }

  var FUND_BARS = [
    { key: "score", title: "Оценка", fixed: [0, 100] },
    { key: "pe_ratio_ttm", title: "P/E" },
    { key: "price_to_book_ttm", title: "P/B" },
    { key: "eps_ttm", title: "EPS", unit: "₽", tip: "Прибыль на акцию, ₽" },
    { key: "roe", title: "ROE" },
    { key: "dividend_yield_ttm", title: "Дивиденд" },
    {
      key: "market_capitalization",
      title: "Кап.",
      unit: "₽",
      tip: "Рыночная капитализация, ₽",
      log: true,
    },
  ];

  function fundScaleLabel(key, n) {
    if (n === null || !isFinite(Number(n))) return "—";
    if (key === "score") return String(Math.round(Number(n)));
    if (key === "roe" || key === "dividend_yield_ttm") {
      return Number(n).toLocaleString("ru-RU", { maximumFractionDigits: 1 }) + "%";
    }
    if (key === "eps_ttm") return epsLabel(n);
    if (key === "market_capitalization") return capLabel(n);
    return plainNumber(n);
  }

  function fundScales(items) {
    var scales = {};
    FUND_BARS.forEach(function (bar) {
      if (bar.fixed) {
        scales[bar.key] = { lo: bar.fixed[0], hi: bar.fixed[1], labelLo: bar.fixed[0], labelHi: bar.fixed[1] };
        return;
      }
      var values = [];
      items.forEach(function (row) {
        var n = fundPoint(row, bar.key);
        if (n === null || (bar.log && n <= 0)) return;
        values.push(n);
      });
      values.sort(function (a, b) { return a - b; });
      var labelLo = values.length < 8 ? values[0] : fundPercentile(values, 0.1);
      var labelHi = values.length < 8 ? values[values.length - 1] : fundPercentile(values, 0.9);
      if (labelLo == null) labelLo = 0;
      if (labelHi == null) labelHi = 0;
      var lo = labelLo;
      var hi = labelHi;
      if (bar.log && labelLo > 0 && labelHi > 0) {
        lo = Math.log(labelLo);
        hi = Math.log(labelHi);
      }
      scales[bar.key] = { lo: lo, hi: hi, log: !!bar.log, labelLo: labelLo, labelHi: labelHi };
    });
    return scales;
  }

  function fundValueText(row, bar) {
    var n = fundPoint(row, bar.key);
    if (n === null) return "—";
    if (bar.key === "score") return String(Math.round(n));
    if (bar.key === "roe" || bar.key === "dividend_yield_ttm") return fundScaleLabel(bar.key, n);
    if (bar.key === "eps_ttm") return epsLabel(n);
    if (bar.key === "market_capitalization") return capLabel(n);
    return plainNumber(n);
  }

  function fundBar(row, bar, scale) {
    var n = fundPoint(row, bar.key);
    var text = fundValueText(row, bar);
    var width = 0;
    if (n !== null && scale && isFinite(scale.lo) && isFinite(scale.hi)) {
      if (scale.hi === scale.lo) width = 100;
      else {
        var point = n;
        if (scale.log) point = n > 0 ? Math.log(n) : scale.lo;
        width = Math.max(0, Math.min(1, (point - scale.lo) / (scale.hi - scale.lo))) * 100;
      }
    }
    var range = fundScaleLabel(bar.key, scale.labelLo) + " — " + fundScaleLabel(bar.key, scale.labelHi);
    return '<td class="num' + (n === null ? " num-miss" : "") + '" title="' + escapeHtml(bar.title + " " + text + ", шкала " + range) + '"><span class="num-scale"><span>' + escapeHtml(text) + '</span><span class="scale-track" aria-hidden="true"><span class="scale-fill" style="width:' + width.toFixed(1) + '%"></span></span></span></td>';
  }

  function fundPlainCell(row, bar) {
    var n = fundPoint(row, bar.key);
    var text = fundValueText(row, bar);
    return (
      '<td class="num' +
      (n === null ? " num-miss" : "") +
      '">' +
      escapeHtml(text) +
      "</td>"
    );
  }

  function fundScoreTip(row) {
    var scores = row.scores || {};
    var total = fundScoreTotal(row);
    var v = scores.value != null ? Math.round(scores.value) : "—";
    var q = scores.quality != null ? Math.round(scores.quality) : "—";
    var d = scores.div != null ? Math.round(scores.div) : "—";
    return (
      "Итого " +
      (total >= 0 ? Math.round(total) : "—") +
      " из 100 = дешево (P/E, P/B) " +
      v +
      " · качество (ROE, EPS) " +
      q +
      " · дивиденд " +
      d +
      ". Веса 40% / 35% / 25%."
    );
  }

  function fundScoreCell(row) {
    var total = fundScoreTotal(row);
    var text = total >= 0 ? String(Math.round(total)) : "—";
    var mark = total >= 70 ? '<span class="ind-mark">рек.</span>' : "";
    return (
      '<td class="num ind-score ' +
      fundScoreTone(total) +
      '" title="' +
      escapeHtml(fundScoreTip(row)) +
      '"><span class="ind-score__val">' +
      escapeHtml(text) +
      "</span>" +
      mark +
      "</td>"
    );
  }

  function fundMissing(row) {
    return fundFields(row).filter(function (pair) {
      return pair[1] === null || pair[1] === undefined || pair[1] === "";
    }).map(function (pair) { return pair[0]; });
  }

  function fundFresh(ts) {
    if (!ts) return "нет даты";
    var hours = (Date.now() - new Date(ts).getTime()) / 36e5;
    if (!isFinite(hours) || hours < 0) return "нет даты";
    if (hours < 24) return "свежие";
    if (hours < 24 * 7) return "старше суток";
    return "устарели";
  }

  function fundScoreTotal(row) {
    var n = Number((row.scores || {}).total);
    return isFinite(n) ? n : -1;
  }

  function fundPassesDataMode(row, mode) {
    var missing = fundMissing(row);
    var fresh = fundFresh(row.ts);
    if (mode === "gaps") return missing.length > 0;
    if (mode === "full") return missing.length === 0;
    if (mode === "stale") return fresh !== "свежие";
    return true;
  }

  function fundPassesLens(row, lens) {
    var score = fundScoreTotal(row);
    if (lens === "strong") return score >= 70;
    if (lens === "weak") return score >= 0 && score < 70;
    return true;
  }

  function fundSectorId(row) {
    return String(row.sector || "other");
  }

  function renderTestCompanies() {
    var data = lastFundamentals || { items: [], sectors: [] };
    var items = (data.items || []).slice();
    var query = (lastCompaniesQuery || "").trim().toUpperCase();
    var modeAllowed = { gaps: 1, full: 1, stale: 1, all: 1 };
    var lensAllowed = { strong: 1, all: 1, weak: 1 };
    var mode = modeAllowed[lastFundMode] ? lastFundMode : "all";
    var lens = lensAllowed[lastFundLens] ? lastFundLens : "strong";
    var sector = lastCompaniesSector || "all";

    var afterQuery = items.filter(function (row) {
      var blob = ((row.ticker || "") + " " + (row.name || "")).toUpperCase();
      return !query || blob.indexOf(query) !== -1;
    });
    var afterData = afterQuery.filter(function (row) {
      return fundPassesDataMode(row, mode);
    });

    var strongCount = 0;
    var weakCount = 0;
    var holeNames = 0;
    var staleNames = 0;
    afterQuery.forEach(function (row) {
      var score = fundScoreTotal(row);
      if (score >= 70) strongCount += 1;
      else if (score >= 0) weakCount += 1;
      if (fundMissing(row).length) holeNames += 1;
      if (fundFresh(row.ts) !== "свежие") staleNames += 1;
    });

    // В конкретной отрасли показываем всех — иначе «Рекомендуем» прячет слабые.
    var shown = afterData.filter(function (row) {
      if (sector !== "all" && fundSectorId(row) !== sector) return false;
      if (sector === "all") return fundPassesLens(row, lens);
      return true;
    });
    shown.sort(function (a, b) {
      return fundScoreTotal(b) - fundScoreTotal(a);
    });

    var sectorMeta = {};
    (data.sectors || []).forEach(function (group) {
      sectorMeta[group.id] = group;
    });
    var sectorOrder = (data.sectors || []).map(function (group) {
      return group.id;
    });
    var sectorBuckets = {};
    shown.forEach(function (row) {
      var id = fundSectorId(row);
      if (!sectorBuckets[id]) sectorBuckets[id] = [];
      sectorBuckets[id].push(row);
    });
    var sectorIds = sectorOrder.filter(function (id) {
      return sectorBuckets[id] && sectorBuckets[id].length;
    });
    Object.keys(sectorBuckets).forEach(function (id) {
      if (sectorIds.indexOf(id) === -1) sectorIds.push(id);
    });

    var strongBySector = {};
    afterData.forEach(function (row) {
      if (fundScoreTotal(row) < 70) return;
      var id = fundSectorId(row);
      strongBySector[id] = (strongBySector[id] || 0) + 1;
    });
    var strongSectors = Object.keys(strongBySector).length;
    var heads =
      "<th>Компания</th>" +
      FUND_BARS.map(function (bar) {
        if (bar.key === "score") {
          return (
            '<th class="num">Оценка' +
            whatis(
              "Оценка",
              "Одна цифра 0–100. Складывается из трёх частей: насколько дешево (P/E и P/B), качество бизнеса (ROE и EPS) и дивиденд. Веса 40% / 35% / 25%. ≥70 — рекомендуем смотреть. Наведите на цифру в строке — увидите разбивку."
            ) +
            "</th>"
          );
        }
        var tip = bar.tip ? ' title="' + escapeHtml(bar.tip) + '"' : "";
        var unit = bar.unit
          ? '<span class="ind-unit">' + escapeHtml(bar.unit) + "</span>"
          : "";
        return (
          '<th class="num"' +
          tip +
          ">" +
          escapeHtml(bar.title) +
          unit +
          "</th>"
        );
      }).join("");

    function industryRows(list) {
      return list
        .map(function (row) {
          var strong = fundScoreTotal(row) >= 70;
          return (
            '<tr class="' +
            (strong ? "is-strong" : "is-weak") +
            '">' +
            companyCell(row) +
            FUND_BARS.map(function (bar) {
              if (bar.key === "score") return fundScoreCell(row);
              return fundPlainCell(row, bar);
            }).join("") +
            "</tr>"
          );
        })
        .join("");
    }

    function industryBlock(id, rows) {
      var meta = sectorMeta[id] || {};
      var title = meta.title || rows[0].sector_title || id;
      var totalInSector = meta.count != null ? meta.count : rows.length;
      var strongHere = strongBySector[id] || 0;
      var top = rows.filter(function (row) {
        return fundScoreTotal(row) >= 70;
      });
      var rest = rows.filter(function (row) {
        return fundScoreTotal(row) < 70;
      });
      var body =
        industryRows(top) +
        (top.length && rest.length
          ? '<tr class="ind-split"><td colspan="8">Ниже порога</td></tr>'
          : "") +
        industryRows(rest);
      return (
        '<section class="industry" data-industry="' +
        escapeHtml(id) +
        '">' +
        '<header class="industry__head">' +
        "<h3>" +
        escapeHtml(title) +
        "</h3>" +
        '<p class="industry__meta"><span>' +
        plainNumber(strongHere) +
        " рекомендуем</span><span>" +
        plainNumber(rows.length) +
        " в списке</span><span>" +
        plainNumber(totalInSector) +
        " в отрасли</span></p>" +
        "</header>" +
        '<div class="table-scroll"><table class="data-table industry__table"><thead><tr>' +
        heads +
        "</tr></thead><tbody>" +
        body +
        "</tbody></table></div></section>"
      );
    }

    var chipTotals = {};
    var chipStrong = {};
    afterData.forEach(function (row) {
      var id = fundSectorId(row);
      chipTotals[id] = (chipTotals[id] || 0) + 1;
      if (fundScoreTotal(row) >= 70) chipStrong[id] = (chipStrong[id] || 0) + 1;
    });
    var allChipCount = afterData.filter(function (row) {
      return fundPassesLens(row, lens);
    }).length;
    var sectorChips =
      '<div class="industry-chips" role="group" aria-label="Отрасль">' +
      '<button type="button" data-fund-sector="all"' +
      (sector === "all" ? ' aria-pressed="true"' : "") +
      "><span>Все отрасли</span><strong>" +
      plainNumber(allChipCount) +
      "</strong></button>" +
      sectorOrder
        .map(function (id) {
          var total = chipTotals[id] || 0;
          if (!total && sector !== id) return "";
          var meta = sectorMeta[id] || {};
          var label =
            lens === "strong" && sector === "all"
              ? plainNumber(chipStrong[id] || 0) + "/" + plainNumber(total)
              : plainNumber(total);
          return (
            '<button type="button" data-fund-sector="' +
            escapeHtml(id) +
            '"' +
            (sector === id ? ' aria-pressed="true"' : "") +
            "><span>" +
            escapeHtml(meta.title || id) +
            "</span><strong>" +
            escapeHtml(label) +
            "</strong></button>"
          );
        })
        .join("") +
      "</div>";

    var blocks = sectorIds
      .map(function (id) {
        return industryBlock(id, sectorBuckets[id]);
      })
      .join("");

    var summary =
      sector !== "all"
        ? "Отрасль целиком: <strong>" +
          plainNumber(shown.length) +
          "</strong> компаний в списке. Фильтр «Рекомендуем» действует только в «Все отрасли»."
        : lens === "strong"
          ? "Рекомендуем по показателям: <strong>" +
            plainNumber(strongCount) +
            "</strong> компаний в <strong>" +
            plainNumber(strongSectors) +
            "</strong> отраслях (скор ≥70)."
          : lens === "weak"
            ? "Слабее порога: <strong>" +
              plainNumber(weakCount) +
              "</strong> компаний со скором ниже 70."
            : "Все компании с цифрами брокера: <strong>" +
              plainNumber(afterQuery.length) +
              "</strong>.";

    var empty = !items.length
      ? "Список ещё грузится"
      : query
        ? "Такой компании нет"
        : sector !== "all"
          ? "В этой отрасли пусто"
          : lens === "strong"
            ? "В этом срезе нет компаний со скором ≥70"
            : "В этом срезе пусто";

    byId("page-body").innerHTML =
      '<section class="industries">' +
      '<div class="industries__toolbar">' +
      '<p class="industries__summary">' +
      summary +
      " Скор из P/E, P/B, EPS, ROE и дивиденда.</p>" +
      '<div class="tape-bar industries__actions">' +
      '<button type="button" class="primary" id="fund-refresh">Обновить с брокера</button>' +
      '<input id="fund-find" class="tape-find" type="search" placeholder="Тикер или имя" value="' +
      escapeHtml(lastCompaniesQuery || "") +
      '" aria-label="Найти компанию">' +
      "</div></div>" +
      '<div class="tape-filters" role="group" aria-label="Сила по показателям">' +
      '<button type="button" data-fund-lens="strong"' +
      (lens === "strong" ? ' aria-pressed="true"' : "") +
      "><span>Рекомендуем</span><strong>" +
      plainNumber(strongCount) +
      "</strong></button>" +
      '<button type="button" data-fund-lens="all"' +
      (lens === "all" ? ' aria-pressed="true"' : "") +
      "><span>Все</span><strong>" +
      plainNumber(afterQuery.length) +
      "</strong></button>" +
      '<button type="button" data-fund-lens="weak"' +
      (lens === "weak" ? ' aria-pressed="true"' : "") +
      "><span>Слабее</span><strong>" +
      plainNumber(weakCount) +
      "</strong></button>" +
      "</div>" +
      sectorChips +
      '<div class="tape-filters industries__data" role="group" aria-label="Полнота данных">' +
      '<button type="button" data-fund-mode="all"' +
      (mode === "all" ? ' aria-pressed="true"' : "") +
      "><span>Любые данные</span></button>" +
      '<button type="button" data-fund-mode="full"' +
      (mode === "full" ? ' aria-pressed="true"' : "") +
      "><span>Без дыр</span><strong>" +
      plainNumber(Math.max(0, afterQuery.length - holeNames)) +
      "</strong></button>" +
      '<button type="button" data-fund-mode="gaps"' +
      (mode === "gaps" ? ' aria-pressed="true"' : "") +
      "><span>Дыры</span><strong>" +
      plainNumber(holeNames) +
      "</strong></button>" +
      '<button type="button" data-fund-mode="stale"' +
      (mode === "stale" ? ' aria-pressed="true"' : "") +
      "><span>Старые</span><strong>" +
      plainNumber(staleNames) +
      "</strong></button>" +
      "</div>" +
      '<p id="fund-board-note" class="tape-note">' +
      escapeHtml(lastCompaniesNote || "") +
      "</p>" +
      (blocks || '<p class="industries__empty">' + escapeHtml(empty) + "</p>") +
      "</section>";
    bindTestCompanies();
  }

  function bindTestCompanies() {
    document.querySelectorAll("[data-fund-lens]").forEach(function (btn) {
      btn.onclick = function () {
        lastFundLens = btn.getAttribute("data-fund-lens") || "strong";
        renderTestCompanies();
      };
    });
    document.querySelectorAll("[data-fund-mode]").forEach(function (btn) {
      btn.onclick = function () {
        lastFundMode = btn.getAttribute("data-fund-mode") || "all";
        renderTestCompanies();
      };
    });
    document.querySelectorAll("[data-fund-sector]").forEach(function (btn) {
      btn.onclick = function () {
        lastCompaniesSector = btn.getAttribute("data-fund-sector") || "all";
        renderTestCompanies();
      };
    });
    var find = byId("fund-find");
    if (find) {
      find.oninput = function () {
        lastCompaniesQuery = find.value || "";
        var pos = find.selectionStart;
        renderTestCompanies();
        var again = byId("fund-find");
        if (again) {
          again.focus();
          again.selectionStart = again.selectionEnd = pos;
        }
      };
    }
    var refresh = byId("fund-refresh");
    if (refresh) {
      refresh.onclick = function () {
        var note = byId("fund-board-note");
        refresh.disabled = true;
        if (note) note.textContent = "Обновляю показатели у брокера…";
        apiPost("/fundamentals/refresh", {}, { timeoutMs: 180000 })
          .then(function () {
            lastCompaniesNote = "Показатели обновлены.";
            return refreshCompanies();
          })
          .catch(function (err) {
            lastCompaniesNote = err.message || "брокер не отдал показатели";
            renderTestCompanies();
          })
          .finally(function () {
            refresh.disabled = false;
          });
      };
    }
  }

  function whatIfDefaultStart() {
    var d = new Date();
    d.setFullYear(d.getFullYear() - 2);
    function pad(n) {
      return (n < 10 ? "0" : "") + n;
    }
    return d.getFullYear() + "-" + pad(d.getMonth() + 1) + "-" + pad(d.getDate());
  }

  function whatIfTickerNames() {
    var names = {};
    function put(ticker, name) {
      var t = String(ticker || "").toUpperCase();
      var n = String(name || "").trim();
      if (!t || !n || n.toUpperCase() === t) return;
      names[t] = n;
    }
    ((lastCandlesCoverage && lastCandlesCoverage.items) || []).forEach(function (row) {
      put(row.ticker, row.name);
    });
    ((lastFundamentals && lastFundamentals.items) || []).forEach(function (row) {
      put(row.ticker, row.name);
    });
    return names;
  }

  function whatIfCompanyLabel(leg) {
    var ticker = String((leg && leg.ticker) || "").toUpperCase();
    if (!ticker) return "—";
    var hints = whatIfTickerNames();
    var raw = String((leg && leg.name) || "").trim();
    var name = raw && raw.toUpperCase() !== ticker ? raw : hints[ticker] || "";
    if (name && name.toUpperCase() === ticker) name = "";
    return name ? name + " · " + ticker : ticker;
  }

  function whatIfSelectedTickers() {
    var pool = lastDeskTickers && lastDeskTickers.length ? lastDeskTickers : [];
    if (lastWhatIfTickers == null) {
      var defaults = deskDefaultTickers(pool);
      return defaults.length ? defaults : pool.slice(0, 14);
    }
    return lastWhatIfTickers.filter(function (ticker) {
      return pool.indexOf(ticker) >= 0;
    });
  }

  function whatIfEqualAmounts(tickers, capital) {
    var n = tickers.length;
    var out = {};
    if (!n) return out;
    var base = Math.floor((Number(capital) || 0) / n);
    var left = Math.round(Number(capital) || 0) - base * n;
    tickers.forEach(function (ticker, i) {
      out[ticker] = base + (i === 0 ? left : 0);
    });
    return out;
  }

  function whatIfAmountsMap(tickers) {
    if (lastWhatIfEqual || !lastWhatIfAmounts) {
      return whatIfEqualAmounts(tickers, lastWhatIfCapital);
    }
    var out = {};
    tickers.forEach(function (ticker) {
      var v = Number(lastWhatIfAmounts[ticker]);
      out[ticker] = isFinite(v) && v > 0 ? v : 0;
    });
    return out;
  }

  function whatIfTone(pct) {
    var n = Number(pct);
    if (!isFinite(n)) return "fund-tone--muted";
    if (n >= 0.1) return "fund-tone--good";
    if (n >= 0) return "fund-tone--mid";
    return "fund-tone--bad";
  }

  function renderWhatIf() {
    if (!lastWhatIfStart) lastWhatIfStart = whatIfDefaultStart();
    var tickers = whatIfSelectedTickers();
    var amounts = whatIfAmountsMap(tickers);
    var sumAmt = 0;
    tickers.forEach(function (t) {
      sumAmt += Number(amounts[t]) || 0;
    });
    var names = whatIfTickerNames();
    var sectors = (lastDeskGroups && lastDeskGroups.sectors) || [];
    var moexTickers = (lastDeskGroups && lastDeskGroups.moex) || [];
    var sp500Tickers = (lastDeskGroups && lastDeskGroups.sp500) || [];
    var moexSectors = sectors.filter(function (sector) {
      return sector && sector.id !== "sp500";
    });
    var spSector = sectors.filter(function (sector) {
      return sector && sector.id === "sp500";
    })[0] || null;
    var perHint =
      tickers.length
        ? tickers.length +
          " бумаг · поровну ~" +
          rubles(Math.floor((Number(lastWhatIfCapital) || 0) / tickers.length))
        : "выберите бумаги";
    function sectorChecksHtml(sector) {
      var items = (sector && sector.tickers) || [];
      var selected = tickers.filter(function (ticker) {
        return items.indexOf(ticker) >= 0;
      });
      return renderDeskCheckGroup(
        "whatif-ticker",
        (sector.title || "Тикеры") +
          " (" +
          selected.length +
          "/" +
          items.length +
          ")",
        items,
        selected
      );
    }
    var marketPick =
      '<div class="desk-market-actions" role="group" aria-label="Рынок">' +
      '<button type="button" class="ghost compact" data-whatif-market="moex"' +
      (moexTickers.length ? "" : " disabled") +
      ">РФ акции (" +
      escapeHtml(String(moexTickers.length)) +
      ")</button>" +
      '<button type="button" class="ghost compact" data-whatif-market="sp500"' +
      (sp500Tickers.length ? "" : " disabled") +
      ">Западные (" +
      escapeHtml(String(sp500Tickers.length)) +
      ")</button>" +
      '<button type="button" class="ghost compact" data-whatif-market="none">сбросить</button>' +
      "</div>";
    var tickerChecks =
      marketPick +
      '<div class="desk-market-break">Россия · MOEX</div>' +
      moexSectors.map(sectorChecksHtml).join("") +
      (spSector
        ? '<div class="desk-market-break">Запад · S&P 500</div>' +
          sectorChecksHtml(spSector)
        : "");
    var showAmountInputs = tickers.length > 0 && tickers.length <= 40;
    var amountBlock = "";
    if (tickers.length) {
      if (showAmountInputs) {
        var amountRows = tickers
          .map(function (ticker) {
            var label = names[ticker]
              ? escapeHtml(names[ticker]) +
                ' <small class="muted">' +
                escapeHtml(ticker) +
                "</small>"
              : escapeHtml(ticker);
            return (
              "<tr><td>" +
              label +
              '</td><td class="num"><input type="text" inputmode="decimal" data-rub-input data-whatif-amt="' +
              escapeHtml(ticker) +
              '" value="' +
              escapeHtml(formatRubGrouped(amounts[ticker] || 0)) +
              '"></td></tr>'
            );
          })
          .join("");
        amountBlock =
          '<section class="whatif-amounts">' +
          '<div class="whatif-amounts__head">' +
          "<h3>Суммы на бумагу</h3>" +
          '<button type="button" class="ghost compact" id="whatif-equal">поровну</button>' +
          "</div>" +
          '<p class="source-line">Сумма строк: ' +
          escapeHtml(rubles(sumAmt)) +
          (Math.abs(sumAmt - Number(lastWhatIfCapital)) > 0.5
            ? " · отличается от бюджета — считаем по суммам строк"
            : "") +
          "</p>" +
          wrapTableScroll(
            '<table class="data-table compact whatif-amt-table"><thead><tr><th>Компания</th><th class="num">Сумма, ₽</th></tr></thead><tbody>' +
              amountRows +
              "</tbody></table>"
          ) +
          "</section>";
      } else {
        amountBlock =
          '<section class="whatif-amounts">' +
          '<div class="whatif-amounts__head">' +
          "<h3>Суммы на бумагу</h3>" +
          '<button type="button" class="ghost compact" id="whatif-equal">поровну</button>' +
          "</div>" +
          '<p class="source-line">Выбрано ' +
          escapeHtml(String(tickers.length)) +
          " бумаг — делим бюджет поровну (~" +
          escapeHtml(
            rubles(
              Math.floor((Number(lastWhatIfCapital) || 0) / tickers.length)
            )
          ) +
          "). Чтобы править суммы вручную, оставьте не больше 40 бумаг.</p>" +
          "</section>";
      }
    }
    var result = lastWhatIfResult;
    var resultHtml = "";
    if (result && result.error) {
      resultHtml =
        '<p class="empty whatif-error">' + escapeHtml(result.error) + "</p>";
    } else if (result) {
      var legs = (result.legs || [])
        .slice()
        .sort(function (a, b) {
          return Number(b.pnl_pct || 0) - Number(a.pnl_pct || 0);
        });
      var legRows = legs
        .map(function (leg) {
          var tone = whatIfTone(leg.pnl_pct);
          return (
            '<tr class="' +
            tone +
            '"><td>' +
            escapeHtml(whatIfCompanyLabel(leg)) +
            '</td><td class="num">' +
            escapeHtml(ruDay(leg.entry_day)) +
            "<br><small>" +
            escapeHtml(rubles(leg.entry_close)) +
            '</small></td><td class="num">' +
            escapeHtml(ruDay(leg.exit_day)) +
            "<br><small>" +
            escapeHtml(rubles(leg.exit_close)) +
            '</small></td><td class="num">' +
            escapeHtml(rubles(leg.invested)) +
            '</td><td class="num">' +
            escapeHtml(rubles(leg.final_value)) +
            '</td><td class="num">' +
            escapeHtml(rubles(leg.pnl)) +
            '</td><td class="num">' +
            escapeHtml(plainNumber(Number(leg.pnl_pct) * 100) + "%") +
            "</td></tr>"
          );
        })
        .join("");
      var skipNote = (result.skipped || []).length
        ? '<p class="source-line">Пропущено: ' +
          escapeHtml(
            (result.skipped || [])
              .map(function (row) {
                return (row.ticker || "") + " (" + (row.reason || "") + ")";
              })
              .join(", ")
          ) +
          "</p>"
        : "";
      resultHtml =
        '<section class="whatif-result" data-tour="whatif-result">' +
        '<div class="whatif-kpis">' +
        '<div><span class="k">Итог</span><strong>' +
        escapeHtml(rubles(result.final_equity)) +
        "</strong></div>" +
        '<div><span class="k">PnL</span><strong class="' +
        whatIfTone(result.pnl_pct) +
        '">' +
        escapeHtml(rubles(result.pnl)) +
        "</strong></div>" +
        '<div><span class="k">Доходность</span><strong class="' +
        whatIfTone(result.pnl_pct) +
        '">' +
        escapeHtml(plainNumber(Number(result.pnl_pct) * 100) + "%") +
        "</strong></div>" +
        '<div><span class="k">Срок</span><strong>' +
        escapeHtml(String(result.days != null ? result.days : "—")) +
        " дн.</strong></div>" +
        "</div>" +
        wrapTableScroll(
          '<table class="data-table"><thead><tr>' +
            "<th>Компания</th><th class=\"num\">Купил</th><th class=\"num\">Сейчас</th>" +
            "<th class=\"num\">Вложено</th><th class=\"num\">Стоит</th>" +
            "<th class=\"num\">PnL</th><th class=\"num\">%</th>" +
            "</tr></thead><tbody>" +
            (legRows || '<tr><td colspan="7">Нет удачных ног</td></tr>') +
            "</tbody></table>"
        ) +
        skipNote +
        '<p class="source-line">Комиссия ' +
        escapeHtml(String(result.commission_bps != null ? result.commission_bps : "—")) +
        " bps · дивиденды не учитываются · заявка не ставится</p>" +
        "</section>";
    }

    byId("page-body").innerHTML =
      '<section class="panel whatif" data-tour="whatif">' +
      "<h3>Если бы купил тогда</h3>" +
      '<div class="whatif-params filters">' +
      '<label class="field compact">бюджет, ₽' +
      '<input id="whatif-capital" type="text" inputmode="decimal" data-rub-input value="' +
      escapeHtml(formatRubGrouped(lastWhatIfCapital)) +
      '"></label>' +
      '<label class="field compact">дата покупки' +
      '<input id="whatif-start" type="date" value="' +
      escapeHtml(lastWhatIfStart) +
      '"></label>' +
      '<button type="button" class="primary" id="whatif-run"' +
      (lastWhatIfBusy || !tickers.length ? " disabled" : "") +
      ">" +
      (lastWhatIfBusy ? "Считаю…" : "Посчитать") +
      "</button>" +
      "</div>" +
      '<p class="source-line" id="whatif-hint">' +
      escapeHtml(perHint) +
      "</p>" +
      '<div class="desk-batch-pick" data-tour="whatif-pick">' +
      tickerChecks +
      "</div>" +
      amountBlock +
      resultHtml +
      "</section>";
    bindWhatIfControls();
  }

  function bindWhatIfControls() {
    var capitalEl = byId("whatif-capital");
    var startEl = byId("whatif-start");
    wireRubInputs(byId("page-body"));
    if (capitalEl) {
      capitalEl.onchange = function () {
        lastWhatIfCapital = Math.max(0, parseRubInput(capitalEl.value) || 0);
        capitalEl.value = formatRubGrouped(lastWhatIfCapital);
        if (lastWhatIfEqual) lastWhatIfAmounts = null;
        renderWhatIf();
      };
    }
    if (startEl) {
      startEl.onchange = function () {
        lastWhatIfStart = startEl.value || whatIfDefaultStart();
      };
    }
    var equalBtn = byId("whatif-equal");
    if (equalBtn) {
      equalBtn.onclick = function () {
        lastWhatIfEqual = true;
        lastWhatIfAmounts = null;
        renderWhatIf();
      };
    }
    document.querySelectorAll("[data-whatif-amt]").forEach(function (input) {
      input.onchange = function () {
        var ticker = input.getAttribute("data-whatif-amt");
        if (!ticker) return;
        lastWhatIfEqual = false;
        lastWhatIfAmounts = whatIfAmountsMap(whatIfSelectedTickers());
        var amt = Math.max(0, parseRubInput(input.value) || 0);
        lastWhatIfAmounts[ticker] = amt;
        input.value = formatRubGrouped(amt);
        renderWhatIf();
      };
    });
    var pick = document.querySelector('[data-tour="whatif-pick"]');
    if (pick) {
      pick.addEventListener("change", function (ev) {
        var input = ev.target;
        if (
          !input ||
          !input.getAttribute ||
          input.getAttribute("data-desk-check") !== "whatif-ticker"
        ) {
          return;
        }
        lastWhatIfTickers = Array.prototype.slice
          .call(
            document.querySelectorAll(
              'input[data-desk-check="whatif-ticker"]:checked'
            )
          )
          .map(function (el) {
            return String(el.value || "").toUpperCase();
          })
          .filter(Boolean);
        if (lastWhatIfEqual) lastWhatIfAmounts = null;
        renderWhatIf();
      });
      pick.addEventListener("click", function (ev) {
        var marketBtn =
          ev.target && ev.target.closest
            ? ev.target.closest("[data-whatif-market]")
            : null;
        if (marketBtn) {
          var market = marketBtn.getAttribute("data-whatif-market") || "";
          if (market === "moex") {
            lastWhatIfTickers = ((lastDeskGroups && lastDeskGroups.moex) || []).slice();
          } else if (market === "sp500") {
            lastWhatIfTickers = ((lastDeskGroups && lastDeskGroups.sp500) || []).slice();
          } else {
            lastWhatIfTickers = [];
          }
          if (lastWhatIfEqual) lastWhatIfAmounts = null;
          renderWhatIf();
          return;
        }
        var btn =
          ev.target && ev.target.closest
            ? ev.target.closest(
                "[data-desk-check-all], [data-desk-check-none]"
              )
            : null;
        if (!btn) return;
        var kind =
          btn.getAttribute("data-desk-check-all") ||
          btn.getAttribute("data-desk-check-none");
        if (kind !== "whatif-ticker") return;
        var all = !!btn.getAttribute("data-desk-check-all");
        var scopeRaw = btn.getAttribute("data-desk-scope") || "";
        var scopeItems = scopeRaw ? scopeRaw.split(",").filter(Boolean) : [];
        var current = whatIfSelectedTickers();
        if (all) {
          var merged = current.slice();
          scopeItems.forEach(function (ticker) {
            if (merged.indexOf(ticker) < 0) merged.push(ticker);
          });
          lastWhatIfTickers = merged;
        } else {
          lastWhatIfTickers = current.filter(function (ticker) {
            return scopeItems.indexOf(ticker) < 0;
          });
        }
        if (lastWhatIfEqual) lastWhatIfAmounts = null;
        renderWhatIf();
      });
    }
    var run = byId("whatif-run");
    if (run) {
      run.onclick = function () {
        var tickers = whatIfSelectedTickers();
        if (!tickers.length) return;
        if (capitalEl) {
          lastWhatIfCapital = Math.max(0, parseRubInput(capitalEl.value) || 0);
          capitalEl.value = formatRubGrouped(lastWhatIfCapital);
        }
        if (startEl) {
          lastWhatIfStart = startEl.value || whatIfDefaultStart();
        }
        var amounts = whatIfAmountsMap(tickers);
        var body =
          lastWhatIfEqual || tickers.length > 40
            ? {
                start: lastWhatIfStart,
                capital: lastWhatIfCapital,
                tickers: tickers,
              }
            : {
                start: lastWhatIfStart,
                allocations: amounts,
              };
        lastWhatIfBusy = true;
        lastWhatIfResult = null;
        renderWhatIf();
        apiPost("/desk/buyhold", body, { timeoutMs: 180000 })
          .then(function (data) {
            lastWhatIfResult = data;
          })
          .catch(function (err) {
            var msg = err.message || "не удалось посчитать";
            if (err.status === 404) {
              msg =
                "API без /desk/buyhold — перезапустите кабинет (python -m app) и обновите страницу.";
            }
            lastWhatIfResult = { error: msg };
          })
          .finally(function () {
            lastWhatIfBusy = false;
            renderWhatIf();
          });
      };
    }
  }

  function refreshWhatIf() {
    var jobs = [];
    if (!whatifListTried || !(lastDeskTickers && lastDeskTickers.length)) {
      whatifListTried = true;
      jobs.push(
        apiGet("/desk/candles?tf=1d")
          .then(function (data) {
            applyDeskCandleUniverse(data);
          })
          .catch(function () {})
      );
    }
    if (!lastCandlesCoverage) {
      jobs.push(
        apiGet("/candles/coverage?tf=1d")
          .then(function (data) {
            lastCandlesCoverage = data;
          })
          .catch(function () {})
      );
    }
    if (!jobs.length) {
      renderWhatIf();
      return Promise.resolve();
    }
    return Promise.all(jobs).then(function () {
      if (currentRoute === "whatif") renderWhatIf();
    });
  }

  function renderTestStrategy() {
    var picked = lastDeskSleeve || "abs_momentum_4";
    var groups = SLEEVE_GROUPS.map(function (group) {
      var buttons = group.ids.map(function (id) {
        var on = id === picked ? ' aria-pressed="true"' : "";
        return '<button type="button" data-sleeve="' + escapeHtml(id) + '"' + on + ">" + escapeHtml(SLEEVE_NAMES[id] || id) + "</button>";
      }).join("");
      return "<section><h3>" + escapeHtml(group.title) + "</h3><div class=\"sleeve-picks\">" + buttons + "</div></section>";
    }).join("");
    var names = {};
    ((lastCandlesCoverage && lastCandlesCoverage.items) || []).forEach(function (row) {
      if (row.ticker) names[row.ticker] = row.name || "";
    });
    function tickerLabel(ticker) {
      var name = names[ticker];
      if (name && String(name).toUpperCase() !== ticker) return name + " · " + ticker;
      return ticker;
    }
    var sectors = (lastDeskGroups && lastDeskGroups.sectors) || [];
    var ticker = lastDeskTicker || "SBER";
    var tickerHtml;
    if (sectors.length) {
      tickerHtml = '<select id="test-ticker">' + sectors.map(function (sector) {
        var opts = (sector.tickers || []).map(function (item) {
          return '<option value="' + escapeHtml(item) + '"' + (item === ticker ? " selected" : "") + ">" + escapeHtml(tickerLabel(item)) + "</option>";
        }).join("");
        return '<optgroup label="' + escapeHtml(sector.title || sector.id || "Бумага") + '">' + opts + "</optgroup>";
      }).join("") + "</select>";
    } else {
      tickerHtml = '<input id="test-ticker" value="' + escapeHtml(ticker) + '" maxlength="12" spellcheck="false">';
    }
    var result = lastDeskBacktest;
    var resultHtml = "<p class=\"muted\">Здесь будут доходность, итог в рублях, число сделок и просадка. Заявка не ставится.</p>";
    if (result && result.error) {
      resultHtml = "<p class=\"error\">" + escapeHtml(result.error) + "</p>";
    } else if (result && result.backtest) {
      var summary = (result.backtest || {}).summary || {};
      var ret = summary.total_return;
      resultHtml =
        "<h3>" + escapeHtml(SLEEVE_NAMES[picked] || picked) + " · " + escapeHtml(tickerLabel(lastDeskTicker || "")) + "</h3>" +
        '<dl class="tape-result">' +
        "<div><dt>Доходность</dt><dd>" + (ret == null ? "—" : plainNumber(Number(ret) * 100) + "%") + "</dd></div>" +
        "<div><dt>Итог</dt><dd>" + rubles(summary.net_pnl) + "</dd></div>" +
        "<div><dt>Сделок</dt><dd>" + plainNumber(summary.trades) + "</dd></div>" +
        "<div><dt>Просадка</dt><dd>" + (summary.max_drawdown == null ? "—" : plainNumber(Number(summary.max_drawdown) * 100) + "%") + "</dd></div>" +
        "</dl>";
    }
    byId("page-body").innerHTML =
      '<section class="tape">' +
      '<p class="tape-lead">Четыре группы стратегий. Выбери одну и бумагу из своей отрасли. Считаем по скачанному файлу, заявка не ставится.</p>' +
      '<div class="sleeve-groups">' + groups + "</div>" +
      '<p class="sleeve-how">' + escapeHtml(SLEEVE_LINE[picked] || "") + "</p>" +
      '<div class="tape-run">' +
      "<label>Бумага " + tickerHtml + "</label>" +
      '<button type="button" class="primary" id="test-run">Проверить</button>' +
      "</div>" +
      '<div id="test-run-note"></div>' + resultHtml + "</section>";
    document.querySelectorAll("[data-sleeve]").forEach(function (btn) {
      btn.onclick = function () {
        var box = byId("test-ticker");
        if (box) lastDeskTicker = box.value;
        lastDeskSleeve = btn.getAttribute("data-sleeve") || picked;
        renderTestStrategy();
      };
    });
    var run = byId("test-run");
    if (run) run.onclick = function () {
      var sleeve = lastDeskSleeve || picked;
      var box = byId("test-ticker");
      var symbol = String((box && box.value) || "").trim().toUpperCase();
      if (!/^[A-Z0-9]{1,12}$/.test(symbol)) {
        window.alert("Тикер: латинские буквы и цифры, до 12 знаков");
        return;
      }
      lastDeskSleeve = sleeve;
      lastDeskTicker = symbol;
      run.disabled = true;
      var note = byId("test-run-note");
      if (note) note.textContent = "Считаю " + (SLEEVE_NAMES[sleeve] || sleeve) + " по " + tickerLabel(symbol) + "…";
      apiPost("/backtests", { sleeve: sleeve, ticker: symbol }, { timeoutMs: 120000 }).then(function (data) {
        lastDeskBacktest = data.result || data;
        renderTestStrategy();
      }).catch(function (err) {
        lastDeskBacktest = { error: err.message || "прогон не удался" };
        renderTestStrategy();
      });
    };
    if (!deskListTried) {
      deskListTried = true;
      var jobs = [];
      if (!sectors.length) {
        jobs.push(apiGet("/desk/candles?tf=1d").then(function (data) {
          applyDeskCandleUniverse(data);
        }).catch(function () {}));
      }
      if (!lastCandlesCoverage) {
        jobs.push(apiGet("/candles/coverage").then(function (data) {
          lastCandlesCoverage = data;
        }).catch(function () {}));
      }
      if (jobs.length) {
        Promise.all(jobs).then(function () {
          if (currentRoute === "strategies") renderTestStrategy();
        });
      }
    }
  }

  function renderDeskHome() {
    byId("page-body").innerHTML =
      '<div class="desk-fork">' +
      '<section class="desk-pane desk-pane-test">' +
      "<h3>Тест</h3>" +
      "<p>Скачиваем свечи и проверяем стратегии на истории. Брокеру отсюда ничего не отправляется.</p>" +
      "<ul><li>Скачать свечи</li><li>Проверить стратегию</li><li>Посмотреть, что вышло</li></ul>" +
      '<a class="desk-go" href="#/candles">Открыть тест</a>' +
      "</section>" +
      '<section class="desk-pane desk-pane-work">' +
      "<h3>Работа</h3>" +
      "<p>Песочницы брокера: у каждой свой счёт и одна стратегия. Деньги игровые.</p>" +
      '<p id="desk-work-status">Смотрю счёт…</p>' +
      '<a class="desk-go" href="#/work">Открыть работу</a>' +
      "</section>" +
      "</div>";
    apiGet("/work").then(function (data) {
      var box = byId("desk-work-status");
      if (!box) return;
      var step = (data.steps || []).filter(function (item) { return item.ok; }).length;
      var cash = data.portfolio && data.portfolio.cash != null ? data.portfolio.cash : "";
      box.textContent = "Шаг " + step + " из 5. На счёте " + rubles(cash) + ".";
    }).catch(function () {
      var box = byId("desk-work-status");
      if (box) box.textContent = "Счёт сейчас не прочитался.";
    });
  }

  function renderStrategies() {
    if (deskMode() === "test") {
      var testBody = byId("page-body");
      testBody.innerHTML = renderStrategiesDesk();
      bindStrategiesLabControls();
      if (!deskListTried || !(lastDeskTickers && lastDeskTickers.length)) {
        deskListTried = true;
        apiGet("/desk/candles?tf=1d")
          .then(function (data) {
            applyDeskCandleUniverse(data);
          })
          .catch(function () {})
          .then(function () {
            if (currentRoute === "strategies" && deskMode() === "test") {
              renderStrategies();
            }
          });
      }
      return;
    }
    var body = byId("page-body");
    var sleeveId = strategiesSleeveFromHash();
    if (sleeveId) {
      body.innerHTML = renderStrategiesSleeveCard(sleeveId);
      bindSignalFilters();
      return;
    }
    signalFilterTicker = "";
    signalFilterKind = "";
    body.innerHTML = candlePullHtml() + renderStrategiesCompare();
    body.querySelectorAll("tr[data-href]").forEach(function (row) {
      row.addEventListener("click", function (event) {
        if (event.target && event.target.closest && event.target.closest("a")) {
          return;
        }
        location.hash = row.getAttribute("data-href");
      });
    });
    bindStrategiesLabControls();
    bindCandlePull();
  }

  function syncBudgetInputs(changedEl) {
    var pool = tradingPoolRub();
    if (pool <= 0) return;
    var sleeve = changedEl.getAttribute("data-sleeve-weight") ||
      changedEl.getAttribute("data-sleeve-capital");
    if (!sleeve) return;
    var pctEl = document.querySelector(
      '[data-sleeve-weight="' + sleeve + '"]'
    );
    var capEl = document.querySelector(
      '[data-sleeve-capital="' + sleeve + '"]'
    );
    if (!pctEl || !capEl) return;
    if (changedEl.hasAttribute("data-sleeve-weight")) {
      var pct = Number(pctEl.value);
      if (!isFinite(pct) || pct < 0) pct = 0;
      capEl.value = formatRubGrouped(Math.round((pool * pct) / 100));
    } else {
      var capital = parseRubInput(capEl.value);
      if (!isFinite(capital) || capital < 0) capital = 0;
      pctEl.value = String(Math.round((capital / pool) * 1000) / 10);
    }
  }

  function reloadStrategiesPlanAndStatus() {
    return Promise.all([
      apiGet(
        "/allocation/plan?example_price=" +
          encodeURIComponent(String(planExamplePrice || 250))
      )
        .then(function (plan) {
          lastAllocPlan = plan;
          return plan;
        })
        .catch(function () {
          return null;
        }),
      apiGet("/allocation")
        .then(function (data) {
          lastAllocation = data;
          return data;
        })
        .catch(function () {
          return null;
        }),
      apiGet("/status")
        .then(function (data) {
          lastStatus = data;
          lastStatusAt = new Date();
          return data;
        })
        .catch(function () {
          return null;
        }),
    ]).then(function () {
      if (currentRoute === "strategies") renderStrategies();
    });
  }

  function bindStrategiesLabControls() {
    wireRubInputs(byId("page-body"));
    document.querySelectorAll("[data-sleeve-weight], [data-sleeve-capital]").forEach(
      function (el) {
        el.addEventListener("input", function () {
          syncBudgetInputs(el);
        });
        el.addEventListener("change", function () {
          syncBudgetInputs(el);
        });
      }
    );
    bindCapitalSettingsActions("strategies", function () {
      return reloadStrategiesPlanAndStatus();
    });
    var whatIfCap = byId("plan-whatif-capital");
    var whatIfPrice = byId("plan-example-price");
    function refreshWhatIf() {
      if (whatIfCap) {
        var n = parseRubInput(whatIfCap.value);
        if (!isFinite(n) || n < 0) n = 0;
        whatIfCap.value = formatRubGrouped(n);
        planWhatIfCapital = whatIfCap.value;
      }
      if (whatIfPrice) {
        var price = Number(whatIfPrice.value);
        planExamplePrice = isFinite(price) && price > 0 ? price : 250;
      }
      apiGet(
        "/allocation/plan?example_price=" +
          encodeURIComponent(String(planExamplePrice))
      )
        .then(function (plan) {
          lastAllocPlan = plan;
        })
        .catch(function () {})
        .finally(function () {
          renderStrategies();
        });
    }
    if (whatIfCap) {
      whatIfCap.addEventListener("change", refreshWhatIf);
      whatIfCap.addEventListener("keydown", function (event) {
        if (event.key === "Enter") {
          event.preventDefault();
          refreshWhatIf();
        }
      });
    }
    if (whatIfPrice) {
      whatIfPrice.addEventListener("change", refreshWhatIf);
      whatIfPrice.addEventListener("keydown", function (event) {
        if (event.key === "Enter") {
          event.preventDefault();
          refreshWhatIf();
        }
      });
    }
    var saveBtn = byId("strategies-budget-save");
    if (saveBtn) {
      saveBtn.addEventListener("click", function () {
        var inputs = document.querySelectorAll("[data-sleeve-weight]");
        var weights = [];
        var sumPct = 0;
        inputs.forEach(function (el) {
          var pct = Number(el.value);
          if (!isFinite(pct) || pct < 0) pct = 0;
          sumPct += pct;
          weights.push({
            sleeve: el.getAttribute("data-sleeve-weight"),
            weight: Math.round(pct * 10) / 1000,
          });
        });
        var status = byId("strategies-budget-status");
        if (Math.abs(sumPct - 100) > 0.15) {
          if (status) {
            status.textContent =
              "Сумма долей сейчас " +
              sumPct.toLocaleString("ru-RU") +
              "% — нужно ровно 100%.";
          }
          return;
        }
        var norm = [];
        var left = 1;
        weights.forEach(function (row, i) {
          if (i === weights.length - 1) {
            norm.push({ sleeve: row.sleeve, weight: Math.round(left * 1e6) / 1e6 });
          } else {
            var w = Math.round((row.weight / (sumPct / 100)) * 1e6) / 1e6;
            left = Math.round((left - w) * 1e6) / 1e6;
            norm.push({ sleeve: row.sleeve, weight: w });
          }
        });
        saveBtn.disabled = true;
        apiPut("/allocation/weights", { weights: norm })
          .then(function (data) {
            lastAllocation = data;
            if (status) status.textContent = "Бюджеты сохранены.";
            return apiGet(
              "/allocation/plan?example_price=" +
                encodeURIComponent(String(planExamplePrice))
            ).then(function (plan) {
              lastAllocPlan = plan;
              renderStrategies();
            });
          })
          .catch(function (err) {
            if (status) {
              status.textContent =
                "Не удалось сохранить: " + (err.message || "ошибка");
            }
          })
          .finally(function () {
            saveBtn.disabled = false;
          });
      });
    }
    var runAllBtn = byId("desk-run-all");
    function readDeskChecks(kind) {
      return Array.prototype.slice
        .call(
          document.querySelectorAll(
            'input[data-desk-check="' + kind + '"]:checked'
          )
        )
        .map(function (el) {
          return String(el.value || "").trim();
        })
        .filter(Boolean);
    }
    function syncDeskPickFromDom() {
      lastDeskBatchSleeves = readDeskChecks("sleeve");
      lastDeskBatchTickers = readDeskChecks("ticker").map(function (ticker) {
        return ticker.toUpperCase();
      });
    }
    var pickRoot = document.querySelector('[data-tour="strategies-desk-pick"]');
    if (pickRoot) {
      pickRoot.addEventListener("change", function (ev) {
        var input = ev.target;
        if (
          !input ||
          !input.getAttribute ||
          !input.getAttribute("data-desk-check")
        ) {
          return;
        }
        syncDeskPickFromDom();
        renderStrategies();
      });
      pickRoot.addEventListener("click", function (ev) {
        var marketBtn =
          ev.target && ev.target.closest
            ? ev.target.closest("[data-desk-market]")
            : null;
        if (marketBtn) {
          var market = marketBtn.getAttribute("data-desk-market") || "";
          var moexPool = (lastDeskGroups && lastDeskGroups.moex) || [];
          var westPool = (lastDeskGroups && lastDeskGroups.sp500) || [];
          if (market === "moex") {
            lastDeskBatchTickers = moexPool.slice();
          } else if (market === "sp500") {
            lastDeskBatchTickers = westPool.slice();
          } else if (market === "none") {
            lastDeskBatchTickers = [];
          }
          renderStrategies();
          return;
        }
        var btn = ev.target && ev.target.closest
          ? ev.target.closest("[data-desk-check-all], [data-desk-check-none]")
          : null;
        if (!btn) return;
        var kind =
          btn.getAttribute("data-desk-check-all") ||
          btn.getAttribute("data-desk-check-none");
        var all = !!btn.getAttribute("data-desk-check-all");
        if (kind === "sleeve") {
          lastDeskBatchSleeves = all ? ACTIVE_SLEEVE_IDS.slice() : [];
        } else if (kind === "ticker") {
          var scopeRaw = btn.getAttribute("data-desk-scope") || "";
          var scopeItems = scopeRaw
            ? scopeRaw.split(",").filter(Boolean)
            : lastDeskTickers && lastDeskTickers.length
              ? lastDeskTickers.slice()
              : [];
          var current = deskBatchTickerSelection(
            lastDeskTickers && lastDeskTickers.length
              ? lastDeskTickers
              : scopeItems
          );
          if (all) {
            var merged = current.slice();
            scopeItems.forEach(function (ticker) {
              if (merged.indexOf(ticker) < 0) merged.push(ticker);
            });
            lastDeskBatchTickers = merged;
          } else {
            lastDeskBatchTickers = current.filter(function (ticker) {
              return scopeItems.indexOf(ticker) < 0;
            });
          }
        }
        renderStrategies();
      });
    }
    if (runAllBtn) {
      runAllBtn.addEventListener("click", function () {
        syncDeskPickFromDom();
        var sleeves = deskBatchSleeveSelection();
        var tickers = deskBatchTickerSelection(
          lastDeskTickers && lastDeskTickers.length
            ? lastDeskTickers
            : [lastDeskTicker || "SBER"]
        );
        if (!sleeves.length || !tickers.length) {
          lastDeskBatch = {
            error: "Отметьте хотя бы один рукав и один тикер",
          };
          renderStrategies();
          return;
        }
        runAllBtn.disabled = true;
        runAllBtn.textContent = "Прогоняю…";
        apiPost(
          "/desk/backtests/batch",
          { sleeves: sleeves, tickers: tickers },
          { timeoutMs: FETCH_TIMEOUT_BATCH_MS }
        )
          .then(function (data) {
            lastDeskBatch = data;
            lastDeskBatchOpen = null;
            renderStrategies();
          })
          .catch(function (err) {
            lastDeskBatch = { error: err.message || "ошибка пакетного прогона" };
            lastDeskBatchOpen = null;
            renderStrategies();
          });
      });
    }
    var batchRoot = document.querySelector('[data-tour="strategies-desk-batch"]');
    if (batchRoot) {
      batchRoot.addEventListener("click", function (ev) {
        var row = ev.target && ev.target.closest
          ? ev.target.closest("tr.desk-batch-row")
          : null;
        if (!row) return;
        var key = row.getAttribute("data-batch-key");
        if (!key) return;
        lastDeskBatchOpen = lastDeskBatchOpen === key ? null : key;
        renderStrategies();
      });
      batchRoot.addEventListener("keydown", function (ev) {
        if (ev.key !== "Enter" && ev.key !== " ") return;
        var row = ev.target && ev.target.closest
          ? ev.target.closest("tr.desk-batch-row")
          : null;
        if (!row) return;
        ev.preventDefault();
        var key = row.getAttribute("data-batch-key");
        if (!key) return;
        lastDeskBatchOpen = lastDeskBatchOpen === key ? null : key;
        renderStrategies();
      });
    }
  }

  function refreshStrategies() {
    var sleeveId = strategiesSleeveFromHash();
    var listPromise = apiGet("/sleeves")
      .then(function (data) {
        lastSleeves = (data && data.sleeves) || lastSleeves;
        return data;
      })
      .catch(function () {
        return null;
      });
    var detailPromise = sleeveId
      ? apiGet("/sleeves/" + encodeURIComponent(sleeveId))
          .then(function (data) {
            lastSleeveDetail = data;
            return data;
          })
          .catch(function (err) {
            if (err && err.status === 404) {
              lastSleeveDetail = {
                sleeve: sleeveId,
                signals: [],
                positions: [],
                pnl: {},
              };
            }
            return null;
          })
      : Promise.resolve(null);
    var allocPromise = apiGet("/allocation")
      .then(function (data) {
        lastAllocation = data;
        return data;
      })
      .catch(function () {
        return null;
      });
    var planPromise = apiGet(
      "/allocation/plan?example_price=" +
        encodeURIComponent(String(planExamplePrice || 250))
    )
      .then(function (data) {
        lastAllocPlan = data;
        return data;
      })
      .catch(function () {
        return null;
      });
    var candlesPromise = apiGet("/desk/candles?tf=1d")
      .then(function (data) {
        applyDeskCandleUniverse(data);
        return data;
      })
      .catch(function () {
        return null;
      });
    return Promise.all([
      listPromise,
      detailPromise,
      allocPromise,
      planPromise,
      candlesPromise,
    ]).then(function () {
      sleeveDetailLoading = false;
      if (currentRoute === "strategies") renderStrategies();
    });
  }

  function portfolioTabsHtml() {
    var tabs = [
      { id: "capital", label: "Капитал" },
      { id: "positions", label: "Позиции" },
      { id: "vault", label: "Сейф" },
      { id: "allocation", label: "Аллокация" },
      { id: "drift", label: "Расхождение" },
    ];
    return (
      '<div class="tabs" role="tablist" aria-label="Разделы портфеля" data-tour="portfolio-tabs">' +
      tabs
        .map(function (tab) {
          return (
            '<button type="button" role="tab" id="portfolio-tab-' +
            tab.id +
            '" aria-controls="portfolio-panel" aria-selected="' +
            (portfolioTab === tab.id ? "true" : "false") +
            '" data-tab="' +
            tab.id +
            '"' +
            (portfolioTab === tab.id ? ' class="active"' : "") +
            ">" +
            tab.label +
            "</button>"
          );
        })
        .join("") +
      "</div>"
    );
  }

  function renderPortfolioCapital() {
    var book = (lastStatus && lastStatus.portfolio) || null;
    if (!book) {
      return (
        '<section class="panel" data-tour="portfolio-capital">' +
        "<h3>Капитал</h3>" +
        (blockErrorHtml("portfolio") ||
          '<p class="empty">Книга ещё не загрузилась. Это не нулевой баланс — нажмите «Обновить».</p>') +
        "</section>"
      );
    }
    return (
      '<section class="panel" data-tour="portfolio-capital">' +
      "<h3>Капитал</h3>" +
      "<p>Сводка paper-книги: где лежат деньги лаборатории прямо сейчас. " +
      'Изменить депозит и лимит на бумагу — в <a class="panel-link" href="#/settings">Настройках</a>.</p>' +
      blockErrorHtml("portfolio") +
      '<div class="metrics">' +
      '<div class="metric hero" data-tour="portfolio-equity"><div class="k">стоимость счёта' +
      whatis(
        "Стоимость счёта",
        "Кэш + сейф + оценка позиций в paper-книге."
      ) +
      '</div><div class="v">' +
      money(book.equity) +
      "</div></div>" +
      '<div class="metric" data-tour="portfolio-cash"><div class="k">свободный кэш' +
      whatis(
        "Свободный кэш",
        "Деньги на торговом счёте книги, ещё не в позициях и не в сейфе."
      ) +
      '</div><div class="v">' +
      money(book.cash) +
      "</div></div>" +
      '<div class="metric" data-tour="portfolio-vault"><div class="k">сейф прибыли' +
      whatis(
        "Сейф прибыли",
        "Доля зафиксированной прибыли, которую лаборатория откладывает."
      ) +
      '</div><div class="v">' +
      money(book.vault) +
      "</div></div></div>" +
      '<p class="source-line" data-tour="portfolio-source">Источник: журнал проводок + позиции</p>' +
      '<div class="disclaimer" data-tour="portfolio-disclaimer">' +
      "Цифры из лабораторной книги (paper). Это не баланс экрана Тинькофф Инвестиций." +
      "</div></section>"
    );
  }

  function shortId(value) {
    var raw = String(value || "");
    if (!raw) return "—";
    if (raw.length <= 10) return raw;
    return raw.slice(0, 8) + "…";
  }

  function renderPortfolioPositions() {
    var book = (lastStatus && lastStatus.portfolio) || {};
    var rows = book.positions || [];
    var equity = Number(book.equity) || 0;
    var table = "";
    if (rows.length) {
      table =
        '<div class="position-grid" data-tour="portfolio-positions-table">' +
        rows
          .map(function (row) {
            var qty = Number(row.qty) || 0;
            var value = Number(row.market_value);
            var share =
              equity > 0 && isFinite(value)
                ? ((value / equity) * 100).toFixed(1).replace(".", ",") + "%"
                : "—";
            var sleeve = SLEEVE_NAMES[row.sleeve] || row.sleeve || "—";
            var pnl = Number(row.unrealized_pnl || 0);
            return (
              '<article class="position-card">' +
              '<div class="position-card__head"><div><span class="section-kicker">' +
              escapeHtml(sleeve) +
              "</span><h4>" +
              escapeHtml(row.ticker || shortId(row.instrument_id)) +
              "</h4></div><span class=\"mark-state is-" +
              escapeHtml(row.mark_quality || "missing") +
              '">' +
              escapeHtml(MARK_QUALITY_RU[row.mark_quality] || row.mark_quality || "нет цены") +
              "</span></div>" +
              '<div class="position-card__value">' +
              money(row.market_value) +
              "</div>" +
              '<div class="position-card__pnl ' +
              (pnl > 0 ? "is-positive" : pnl < 0 ? "is-negative" : "") +
              '">Открытый результат ' +
              money(row.unrealized_pnl) +
              "</div>" +
              '<dl><div><dt>Количество</dt><dd>' +
              escapeHtml(String(qty)) +
              "</dd></div><div><dt>Себестоимость</dt><dd>" +
              money(row.cost_basis) +
              "</dd></div><div><dt>Рыночная цена</dt><dd>" +
              money(row.mark) +
              "</dd></div><div><dt>Доля</dt><dd>" +
              escapeHtml(share) +
              "</dd></div></dl>" +
              '<p class="position-card__source">' +
              escapeHtml(row.mark_source || "источник не указан") +
              " · " +
              escapeHtml(formatSignalTime(row.mark_as_of)) +
              "</p></article>"
            );
          })
          .join("") +
        "</div>";
    } else {
      table =
        '<p class="empty" data-tour="portfolio-positions-empty">' +
        "Позиций нет — стратегия ещё не входила в рынок или книга только с депозитом. " +
        '<a class="panel-link" href="#/strategies">Откройте Стратегии → сигналы</a>, чтобы понять, были ли решения.' +
        "</p>";
    }
    return (
      '<section class="panel" data-tour="portfolio-positions">' +
      "<h3>Позиции</h3>" +
      "<p>Себестоимость → рыночная оценка → результат с источником и свежестью каждой цены.</p>" +
      table +
      "</section>"
    );
  }

  function pctLabel(value) {
    var n = Number(value);
    if (!isFinite(n)) return "—";
    return (Math.round(n * 1000) / 10).toLocaleString("ru-RU") + "%";
  }

  function renderPortfolioAllocation() {
    var alloc = lastAllocation || {
      sleeve_share: 0.4,
      equity: ((lastStatus && lastStatus.portfolio) || {}).equity,
      sleeves: [],
    };
    var rows = alloc.sleeves || [];
    var table = "";
    if (rows.length) {
      table = wrapTableScroll(
        '<table class="data-table" data-tour="portfolio-alloc-table">' +
          "<thead><tr><th>рукав</th><th>вес</th><th>капитал рукава</th></tr></thead><tbody>" +
          rows
            .map(function (row) {
              var name = SLEEVE_NAMES[row.sleeve] || row.sleeve || "—";
              return (
                "<tr>" +
                "<td>" +
                escapeHtml(name) +
                "</td><td>" +
                escapeHtml(pctLabel(row.weight)) +
                "</td><td>" +
                money(row.capital) +
                "</td></tr>"
              );
            })
            .join("") +
          "</tbody></table>"
      );
    } else {
      table =
        '<p class="empty" data-tour="portfolio-alloc-empty">Аллокация ещё не пришла с сервера. Обновите статус или откройте вкладку снова.</p>';
    }
    return (
      '<section class="panel" data-tour="portfolio-alloc-panel">' +
      "<h3>Аллокация</h3>" +
      "<p data-tour=\"portfolio-alloc-intro\">" +
      "Как капитал делится между рукавами. Торговый пул = стоимость счёта × потолок (сейчас 40%). " +
      "Каждый рукав получает свою долю от этого пула: при equal-weight 25% × 800 000 = 200 000 ₽." +
      "</p>" +
      '<div class="metrics">' +
      '<div class="metric" data-tour="portfolio-alloc-equity"><div class="k">стоимость счёта</div><div class="v">' +
      money(alloc.equity) +
      "</div></div>" +
      '<div class="metric" data-tour="portfolio-alloc-share"><div class="k">потолок рукава' +
      whatis(
        "Потолок рукава",
        "Доля стоимости счёта, в пределах которой рукава делят торговый капитал. Сейчас 40%."
      ) +
      '</div><div class="v">' +
      escapeHtml(pctLabel(alloc.sleeve_share)) +
      "</div></div></div>" +
      table +
      '<details class="fold" data-tour="portfolio-alloc-how">' +
      "<summary>Как считается</summary>" +
      "<p>Два рукава → вес 50/50. Капитал рукава = стоимость счёта × 0,40 × вес. Это лимит аллокатора, не факт позиций.</p>" +
      "</details></section>"
    );
  }

  function driftStateHtml() {
    if (sandboxCashKnown === null || sandboxCashKnown === undefined || sandboxCashKnown === "") {
      return (
        '<p class="empty" data-tour="portfolio-drift-empty">' +
        "Кэш sandbox неизвестен — сверка недоступна. Введите сумму из sandbox и нажмите «Сверить». " +
        "Пока кэш песочницы не задан, кабинет не показывает «сходятся» и не рисует нулевое расхождение." +
        "</p>"
      );
    }
    if (!lastDrift) {
      return (
        '<p class="empty" data-tour="portfolio-drift-pending">Ждём ответ сверки…</p>'
      );
    }
    var alert = !!lastDrift.alert;
    var cls = alert ? "bad" : "ok";
    var label = alert ? "расхождение выше порога" : "в пределах порога";
    return (
      '<div class="metrics" data-tour="portfolio-drift-result">' +
      '<div class="metric"><div class="k">кэш книги</div><div class="v">' +
      money(lastDrift.ledger_cash) +
      "</div></div>" +
      '<div class="metric"><div class="k">кэш sandbox</div><div class="v">' +
      money(lastDrift.sandbox_cash) +
      "</div></div>" +
      '<div class="metric" data-tour="portfolio-drift-delta"><div class="k">расхождение</div><div class="v">' +
      money(lastDrift.drift) +
      "</div></div>" +
      '<div class="metric"><div class="k">состояние</div><div class="v">' +
      '<span class="status-pill inline"><span class="dot ' +
      cls +
      '"></span>' +
      escapeHtml(label) +
      "</span></div></div></div>" +
      '<p class="source-line">Порог алерта: ' +
      money(lastDrift.threshold) +
      ". Расхождение = кэш книги − кэш sandbox.</p>"
    );
  }

  function renderPortfolioDrift() {
    var book = (lastStatus && lastStatus.portfolio) || {};
    var known =
      sandboxCashKnown !== null &&
      sandboxCashKnown !== undefined &&
      sandboxCashKnown !== "";
    return (
      '<section class="panel" data-tour="portfolio-drift-panel">' +
      "<h3>Расхождение</h3>" +
      "<p data-tour=\"portfolio-drift-intro\">" +
      "Сверка кэша paper-книги с кэшем sandbox. Без известного sandbox кабинет не притворяется, что всё сходится." +
      "</p>" +
      '<div class="metrics">' +
      '<div class="metric" data-tour="portfolio-drift-ledger"><div class="k">кэш книги сейчас</div><div class="v">' +
      money(book.cash) +
      "</div></div></div>" +
      '<label class="field" data-tour="portfolio-drift-input">' +
      "<span>кэш sandbox (₽)</span>" +
      '<input type="text" id="drift-sandbox-cash" inputmode="decimal" placeholder="например 1000000" value="' +
      (known ? escapeHtml(String(sandboxCashKnown)) : "") +
      '">' +
      "</label>" +
      '<div class="panel-actions">' +
      '<button type="button" class="primary" id="btn-drift-check">Сверить</button>' +
      '<button type="button" class="ghost" id="btn-drift-clear">Сбросить sandbox</button>' +
      "</div>" +
      driftStateHtml() +
      '<details class="fold">' +
      "<summary>Как считается</summary>" +
      "<p>Сверка принимает кэш песочницы явно. Если его нет — пустое состояние, не «расхождение 0». " +
      "Алерт, когда |книга − песочница| больше порога (по умолчанию 1 ₽).</p>" +
      "</details></section>"
    );
  }

  function renderPortfolioVault() {
    var vault =
      lastVault || (lastStatus && lastStatus.vault) || {
        deposit: 0,
        accumulated: 0,
        phase: "50",
        remaining: 0,
      };
    var deposit = Number(vault.deposit) || 0;
    var accumulated = Number(vault.accumulated) || 0;
    var pct =
      deposit > 0 ? Math.min(100, Math.round((accumulated / deposit) * 100)) : 0;
    var phase = String(vault.phase || "50");
    var phaseLabel =
      phase === "20"
        ? "сейчас откладываем 20% зафиксированной прибыли"
        : "сейчас откладываем 50% зафиксированной прибыли";
    return (
      '<section class="panel" data-tour="portfolio-vault-panel">' +
      "<h3>Сейф прибыли</h3>" +
      "<p data-tour=\"portfolio-vault-rule\">" +
      "Пока накоплено меньше депозита, в сейф уходит половина зафиксированной прибыли. " +
      "После перекрытия депозита — пятая часть. Сейф не трогает нереализованную переоценку." +
      "</p>" +
      '<div class="metrics">' +
      '<div class="metric" data-tour="portfolio-vault-deposit"><div class="k">депозит' +
      whatis(
        "Депозит",
        "Сумма внешних пополнений paper-книги. Сейф стремится накопить столько же из зафиксированной прибыли. Это не стоимость счёта и не торговый потолок."
      ) +
      '</div><div class="v">' +
      money(vault.deposit) +
      "</div></div>" +
      '<div class="metric" data-tour="portfolio-vault-acc"><div class="k">накоплено' +
      whatis("Накоплено", "Сколько уже отложено в сейф из зафиксированной прибыли.") +
      '</div><div class="v">' +
      money(vault.accumulated) +
      "</div></div>" +
      '<div class="metric" data-tour="portfolio-vault-phase"><div class="k">фаза</div><div class="v">' +
      escapeHtml(phase) +
      "%</div></div>" +
      '<div class="metric"><div class="k">до перекрытия</div><div class="v">' +
      money(vault.remaining) +
      "</div></div></div>" +
      '<p class="source-line">' +
      escapeHtml(phaseLabel) +
      ". Прогресс до перекрытия депозита: " +
      pct +
      "%.</p>" +
      '<div class="progress" data-tour="portfolio-vault-progress" aria-hidden="true"><span style="width:' +
      pct +
      '%"></span></div>' +
      '<details class="fold" data-tour="portfolio-vault-how">' +
      "<summary>Как считается</summary>" +
      "<p>Пока накоплено &lt; депозита: в сейф идёт 50% от каждой зафиксированной прибыли. " +
      "Когда накоплено ≥ депозита, фаза меняется на 20%. Нереализованная переоценка (рост позиции без продажи) в сейф не входит.</p>" +
      "</details></section>"
    );
  }

  function parseSandboxCash(raw) {
    var text = String(raw || "")
      .trim()
      .replace(/\s/g, "")
      .replace(",", ".");
    if (!text) return null;
    var n = Number(text);
    if (!isFinite(n)) return null;
    return n;
  }

  function refreshDrift() {
    if (sandboxCashKnown === null || sandboxCashKnown === undefined || sandboxCashKnown === "") {
      lastDrift = null;
      return Promise.resolve(null);
    }
    var q =
      "/admin/drift?sandbox_cash=" + encodeURIComponent(String(sandboxCashKnown));
    return apiGet(q)
      .then(function (data) {
        lastDrift = data;
        if (currentRoute === "portfolio" && portfolioTab === "drift") {
          renderPortfolio();
        }
        return data;
      })
      .catch(function () {
        lastDrift = null;
        if (currentRoute === "portfolio" && portfolioTab === "drift") {
          renderPortfolio();
        }
        return null;
      });
  }

  function refreshPortfolioBook() {
    routeLoading = true;
    if (currentRoute === "portfolio") {
      byId("page-body").innerHTML = portfolioTabsHtml() + skeletonHtml(3);
    }
    return Promise.all([
      apiGet("/portfolio")
        .then(function (data) {
          clearLoadError("portfolio");
          return data;
        })
        .catch(function (err) {
          setLoadError("portfolio", err);
          return (lastStatus && lastStatus.portfolio) || null;
        }),
      apiGet("/vault")
        .then(function (data) {
          clearLoadError("vault");
          return data;
        })
        .catch(function (err) {
          setLoadError("vault", err);
          return lastVault || (lastStatus && lastStatus.vault) || null;
        }),
      apiGet("/allocation")
        .then(function (data) {
          clearLoadError("allocation");
          return data;
        })
        .catch(function (err) {
          setLoadError("allocation", err);
          return lastAllocation;
        }),
      apiGet("/allocation/plan")
        .then(function (data) {
          return data;
        })
        .catch(function () {
          return lastAllocPlan;
        }),
    ]).then(function (parts) {
      if (parts[0]) {
        lastStatus = Object.assign({}, lastStatus || {}, { portfolio: parts[0] });
      }
      if (parts[1]) {
        lastVault = parts[1];
        lastStatus = Object.assign({}, lastStatus || {}, { vault: parts[1] });
      }
      if (parts[2]) {
        lastAllocation = parts[2];
      }
      if (parts[3]) {
        lastAllocPlan = parts[3];
      }
      routeLoading = false;
      var driftPromise = refreshDrift();
      return driftPromise.then(function () {
        if (currentRoute === "portfolio") renderPortfolio();
        return parts;
      });
    });
  }

  function bindDriftActions() {
    var checkBtn = byId("btn-drift-check");
    var clearBtn = byId("btn-drift-clear");
    if (checkBtn) {
      checkBtn.addEventListener("click", function () {
        var input = byId("drift-sandbox-cash");
        var parsed = parseSandboxCash(input && input.value);
        if (parsed === null) {
          sandboxCashKnown = null;
          lastDrift = null;
          renderPortfolio();
          return;
        }
        sandboxCashKnown = parsed;
        refreshDrift();
      });
    }
    if (clearBtn) {
      clearBtn.addEventListener("click", function () {
        sandboxCashKnown = null;
        lastDrift = null;
        renderPortfolio();
      });
    }
  }

  function renderPortfolio() {
    var body = byId("page-body");
    if (routeLoading && currentRoute === "portfolio") {
      body.innerHTML =
        portfolioTabsHtml() +
        '<div id="portfolio-panel" role="tabpanel" aria-labelledby="portfolio-tab-' +
        portfolioTab +
        '">' +
        skeletonHtml(3) +
        "</div>";
      return;
    }
    var content = "";
    if (portfolioTab === "capital") content = renderPortfolioCapital();
    else if (portfolioTab === "positions") content = renderPortfolioPositions();
    else if (portfolioTab === "vault") content = renderPortfolioVault();
    else if (portfolioTab === "allocation") content = renderPortfolioAllocation();
    else content = renderPortfolioDrift();

    body.innerHTML =
      portfolioTabsHtml() +
      '<div id="portfolio-panel" role="tabpanel" aria-labelledby="portfolio-tab-' +
      portfolioTab +
      '">' +
      content +
      "</div>";
    body.querySelectorAll(".tabs button").forEach(function (btn) {
      btn.addEventListener("click", function () {
        portfolioTab = btn.getAttribute("data-tab") || "capital";
        setRouteTab("portfolio", portfolioTab);
      });
    });
    if (portfolioTab === "drift") bindDriftActions();
  }

  var workData = null;
  var workRange = "day";
  var workSort = "risk";
  var workPollTimer = null;
  var workClockTimer = null;
  var workPrevNums = {};
  var workSeenTrades = null;
  var workChartPoints = {};
  var workSetupOpen = false;
  var workPayinOpen = false;
  var workDesk = (function () {
    try {
      return window.localStorage.getItem("work.desk") || "main";
    } catch (e) {
      return "main";
    }
  })();
  var workDesks = null;
  var workView = "all";
  var workCreateOpen = false;
  var WORK_LINE_COLORS = ["#172019", "#1f8a55", "#2f6fb0", "#b7791f", "#8e44ad", "#c23f3f", "#0e8a8a"];
  var workPayinDraft = "";
  var workParamsDraft = null;
  var workLastOkAt = null;
  var workLastFailAt = null;
  var workDrawn = {};
  var WORK_POLL_MS = 30000;
  var WORK_SESSION = { open: 10 * 60, close: 18 * 60 + 50 };
  var WORK_DECISION_RU = {
    sent: "отправлено",
    disabled: "заявки выключены",
    no_account: "счёт не выбран",
    no_room_name: "потолок на бумагу",
    no_room_sleeve: "рукав заполнен",
    no_price: "нет цены",
    nothing_to_sell: "нечего продавать",
    no_instrument: "бумага не найдена",
    broker_error: "брокер не принял заявку",
    below_lot: "денег меньше одного лота",
    too_small: "слишком мелко — меньше половины доли",
    stale_data: "нет свечей — продажа не проверена",
  };
  var WORK_VERDICT = {
    hold: { label: "Держим", tone: "ok" },
    watch: { label: "Под наблюдением", tone: "warn" },
    exit: { label: "Выход на закрытии", tone: "bad" },
  };

  function workNum(v) {
    if (v === null || v === undefined || v === "") return null;
    var n = Number(v);
    return isFinite(n) ? n : null;
  }

  function workPct(v, signed) {
    var n = workNum(v);
    if (n === null) return "—";
    var s = (Math.round(n * 10000) / 100).toLocaleString("ru-RU", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });
    return (signed && n > 0 ? "+" : "") + s + "%";
  }

  function workRub(v, signed) {
    var n = workNum(v);
    if (n === null) return "—";
    return (signed && n > 0 ? "+" : "") + rubles(n);
  }

  function workPrice(v) {
    var n = workNum(v);
    if (n === null) return "—";
    var digits = Math.abs(n) < 1 ? 4 : Math.abs(n) < 100 ? 2 : 2;
    return n.toLocaleString("ru-RU", { minimumFractionDigits: digits, maximumFractionDigits: digits }) + " ₽";
  }

  function workTone(v) {
    var n = workNum(v);
    if (n === null || n === 0) return "flat";
    return n > 0 ? "up" : "down";
  }

  function workArrow(v) {
    var n = workNum(v);
    if (n === null || n === 0) return "";
    return n > 0 ? "▲ " : "▼ ";
  }

  function workMskParts(date) {
    var d = new Date(date.getTime() + 3 * 3600 * 1000);
    return { h: d.getUTCHours(), m: d.getUTCMinutes(), s: d.getUTCSeconds(), day: d.getUTCDay() };
  }

  function workClock(date) {
    var p = workMskParts(date);
    function pad(n) { return (n < 10 ? "0" : "") + n; }
    return pad(p.h) + ":" + pad(p.m) + ":" + pad(p.s);
  }

  function workCountdown(iso) {
    var ms = Date.parse(iso || "") - Date.now();
    if (!isFinite(ms)) return "—";
    if (ms <= 0) return "сейчас";
    var s = Math.floor(ms / 1000);
    var d = Math.floor(s / 86400);
    var h = Math.floor((s % 86400) / 3600);
    var m = Math.floor((s % 3600) / 60);
    var sec = s % 60;
    function pad(n) { return (n < 10 ? "0" : "") + n; }
    return (d ? d + " д " : "") + pad(h) + ":" + pad(m) + ":" + pad(sec);
  }

  function workShortId(id) {
    var s = String(id || "");
    return s.length > 8 ? "…" + s.slice(-6) : s || "—";
  }

  function workLabel(row) {
    var ticker = String((row && row.ticker) || "").toUpperCase();
    var name = String((row && row.name) || "").trim();
    if (name && name.toUpperCase() !== ticker) return name;
    return ticker || "—";
  }

  function workSharePct(share) {
    var n = Number(share) * 100;
    if (!isFinite(n)) return "";
    return String(Math.round(n * 100) / 100).replace(".", ",");
  }

  function workPctFromRub(rub, equity) {
    var eq = Number(equity);
    if (!(eq > 0) || !isFinite(rub)) return "";
    return String(Math.round((rub / eq) * 10000) / 100).replace(".", ",");
  }

  /* ---------- мини-набор графиков (SVG-строки, цвета через CSS) ---------- */

  function chartScale(values, pad) {
    var nums = values.filter(function (v) { return v !== null && isFinite(v); });
    if (!nums.length) return null;
    var min = Math.min.apply(null, nums);
    var max = Math.max.apply(null, nums);
    var span = max - min;
    var p = span * (pad == null ? 0.08 : pad) || Math.abs(max) * 0.01 || 1;
    return { min: min - p, max: max + p };
  }

  function chartPath(pts) {
    return pts.map(function (p, i) {
      return (i ? "L" : "M") + p[0].toFixed(1) + "," + p[1].toFixed(1);
    }).join(" ");
  }

  function chartLine(id, points, opts) {
    opts = opts || {};
    if (!points || points.length < 2) {
      return '<div class="wchart-empty">' + escapeHtml(opts.empty || "Мало точек для графика.") + "</div>";
    }
    var w = 960;
    var h = opts.height || 260;
    var padL = 6;
    var padR = 86;
    var padT = 14;
    var padB = 26;
    var iw = w - padL - padR;
    var ih = h - padT - padB;
    var vals = points.map(function (p) { return p.v; });
    var base = opts.base != null ? opts.base : vals[0];
    var sc = chartScale(vals.concat([base]));
    var t0 = points[0].t;
    var t1 = points[points.length - 1].t;
    var tspan = t1 - t0 || 1;
    function x(t) { return padL + ((t - t0) / tspan) * iw; }
    function y(v) { return padT + (1 - (v - sc.min) / (sc.max - sc.min)) * ih; }
    var xy = points.map(function (p) { return [x(p.t), y(p.v)]; });
    var line = chartPath(xy);
    var by = y(base);
    var area = line + " L" + xy[xy.length - 1][0].toFixed(1) + "," + by.toFixed(1) + " L" + xy[0][0].toFixed(1) + "," + by.toFixed(1) + " Z";
    var clipUp = "wc-up-" + id;
    var clipDn = "wc-dn-" + id;
    var grid = "";
    for (var g = 0; g <= 3; g++) {
      var gv = sc.min + ((sc.max - sc.min) * g) / 3;
      var gy = y(gv);
      grid +=
        '<line class="wchart-grid" x1="' + padL + '" x2="' + (w - padR) + '" y1="' + gy.toFixed(1) + '" y2="' + gy.toFixed(1) + '"></line>' +
        '<text class="wchart-ylab" x="' + (w - padR + 8) + '" y="' + (gy + 4).toFixed(1) + '">' + escapeHtml(opts.fmtY ? opts.fmtY(gv) : formatRubGrouped(gv)) + "</text>";
    }
    var xl = "";
    var ticks = Math.min(5, points.length - 1);
    for (var k = 0; k <= ticks; k++) {
      var tt = t0 + (tspan * k) / ticks;
      var anchor = k === 0 ? "start" : k === ticks ? "end" : "middle";
      xl += '<text class="wchart-xlab" text-anchor="' + anchor + '" x="' + x(tt).toFixed(1) + '" y="' + (h - 6) + '">' + escapeHtml(opts.fmtX ? opts.fmtX(tt, false, tspan) : "") + "</text>";
    }
    var marks = (opts.marks || []).map(function (m) {
      if (m.t < t0 || m.t > t1) return "";
      var mx = x(m.t);
      var my = y(m.v);
      var cls = m.side === "payin" ? "wmark wmark--payin" : m.side === "sell" ? "wmark wmark--sell" : m.layer > 1 ? "wmark wmark--add" : "wmark wmark--buy";
      var shape = m.side === "payin"
        ? '<rect x="' + (mx - 5).toFixed(1) + '" y="' + (my - 5).toFixed(1) + '" width="10" height="10" rx="2"></rect>'
        : m.side === "sell"
        ? '<path d="M' + (mx - 6).toFixed(1) + "," + (my - 5).toFixed(1) + " L" + (mx + 6).toFixed(1) + "," + (my - 5).toFixed(1) + " L" + mx.toFixed(1) + "," + (my + 6).toFixed(1) + ' Z"></path>'
        : m.layer > 1
          ? '<path d="M' + mx.toFixed(1) + "," + (my - 6).toFixed(1) + " L" + (mx + 6).toFixed(1) + "," + my.toFixed(1) + " L" + mx.toFixed(1) + "," + (my + 6).toFixed(1) + " L" + (mx - 6).toFixed(1) + "," + my.toFixed(1) + ' Z"></path>'
          : '<path d="M' + (mx - 6).toFixed(1) + "," + (my + 5).toFixed(1) + " L" + (mx + 6).toFixed(1) + "," + (my + 5).toFixed(1) + " L" + mx.toFixed(1) + "," + (my - 6).toFixed(1) + ' Z"></path>';
      return '<g class="' + cls + '"><title>' + escapeHtml(m.title || "") + "</title>" + shape + "</g>";
    }).join("");
    var last = xy[xy.length - 1];
    var firstDraw = !workDrawn[id];
    workDrawn[id] = true;
    workChartPoints[id] = {
      points: points,
      xy: xy,
      w: w,
      h: h,
      padT: padT,
      padB: padB,
      base: base,
      fmtX: opts.fmtX,
      fmtY: opts.fmtY,
    };
    return (
      '<div class="wchart" data-wchart="' + escapeHtml(id) + '">' +
      '<svg class="wchart-svg' + (firstDraw ? " is-draw" : "") + '" viewBox="0 0 ' + w + " " + h + '" preserveAspectRatio="none" role="img" aria-label="' + escapeHtml(opts.label || "График") + '">' +
      "<defs>" +
      '<clipPath id="' + clipUp + '"><rect x="0" y="0" width="' + w + '" height="' + by.toFixed(1) + '"></rect></clipPath>' +
      '<clipPath id="' + clipDn + '"><rect x="0" y="' + by.toFixed(1) + '" width="' + w + '" height="' + (h - by).toFixed(1) + '"></rect></clipPath>' +
      "</defs>" +
      grid +
      '<path class="wchart-area wchart-area--up" clip-path="url(#' + clipUp + ')" d="' + area + '"></path>' +
      '<path class="wchart-area wchart-area--down" clip-path="url(#' + clipDn + ')" d="' + area + '"></path>' +
      '<line class="wchart-base" x1="' + padL + '" x2="' + (w - padR) + '" y1="' + by.toFixed(1) + '" y2="' + by.toFixed(1) + '"></line>' +
      '<path class="wchart-line" pathLength="1" d="' + line + '"></path>' +
      marks +
      (opts.pulse ? '<circle class="wpulse" cx="' + last[0].toFixed(1) + '" cy="' + last[1].toFixed(1) + '" r="5"></circle>' : "") +
      '<circle class="wchart-dot" cx="' + last[0].toFixed(1) + '" cy="' + last[1].toFixed(1) + '" r="4"></circle>' +
      xl +
      '<line class="wchart-cross" x1="0" x2="0" y1="' + padT + '" y2="' + (h - padB) + '" hidden></line>' +
      '<circle class="wchart-cross-dot" r="5" cx="0" cy="0" hidden></circle>' +
      "</svg>" +
      '<div class="wchart-tip" hidden></div>' +
      "</div>"
    );
  }

  function bindChartCrosshair(root) {
    (root || document).querySelectorAll("[data-wchart]").forEach(function (box) {
      var id = box.getAttribute("data-wchart");
      var data = workChartPoints[id];
      var svg = box.querySelector("svg");
      if (!data || !svg) return;
      var vline = svg.querySelector(".wchart-cross");
      var dot = svg.querySelector(".wchart-cross-dot");
      var tip = box.querySelector(".wchart-tip");
      function hide() {
        vline.setAttribute("hidden", "");
        dot.setAttribute("hidden", "");
        tip.hidden = true;
      }
      box.onpointerleave = hide;
      box.onpointermove = function (ev) {
        var rect = svg.getBoundingClientRect();
        if (!rect.width) return;
        var vx = ((ev.clientX - rect.left) / rect.width) * data.w;
        var best = 0;
        var bestD = Infinity;
        for (var i = 0; i < data.xy.length; i++) {
          var d = Math.abs(data.xy[i][0] - vx);
          if (d < bestD) { bestD = d; best = i; }
        }
        var p = data.xy[best];
        var pt = data.points[best];
        vline.setAttribute("x1", p[0].toFixed(1));
        vline.setAttribute("x2", p[0].toFixed(1));
        vline.removeAttribute("hidden");
        dot.setAttribute("cx", p[0].toFixed(1));
        dot.setAttribute("cy", p[1].toFixed(1));
        dot.removeAttribute("hidden");
        var delta = data.base ? pt.v / data.base - 1 : null;
        tip.innerHTML =
          "<span>" + escapeHtml(data.fmtX ? data.fmtX(pt.t, true) : "") + "</span>" +
          "<strong>" + escapeHtml(data.fmtY ? data.fmtY(pt.v) : rubles(pt.v)) + "</strong>" +
          (delta !== null ? '<em class="is-' + workTone(delta) + '">' + escapeHtml(workPct(delta, true)) + " к началу</em>" : "");
        tip.hidden = false;
        var left = (p[0] / data.w) * rect.width;
        tip.style.left = Math.min(Math.max(left, 70), rect.width - 70) + "px";
      };
    });
  }

  function chartSpark(spark, opts) {
    opts = opts || {};
    var closes = (spark && spark.closes) || [];
    var days = (spark && spark.days) || [];
    if (closes.length < 2) return '<div class="wspark-empty">Нет дневок для графика</div>';
    var nowV = workNum(spark.now);
    var w = 320;
    var h = 84;
    var padT = 6;
    var padB = 6;
    var n = closes.length + (nowV !== null ? 1 : 0);
    var vals = closes.slice();
    (spark.sma || []).forEach(function (v) { if (v !== null) vals.push(v); });
    (spark.avg_steps || []).forEach(function (s) { vals.push(s.avg); });
    if (nowV !== null) vals.push(nowV);
    var sc = chartScale(vals, 0.06);
    function x(i) { return (i / (n - 1)) * w; }
    function y(v) { return padT + (1 - (v - sc.min) / (sc.max - sc.min)) * (h - padT - padB); }
    var dayIdx = {};
    days.forEach(function (d, i) { dayIdx[d] = i; });
    function idxFor(day) {
      if (dayIdx[day] != null) return dayIdx[day];
      for (var i = 0; i < days.length; i++) if (days[i] >= day) return i;
      return days.length - 1;
    }
    var pts = closes.map(function (c, i) { return [x(i), y(c)]; });
    var line = chartPath(pts);
    var avgNow = workNum(opts.avg);
    var lastClose = closes[closes.length - 1];
    var up = avgNow === null || (nowV !== null ? nowV : lastClose) >= avgNow;
    var area = line + " L" + pts[pts.length - 1][0].toFixed(1) + "," + h + " L0," + h + " Z";
    var sma = "";
    var smaPts = [];
    (spark.sma || []).forEach(function (v, i) { if (v !== null) smaPts.push([x(i), y(v)]); });
    if (smaPts.length > 1) sma = '<path class="wspark-sma" d="' + chartPath(smaPts) + '"></path>';
    var steps = "";
    var st = spark.avg_steps || [];
    if (st.length) {
      var seg = [];
      st.forEach(function (s, k) {
        var i0 = idxFor(s.day);
        var i1 = k + 1 < st.length ? idxFor(st[k + 1].day) : n - 1;
        seg.push("M" + x(i0).toFixed(1) + "," + y(s.avg).toFixed(1) + " L" + x(i1).toFixed(1) + "," + y(s.avg).toFixed(1));
      });
      steps = '<path class="wspark-avg" d="' + seg.join(" ") + '"></path>';
    } else if (avgNow !== null) {
      steps = '<path class="wspark-avg" d="M0,' + y(avgNow).toFixed(1) + " L" + w + "," + y(avgNow).toFixed(1) + '"></path>';
    }
    var marks = (spark.marks || []).map(function (m) {
      var i = idxFor(m.day);
      var mx = x(i);
      var my = y(m.price || closes[i]);
      var cls = m.side === "sell" ? "wmark--sell" : m.layer > 1 ? "wmark--add" : "wmark--buy";
      return '<circle class="wspark-mark ' + cls + '" cx="' + mx.toFixed(1) + '" cy="' + my.toFixed(1) + '" r="3.5"><title>' +
        escapeHtml((m.side === "sell" ? "Продажа" : m.layer > 1 ? "Докуп " + m.layer : "Покупка") + " · " + ruDay(m.day) + " · " + workPrice(m.price)) + "</title></circle>";
    }).join("");
    var nowSeg = "";
    if (nowV !== null) {
      var lx = pts[pts.length - 1];
      var nx = x(n - 1);
      var ny = y(nowV);
      nowSeg =
        '<path class="wspark-now-seg" d="M' + lx[0].toFixed(1) + "," + lx[1].toFixed(1) + " L" + nx.toFixed(1) + "," + ny.toFixed(1) + '"></path>' +
        '<circle class="wpulse" cx="' + nx.toFixed(1) + '" cy="' + ny.toFixed(1) + '" r="4"></circle>' +
        '<circle class="wspark-now" cx="' + nx.toFixed(1) + '" cy="' + ny.toFixed(1) + '" r="3.5"></circle>';
    }
    return (
      '<svg class="wspark is-' + (up ? "up" : "down") + '" viewBox="0 0 ' + w + " " + h + '" preserveAspectRatio="none" role="img" aria-label="Цена с даты входа">' +
      '<path class="wspark-area" d="' + area + '"></path>' +
      sma + steps +
      '<path class="wspark-line" pathLength="1" d="' + line + '"></path>' +
      marks + nowSeg +
      "</svg>"
    );
  }

  function chartMiniSpark(values) {
    var vals = (values || []).filter(function (v) { return v !== null && isFinite(v); });
    if (vals.length < 2) return "";
    var sc = chartScale(vals, 0.1);
    var w = 120;
    var h = 28;
    var pts = vals.map(function (v, i) {
      return [(i / (vals.length - 1)) * w, 2 + (1 - (v - sc.min) / (sc.max - sc.min)) * (h - 4)];
    });
    var tone = vals[vals.length - 1] >= vals[0] ? "up" : "down";
    return '<svg class="wmini is-' + tone + '" viewBox="0 0 ' + w + " " + h + '" preserveAspectRatio="none" aria-hidden="true"><path d="' + chartPath(pts) + '"></path></svg>';
  }

  function chartBullet(opts) {
    var min = opts.min;
    var max = opts.max;
    var span = max - min || 1;
    function pos(v) { return Math.max(0, Math.min(100, ((v - min) / span) * 100)); }
    var value = workNum(opts.value);
    var zones = (opts.zones || []).map(function (z) {
      var a = pos(z.from);
      var b = pos(z.to);
      return '<span class="wbullet-zone wbullet-zone--' + z.tone + '" style="left:' + a.toFixed(1) + "%;width:" + (b - a).toFixed(1) + '%"></span>';
    }).join("");
    var floor = opts.floor != null
      ? '<span class="wbullet-floor" style="left:' + pos(opts.floor).toFixed(1) + '%" title="' + escapeHtml(opts.floorLabel || "") + '"></span>'
      : "";
    var runner = value === null
      ? ""
      : '<span class="wbullet-runner wbullet-runner--' + (opts.tone || "ok") + '" style="left:' + pos(value).toFixed(1) + '%"></span>';
    return (
      '<div class="wbullet">' +
      '<div class="wbullet-head"><span>' + escapeHtml(opts.label) + "</span><strong class=\"is-" + escapeHtml(opts.tone || "ok") + '">' + escapeHtml(opts.valueText) + "</strong></div>" +
      '<div class="wbullet-track">' + zones + floor + runner + "</div>" +
      (opts.note ? '<div class="wbullet-note">' + escapeHtml(opts.note) + "</div>" : "") +
      "</div>"
    );
  }

  function chartBar(fill, opts) {
    var n = Math.max(0, Math.min(1.2, Number(fill) || 0));
    var tone = n > 1 ? "bad" : n > 0.9 ? "warn" : "ok";
    return (
      '<div class="wbar">' +
      '<div class="wbullet-head"><span>' + escapeHtml(opts.label) + "</span><strong>" + escapeHtml(opts.valueText) + "</strong></div>" +
      '<div class="wbar-track"><span class="wbar-fill wbar-fill--' + tone + '" style="width:' + (Math.min(1, n) * 100).toFixed(1) + '%"></span>' +
      (n > 1 ? '<span class="wbar-over" style="width:' + ((n - 1) * 100).toFixed(1) + '%"></span>' : "") +
      "</div></div>"
    );
  }

  function chartDonut(segments, center, sub) {
    var total = segments.reduce(function (acc, s) { return acc + Math.max(0, s.value); }, 0);
    var r = 54;
    var c = 2 * Math.PI * r;
    var off = 0;
    var arcs = total > 0
      ? segments.map(function (s) {
          var len = (Math.max(0, s.value) / total) * c;
          var gap = len > 4 ? 2 : 0;
          var html = '<circle class="wdonut-seg wdonut-seg--' + s.tone + '" r="' + r + '" cx="70" cy="70" stroke-dasharray="' + Math.max(0, len - gap).toFixed(2) + " " + (c - Math.max(0, len - gap)).toFixed(2) + '" stroke-dashoffset="' + (-off).toFixed(2) + '"><title>' + escapeHtml(s.title) + "</title></circle>";
          off += len;
          return html;
        }).join("")
      : '<circle class="wdonut-seg wdonut-seg--cash" r="' + r + '" cx="70" cy="70"></circle>';
    return (
      '<svg class="wdonut" viewBox="0 0 140 140" role="img" aria-label="Распределение счёта">' +
      '<g transform="rotate(-90 70 70)">' + arcs + "</g>" +
      '<text x="70" y="68" text-anchor="middle" class="wdonut-big">' + escapeHtml(center) + "</text>" +
      '<text x="70" y="86" text-anchor="middle" class="wdonut-sub">' + escapeHtml(sub) + "</text>" +
      "</svg>"
    );
  }

  /* ---------- секции экрана ---------- */

  function workStepMap(data) {
    var ok = {};
    (data.steps || []).forEach(function (s) { ok[s.id] = !!s.ok; });
    return ok;
  }

  function workCurrentStep(data) {
    var steps = data.steps || [];
    for (var i = 0; i < steps.length; i++) if (!steps[i].ok) return steps[i].id;
    return null;
  }

  function workUrl(path) {
    return path + (path.indexOf("?") >= 0 ? "&" : "?") + "desk=" + encodeURIComponent(workDesk);
  }

  function workViewFromHash() {
    var raw = hashPath();
    if (raw.indexOf("work/") !== 0) return "all";
    return decodeURIComponent(raw.slice("work/".length).split("/")[0] || "") || "all";
  }

  function workSetDesk(id) {
    if (!id || id === workDesk) return;
    workDesk = id;
    try {
      window.localStorage.setItem("work.desk", id);
    } catch (e) {}
    workParamsDraft = null;
    workSetupOpen = false;
    workPayinOpen = false;
    workPayinDraft = "";
    workData = null;
  }

  function workSelectDesk(id) {
    if (!id) return;
    location.hash = "#/work/" + encodeURIComponent(id);
  }

  function workOnDesk() {
    return workView !== "all" && workView !== "new";
  }

  function workSetTitle() {
    var title = "Песочницы T-Invest";
    var intro = "Все песочницы T-Invest рядом: у каждой свой счёт брокера и одна дневная стратегия. Боевой счёт не подключён.";
    if (workView === "new") {
      title = "Новая песочница";
      intro = "Отдельный счёт в песочнице брокера с игровыми деньгами и одна стратегия — чтобы результаты не смешивались.";
    } else if (workOnDesk()) {
      var desk = workData && workData.desk;
      var meta = ((workDesks && workDesks.desks) || []).filter(function (d) { return d.id === workDesk; })[0];
      title = "Песочница · " + ((desk && desk.name) || (meta && meta.name) || "…");
      intro = "Счёт, бюджет, решение дня, позиции и сделки этой песочницы.";
    }
    byId("page-title").textContent = title;
    byId("page-intro").textContent = intro;
    document.title = "i.datagon · " + title;
  }

  var workNavSig = "";
  function workSyncNav(force) {
    if (currentRoute !== "work") return;
    var sig = JSON.stringify(((workDesks && workDesks.desks) || []).map(function (d) {
      return [d.id, d.name, d.enabled, d.ready];
    }));
    if (force || sig !== workNavSig) {
      workNavSig = sig;
      renderNav();
    }
    var raw = hashPath();
    syncNavActive(raw === "work/" ? "work" : raw);
  }

  function chartMulti(series) {
    var lines = series.filter(function (s) { return s.points.length > 1; });
    if (!lines.length) {
      return '<div class="wchart-empty">Кривые появятся, когда воркер сделает отметки по счетам (раз в минуту).</div>';
    }
    var w = 960;
    var h = 220;
    var padR = 70;
    var padT = 10;
    var padB = 24;
    var all = [0];
    var t0 = Infinity;
    var t1 = -Infinity;
    lines.forEach(function (s) {
      s.points.forEach(function (p) {
        all.push(p.v);
        t0 = Math.min(t0, p.t);
        t1 = Math.max(t1, p.t);
      });
    });
    var sc = chartScale(all, 0.1);
    var tspan = t1 - t0 || 1;
    function x(t) { return ((t - t0) / tspan) * (w - padR); }
    function y(v) { return padT + (1 - (v - sc.min) / (sc.max - sc.min)) * (h - padT - padB); }
    var grid = "";
    for (var g = 0; g <= 3; g++) {
      var gv = sc.min + ((sc.max - sc.min) * g) / 3;
      grid += '<line class="wchart-grid" x1="0" x2="' + (w - padR) + '" y1="' + y(gv).toFixed(1) + '" y2="' + y(gv).toFixed(1) + '"></line>' +
        '<text class="wchart-ylab" x="' + (w - padR + 8) + '" y="' + (y(gv) + 4).toFixed(1) + '">' + escapeHtml(workPct(gv, true)) + "</text>";
    }
    var fmt = workTimeFmt("all");
    var xl = '<text class="wchart-xlab" x="0" y="' + (h - 6) + '">' + escapeHtml(fmt(t0, false, tspan)) + "</text>" +
      '<text class="wchart-xlab" text-anchor="end" x="' + (w - padR) + '" y="' + (h - 6) + '">' + escapeHtml(fmt(t1, false, tspan)) + "</text>";
    var paths = lines.map(function (s) {
      var pts = s.points.map(function (p) { return [x(p.t), y(p.v)]; });
      var last = pts[pts.length - 1];
      return '<path class="wmulti-line' + (s.active ? " is-active" : "") + '" style="stroke:' + s.color + '" d="' + chartPath(pts) + '"></path>' +
        '<circle cx="' + last[0].toFixed(1) + '" cy="' + last[1].toFixed(1) + '" r="4" style="fill:' + s.color + '"></circle>';
    }).join("");
    return (
      '<svg class="wchart-svg wmulti" viewBox="0 0 ' + w + " " + h + '" preserveAspectRatio="none" role="img" aria-label="Результат песочниц в процентах от старта">' +
      grid +
      '<line class="wchart-base" x1="0" x2="' + (w - padR) + '" y1="' + y(0).toFixed(1) + '" y2="' + y(0).toFixed(1) + '"></line>' +
      paths + xl + "</svg>"
    );
  }

  function workCreateHtml(ov) {
    var free = (ov.strategies || []).filter(function (s) { return !s.used; });
    if (!free.length) {
      return '<div class="wcreate"><p class="muted">Все дневные стратегии уже в песочницах. Внутридневные (скальп, утро, вечер) подключим отдельно.</p><button type="button" class="ghost" id="work-create-cancel">Закрыть</button></div>';
    }
    var opts = free.map(function (s) {
      return '<label class="wstrat"><input type="radio" name="work-new-sleeve" value="' + escapeHtml(s.id) + '">' +
        "<span><strong>" + escapeHtml(s.title) + "</strong><small>" + escapeHtml(s.signal) + "</small></span></label>";
    }).join("");
    return (
      '<div class="wcreate" id="work-create">' +
      "<h4>Новая песочница</h4>" +
      "<p class=\"muted\">Откроем отдельный счёт в песочнице брокера и положим на него игровые деньги. Одна песочница — одна стратегия, чтобы результаты не смешивались. Решение — раз в день в 18:50 МСК, как у остальных.</p>" +
      '<div class="wstrat-list">' + opts + "</div>" +
      '<div class="wcreate-row">' +
      '<label>Название (необязательно)<input id="work-new-name" type="text" maxlength="60" autocomplete="off" placeholder="как у стратегии"></label>' +
      '<label>Стартовый депозит, ₽<input id="work-new-deposit" type="text" inputmode="decimal" data-rub-input autocomplete="off" value="1 000 000"></label>' +
      "</div>" +
      '<div class="wsetup-acts"><button type="button" class="primary" id="work-create-send">Открыть счёт и подключить</button><button type="button" class="ghost" id="work-create-cancel">Отмена</button></div>' +
      "</div>"
    );
  }

  function workBoardKpisHtml(desks) {
    var equity = 0;
    var pnl = 0;
    var hasPnl = false;
    var on = 0;
    desks.forEach(function (d) {
      equity += Number(d.equity) || 0;
      if (d.pnl !== null && d.pnl !== undefined && isFinite(Number(d.pnl))) {
        pnl += Number(d.pnl);
        hasPnl = true;
      }
      if (d.enabled) on += 1;
    });
    var base = equity - pnl;
    function tile(label, value, sub, tone) {
      return (
        '<div class="wkpi"><span class="wkpi-k">' + escapeHtml(label) + "</span>" +
        '<strong class="wkpi-v' + (tone ? " is-" + tone : "") + '">' + escapeHtml(value) + "</strong>" +
        (sub ? '<span class="wkpi-sub' + (tone ? " is-" + tone : "") + '">' + escapeHtml(sub) + "</span>" : "") +
        "</div>"
      );
    }
    return (
      '<section class="wkpis wkpis--board" id="work-board-kpis">' +
      tile("На всех счетах", equity ? rubles(equity) : "—", desks.length + " " + workPlural(desks.length, "песочница", "песочницы", "песочниц")) +
      tile("Результат вместе", hasPnl ? workRub(pnl, true) : "—", hasPnl && base > 0 ? workPct(pnl / base, true) + " без пополнений" : "", hasPnl ? workTone(pnl) : "") +
      tile("Заявки включены", on + " из " + desks.length, on < desks.length ? "остальные ждут настройки или выключены" : "все торгуют") +
      "</section>"
    );
  }

  function workPlural(n, one, few, many) {
    var m10 = n % 10;
    var m100 = n % 100;
    if (m10 === 1 && m100 !== 11) return one;
    if (m10 >= 2 && m10 <= 4 && (m100 < 12 || m100 > 14)) return few;
    return many;
  }

  function workNewHtml(ov) {
    if (!ov) return '<div class="wskeleton"><span></span><span></span></div>';
    return '<section class="wpanel">' + workCreateHtml(ov).replace("<h4>Новая песочница</h4>", "") + "</section>";
  }

  function workBoardHtml(ov) {
    if (!ov) return "";
    var desks = ov.desks || [];
    var series = desks.map(function (d, i) {
      return {
        color: WORK_LINE_COLORS[i % WORK_LINE_COLORS.length],
        active: true,
        points: (d.curve || []).map(function (p) { return { t: Date.parse(p.ts), v: Number(p.pct) }; })
          .filter(function (p) { return isFinite(p.t) && isFinite(p.v); }),
      };
    });
    var tabs = desks.map(function (d, i) {
      var status = d.enabled ? '<span class="wpill wpill--on"><i class="wdot"></i>заявки</span>'
        : d.ready ? '<span class="wpill">выкл</span>' : '<span class="wpill wpill--wait">настройка</span>';
      return (
        '<button type="button" class="wdesk" data-work-desk="' + escapeHtml(d.id) + '" title="Открыть песочницу">' +
        '<span class="wdesk-top"><i class="wdesk-color" style="background:' + WORK_LINE_COLORS[i % WORK_LINE_COLORS.length] + '"></i><strong>' + escapeHtml(d.name) + "</strong>" + status + "</span>" +
        (d.name !== d.strategy.title ? '<span class="wdesk-strat">' + escapeHtml(d.strategy.title) + "</span>" : '<span class="wdesk-strat">' + escapeHtml(d.id === "main" ? "основная" : "стратегия по имени") + "</span>") +
        '<span class="wdesk-nums"><span>' + escapeHtml(d.equity ? rubles(d.equity) : "—") + '</span><em class="is-' + workTone(d.pnl) + '">' + escapeHtml(workPct(d.pnl_pct, true)) + "</em></span>" +
        chartMiniSpark(series[i].points.map(function (p) { return p.v; })) +
        "</button>"
      );
    }).join("");
    var compare = "";
    if (desks.length) {
      var rows = desks.map(function (d, i) {
        return (
          "<tr>" +
          '<td><i class="wdesk-color" style="background:' + WORK_LINE_COLORS[i % WORK_LINE_COLORS.length] + '"></i><a href="#/work/' + encodeURIComponent(d.id) + '">' + escapeHtml(d.name) + "</a></td>" +
          "<td>" + escapeHtml(d.strategy.title) + "</td>" +
          '<td class="num">' + escapeHtml(d.equity ? rubles(d.equity) : "—") + "</td>" +
          '<td class="num is-' + workTone(d.pnl) + '">' + escapeHtml(workRub(d.pnl, true)) + "</td>" +
          '<td class="num is-' + workTone(d.pnl_pct) + '">' + escapeHtml(workPct(d.pnl_pct, true)) + "</td>" +
          '<td class="num is-' + (d.drawdown < -0.0001 ? "down" : "flat") + '">' + escapeHtml(workPct(d.drawdown)) + "</td>" +
          '<td class="num">' + escapeHtml(String(d.positions)) + " / " + escapeHtml(String(d.trades)) + "</td>" +
          '<td class="num">' + escapeHtml(workPct(d.sleeve_fill)) + "</td>" +
          "</tr>"
        );
      }).join("");
      compare =
        '<section class="wpanel wcompare" id="work-compare">' +
        '<div class="wpanel-head"><div><h3>Сравнение</h3><span class="wpanel-sub muted">результат в % от первой отметки счёта, без пополнений</span></div></div>' +
        chartMulti(series) +
        '<div class="table-scroll"><table class="wcompare-table"><thead><tr><th>Песочница</th><th>Стратегия</th><th class="num">Счёт</th><th class="num">Результат</th><th class="num">%</th><th class="num">Просадка</th><th class="num">Позиции / сделки</th><th class="num">Загрузка</th></tr></thead><tbody>' + rows + "</tbody></table></div>" +
        "</section>";
    }
    return (
      workBoardKpisHtml(desks) +
      '<section class="wpanel wdesks" id="work-desks">' +
      '<div class="wpanel-head"><div><h3>Песочницы</h3><span class="wpanel-sub muted">у каждой свой счёт брокера и одна стратегия · нажмите, чтобы открыть</span></div>' +
      (workCreateOpen ? "" : '<button type="button" class="primary" id="work-create-open">+ Новая песочница</button>') + "</div>" +
      (workCreateOpen ? workCreateHtml(ov) : "") +
      '<div class="wdesk-list">' + tabs + "</div>" +
      "</section>" +
      compare
    );
  }

  function workContoursHtml(data) {
    var ok = workStepMap(data);
    var enabled = !!data.enabled;
    var current = workCurrentStep(data);
    var pill = enabled
      ? '<span class="wpill wpill--on"><i class="wdot"></i>Заявки включены</span>'
      : current && current !== "enabled"
        ? '<span class="wpill wpill--wait">Ждёт шага ' + ((data.steps || []).map(function (s) { return s.id; }).indexOf(current) + 1) + "</span>"
        : '<span class="wpill wpill--off">Заявки выключены</span>';
    var dayVals = (data.curve_day || []).map(function (p) { return Number(p.equity); });
    var live = data.live || { checklist: [], ready: 0, total: 10 };
    var cells = (live.checklist || []).map(function (row) {
      return '<i class="wready-cell' + (row.ok ? " is-ok" : "") + '" title="' + escapeHtml(row.title) + '"></i>';
    }).join("");
    var list = (live.checklist || []).map(function (row) {
      return "<li class=\"" + (row.ok ? "is-ok" : "") + "\">" + escapeHtml(row.title) + "</li>";
    }).join("");
    return (
      '<div class="wcontours">' +
      '<section class="wcontour wcontour--sandbox" id="work-sandbox">' +
      '<div class="wcontour-top"><span class="wbadge wbadge--sandbox">Песочница</span><strong class="wcontour-name">' + escapeHtml((data.desk && data.desk.name) || "") + "</strong>" +
      '<span class="wcontour-acc">счёт ' + escapeHtml(workShortId(data.account_id)) + "</span>" + pill + "</div>" +
      (ok.account
        ? '<div class="wcontour-main"><div>' +
          '<div class="wbig" data-wnum="equity" data-wfmt="rub">' + escapeHtml(rubles(data.equity)) + "</div>" +
          '<div class="wsub is-' + workTone(data.pnl_total) + '">' +
          escapeHtml(workArrow(data.pnl_total) + workRub(data.pnl_total, true)) + " · " + escapeHtml(workPct(data.pnl_total_pct, true)) +
          ' <span class="muted">с запуска</span></div>' +
          "</div>" + chartMiniSpark(dayVals) + "</div>"
        : '<p class="wcontour-note">Счёт ещё не выбран — пройдите запуск ниже.</p>') +
      (ok.account ? workPayinHtml(data) : "") +
      (data.desk && data.desk.id !== "main" ? '<div class="wpayin"><button type="button" class="ghost compact danger-ghost" id="work-archive">Убрать песочницу</button></div>' : "") +
      '<div class="wcontour-foot">Следующее решение через <strong data-countdown="' + escapeHtml(data.next_run_at || "") + '">' + escapeHtml(workCountdown(data.next_run_at)) + "</strong> · 18:50 МСК по закрытому дню</div>" +
      "</section>" +
      '<section class="wcontour wcontour--live" id="work-live-contour" aria-label="Боевой счёт не подключён">' +
      '<div class="wcontour-top"><span class="wbadge wbadge--live">Боевой · не подключён</span>' +
      '<svg class="wlock" viewBox="0 0 24 24" aria-hidden="true"><rect x="5" y="11" width="14" height="10" rx="2"></rect><path d="M8 11V8a4 4 0 0 1 8 0v3"></path></svg></div>' +
      '<p class="wcontour-note">Заявки на реальные деньги отключены кодом (<code>' + escapeHtml(live.flag || "live=0") + "</code>). Включается только решением человека и правкой <code>.env</code> на сервере — не из кабинета.</p>" +
      '<div class="wready"><div class="wready-cells">' + cells + "</div><span>Готовность " + escapeHtml(String(live.ready || 0)) + " из " + escapeHtml(String(live.total || 10)) + "</span></div>" +
      '<details class="wready-list"><summary>Что должно стать зелёным</summary><ol>' + list + "</ol></details>" +
      "</section>" +
      "</div>"
    );
  }

  function workPayinHtml(data) {
    var total = Number(data.payins_total) || 0;
    var note = total > 0 ? "Пополнено после открытия: " + rubles(total) + " — в результат не входит." : "";
    if (!workPayinOpen) {
      return (
        '<div class="wpayin"><button type="button" class="ghost compact" id="work-payin-open">+ Пополнить счёт</button>' +
        (note ? '<span class="muted">' + escapeHtml(note) + "</span>" : "") + "</div>"
      );
    }
    var chips = [100000, 500000, 1000000].map(function (n) {
      return '<button type="button" class="wchip-btn" data-payin-add="' + n + '">+' + escapeHtml(formatRubGrouped(n)) + "</button>";
    }).join("");
    return (
      '<div class="wpayin wpayin--open" id="work-payin">' +
      '<label class="wpayin-field">Сколько добавить, ₽<input id="work-payin-amount" type="text" inputmode="decimal" data-rub-input autocomplete="off" placeholder="500 000" value="' + escapeHtml(workPayinDraft) + '"></label>' +
      '<div class="wpayin-chips">' + chips + "</div>" +
      '<div class="wsetup-acts"><button type="button" class="primary" id="work-payin-send">Пополнить</button><button type="button" class="ghost" id="work-payin-cancel">Отмена</button></div>' +
      '<p class="muted wpayin-note">Игровые рубли брокера. Вывести их из песочницы нельзя — чтобы уменьшить счёт, открывают новый. Пополнение не считается прибылью.</p>' +
      "</div>"
    );
  }

  function workPreviewHtml(equity, sleevePct, capPct) {
    var eq = Number(equity) > 0 ? Number(equity) : 1000000;
    var s = Number(sleevePct) / 100;
    var c = Number(capPct) / 100;
    if (!(s > 0 && s < 1 && c > 0 && c < 1)) {
      return '<div class="wpreview"><p class="muted">Введите обе доли — покажу, как разложатся деньги.</p></div>';
    }
    var names = c <= s ? Math.floor(s / c + 1e-9) : 0;
    var blocks = "";
    for (var i = 0; i < names && i < 20; i++) {
      blocks += '<span class="wpreview-name" style="width:' + (c * 100).toFixed(2) + '%"><em>' + (i + 1) + "</em></span>";
    }
    var rest = Math.max(0, s - names * c);
    if (rest > 0.0001) blocks += '<span class="wpreview-rest" style="width:' + (rest * 100).toFixed(2) + '%"></span>';
    return (
      '<div class="wpreview">' +
      '<div class="wpreview-bar">' + blocks + '<span class="wpreview-cash" style="width:' + ((1 - s) * 100).toFixed(2) + '%"><em>кэш</em></span></div>' +
      '<div class="wpreview-brace" style="width:' + (s * 100).toFixed(2) + '%"><span>рукав ' + escapeHtml(plainNumber(s * 100)) + "% = " + escapeHtml(rubles(eq * s)) + "</span></div>" +
      '<p class="wpreview-line">' +
      (names
        ? "До <strong>" + names + "</strong> " + (names === 1 ? "бумаги" : "бумаг") + " по <strong>" + escapeHtml(rubles(eq * c)) + "</strong> · свободный кэш <strong>" + escapeHtml(rubles(eq * (1 - s))) + "</strong> · от equity " + escapeHtml(rubles(eq))
        : '<span class="is-bad">На одну бумагу нельзя больше, чем на весь рукав.</span>') +
      "</p></div>"
    );
  }

  function workSetupHtml(data) {
    var steps = data.steps || [];
    var ok = workStepMap(data);
    var current = workCurrentStep(data);
    var allOk = !current;
    var sleevePct = workSharePct(data.sleeve_share || "0.40");
    var capPct = workSharePct(data.name_cap || "0.10");
    if (workParamsDraft) {
      sleevePct = workParamsDraft.sleeve;
      capPct = workParamsDraft.cap;
    }
    var eq = Number(data.equity) || 0;
    if (allOk && !workSetupOpen) {
      return (
        '<section class="wsetup wsetup--done" id="work-setup">' +
        '<div class="wsetup-line"><span class="wcheck">✓</span>' +
        "<span>Рукав <strong>" + escapeHtml(sleevePct) + "%</strong> (" + escapeHtml(rubles(data.sleeve_rub)) + ")" +
        " · на бумагу <strong>" + escapeHtml(capPct) + "%</strong> (" + escapeHtml(rubles(data.name_cap_rub)) + ")" +
        " · до " + escapeHtml(String(data.max_names || 0)) + " бумаг</span>" +
        '<span class="wsetup-acts"><button type="button" class="ghost" id="work-edit">Изменить бюджет</button>' +
        (data.enabled
          ? '<button type="button" class="ghost danger-ghost" id="work-off">Выключить заявки</button>'
          : '<button type="button" class="primary" id="work-on">Включить заявки</button>') +
        "</span></div></section>"
      );
    }
    var dots = steps.map(function (s, i) {
      var cls = s.ok ? "is-done" : s.id === current ? "is-current" : "";
      return '<li class="' + cls + '"><span class="wstep-dot">' + (s.ok ? "✓" : i + 1) + "</span><span class=\"wstep-title\">" + escapeHtml(s.title) + "</span></li>";
    }).join("");
    var focus = workSetupOpen && (allOk || current === "enabled") ? "params" : current;
    var panel = "";
    if (focus === "token") {
      panel =
        "<h4>Связь с песочницей T-Invest</h4>" +
        "<p>Токен песочницы лежит на сервере. Проверим, что API отвечает и счета видны.</p>" +
        (data.error ? '<p class="wsetup-err">' + escapeHtml(data.error) + "</p>" : "") +
        '<div class="wsetup-acts"><button type="button" class="primary" id="work-probe">Проверить связь</button></div>';
    } else if (focus === "account") {
      var accs = (data.accounts || []).map(function (row, i) {
        var id = row.broker_account_id || "";
        return '<label class="wacc"><input type="radio" name="work-acc" value="' + escapeHtml(id) + '"' + (id === data.account_id || (!data.account_id && i === 0) ? " checked" : "") + ">" +
          "<span><strong>" + escapeHtml(row.name || "Счёт песочницы") + "</strong><small>" + escapeHtml(workShortId(id)) + " · " + escapeHtml(row.status || "") + "</small></span></label>";
      }).join("");
      panel =
        "<h4>Счёт песочницы</h4>" +
        (accs
          ? '<div class="wacc-list">' + accs + '</div><div class="wsetup-acts"><button type="button" class="primary" id="work-account-save">Выбрать счёт</button><button type="button" class="ghost" id="work-open">Открыть новый с 1 000 000 ₽</button></div>'
          : '<p>Счетов пока нет. Откроем счёт песочницы и положим 1 000 000 игровых ₽.</p><div class="wsetup-acts"><button type="button" class="primary" id="work-open">Открыть счёт с 1 000 000 ₽</button></div>');
    } else if (focus === "strategy") {
      var strat = (data.desk && data.desk.strategy) || { title: "Абс. моментум-4", rules: true };
      panel = !strat.rules
        ? "<h4>" + escapeHtml(strat.title) + "</h4>" +
          "<p>" + escapeHtml(strat.signal || "") + "</p>" +
          (strat.holds ? '<p class="muted">' + escapeHtml(strat.holds) + "</p>" : "") +
          '<p class="muted">Решение — раз в день, в 18:50 МСК по закрытому бару.</p>' +
          '<div class="wsetup-acts"><button type="button" class="primary" id="work-strategy">Подключить ' + escapeHtml(strat.title) + "</button></div>"
        : "<h4>Абс. моментум-4</h4>" +
        '<ul class="wrules">' +
        '<li><i class="wrule wrule--in">▲</i><span><strong>Вход</strong> — цена выше средней за 30 дней, рост за 15 дней ≥ 0, не перегрета (цена/SMA ≤ 1,10), рынок широкий (≥ 42% бумаг выше SMA).</span></li>' +
        '<li><i class="wrule wrule--out">▼</i><span><strong>Выход</strong> — 4 закрытия подряд с ростом за 15 дней ниже −1%.</span></li>' +
        '<li><i class="wrule wrule--trail">◆</i><span><strong>Трейл</strong> — после +20% от входа продаём при откате на 4% от пика.</span></li>' +
        "</ul>" +
        '<p class="muted">Решение — раз в день, в 18:50 МСК по закрытому бару. Другие стратегии — в своих песочницах.</p>' +
        '<div class="wsetup-acts"><button type="button" class="primary" id="work-strategy">Подключить Абс. моментум-4</button></div>';
    } else if (focus === "params") {
      panel =
        "<h4>Бюджет рукава</h4>" +
        "<p class=\"muted\">Счёт сейчас " + escapeHtml(rubles(eq)) + ". Введите сумму в рублях или долю в процентах — второе поле посчитается само. Хранится доля: вырастет счёт — вырастет и бюджет.</p>" +
        '<div class="wparams">' +
        '<div class="wparam-row"><span class="wparam-k">Весь рукав</span>' +
        '<label>₽<input id="work-sleeve-rub" type="text" inputmode="decimal" data-rub-input autocomplete="off" value="' + escapeHtml(formatRubGrouped(eq * Number(String(sleevePct).replace(",", ".")) / 100)) + '"></label>' +
        '<label>% счёта<input id="work-sleeve" type="text" inputmode="decimal" autocomplete="off" value="' + escapeHtml(sleevePct) + '"></label></div>' +
        '<div class="wparam-row"><span class="wparam-k">Не больше на одну бумагу</span>' +
        '<label>₽<input id="work-cap-rub" type="text" inputmode="decimal" data-rub-input autocomplete="off" value="' + escapeHtml(formatRubGrouped(eq * Number(String(capPct).replace(",", ".")) / 100)) + '"></label>' +
        '<label>% счёта<input id="work-cap" type="text" inputmode="decimal" autocomplete="off" value="' + escapeHtml(capPct) + '"></label></div>' +
        "</div>" +
        '<div id="work-preview">' + workPreviewHtml(data.equity, sleevePct, capPct) + "</div>" +
        '<p class="wsetup-err" id="work-params-err" hidden></p>' +
        '<div class="wsetup-acts"><button type="button" class="primary" id="work-params">Сохранить бюджет</button>' +
        (workSetupOpen ? '<button type="button" class="ghost" id="work-edit-cancel">Отмена</button>' : "") +
        "</div>";
    } else if (focus === "enabled") {
      panel =
        "<h4>Включить заявки</h4>" +
        '<ul class="wsummary">' +
        "<li>Следующее решение: <strong data-countdown=\"" + escapeHtml(data.next_run_at || "") + '">' + escapeHtml(workCountdown(data.next_run_at)) + "</strong> (18:50 МСК)</li>" +
        "<li>На рукав: <strong>" + escapeHtml(rubles(data.sleeve_rub)) + "</strong>, на одну бумагу до <strong>" + escapeHtml(rubles(data.name_cap_rub)) + "</strong></li>" +
        "<li>Заявки рыночные, только в песочницу T-Invest. Боевой счёт не трогается.</li>" +
        "</ul>" +
        '<div class="wsetup-acts"><button type="button" class="primary" id="work-on">Включить заявки</button><button type="button" class="ghost" id="work-edit">Изменить бюджет</button></div>';
    }
    return (
      '<section class="wsetup" id="work-setup">' +
      '<div class="wsetup-head"><h3>Запуск</h3><span class="muted">' + (allOk ? "всё готово" : "шаг " + ((steps.map(function (s) { return s.id; }).indexOf(current)) + 1) + " из " + steps.length) + "</span></div>" +
      '<ol class="wsteps">' + dots + "</ol>" +
      '<div class="wsetup-panel">' + panel + "</div>" +
      "</section>"
    );
  }

  function workKpisHtml(data) {
    var day = (data.curve_day || []).map(function (p) { return Number(p.equity); });
    var pnlDaySeries = day.length ? day.map(function (v) { return v - day[0]; }) : [];
    var fill = Number(data.sleeve_fill) || 0;
    var ring = 2 * Math.PI * 15;
    function tile(key, label, value, fmt, sub, spark, tone) {
      return (
        '<div class="wkpi">' +
        '<span class="wkpi-k">' + escapeHtml(label) + "</span>" +
        '<strong class="wkpi-v' + (tone ? " is-" + tone : "") + '" data-wnum="' + key + '" data-wfmt="' + fmt + '">' + escapeHtml(value) + "</strong>" +
        (sub ? '<span class="wkpi-sub' + (tone ? " is-" + tone : "") + '">' + escapeHtml(sub) + "</span>" : "") +
        (spark || "") +
        '<span class="wkpi-delta" data-wdelta="' + key + '"></span>' +
        "</div>"
      );
    }
    return (
      '<section class="wkpis" id="work-kpis">' +
      tile("equity", "Стоимость счёта", rubles(data.equity), "rub", "", chartMiniSpark(day)) +
      tile("cash", "Свободный кэш", rubles(data.cash), "rub", data.equity ? workPct(data.cash / data.equity) + " счёта" : "") +
      tile("invested", "В бумагах", rubles(data.invested), "rub", (data.positions || []).length + " поз.") +
      tile("pnl_day", "Результат за день", workRub(data.pnl_day, true), "rubs", workPct(data.pnl_day_pct, true), chartMiniSpark(pnlDaySeries), workTone(data.pnl_day)) +
      tile("pnl_total", "С запуска", workRub(data.pnl_total, true), "rubs", workPct(data.pnl_total_pct, true), "", workTone(data.pnl_total)) +
      '<div class="wkpi wkpi--ring">' +
      '<span class="wkpi-k">Загрузка рукава</span>' +
      '<svg class="wring" viewBox="0 0 40 40"><circle class="wring-bg" cx="20" cy="20" r="15"></circle>' +
      '<circle class="wring-fg' + (fill > 1 ? " is-over" : "") + '" cx="20" cy="20" r="15" stroke-dasharray="' + (Math.min(1, fill) * ring).toFixed(2) + " " + ring.toFixed(2) + '" transform="rotate(-90 20 20)"></circle></svg>' +
      '<strong class="wkpi-v">' + escapeHtml(workPct(fill)) + "</strong>" +
      '<span class="wkpi-sub">из ' + escapeHtml(rubles(data.sleeve_rub)) + "</span>" +
      "</div>" +
      "</section>"
    );
  }

  function workTimeFmt(range) {
    return function (t, full, span) {
      var d = new Date(t + 3 * 3600 * 1000);
      function pad(n) { return (n < 10 ? "0" : "") + n; }
      var hm = pad(d.getUTCHours()) + ":" + pad(d.getUTCMinutes());
      var dm = pad(d.getUTCDate()) + "." + pad(d.getUTCMonth() + 1);
      if (full) return dm + " " + hm + " МСК";
      if (span != null) return span <= 36 * 3600 * 1000 ? hm : dm;
      return range === "day" ? hm : dm;
    };
  }

  function workEquityHtml(data) {
    var points = (data.curve || []).map(function (p) {
      return { t: Date.parse(p.ts), v: Number(p.equity) };
    }).filter(function (p) { return isFinite(p.t) && isFinite(p.v); });
    function valueAt(t) {
      var best = null;
      for (var i = 0; i < points.length; i++) {
        if (best === null || Math.abs(points[i].t - t) < Math.abs(best.t - t)) best = points[i];
      }
      return best ? best.v : null;
    }
    var marks = (data.trades || []).map(function (tr) {
      var t = Date.parse(tr.ts);
      var v = valueAt(t);
      if (!isFinite(t) || v === null) return null;
      return {
        t: t,
        v: v,
        side: tr.side,
        layer: Number(tr.layer) || 1,
        title: (tr.side === "sell" ? "Продажа " : Number(tr.layer) > 1 ? "Докуп " : "Покупка ") + workLabel(tr) + " · " + plainNumber(tr.qty) + " шт по " + workPrice(tr.price),
      };
    }).filter(Boolean);
    (data.payins || []).forEach(function (row) {
      var t = Date.parse(row.ts);
      var v = valueAt(t);
      if (!isFinite(t) || v === null) return;
      marks.push({ t: t, v: v, side: "payin", title: "Пополнение +" + rubles(row.amount) });
    });
    var ranges = [["day", "День"], ["week", "Неделя"], ["month", "Месяц"], ["all", "Всё"]].map(function (r) {
      return '<button type="button" data-work-range="' + r[0] + '"' + (workRange === r[0] ? ' aria-pressed="true"' : "") + ">" + r[1] + "</button>";
    }).join("");
    var first = points.length ? points[0].v : null;
    var last = points.length ? points[points.length - 1].v : null;
    var added = 0;
    if (points.length) {
      (data.payins || []).forEach(function (row) {
        var t = Date.parse(row.ts);
        if (t > points[0].t && t <= points[points.length - 1].t) added += Number(row.amount) || 0;
      });
    }
    var delta = first ? (last - added) / (first + added) - 1 : null;
    return (
      '<section class="wpanel" id="work-equity">' +
      '<div class="wpanel-head"><div><h3>Стоимость счёта</h3>' +
      (delta !== null
        ? '<span class="wpanel-sub is-' + workTone(delta) + '">' + escapeHtml(workArrow(delta) + workRub(last - first - added, true) + " · " + workPct(delta, true)) + " за период" + (added ? ", без пополнений " + escapeHtml(rubles(added)) : "") + "</span>"
        : '<span class="wpanel-sub muted">отметка раз в минуту</span>') +
      '</div><div class="wseg" role="group" aria-label="Период">' + ranges + "</div></div>" +
      chartLine("equity", points, {
        base: first,
        marks: marks,
        pulse: !!data.enabled,
        fmtX: workTimeFmt(workRange),
        label: "Стоимость счёта песочницы",
        empty: "Кривая появится, когда воркер сделает первые отметки (раз в минуту, нужен выбранный счёт).",
      }) +
      '<div class="wlegend"><span><i class="wlg wlg--buy"></i>покупка</span><span><i class="wlg wlg--add"></i>докуп</span><span><i class="wlg wlg--sell"></i>продажа</span><span><i class="wlg wlg--payin"></i>пополнение</span><span><i class="wlg wlg--base"></i>уровень начала периода</span></div>' +
      "</section>"
    );
  }

  function workAllocHtml(data) {
    var positions = data.positions || [];
    var segs = positions.map(function (p) {
      return {
        value: Number(p.value) || 0,
        tone: Number(p.pnl) >= 0 ? "up" : "down",
        title: workLabel(p) + " · " + rubles(p.value) + " · " + workPct(p.weight),
      };
    });
    segs.push({ value: Math.max(0, Number(data.cash) || 0), tone: "cash", title: "Кэш · " + rubles(data.cash) });
    var investedShare = data.equity ? (Number(data.invested) || 0) / data.equity : 0;
    var legend = positions.map(function (p) {
      return (
        '<li><i class="wlg wlg--' + (Number(p.pnl) >= 0 ? "up" : "down") + '"></i>' +
        "<span>" + escapeHtml(workLabel(p)) + "</span>" +
        "<strong>" + escapeHtml(workPct(p.weight)) + "</strong>" +
        '<span class="wcapline"><span style="width:' + (Math.min(1, Number(p.cap_fill) || 0) * 100).toFixed(1) + '%"></span></span>' +
        "</li>"
      );
    }).join("");
    legend += '<li><i class="wlg wlg--cash"></i><span>Кэш</span><strong>' + escapeHtml(workPct(data.equity ? data.cash / data.equity : 0)) + "</strong><span></span></li>";
    return (
      '<section class="wpanel" id="work-alloc">' +
      '<div class="wpanel-head"><div><h3>Распределение</h3><span class="wpanel-sub muted">полоска — сколько занято от потолка на бумагу</span></div></div>' +
      '<div class="walloc">' + chartDonut(segs, workPct(investedShare), "в бумагах") + '<ul class="walloc-legend">' + legend + "</ul></div>" +
      "</section>"
    );
  }

  function workSessionPos(now) {
    var p = workMskParts(now);
    var mins = p.h * 60 + p.m + p.s / 60;
    var span = WORK_SESSION.close - WORK_SESSION.open;
    return Math.max(0, Math.min(1, (mins - WORK_SESSION.open) / span));
  }

  function workDataAlertHtml(data) {
    var rows = data.data_alerts || [];
    if (!rows.length) return "";
    var items = rows.map(function (a) {
      var when = a.last_day ? "последняя свеча " + ruDay(a.last_day) : "свечей нет";
      var lag = a.days_behind ? " · отстаёт на " + a.days_behind + " дн." : "";
      return "<li><strong>" + escapeHtml(a.ticker) + "</strong> — " + escapeHtml(when + lag) + "</li>";
    }).join("");
    return (
      '<div class="callout danger" id="work-data-alert" role="alert">' +
      "<strong>Нет свежих свечей по бумагам в портфеле.</strong> " +
      "Стратегия не видит их цену, поэтому продажу по ним не решает и сама ничего не продаст. " +
      "Проверьте, торгуется ли бумага (остановка торгов, делистинг) — при необходимости закройте позицию вручную в песочнице." +
      '<ul class="wdata-list">' + items + "</ul></div>"
    );
  }

  function workDecisionHtml(data) {
    var now = new Date();
    var p = workMskParts(now);
    var weekend = p.day === 0 || p.day === 6;
    var mins = p.h * 60 + p.m;
    var inSession = !weekend && mins >= WORK_SESSION.open && mins < WORK_SESSION.close;
    var state = weekend ? "выходной, биржа закрыта" : inSession ? "сессия идёт" : mins < WORK_SESSION.open ? "до открытия" : "день закрыт, решение принято";
    var groups = { buy: [], sell: [], flat: 0 };
    (data.signals || []).forEach(function (s) {
      if (s.kind === "buy") groups.buy.push(s);
      else if (s.kind === "sell" || s.kind === "exit") groups.sell.push(s);
      else groups.flat += 1;
    });
    var slots = Math.max(0, (Number(data.max_names) || 0) - (data.positions || []).length);
    function chips(rows, tone, ranked) {
      return rows.slice(0, 24).map(function (s, i) {
        var strength = s.roc !== null && s.roc !== undefined ? " · рост за 15 дн. " + workPct(s.roc, true) : "";
        var miss = ranked && i >= slots;
        return '<span class="wchip wchip--' + (miss ? "muted" : tone) + '" title="' + escapeHtml(s.ticker + strength + (miss ? " · мест в рукаве не хватит" : "")) + '">' + escapeHtml(workLabel(s)) + "</span>";
      }).join("") + (rows.length > 24 ? '<span class="wchip">+' + (rows.length - 24) + "</span>" : "");
    }
    var first = (data.signals || [])[0];
    var sigDay = first
      ? ruDay(first.day || new Date(Date.parse(first.ts) + 3 * 3600 * 1000).toISOString().slice(0, 10))
      : "";
    var slotNote = groups.buy.length > slots
      ? '<p class="muted">Мест в рукаве: ' + slots + " — берём сильнейших по росту за 15 дней, остальные (бледные) ждут.</p>"
      : "";
    var decisions = (data.decisions || []).slice(-12).reverse().map(function (d) {
      var tone = d.status === "sent" ? (d.side === "sell" ? "down" : "up") : d.status === "disabled" ? "muted" : "warn";
      return (
        '<li class="wdec wdec--' + tone + '">' +
        '<span class="wdec-side">' + (d.side === "sell" ? "▼" : "▲") + "</span>" +
        "<span>" + escapeHtml(d.ticker) + " · " + escapeHtml(ruDay(d.day)) + "</span>" +
        "<strong>" + escapeHtml(WORK_DECISION_RU[d.status] || d.status) + "</strong>" +
        "</li>"
      );
    }).join("");
    return (
      '<section class="wpanel" id="work-decision">' +
      '<div class="wpanel-head"><div><h3>Решение дня</h3><span class="wpanel-sub muted">' + escapeHtml(state) + "</span></div>" +
      '<div class="wcount"><span>через</span><strong data-countdown="' + escapeHtml(data.next_run_at || "") + '">' + escapeHtml(workCountdown(data.next_run_at)) + "</strong></div></div>" +
      '<div class="wtimeline"><div class="wtimeline-track"><span class="wtimeline-fill" data-session-fill style="width:' + (workSessionPos(now) * 100).toFixed(2) + '%"></span>' +
      '<span class="wtimeline-now" data-session-now style="left:' + (workSessionPos(now) * 100).toFixed(2) + '%"></span>' +
      '<span class="wtimeline-flag" title="18:50 МСК — решение по закрытому бару"></span></div>' +
      '<div class="wtimeline-labels"><span>10:00</span><span>14:00</span><span>18:50 решение</span></div></div>' +
      (data.signals && data.signals.length
        ? '<div class="wsig"><div class="wsig-row"><span class="wsig-k is-up">Покупка (' + groups.buy.length + ")</span><div>" + (chips(groups.buy, "up", true) || '<span class="muted">нет</span>') + "</div></div>" + slotNote +
          '<div class="wsig-row"><span class="wsig-k is-down">Продажа (' + groups.sell.length + ")</span><div>" + (chips(groups.sell, "down") || '<span class="muted">нет</span>') + "</div></div>" +
          '<p class="muted">Без сигнала: ' + groups.flat + " бумаг · сигналы за " + escapeHtml(sigDay) + "</p></div>"
        : '<p class="muted">Сигналов рукава ещё нет — воркер посчитает их после 18:50 МСК.</p>') +
      (decisions ? '<h4 class="wsub-h">Что стало с сигналами</h4><ul class="wdecs">' + decisions + "</ul>" : "") +
      "</section>"
    );
  }

  function workCardHtml(p) {
    if (!p.trend) return workPlainCardHtml(p);
    var v = WORK_VERDICT[p.verdict] || WORK_VERDICT.hold;
    var trend = p.trend || {};
    var roc = p.roc || {};
    var weak = p.weak || { count: 0, limit: 4 };
    var trail = p.trail || {};
    var ratio = workNum(trend.ratio);
    var trendTone = ratio === null ? "muted" : ratio < 1 ? "bad" : ratio > (trend.stretch || 1.1) || ratio < 1.02 ? "warn" : "ok";
    var rocV = workNum(roc.value);
    var rocFloor = workNum(roc.floor) || -0.01;
    var rocTone = rocV === null ? "muted" : rocV < rocFloor ? "bad" : rocV < rocFloor + 0.02 ? "warn" : "ok";
    var dots = "";
    for (var i = 0; i < (weak.limit || 4); i++) {
      dots += '<i class="wweak-dot' + (i < weak.count ? " is-on" : "") + '"></i>';
    }
    var weakTone = weak.count >= (weak.limit || 4) ? "bad" : weak.count > 0 ? "warn" : "ok";
    var trailHtml;
    if (trail.armed && workNum(trail.exit_price) !== null) {
      var price = workNum(p.price);
      var gap = price ? price / trail.exit_price - 1 : null;
      trailHtml = chartBullet({
        label: "Трейл активен",
        valueText: "выход " + workPrice(trail.exit_price),
        min: trail.exit_price * 0.97,
        max: (trail.peak || price) * 1.01,
        floor: trail.exit_price,
        floorLabel: "уровень выхода",
        value: price,
        tone: gap !== null && gap < 0.01 ? "bad" : gap !== null && gap < 0.025 ? "warn" : "ok",
        note: "пик " + workPrice(trail.peak) + " · запас " + workPct(gap),
      });
    } else {
      var armPct = workNum(trail.arm_pct) || 0.2;
      var have = Math.max(0, workNum(p.pnl_pct) || 0);
      trailHtml = chartBar(have / armPct, {
        label: "До трейла (+" + plainNumber(armPct * 100) + "%)",
        valueText: have >= armPct ? "включится на закрытии" : "ещё " + workPct(armPct - have),
      });
    }
    return (
      '<article class="wpos wpos--' + v.tone + '" data-ticker="' + escapeHtml(p.ticker) + '">' +
      '<header class="wpos-head"><div><h4>' + escapeHtml(workLabel(p)) + "</h4><small>" + escapeHtml(p.ticker) + "</small></div>" +
      '<span class="wverdict wverdict--' + v.tone + '">' + escapeHtml(v.label) + "</span></header>" +
      '<div class="wpos-nums">' +
      '<div class="wpos-pnl is-' + workTone(p.pnl) + '"><strong data-wnum="pos-' + escapeHtml(p.ticker) + '" data-wfmt="rubs">' + escapeHtml(workRub(p.pnl, true)) + "</strong><span>" + escapeHtml(workPct(p.pnl_pct, true)) + "</span></div>" +
      '<div class="wpos-day is-' + workTone(p.day_pct) + '"><span>сегодня</span><strong>' + escapeHtml(workArrow(p.day_pct) + workPct(p.day_pct, true)) + "</strong></div>" +
      "</div>" +
      '<div class="wpos-meta">' + escapeHtml(plainNumber(p.qty)) + " шт · средняя " + escapeHtml(workPrice(p.avg_price)) + " → <strong>" + escapeHtml(workPrice(p.price)) + "</strong> · " + escapeHtml(rubles(p.value)) + "</div>" +
      chartSpark(p.spark, { avg: p.avg_price }) +
      '<div class="wspark-legend"><span><i class="wlg wlg--price"></i>цена</span><span><i class="wlg wlg--sma"></i>SMA' + escapeHtml(String(trend.sma_period || 30)) + '</span><span><i class="wlg wlg--avg"></i>средняя</span><span><i class="wlg wlg--now"></i>сейчас</span></div>' +
      chartBar(p.cap_fill, { label: "Потолок на бумагу", valueText: rubles(p.value) + " из " + rubles(p.cap_rub) }) +
      chartBullet({
        label: "Тренд: цена / SMA" + (trend.sma_period || 30),
        valueText: ratio === null ? "—" : ratio.toLocaleString("ru-RU", { minimumFractionDigits: 2, maximumFractionDigits: 2 }),
        min: 0.85,
        max: 1.2,
        floor: 1,
        floorLabel: "ниже 1,00 — тренд сломан",
        value: ratio,
        tone: trendTone,
        zones: [
          { from: 0.85, to: 1, tone: "bad" },
          { from: trend.stretch || 1.1, to: 1.2, tone: "warn" },
        ],
      }) +
      chartBullet({
        label: "Импульс: рост за " + (roc.lookback || 15) + " дн.",
        valueText: workPct(rocV, true),
        min: -0.1,
        max: 0.15,
        floor: rocFloor,
        floorLabel: "ниже " + workPct(rocFloor) + " — слабый день",
        value: rocV,
        tone: rocTone,
        zones: [{ from: -0.1, to: rocFloor, tone: "bad" }],
      }) +
      '<div class="wweak"><span>Слабые дни подряд</span><span class="wweak-dots">' + dots + "</span><strong class=\"is-" + weakTone + '">' + weak.count + " из " + (weak.limit || 4) + "</strong></div>" +
      trailHtml +
      '<footer class="wpos-foot"><span>' + (p.days_held != null ? escapeHtml(String(p.days_held)) + " дн. в позиции" : "вход не из рукава") + " · слоёв " + escapeHtml(String(p.layers || 0)) + "</span>" +
      '<button type="button" class="ghost compact" data-work-chart="' + escapeHtml(p.ticker) + '">График ↗</button></footer>' +
      '<div class="wpos-big" data-work-big="' + escapeHtml(p.ticker) + '" hidden></div>' +
      "</article>"
    );
  }

  function workPlainCardHtml(p) {
    return (
      '<article class="wpos" data-ticker="' + escapeHtml(p.ticker) + '">' +
      '<header class="wpos-head"><div><h4>' + escapeHtml(workLabel(p)) + "</h4><small>" + escapeHtml(p.ticker) + "</small></div></header>" +
      '<div class="wpos-nums">' +
      '<div class="wpos-pnl is-' + workTone(p.pnl) + '"><strong data-wnum="pos-' + escapeHtml(p.ticker) + '" data-wfmt="rubs">' + escapeHtml(workRub(p.pnl, true)) + "</strong><span>" + escapeHtml(workPct(p.pnl_pct, true)) + "</span></div>" +
      '<div class="wpos-day is-' + workTone(p.day_pct) + '"><span>сегодня</span><strong>' + escapeHtml(workArrow(p.day_pct) + workPct(p.day_pct, true)) + "</strong></div>" +
      "</div>" +
      '<div class="wpos-meta">' + escapeHtml(plainNumber(p.qty)) + " шт · средняя " + escapeHtml(workPrice(p.avg_price)) + " → <strong>" + escapeHtml(workPrice(p.price)) + "</strong> · " + escapeHtml(rubles(p.value)) + "</div>" +
      chartSpark(p.spark, { avg: p.avg_price }) +
      chartBar(p.cap_fill, { label: "Потолок на бумагу", valueText: rubles(p.value) + " из " + rubles(p.cap_rub) }) +
      '<p class="wbullet-note">Выход — по сигналу продажи этой стратегии на закрытии дня.</p>' +
      '<footer class="wpos-foot"><span>' + (p.days_held != null ? escapeHtml(String(p.days_held)) + " дн. в позиции" : "вход не из рукава") + " · слоёв " + escapeHtml(String(p.layers || 0)) + "</span>" +
      '<button type="button" class="ghost compact" data-work-chart="' + escapeHtml(p.ticker) + '">График ↗</button></footer>' +
      '<div class="wpos-big" data-work-big="' + escapeHtml(p.ticker) + '" hidden></div>' +
      "</article>"
    );
  }

  function workPositionsHtml(data) {
    var rows = (data.positions || []).slice();
    var verdictRank = { exit: 0, watch: 1, hold: 2 };
    if (workSort === "pnl") rows.sort(function (a, b) { return (Number(b.pnl_pct) || 0) - (Number(a.pnl_pct) || 0); });
    else if (workSort === "weight") rows.sort(function (a, b) { return (Number(b.weight) || 0) - (Number(a.weight) || 0); });
    else rows.sort(function (a, b) {
      return (verdictRank[a.verdict] - verdictRank[b.verdict]) || (((b.weak && b.weak.count) || 0) - ((a.weak && a.weak.count) || 0));
    });
    var sorts = [["risk", "Риск выхода"], ["pnl", "Результат"], ["weight", "Вес"]].map(function (s) {
      return '<button type="button" data-work-sort="' + s[0] + '"' + (workSort === s[0] ? ' aria-pressed="true"' : "") + ">" + s[1] + "</button>";
    }).join("");
    var buys = (data.signals || []).filter(function (s) { return s.kind === "buy"; }).length;
    var body = rows.length
      ? '<div class="wpos-grid">' + rows.map(workCardHtml).join("") + "</div>"
      : '<div class="wempty"><svg viewBox="0 0 64 48" aria-hidden="true"><path d="M6 14h52l-6 28H12z"></path><path d="M20 14l8-10M44 14l-8-10"></path></svg>' +
        "<p><strong>Позиций нет.</strong> Следующее решение через <span data-countdown=\"" + escapeHtml(data.next_run_at || "") + '">' + escapeHtml(workCountdown(data.next_run_at)) + "</span>" +
        (buys ? "; кандидатов на вход в последнем прогоне: " + buys : "") + ".</p></div>";
    return (
      '<section class="wpanel" id="work-positions">' +
      '<div class="wpanel-head"><div><h3>Позиции</h3><span class="wpanel-sub muted">' + rows.length + " · цена брокера, правила выхода «" + escapeHtml((data.desk && data.desk.strategy && data.desk.strategy.title) || "") + "»</span></div>" +
      (rows.length > 1 ? '<div class="wseg" role="group" aria-label="Сортировка">' + sorts + "</div>" : "") + "</div>" +
      body +
      "</section>"
    );
  }

  function workTradesHtml(data) {
    var rows = (data.trades || []).slice().reverse();
    var seen = workSeenTrades;
    var next = {};
    var items = rows.slice(0, 60).map(function (tr) {
      var key = tr.broker_order_id || tr.ts + tr.ticker + tr.side;
      next[key] = 1;
      var fresh = seen && !seen[key];
      var sell = tr.side === "sell";
      var add = !sell && Number(tr.layer) > 1;
      return (
        '<li class="wtrade' + (fresh ? " is-fresh" : "") + '">' +
        '<span class="wtrade-ico wtrade-ico--' + (sell ? "sell" : add ? "add" : "buy") + '">' + (sell ? "▼" : add ? "◆" : "▲") + "</span>" +
        '<div class="wtrade-main"><strong>' + escapeHtml(workLabel(tr)) + "</strong> <small>" + escapeHtml(tr.ticker) + "</small>" +
        "<span>" + escapeHtml(sell ? "Продажа" : add ? "Докуп, слой " + tr.layer : "Покупка") + " · " + escapeHtml(plainNumber(tr.qty)) + " шт × " + escapeHtml(workPrice(tr.price)) + " = " + escapeHtml(rubles(tr.amount)) +
        (add ? " · средняя после " + escapeHtml(workPrice(tr.avg_after)) : "") + "</span></div>" +
        (sell && tr.realized != null ? '<span class="wpill wpill--' + (tr.realized >= 0 ? "up" : "down") + '">' + escapeHtml(workRub(tr.realized, true)) + " · " + escapeHtml(workPct(tr.realized_pct, true)) + "</span>" : "") +
        '<time>' + escapeHtml(String(tr.ts || "").replace("T", " ").slice(0, 16)) + "</time>" +
        "</li>"
      );
    }).join("");
    workSeenTrades = next;
    return (
      '<section class="wpanel" id="work-trades">' +
      '<div class="wpanel-head"><div><h3>Сделки рукава</h3><span class="wpanel-sub muted">новые сверху</span></div></div>' +
      (items ? '<ol class="wtrades">' + items + "</ol>" : '<p class="muted">Заявок рукава ещё не было.</p>') +
      "</section>"
    );
  }

  /* ---------- сборка, опрос, движение ---------- */

  function renderWork() {
    byId("page-body").innerHTML =
      '<div class="work" id="work-root">' +
      '<div class="whead"><div class="wlive" id="work-live"><i class="wdot"></i><span>подключаюсь…</span></div></div>' +
      '<div class="wskeleton"><span></span><span></span><span></span></div>' +
      "</div>";
  }

  function refreshWork() {
    var desksReq = apiGet("/work/desks").then(function (ov) {
      workDesks = ov;
      workSyncNav();
      return ov;
    });
    if (!workOnDesk()) {
      return desksReq
        .then(function (ov) {
          workLastOkAt = new Date();
          workLastFailAt = null;
          paintWorkBoard();
          startWorkTimers();
          return ov;
        })
        .catch(function (err) {
          workLastFailAt = new Date();
          var root = byId("work-root");
          if (root && !workDesks) root.innerHTML += '<p class="wsetup-err">' + escapeHtml((err && err.message) || "API не ответил") + "</p>";
          paintWorkLive();
          startWorkTimers();
          return null;
        });
    }
    desksReq = desksReq.catch(function () { return workDesks; });
    return apiGet(workUrl("/work?range=" + encodeURIComponent(workRange)))
      .catch(function (err) {
        if (err && err.status === 404) {
          workSetStatus("", "");
          location.hash = "#/work";
          return null;
        }
        throw err;
      })
      .then(function (data) {
        return desksReq.then(function () { return data; });
      })
      .then(function (data) {
        if (!data || !workOnDesk()) return data;
        workLastOkAt = new Date();
        workLastFailAt = null;
        workData = data;
        workSetTitle();
        paintWork(data);
        startWorkTimers();
        return data;
      })
      .catch(function (err) {
        workLastFailAt = new Date();
        if (!workData) {
          var root = byId("work-root");
          if (root) {
            root.innerHTML += '<p class="wsetup-err">' + escapeHtml(err.message || "API не ответил") + "</p>";
          }
        }
        paintWorkLive();
        startWorkTimers();
        return null;
      });
  }

  function paintWorkLive() {
    var box = byId("work-live");
    if (!box) return;
    if (workLastFailAt && (!workLastOkAt || workLastFailAt > workLastOkAt)) {
      var mins = workLastOkAt ? Math.max(1, Math.round((Date.now() - workLastOkAt.getTime()) / 60000)) : 0;
      box.className = "wlive is-off";
      box.innerHTML = '<i class="wdot"></i><span>нет связи' + (mins ? " " + mins + " мин" : "") + "</span>";
      return;
    }
    if (!workLastOkAt) return;
    box.className = "wlive is-on is-blink";
    box.innerHTML = '<i class="wdot"></i><span>живое · ' + escapeHtml(workClock(workLastOkAt)) + " МСК</span>";
    window.setTimeout(function () { box.classList.remove("is-blink"); }, 900);
  }

  function workCollectNums() {
    var out = {};
    document.querySelectorAll("#work-root [data-wnum]").forEach(function (el) {
      out[el.getAttribute("data-wnum")] = el.textContent;
    });
    return out;
  }

  function workParseShown(text) {
    var n = parseRubInput(String(text || "").replace(/[^\d,.\-+\s\u00a0]/g, ""));
    return isFinite(n) ? n : null;
  }

  function workCountUp(el, from, to, fmt) {
    var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    function show(v) {
      el.textContent = fmt === "rubs" ? workRub(v, true) : rubles(v);
    }
    if (reduce || from === null || !isFinite(from) || Math.abs(to - from) < 0.005) {
      show(to);
      return;
    }
    var start = performance.now();
    var dur = 450;
    function step(now) {
      var k = Math.min(1, (now - start) / dur);
      var e = 1 - Math.pow(1 - k, 3);
      show(from + (to - from) * e);
      if (k < 1) window.requestAnimationFrame(step);
    }
    window.requestAnimationFrame(step);
  }

  function workAnimateNums(prev, data) {
    var targets = {
      equity: data.equity,
      cash: data.cash,
      invested: data.invested,
      pnl_day: data.pnl_day,
      pnl_total: data.pnl_total,
    };
    (data.positions || []).forEach(function (p) { targets["pos-" + p.ticker] = p.pnl; });
    document.querySelectorAll("#work-root [data-wnum]").forEach(function (el) {
      var key = el.getAttribute("data-wnum");
      var to = workNum(targets[key]);
      if (to === null || prev[key] == null) return;
      var from = workParseShown(prev[key]);
      if (from === null || Math.abs(to - from) < 0.005) return;
      workCountUp(el, from, to, el.getAttribute("data-wfmt"));
      var host = el.closest(".wkpi, .wpos, .wcontour") || el;
      host.classList.remove("tick-up", "tick-down");
      void host.offsetWidth;
      host.classList.add(to > from ? "tick-up" : "tick-down");
      var delta = document.querySelector('#work-root [data-wdelta="' + key + '"]');
      if (delta) {
        delta.textContent = workRub(to - from, true);
        delta.className = "wkpi-delta is-show is-" + workTone(to - from);
        window.setTimeout(function () { delta.classList.remove("is-show"); }, 3000);
      }
    });
  }

  function workEditing() {
    var a = document.activeElement;
    return !!(a && a.closest && a.closest("#work-root") && /INPUT|SELECT|TEXTAREA/.test(a.tagName));
  }

  function paintWork(data, force) {
    var root = byId("work-root");
    if (!root) return;
    if (!force && workEditing()) {
      paintWorkLive();
      return;
    }
    var prevNums = workCollectNums();
    var hadSections = !!byId("work-kpis") || !!byId("work-setup");
    var ok = workStepMap(data);
    var setupHtml = workSetupHtml(data);
    var body =
      workContoursHtml(data) +
      '<div id="work-setup-slot"></div>' +
      '<p class="wstatus" id="work-status" role="status" aria-live="polite"></p>' +
      (ok.account
        ? workDataAlertHtml(data) +
          workKpisHtml(data) +
          workEquityHtml(data) +
          '<div class="wtwo">' + workAllocHtml(data) + workDecisionHtml(data) + "</div>" +
          workPositionsHtml(data) +
          workTradesHtml(data)
        : "");
    var statusText = (byId("work-status") || {}).textContent || "";
    var statusClass = (byId("work-status") || {}).className || "wstatus";
    var head = root.querySelector(".whead");
    root.innerHTML = "";
    if (head) root.appendChild(head);
    var wrap = document.createElement("div");
    wrap.innerHTML = body;
    while (wrap.firstChild) root.appendChild(wrap.firstChild);
    var slot = byId("work-setup-slot");
    slot.outerHTML = setupHtml;
    var st = byId("work-status");
    if (st && statusText) {
      st.textContent = statusText;
      st.className = statusClass;
    }
    root.classList.toggle("is-first", !hadSections);
    paintWorkLive();
    if (hadSections) workAnimateNums(prevNums, data);
    bindChartCrosshair(root);
    bindWork();
  }

  function paintWorkBoard(force) {
    var root = byId("work-root");
    if (!root || workOnDesk()) return;
    if (!force && (workEditing() || byId("work-create"))) {
      paintWorkLive();
      return;
    }
    var statusText = (byId("work-status") || {}).textContent || "";
    var statusClass = (byId("work-status") || {}).className || "wstatus";
    var head = root.querySelector(".whead");
    root.innerHTML = "";
    if (head) root.appendChild(head);
    var wrap = document.createElement("div");
    wrap.innerHTML =
      '<p class="wstatus" id="work-status" role="status" aria-live="polite"></p>' +
      (workView === "new" ? workNewHtml(workDesks) : workBoardHtml(workDesks));
    while (wrap.firstChild) root.appendChild(wrap.firstChild);
    var st = byId("work-status");
    if (st && statusText) {
      st.textContent = statusText;
      st.className = statusClass;
    }
    paintWorkLive();
    bindWork();
  }

  function workSetStatus(text, tone) {
    var st = byId("work-status");
    if (!st) return;
    st.textContent = text || "";
    st.className = "wstatus" + (tone ? " is-" + tone : "") + (text ? " is-show" : "");
  }

  function workAction(btn, run, okText) {
    if (btn) {
      btn.disabled = true;
      btn.setAttribute("aria-busy", "true");
    }
    workSetStatus("Выполняю…", "busy");
    return Promise.resolve()
      .then(run)
      .then(function () {
        workSetStatus(okText || "Готово.", "ok");
        return refreshWork();
      })
      .catch(function (err) {
        workSetStatus((err && err.message) || "Не получилось.", "bad");
      })
      .finally(function () {
        if (btn && document.body.contains(btn)) {
          btn.disabled = false;
          btn.removeAttribute("aria-busy");
        }
      });
  }

  function workReadPercent(raw, label) {
    var s = String(raw || "").trim().replace(",", ".").replace("%", "");
    if (!/^\d{1,2}(\.\d+)?$/.test(s)) throw new Error(label + ": число от 1 до 99");
    var n = Number(s);
    if (!(n >= 1 && n <= 99)) throw new Error(label + ": от 1 до 99");
    return n;
  }

  function workValidateParams() {
    var sleeveEl = byId("work-sleeve");
    var capEl = byId("work-cap");
    var err = byId("work-params-err");
    var btn = byId("work-params");
    if (!sleeveEl || !capEl) return null;
    var sleeve = null;
    var cap = null;
    var msg = "";
    try {
      sleeve = workReadPercent(sleeveEl.value, "Доля рукава");
      cap = workReadPercent(capEl.value, "На одну бумагу");
      if (cap > sleeve) msg = "На одну бумагу нельзя больше, чем на весь рукав.";
    } catch (e) {
      msg = e.message;
    }
    workParamsDraft = { sleeve: sleeveEl.value, cap: capEl.value };
    var preview = byId("work-preview");
    if (preview) preview.innerHTML = workPreviewHtml(workData && workData.equity, sleeve || 0, cap || 0);
    if (err) {
      err.textContent = msg;
      err.hidden = !msg;
    }
    if (btn) btn.disabled = !!msg;
    return msg ? null : { sleeve: sleeve, cap: cap };
  }

  function bindWork() {
    document.querySelectorAll("[data-work-desk]").forEach(function (btn) {
      btn.onclick = function () { workSelectDesk(btn.getAttribute("data-work-desk")); };
    });
    var archive = byId("work-archive");
    if (archive) archive.onclick = function () {
      var name = (workData && workData.desk && workData.desk.name) || "песочницу";
      askConfirm({
        title: "Убрать «" + name + "»?",
        text: "Заявки выключатся, песочница пропадёт из списка и сравнения. Счёт у брокера и история сделок останутся в файле на сервере.",
        okLabel: "Убрать",
        danger: true,
      }).then(function (yes) {
        if (!yes) return;
        workAction(archive, function () {
          return apiPost(workUrl("/work/desks/archive"), {}).then(function () {
            workDesk = "main";
            try {
              window.localStorage.setItem("work.desk", "main");
            } catch (e) {}
            workDrawn = {};
            workSeenTrades = null;
            location.hash = "#/work";
          });
        }, "Песочница убрана.");
      });
    };
    var createOpen = byId("work-create-open");
    if (createOpen) createOpen.onclick = function () {
      workCreateOpen = true;
      paintWorkBoard(true);
      var form = byId("work-create");
      if (form) form.scrollIntoView({ block: "nearest", behavior: "smooth" });
    };
    var createCancel = byId("work-create-cancel");
    if (createCancel) createCancel.onclick = function () {
      workCreateOpen = false;
      if (workView === "new") location.hash = "#/work";
      else paintWorkBoard(true);
    };
    var deposit = byId("work-new-deposit");
    if (deposit) bindRubInput(deposit);
    var createSend = byId("work-create-send");
    if (createSend) createSend.onclick = function () {
      var picked = document.querySelector('input[name="work-new-sleeve"]:checked');
      var amount = parseRubInput(deposit ? deposit.value : "");
      var name = ((byId("work-new-name") || {}).value || "").trim();
      if (!picked) {
        workSetStatus("Выберите стратегию для новой песочницы.", "bad");
        return;
      }
      if (!isFinite(amount) || amount < 1000) {
        workSetStatus("Стартовый депозит от 1 000 ₽.", "bad");
        return;
      }
      var title = picked.closest(".wstrat").querySelector("strong").textContent;
      askConfirm({
        title: "Открыть песочницу «" + (name || title) + "»?",
        text: "Брокер откроет новый счёт песочницы и зачислит " + formatRubGrouped(amount) + " игровых ₽. Заявки останутся выключенными, пока вы не зададите бюджет и не включите их.",
        okLabel: "Открыть",
        danger: false,
      }).then(function (yes) {
        if (!yes) return;
        workAction(createSend, function () {
          return apiPost("/work/desks", { sleeve: picked.value, name: name, deposit: String(Math.round(amount)) }, { timeoutMs: 45000 }).then(function (out) {
            workCreateOpen = false;
            workParamsDraft = null;
            workSeenTrades = null;
            workDrawn = {};
            workSelectDesk(out.desk);
          });
        }, "Песочница открыта. Задайте бюджет и включите заявки.");
      });
    };
    var probe = byId("work-probe");
    if (probe) probe.onclick = function () {
      workAction(probe, function () { return apiPost("/work/probe", {}); }, "Песочница отвечает.");
    };
    var open = byId("work-open");
    if (open) open.onclick = function () {
      workAction(open, function () { return apiPost(workUrl("/work/open"), {}, { timeoutMs: 45000 }); }, "Счёт открыт, 1 000 000 ₽ зачислены.");
    };
    var accountBtn = byId("work-account-save");
    if (accountBtn) accountBtn.onclick = function () {
      var picked = document.querySelector('input[name="work-acc"]:checked');
      workAction(accountBtn, function () {
        if (!picked) throw new Error("Выберите счёт.");
        return apiPost(workUrl("/work/account"), { account_id: picked.value });
      }, "Счёт выбран.");
    };
    var strategy = byId("work-strategy");
    if (strategy) strategy.onclick = function () {
      workAction(strategy, function () { return apiPost(workUrl("/work/strategy"), {}); }, "Стратегия подключена.");
    };
    var sleeveEl = byId("work-sleeve");
    var capEl = byId("work-cap");
    var eqNow = workData ? Number(workData.equity) || 0 : 0;
    [[sleeveEl, byId("work-sleeve-rub")], [capEl, byId("work-cap-rub")]].forEach(function (pair) {
      var pctEl = pair[0];
      var rubEl = pair[1];
      if (!pctEl || !rubEl) return;
      pctEl.oninput = function () {
        var n = Number(String(pctEl.value).replace(",", "."));
        rubEl.value = isFinite(n) && pctEl.value.trim() ? formatRubGrouped((eqNow * n) / 100) : "";
        workValidateParams();
      };
      rubEl.oninput = function () {
        var rub = parseRubInput(rubEl.value);
        pctEl.value = isFinite(rub) ? workPctFromRub(rub, eqNow) : "";
        workValidateParams();
      };
      bindRubInput(rubEl);
    });
    if (sleeveEl) workValidateParams();
    var payOpen = byId("work-payin-open");
    if (payOpen) payOpen.onclick = function () {
      workPayinOpen = true;
      if (workData) paintWork(workData, true);
      var el = byId("work-payin-amount");
      if (el) el.focus();
    };
    var payAmount = byId("work-payin-amount");
    if (payAmount) {
      bindRubInput(payAmount);
      payAmount.oninput = function () { workPayinDraft = payAmount.value; };
    }
    document.querySelectorAll("[data-payin-add]").forEach(function (btn) {
      btn.onclick = function () {
        var cur = parseRubInput(payAmount ? payAmount.value : "");
        var next = (isFinite(cur) ? cur : 0) + Number(btn.getAttribute("data-payin-add"));
        workPayinDraft = formatRubGrouped(next);
        if (payAmount) payAmount.value = workPayinDraft;
      };
    });
    var payCancel = byId("work-payin-cancel");
    if (payCancel) payCancel.onclick = function () {
      workPayinOpen = false;
      workPayinDraft = "";
      if (workData) paintWork(workData, true);
    };
    var paySend = byId("work-payin-send");
    if (paySend) paySend.onclick = function () {
      var amount = parseRubInput(payAmount ? payAmount.value : "");
      if (!isFinite(amount) || amount < 1000) {
        workSetStatus("Пополнение от 1 000 ₽.", "bad");
        return;
      }
      if (payAmount) payAmount.value = formatRubGrouped(amount);
      askConfirm({
        title: "Пополнить песочницу на " + formatRubGrouped(amount) + " ₽?",
        text: "Брокер зачислит игровые рубли на счёт " + workShortId(workData && workData.account_id) + ". Вывести их обратно нельзя. В результат стратегии пополнение не входит.",
        okLabel: "Пополнить",
        danger: false,
      }).then(function (yes) {
        if (!yes) return;
        workAction(paySend, function () {
          return apiPost(workUrl("/work/payin"), { amount: String(Math.round(amount * 100) / 100) }).then(function () {
            workPayinOpen = false;
            workPayinDraft = "";
          });
        }, "Счёт пополнен на " + formatRubGrouped(amount) + " ₽.");
      });
    };
    var params = byId("work-params");
    if (params) params.onclick = function () {
      var vals = workValidateParams();
      if (!vals) return;
      workAction(params, function () {
        return apiPost(workUrl("/work/params"), {
          sleeve_share: (vals.sleeve / 100).toFixed(4),
          name_cap: (vals.cap / 100).toFixed(4),
        }).then(function () {
          workSetupOpen = false;
          workParamsDraft = null;
        });
      }, "Бюджет сохранён: рукав " + plainNumber(vals.sleeve) + "%, на бумагу " + plainNumber(vals.cap) + "%.");
    };
    var edit = byId("work-edit");
    if (edit) edit.onclick = function () {
      workSetupOpen = true;
      if (workData) paintWork(workData, true);
      var el = byId("work-sleeve");
      if (el) el.focus();
    };
    var cancel = byId("work-edit-cancel");
    if (cancel) cancel.onclick = function () {
      workSetupOpen = false;
      workParamsDraft = null;
      if (workData) paintWork(workData, true);
    };
    var on = byId("work-on");
    if (on) on.onclick = function () {
      askConfirm({
        title: "Включить заявки в песочнице?",
        text: "С ближайшего решения (18:50 МСК) рукав будет ставить рыночные заявки в песочницу T-Invest. Деньги игровые, боевой счёт не трогается.",
        okLabel: "Включить",
        danger: false,
      }).then(function (yes) {
        if (!yes) return;
        workAction(on, function () { return apiPost(workUrl("/work/enable"), { enabled: true }); }, "Заявки включены.");
      });
    };
    var off = byId("work-off");
    if (off) off.onclick = function () {
      askConfirm({
        title: "Выключить заявки?",
        text: "Сигналы продолжат считаться, но заявки в песочницу уходить не будут. Открытые позиции останутся.",
        okLabel: "Выключить",
        danger: true,
      }).then(function (yes) {
        if (!yes) return;
        workAction(off, function () { return apiPost(workUrl("/work/enable"), { enabled: false }); }, "Заявки выключены.");
      });
    };
    document.querySelectorAll("[data-work-range]").forEach(function (btn) {
      btn.onclick = function () {
        workRange = btn.getAttribute("data-work-range") || "day";
        workDrawn.equity = false;
        refreshWork();
      };
    });
    document.querySelectorAll("[data-work-sort]").forEach(function (btn) {
      btn.onclick = function () {
        workSort = btn.getAttribute("data-work-sort") || "risk";
        if (workData) paintWork(workData, true);
      };
    });
    document.querySelectorAll("[data-work-chart]").forEach(function (btn) {
      btn.onclick = function () {
        var ticker = btn.getAttribute("data-work-chart");
        var box = document.querySelector('[data-work-big="' + ticker + '"]');
        var card = btn.closest(".wpos");
        if (!box || !card) return;
        if (!box.hidden) {
          box.hidden = true;
          card.classList.remove("is-wide");
          btn.textContent = "График ↗";
          return;
        }
        card.classList.add("is-wide");
        btn.textContent = "Свернуть";
        box.hidden = false;
        box.innerHTML = '<p class="muted">Загружаю 80 дней…</p>';
        apiGet(workUrl("/work/chart?ticker=" + encodeURIComponent(ticker))).then(function (chart) {
          var pts = (chart.bars || []).map(function (b) {
            return { t: Date.parse(b.ts + "T15:50:00Z"), v: Number(b.close) };
          }).filter(function (p) { return isFinite(p.t) && isFinite(p.v); });
          var marks = (chart.marks || []).map(function (m) {
            var t = Date.parse(String(m.ts || "").slice(0, 10) + "T15:50:00Z");
            return { t: t, v: Number(m.price), side: m.side, layer: Number(m.layer) || 1, title: (m.side === "sell" ? "Продажа" : "Покупка") + " · " + workPrice(m.price) };
          });
          box.innerHTML = chartLine("pos-" + ticker, pts, {
            marks: marks,
            height: 220,
            fmtX: workTimeFmt("month"),
            fmtY: function (v) { return workPrice(v); },
            label: "Цена " + ticker,
          });
          bindChartCrosshair(box);
        }).catch(function (err) {
          box.innerHTML = '<p class="wsetup-err">' + escapeHtml(err.message || "график не загрузился") + "</p>";
        });
      };
    });
  }

  function workTick() {
    document.querySelectorAll("#work-root [data-countdown]").forEach(function (el) {
      el.textContent = workCountdown(el.getAttribute("data-countdown"));
    });
    var pos = (workSessionPos(new Date()) * 100).toFixed(2) + "%";
    var fill = document.querySelector("#work-root [data-session-fill]");
    var nowEl = document.querySelector("#work-root [data-session-now]");
    if (fill) fill.style.width = pos;
    if (nowEl) nowEl.style.left = pos;
  }

  function startWorkTimers() {
    if (!workClockTimer) workClockTimer = window.setInterval(function () {
      if (currentRoute !== "work") return stopWorkTimers();
      workTick();
    }, 1000);
    if (!workPollTimer) workPollTimer = window.setInterval(function () {
      if (currentRoute !== "work") return stopWorkTimers();
      if (document.hidden) return;
      refreshWork();
    }, WORK_POLL_MS);
  }

  function stopWorkTimers() {
    if (workClockTimer) window.clearInterval(workClockTimer);
    if (workPollTimer) window.clearInterval(workPollTimer);
    workClockTimer = null;
    workPollTimer = null;
  }

  document.addEventListener("visibilitychange", function () {
    if (!document.hidden && currentRoute === "work" && workData) refreshWork();
  });

  function showRoute(id) {
    if (!authed) return;
    var route = null;
    for (var i = 0; i < ROUTES.length; i++) {
      if (ROUTES[i].id === id) {
        route = ROUTES[i];
        break;
      }
    }
    if (!route) route = ROUTES[0];
    if (currentRoute === "companies" && route.id !== "companies") {
      stopCompaniesPoll();
    }
    if (route.id !== "work") stopWorkTimers();
    currentRoute = route.id;
    renderNav();
    syncNavActive(route.id);
    closeMobileMore();

    byId("page-title").textContent = route.title;
    byId("page-intro").textContent = route.intro;
    document.title = "i.datagon · " + route.title;

    if (route.id === "home") {
      renderDeskHome();
      return;
    }
    if (route.id === "overview") {
      renderOverview();
      loadOverviewData(true).then(function () {
        maybeStartOverviewTour();
      });
      return;
    }
    if (route.id === "portfolio") {
      var requestedPortfolioTab = hashQuery().tab;
      if (
        requestedPortfolioTab === "positions" ||
        requestedPortfolioTab === "capital" ||
        requestedPortfolioTab === "vault" ||
        requestedPortfolioTab === "allocation" ||
        requestedPortfolioTab === "drift"
      ) {
        portfolioTab = requestedPortfolioTab;
      } else portfolioTab = "capital";
      if (
        portfolioTab !== "positions" &&
        portfolioTab !== "capital" &&
        portfolioTab !== "vault" &&
        portfolioTab !== "allocation" &&
        portfolioTab !== "drift"
      ) {
        portfolioTab = "capital";
      }
      renderPortfolio();
      refreshPortfolioBook().then(function () {
        maybeStartPortfolioTour();
      });
      return;
    }
    if (route.id === "candles") {
      renderCandles();
      refreshCandles();
      pollCandleFillOnce().then(function (data) {
        if (data && data.status === "running") startCandleFillPoll();
      });
      return;
    }
    if (route.id === "strategies") {
      var sleeveTarget = strategiesSleeveFromHash();
      sleeveDetailLoading = !!(
        sleeveTarget &&
        (!lastSleeveDetail || lastSleeveDetail.sleeve !== sleeveTarget)
      );
      renderStrategies();
      refreshStrategies().then(function () {
        maybeStartStrategiesTour();
      });
      return;
    }
    if (route.id === "companies") {
      renderCompanies();
      refreshCompanies();
      startCompaniesPoll();
      return;
    }
    if (route.id === "whatif") {
      renderWhatIf();
      refreshWhatIf();
      return;
    }
    if (route.id === "recommendations") {
      renderRecommendations();
      refreshRecommendations();
      return;
    }
    if (route.id === "agents") {
      if (hashQuery().tab === "proposed") agentsFocusProposed = true;
      renderAgents();
      refreshProposals().then(function () {
        maybeStartAgentsTour();
      });
      return;
    }
    if (route.id === "news") {
      if (hashQuery().tab === "studies") newsTab = "studies";
      else newsTab = "feed";
      renderNews();
      refreshNews().then(function () {
        maybeStartNewsTour();
      });
      return;
    }
    if (route.id === "market") {
      if (hashQuery().tab === "rules") marketTab = "rules";
      else marketTab = "universe";
      renderMarket();
      refreshMarket().then(function () {
        maybeStartMarketTour();
      });
      return;
    }
    if (route.id === "work") {
      workView = workViewFromHash();
      if (workView !== "all" && workView !== "new") workSetDesk(workView);
      workCreateOpen = false;
      workDrawn = {};
      workSeenTrades = null;
      workSyncNav();
      workSetTitle();
      renderWork();
      refreshWork();
      return;
    }
    if (route.id === "journal") {
      if (hashQuery().tab === "ledger") journalTab = "ledger";
      else if (hashQuery().tab === "audit") journalTab = "audit";
      else journalTab = "orders";
      renderJournal();
      refreshJournal().then(function () {
        maybeStartJournalTour();
      });
      return;
    }
    if (route.id === "settings") {
      renderSettings();
      refreshSettings();
      return;
    }
    if (route.id === "help") {
      renderHelpPanel();
      return;
    }
    renderPlaceholder(route);
  }

  function syncFromHash() {
    if (!authed) return;
    var raw = hashPath();
    var id = routeFromHash();
    if ((location.hash || "") === "" || location.hash === "#") {
      setHash(id);
      return;
    }
    if (raw && id === "home" && raw !== "home") {
      setHash("home");
      return;
    }
    showRoute(id);
  }

  function runTour(key, steps) {
    if (!window.CabinTour) return;
    CabinTour.start({
      key: key,
      steps: steps,
      onStep: function (step) {
        if (step.route && authed) setHash(step.route);
      },
    });
  }

  function startGateTour() {
    runTour(GATE_TOUR_KEY, [
      {
        tour: "gate-token",
        title: "Токен кабины — не брокер",
        text: "Сюда вставляется APP_AUTH_TOKEN из .env. Токен Тинькоффа в браузер не вводится и здесь не нужен.",
      },
      {
        tour: "gate-submit",
        title: "Проверка перед входом",
        text: "Кнопка «Войти» проверяет токен запросом к API. При неверном токене кабинет не откроется — вы увидите понятную ошибку.",
      },
    ]);
  }

  function startOverviewTour() {
    setHash("overview");
    window.setTimeout(function () {
      var waiting = proposedList(lastProposals).length;
      var queueStep = waiting
        ? {
            tour: "queue-badge",
            title: "Бейдж очереди",
            text: "В шапке янтарный бейдж с числом предложений, которые ждут решения. Клик ведёт в «Агенты». При нуле бейдж скрыт.",
          }
        : {
            tour: "status-refresh",
            title: "Бейдж очереди",
            text: "Когда появятся предложения со статусом «ждут решения», в шапке справа от бренда всплывёт янтарный бейдж с числом. При нуле его нет — это нормально.",
          };
      runTour(OVERVIEW_TOUR_KEY, [
        {
          tour: "status-strip",
          title: "Сначала статус",
          text: "Пиллы в шапке отвечают: жива ли система, есть ли пульс воркера, не включён ли стоп, включены ли агенты.",
        },
        queueStep,
        {
          tour: "overview-attention",
          title: "Внимание",
          text: "Если горит стоп или ждут решения агентов — баннер будет здесь. Пустой спокойный текст значит, что срочного нет.",
        },
        {
          tour: "overview-capital",
          title: "Капитал",
          text: "Три главные суммы paper-книги: стоимость счёта, свободный кэш и сейф. Подробности — в Портфеле.",
        },
        {
          tour: "overview-queue",
          title: "Очередь решений",
          text: "Здесь до трёх предложений со статусом «ждут решения». Агент сам не торгует.",
        },
        {
          tour: "overview-sleeves",
          title: "Рукава",
          text: "Короткое сравнение стратегий. Полная лента сигналов — в разделе «Стратегии».",
        },
        {
          tour: "nav-overview",
          title: "Меню слева",
          text: "Обзор — домашний экран. Дальше доступны портфель, стратегии, компании, рекомендации, агенты, новости, рынок, журнал, настройки и помощь.",
        },
      ]);
    }, 60);
  }

  function startMenuTour() {
    var steps = [
      {
        tour: "status-strip",
        title: "Статус контура",
        text: "Четыре пилла всегда на виду: система, воркер, торговля (стоп), агенты. Цвет и текст вместе: агенты выключены — янтарный, это не авария.",
      },
      {
        tour: "status-refresh",
        title: "Свежесть данных",
        text: "«Обновить» перечитывает статус. Внизу страницы видно, когда статус обновлялся в последний раз.",
      },
      {
        tour: lastStatus && lastStatus.killed ? "btn-unkill" : "btn-kill",
        title: "Стоп торговли",
        text: "Стоп запрещает новые ордера, но сам позиции не закрывает. И стоп, и снятие стопа — только после подтверждения в диалоге.",
      },
    ].concat(
      ROUTES.map(function (route) {
        return {
          route: route.id,
          tour: "nav-" + route.id,
          title: route.title,
          text: route.hint + ". " + route.intro,
        };
      })
    );
    runTour(MENU_TOUR_KEY, steps);
  }

  function maybeStartOverviewTour() {
    if (!authed || !window.CabinTour) return;
    if (CabinTour.wasSeen(OVERVIEW_TOUR_KEY)) return;
    window.setTimeout(function () {
      if (
        authed &&
        currentRoute === "overview" &&
        !CabinTour.isActive() &&
        !CabinTour.wasSeen(OVERVIEW_TOUR_KEY)
      ) {
        startOverviewTour();
      }
    }, 400);
  }

  function startPortfolioTour() {
    setHash("portfolio");
    portfolioTab = "capital";
    renderPortfolio();
    window.setTimeout(function () {
      var rows = ((lastStatus && lastStatus.portfolio) || {}).positions || [];
      if (!window.CabinTour) return;
      CabinTour.start({
        key: PORTFOLIO_TOUR_KEY,
        steps: [
          {
            tour: "portfolio-tabs",
            title: "Вкладки портфеля",
            text: "Портфель разбит на вкладки: капитал, позиции, сейф, аллокация, расхождение.",
            tab: "capital",
          },
          {
            tour: "portfolio-equity",
            title: "Стоимость счёта",
            text: "Главная сумма paper-книги: кэш + сейф + оценка позиций. Нажмите «?» рядом с подписью, чтобы увидеть короткую справку.",
            tab: "capital",
          },
          {
            tour: "portfolio-cash",
            title: "Свободный кэш",
            text: "Деньги, которые ещё не в позициях и не отложены в сейф.",
            tab: "capital",
          },
          {
            tour: "portfolio-disclaimer",
            title: "Это не брокерский UI",
            text: "Кабинет показывает лабораторную paper-книгу, а не баланс экрана Тинькофф Инвестиций.",
            tab: "capital",
          },
          {
            tour: "portfolio-positions",
            title: "Позиции",
            text: rows.length
              ? "Строка позиции: рукав, инструмент, количество, средняя цена, оценка и доля от стоимости счёта."
              : "Пустое состояние объясняется: нет входов или книга только с депозитом. Есть ссылка в «Стратегии».",
            tab: "positions",
          },
          {
            tour: rows.length
              ? "portfolio-positions-table"
              : "portfolio-positions-empty",
            title: rows.length ? "Как читать строку" : "Что делать, если пусто",
            text: rows.length
              ? "Оценка = количество × средняя цена. Доля считается от текущей стоимости счёта."
              : "Загляните в Стратегии → сигналы: там видно, принимала ли стратегия решения на дневках.",
            tab: "positions",
          },
          {
            tour: "portfolio-vault-rule",
            title: "Зачем сейф",
            text: "Сейф откладывает часть зафиксированной прибыли. Пока депозит не перекрыт — 50%, потом — 20%.",
            tab: "vault",
          },
          {
            tour: "portfolio-vault-phase",
            title: "Фаза 50 или 20",
            text: "Фаза меняется автоматически после перекрытия депозита. Прогресс-бар показывает, сколько уже накоплено относительно депозита.",
            tab: "vault",
          },
          {
            tour: "portfolio-vault-how",
            title: "Как считается",
            text: "Раскройте блок «Как считается», если нужна формула простыми словами. Нереализованная переоценка в сейф не идёт.",
            tab: "vault",
          },
          {
            tour: "portfolio-alloc-intro",
            title: "Аллокация",
            text: "Здесь видно, как капитал делится между рукавами: вес и капитал каждого рукава от стоимости счёта.",
            tab: "allocation",
          },
          {
            tour: lastAllocation && (lastAllocation.sleeves || []).length
              ? "portfolio-alloc-table"
              : "portfolio-alloc-empty",
            title: "Таблица рукавов",
            text: "Капитал рукава = equity × потолок × вес. Это лимит аллокатора, а не список открытых позиций.",
            tab: "allocation",
          },
          {
            tour: "portfolio-drift-intro",
            title: "Расхождение",
            text: "Сверка книги и sandbox. Пока кэш sandbox не введён, кабинет честно пишет, что сверка недоступна.",
            tab: "drift",
          },
          {
            tour:
              sandboxCashKnown === null || sandboxCashKnown === ""
                ? "portfolio-drift-empty"
                : "portfolio-drift-result",
            title:
              sandboxCashKnown === null || sandboxCashKnown === ""
                ? "Без sandbox нет сходимости"
                : "Результат сверки",
            text:
              sandboxCashKnown === null || sandboxCashKnown === ""
                ? "Не показываем нулевое расхождение «из вежливости». Введите кэш песочницы и нажмите «Сверить»."
                : "Расхождение = кэш книги − кэш песочницы. Алерт, если модуль больше порога.",
            tab: "drift",
          },
        ],
        onStep: function (step) {
          if (step.tab && portfolioTab !== step.tab) {
            portfolioTab = step.tab;
            renderPortfolio();
          }
          if (step.route && authed) setHash(step.route);
        },
      });
    }, 60);
  }

  function maybeStartPortfolioTour() {
    if (!authed || !window.CabinTour) return;
    if (CabinTour.wasSeen(PORTFOLIO_TOUR_KEY)) return;
    window.setTimeout(function () {
      if (
        authed &&
        currentRoute === "portfolio" &&
        !CabinTour.isActive() &&
        !CabinTour.wasSeen(PORTFOLIO_TOUR_KEY)
      ) {
        startPortfolioTour();
      }
    }, 400);
  }

  function newsTabsHtml() {
    var tabs = [
      { id: "feed", label: "Лента" },
      { id: "studies", label: "Исследования" },
    ];
    return (
      '<div class="tabs" role="tablist" aria-label="Разделы новостей" data-tour="news-tabs">' +
      tabs
        .map(function (tab) {
          return (
            '<button type="button" role="tab" id="news-tab-' +
            tab.id +
            '" aria-controls="news-panel" aria-selected="' +
            (newsTab === tab.id ? "true" : "false") +
            '" data-news-tab="' +
            tab.id +
            '"' +
            (newsTab === tab.id ? ' class="active"' : "") +
            ">" +
            tab.label +
            "</button>"
          );
        })
        .join("") +
      "</div>"
    );
  }

  function filterNewsRows(rows) {
    var ticker = String(newsFilterTicker || "")
      .trim()
      .toUpperCase();
    var q = String(newsSearch || "")
      .trim()
      .toLowerCase();
    return (rows || []).filter(function (row) {
      if (ticker) {
        var list = (row.tickers || []).map(function (t) {
          return String(t).toUpperCase();
        });
        if (list.indexOf(ticker) < 0) return false;
      }
      if (q && String(row.title || "").toLowerCase().indexOf(q) < 0) {
        return false;
      }
      return true;
    });
  }

  function newsEmptyHtml(total, filtered) {
    if (total === 0) {
      return (
        '<p class="empty" data-tour="news-empty">' +
        "Лента пуста. Запустите загрузку ленты или дождитесь воркера — новости сами сделки не открывают." +
        "</p>"
      );
    }
    if (filtered === 0) {
      return (
        '<p class="empty" data-tour="news-filtered">' +
        "Нет новостей по фильтру. Сбросьте тикер или поиск по заголовку." +
        "</p>"
      );
    }
    return "";
  }

  function renderNewsFeed() {
    var filtered = filterNewsRows(lastNews);
    var tickers = [];
    var seen = {};
    (lastNews || []).forEach(function (row) {
      (row.tickers || []).forEach(function (t) {
        var key = String(t).toUpperCase();
        if (key && !seen[key]) {
          seen[key] = true;
          tickers.push(key);
        }
      });
    });
    var list = "";
    if (filtered.length) {
      list =
        '<div class="news-list" data-tour="news-list">' +
        filtered
          .map(function (row) {
            var chips = (row.tickers || [])
              .map(function (t) {
                return (
                  '<button type="button" class="ticker-chip" data-news-ticker="' +
                  escapeHtml(String(t)) +
                  '">' +
                  escapeHtml(String(t)) +
                  "</button>"
                );
              })
              .join("");
            return (
              '<article class="news-item">' +
              '<div class="news-meta">' +
              "<span>" +
              formatSignalTime(row.ts) +
              "</span><span>" +
              escapeHtml(row.source || "—") +
              "</span></div>" +
              "<h4>" +
              escapeHtml(row.title || "Без заголовка") +
              "</h4>" +
              (chips ? '<div class="ticker-chips">' + chips + "</div>" : "") +
              (row.url
                ? '<a class="panel-link" href="' +
                  escapeHtml(row.url) +
                  '" target="_blank" rel="noopener noreferrer">открыть источник</a>'
                : "") +
              "</article>"
            );
          })
          .join("") +
        "</div>";
    } else if (loadErrors.news && !(lastNews || []).length) {
      list =
        blockErrorHtml("news") ||
        '<p class="empty" data-tour="news-empty">Лента не загрузилась — это не «0 новостей».</p>';
    } else {
      list = newsEmptyHtml((lastNews || []).length, filtered.length);
    }
    var feedBody = isBlockLoading("news")
      ? skeletonHtml(2)
      : blockErrorHtml("news") + list;
    if (loadErrors.news && !(lastNews || []).length && !isBlockLoading("news")) {
      feedBody = list;
    }
    return (
      '<section class="panel" data-tour="news-feed">' +
      "<h3>Лента</h3>" +
      "<p data-tour=\"news-disclaimer\">" +
      "Новости — внешний контур. Они не открывают сделки сами. Research считается offline и без подглядывания в будущее." +
      "</p>" +
      '<div class="filters" data-tour="news-filters">' +
      '<label class="field compact">тикер' +
      '<input type="text" id="news-filter-ticker" list="news-ticker-list" placeholder="SBER" value="' +
      escapeHtml(newsFilterTicker) +
      '">' +
      '<datalist id="news-ticker-list">' +
      tickers
        .map(function (t) {
          return '<option value="' + escapeHtml(t) + '">';
        })
        .join("") +
      "</datalist></label>" +
      '<label class="field compact">поиск' +
      '<input type="text" id="news-search" placeholder="по заголовку" value="' +
      escapeHtml(newsSearch) +
      '"></label>' +
      '<button type="button" class="ghost" id="news-filter-reset">Сбросить</button>' +
      "</div>" +
      feedBody +
      "</section>"
    );
  }

  function formatRetPct(value) {
    var n = Number(value);
    if (!isFinite(n)) return "—";
    var pct = (n * 100).toLocaleString("ru-RU", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });
    return (n > 0 ? "+" : "") + pct + "%";
  }

  function renderNewsStudies() {
    var rows = lastStudies || [];
    var body = "";
    if (rows.length) {
      body = wrapTableScroll(
        '<table class="data-table" data-tour="news-studies-table">' +
          "<thead><tr>" +
          "<th>тикер</th><th>новость</th><th>окно</th><th>результат</th><th></th>" +
          "</tr></thead><tbody>" +
          rows
            .map(function (row) {
              var title = row.title || "без заголовка";
              var windowLabel =
                "T−1…T+" +
                (row.horizon_n != null ? row.horizon_n : "?") +
                " · " +
                formatSignalTime(row.t_minus_ts) +
                " → " +
                formatSignalTime(row.t_plus_ts);
              return (
                "<tr>" +
                "<td>" +
                escapeHtml(row.ticker || "—") +
                "</td><td>" +
                escapeHtml(title) +
                "</td><td>" +
                escapeHtml(windowLabel) +
                "</td><td>" +
                escapeHtml(formatRetPct(row.ret)) +
                "</td><td>" +
                (row.news_url
                  ? '<a class="panel-link" href="' +
                    escapeHtml(row.news_url) +
                    '" target="_blank" rel="noopener noreferrer">новость</a>'
                  : "—") +
                "</td></tr>"
              );
            })
            .join("") +
          "</tbody></table>",
        true
      );
    } else if (isBlockLoading("studies")) {
      body = skeletonHtml(2);
    } else if (loadErrors.studies) {
      body =
        blockErrorHtml("studies") ||
        '<p class="empty" data-tour="news-studies-empty">Исследования не загрузились.</p>';
    } else {
      body =
        '<p class="empty" data-tour="news-studies-empty">' +
        "Ещё не считалось. Research пишется offline по свечам после новости — это не сигнал «покупай»." +
        "</p>";
    }
    return (
      '<section class="panel" data-tour="news-studies">' +
      "<h3>Исследования</h3>" +
      "<p data-tour=\"news-lookahead\">" +
      "Считаем доходность в окне T−1…T+N по уже закрытым дневкам. " +
      "Lookahead запрещён: в расчёт не подглядывают цены «из будущего» относительно новости. " +
      "Строка research — наблюдение, не торговый приказ." +
      "</p>" +
      body +
      "</section>"
    );
  }

  function bindNewsControls() {
    byId("page-body")
      .querySelectorAll("[data-news-tab]")
      .forEach(function (btn) {
        btn.addEventListener("click", function () {
          newsTab = btn.getAttribute("data-news-tab") || "feed";
          setRouteTab("news", newsTab);
        });
      });
    var tickerInput = byId("news-filter-ticker");
    var searchInput = byId("news-search");
    var resetBtn = byId("news-filter-reset");
    function apply() {
      newsFilterTicker = tickerInput ? tickerInput.value : "";
      newsSearch = searchInput ? searchInput.value : "";
      renderNews();
    }
    if (tickerInput) {
      tickerInput.addEventListener("change", apply);
      tickerInput.addEventListener("keydown", function (event) {
        if (event.key === "Enter") apply();
      });
    }
    if (searchInput) {
      searchInput.addEventListener("input", apply);
    }
    if (resetBtn) {
      resetBtn.addEventListener("click", function () {
        newsFilterTicker = "";
        newsSearch = "";
        renderNews();
      });
    }
    byId("page-body")
      .querySelectorAll("[data-news-ticker]")
      .forEach(function (chip) {
        chip.addEventListener("click", function () {
          newsFilterTicker = chip.getAttribute("data-news-ticker") || "";
          newsTab = "feed";
          renderNews();
        });
      });
  }

  function renderNews() {
    var body = byId("page-body");
    var content =
      newsTab === "studies" ? renderNewsStudies() : renderNewsFeed();
    body.innerHTML =
      newsTabsHtml() +
      '<div id="news-panel" role="tabpanel" aria-labelledby="news-tab-' +
      newsTab +
      '">' +
      content +
      "</div>";
    bindNewsControls();
  }

  function refreshNews() {
    setBlockLoading("news", true);
    setBlockLoading("studies", true);
    if (currentRoute === "news") renderNews();
    return Promise.all([
      apiGet("/news")
        .then(function (data) {
          clearLoadError("news");
          return data;
        })
        .catch(function (err) {
          setLoadError("news", err);
          return { news: lastNews };
        })
        .finally(function () {
          setBlockLoading("news", false);
        }),
      apiGet("/news/studies")
        .then(function (data) {
          clearLoadError("studies");
          return data;
        })
        .catch(function (err) {
          setLoadError("studies", err);
          return { studies: lastStudies };
        })
        .finally(function () {
          setBlockLoading("studies", false);
        }),
    ]).then(function (parts) {
      if (parts[0] && parts[0].news) lastNews = parts[0].news;
      if (parts[1] && parts[1].studies) lastStudies = parts[1].studies;
      if (currentRoute === "news") renderNews();
      return parts;
    });
  }

  function marketTabsHtml() {
    var tabs = [
      { id: "universe", label: "Вселенная" },
      { id: "rules", label: "Правила риска" },
    ];
    return (
      '<div class="tabs" role="tablist" aria-label="Разделы рынка" data-tour="market-tabs">' +
      tabs
        .map(function (tab) {
          return (
            '<button type="button" role="tab" id="market-tab-' +
            tab.id +
            '" aria-controls="market-panel" aria-selected="' +
            (marketTab === tab.id ? "true" : "false") +
            '" data-market-tab="' +
            tab.id +
            '"' +
            (marketTab === tab.id ? ' class="active"' : "") +
            ">" +
            tab.label +
            "</button>"
          );
        })
        .join("") +
      "</div>"
    );
  }

  function universeReasonLabel(code) {
    var key = String(code || "");
    if (UNIVERSE_REASON_RU[key]) return UNIVERSE_REASON_RU[key];
    return key ? "причина: " + key : "—";
  }

  function renderMarketUniverse() {
    var data = lastUniverse || { members: [], count: 0, limit: 30 };
    var members = data.members || [];
    var count = data.count != null ? data.count : members.filter(function (row) {
      return row.active;
    }).length;
    var limit = data.limit != null ? data.limit : 30;
    var table = "";
    if (members.length) {
      table = wrapTableScroll(
        '<table class="data-table" data-tour="market-universe-table">' +
          "<thead><tr>" +
          "<th>тикер</th><th>статус</th><th>причина</th><th>обновлено</th>" +
          "</tr></thead><tbody>" +
          members
            .map(function (row) {
              return (
                "<tr>" +
                "<td>" +
                escapeHtml(row.ticker || shortId(row.instrument_id)) +
                "</td><td>" +
                escapeHtml(row.active ? "активна" : "неактивна") +
                "</td><td>" +
                escapeHtml(universeReasonLabel(row.reason)) +
                "</td><td>" +
                formatSignalTime(row.updated_at) +
                "</td></tr>"
              );
            })
            .join("") +
          "</tbody></table>",
        true
      );
    } else {
      table =
        '<p class="empty" data-tour="market-universe-empty">' +
        "Состав ещё не наполнен ситом. Пока вселенная пуста, входы будут отклоняться. " +
        "Запустите воркер/сито или проверьте инструменты." +
        "</p>";
    }
    return (
      '<section class="panel" data-tour="market-universe">' +
      "<h3>Вселенная</h3>" +
      "<p data-tour=\"market-universe-summary\">" +
      "В вселенной " +
      escapeHtml(String(count)) +
      " бумаг (лимит " +
      escapeHtml(String(limit)) +
      "). Только активные тикеры проходят риск-ворота «тикер в вселенной»." +
      "</p>" +
      table +
      "</section>"
    );
  }

  function marketRiskRules() {
    var killed = !!(lastStatus && lastStatus.killed);
    return [
      {
        id: "kill",
        title: "Стоп торговли",
        why: "Аварийный рубильник лаборатории: новые ордера не уходят, пока стоп включён.",
        reject: "В Журнале: «Отклонено: включён стоп торговли» (код killed).",
        live: killed
          ? "сейчас: стоп включён · новые ордера нельзя"
          : "сейчас: стоп выключен · можно выставлять",
        liveTone: killed ? "bad" : "ok",
        actions: true,
      },
      {
        id: "universe",
        title: "Тикер в вселенной",
        why: "Торгуем только бумаги из активного периметра сита.",
        reject:
          "В Журнале: «Отклонено: тикера нет в активной вселенной» (outside_universe).",
      },
      {
        id: "name",
        title: "Доля бумаги",
        why: "Одна позиция не должна съесть слишком большую долю счёта.",
        reject:
          "В Журнале: «Отклонено: слишком большая доля одной бумаги» (name_weight).",
      },
      {
        id: "sleeve",
        title: "Доля рукава",
        why: "Каждый рукав ограничен долей капитала — стратегии не раздуваются без меры.",
        reject:
          "В Журнале: «Отклонено: превышен лимит капитала рукава» (sleeve_weight).",
      },
      {
        id: "daily",
        title: "Дневной убыток",
        why: "Если день уже плохой, новые входы режутся, чтобы не усугублять просадку.",
        reject:
          "В Журнале: «Отклонено: сработал дневной лимит убытка» (daily_loss).",
      },
      {
        id: "once",
        title: "Один вход на бар",
        why: "На одном дневном баре по тикеру не копим повторные входы.",
        reject:
          "В Журнале: «Отклонено: повторный вход в тот же бар» (already_entered).",
      },
      {
        id: "earnings",
        title: "День отчёта",
        why: "В день отчётности эмитента лаборатория ставит veto на входы.",
        reject:
          "В Журнале: «Отклонено: день отчёта эмитента» (earnings_day).",
      },
    ];
  }

  function renderMarketRules() {
    var rules = marketRiskRules();
    var cards = rules
      .map(function (rule) {
        var live = "";
        if (rule.live) {
          live =
            '<p class="rule-live"><span class="dot ' +
            (rule.liveTone || "ok") +
            '"></span>' +
            escapeHtml(rule.live) +
            "</p>";
        }
        var actions = "";
        if (rule.actions) {
          var killed = !!(lastStatus && lastStatus.killed);
          actions =
            '<div class="proposal-actions" data-tour="market-kill-actions">' +
            (killed
              ? '<button type="button" class="primary" id="market-unkill">Снять стоп…</button>'
              : '<button type="button" class="danger" id="market-kill">Стоп торговлю…</button>') +
            '<a class="panel-link" href="#/journal?tab=orders">где увидите отказ → Журнал</a>' +
            "</div>";
        }
        return (
          '<article class="rule-card" data-tour="market-rule-' +
          escapeHtml(rule.id) +
          '">' +
          "<h4>" +
          escapeHtml(rule.title) +
          "</h4>" +
          live +
          "<p><strong>Зачем:</strong> " +
          escapeHtml(rule.why) +
          "</p>" +
          "<p><strong>Что увидите при отказе:</strong> " +
          escapeHtml(rule.reject) +
          "</p>" +
          actions +
          "</article>"
        );
      })
      .join("");
    return (
      '<section class="panel" data-tour="market-rules">' +
      "<h3>Правила риска</h3>" +
      "<p data-tour=\"market-rules-intro\">" +
      "Семь ворот до сделки. Читайте заранее — не простыня кодекса, а короткие карточки. Отказы появятся в Журнале." +
      "</p>" +
      '<div class="rule-grid">' +
      cards +
      "</div></section>"
    );
  }

  function bindMarketRules() {
    var killBtn = byId("market-kill");
    var unkillBtn = byId("market-unkill");
    if (killBtn) {
      killBtn.addEventListener("click", function () {
        requestKill(true).then(function () {
          if (currentRoute === "market") renderMarket();
        });
      });
    }
    if (unkillBtn) {
      unkillBtn.addEventListener("click", function () {
        requestKill(false).then(function () {
          if (currentRoute === "market") renderMarket();
        });
      });
    }
  }

  function renderMarket() {
    var body = byId("page-body");
    var content =
      marketTab === "rules" ? renderMarketRules() : renderMarketUniverse();
    body.innerHTML =
      marketTabsHtml() +
      '<div id="market-panel" role="tabpanel" aria-labelledby="market-tab-' +
      marketTab +
      '">' +
      content +
      "</div>";
    body.querySelectorAll("[data-market-tab]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        marketTab = btn.getAttribute("data-market-tab") || "universe";
        setRouteTab("market", marketTab);
      });
    });
    if (marketTab === "rules") bindMarketRules();
  }

  function refreshMarket() {
    return Promise.all([
      apiGet("/universe").catch(function () {
        return lastUniverse;
      }),
      refreshStatus().catch(function () {
        return lastStatus;
      }),
    ]).then(function (parts) {
      if (parts[0]) lastUniverse = parts[0];
      if (currentRoute === "market") renderMarket();
      return parts;
    });
  }

  function journalTabsHtml() {
    var tabs = [
      { id: "orders", label: "Ордера" },
      { id: "ledger", label: "Проводки" },
      { id: "audit", label: "Сквозной журнал" },
    ];
    return (
      '<div class="tabs" role="tablist" aria-label="Разделы журнала" data-tour="journal-tabs">' +
      tabs
        .map(function (tab) {
          return (
            '<button type="button" role="tab" id="journal-tab-' +
            tab.id +
            '" aria-controls="journal-panel" aria-selected="' +
            (journalTab === tab.id ? "true" : "false") +
            '" data-journal-tab="' +
            tab.id +
            '"' +
            (journalTab === tab.id ? ' class="active"' : "") +
            ">" +
            tab.label +
            "</button>"
          );
        })
        .join("") +
      "</div>"
    );
  }

  function filterOrders(rows) {
    var status = String(orderFilterStatus || "");
    var sleeve = String(orderFilterSleeve || "");
    var ticker = String(orderFilterTicker || "")
      .trim()
      .toUpperCase();
    return (rows || []).filter(function (row) {
      if (status && String(row.status || "") !== status) return false;
      if (sleeve && String(row.sleeve || "") !== sleeve) return false;
      if (ticker && String(row.ticker || "").toUpperCase().indexOf(ticker) < 0) {
        return false;
      }
      return true;
    });
  }

  function orderRejectFromRow(row) {
    if (row.reject_reason) return row.reject_reason;
    if (row.raw && row.raw.reject_reason) return row.raw.reject_reason;
    return "";
  }

  function renderRiskChecks(row) {
    var checks = (row.raw && row.raw.risk_checks) || [];
    if (!checks.length) return "—";
    var allowed = checks.filter(function (check) {
      return check.outcome === "allow";
    }).length;
    var items = checks
      .map(function (check) {
        var explanation = check.reason
          ? ": " + riskReasonLabel(check.reason)
          : "";
        return (
          "<li><code>" +
          escapeHtml(check.code || "check") +
          "</code> — " +
          escapeHtml(check.outcome === "deny" ? "запрет" : "разрешено") +
          escapeHtml(explanation) +
          "</li>"
        );
      })
      .join("");
    return (
      "<details><summary>" +
      escapeHtml(String(allowed) + "/" + String(checks.length)) +
      "</summary><ul class=\"risk-check-list\">" +
      items +
      "</ul></details>"
    );
  }

  function renderJournalOrders() {
    var filtered = filterOrders(lastOrders);
    var statuses = [];
    var sleeves = [];
    var seenS = {};
    var seenV = {};
    (lastOrders || []).forEach(function (row) {
      if (row.status && !seenS[row.status]) {
        seenS[row.status] = true;
        statuses.push(row.status);
      }
      if (row.sleeve && !seenV[row.sleeve]) {
        seenV[row.sleeve] = true;
        sleeves.push(row.sleeve);
      }
    });
    var table = "";
    if (filtered.length) {
      table = wrapTableScroll(
        '<table class="data-table" data-tour="journal-orders-table">' +
          "<thead><tr>" +
          "<th>тикер</th><th>время</th><th>сторона</th><th>кол-во</th>" +
          "<th>статус</th><th>причина</th><th>проверки</th><th>рукав</th>" +
          "</tr></thead><tbody>" +
          filtered
            .map(function (row) {
              var reason = orderRejectFromRow(row);
              var reasonText =
                row.status === "rejected" || reason
                  ? orderRejectLabel(reason || "—")
                  : "—";
              if (reasonText === "Отклонено: —") reasonText = "—";
              return (
                "<tr>" +
                "<td>" +
                escapeHtml(row.ticker || "—") +
                "</td><td>" +
                formatSignalTime(row.created_at) +
                "</td><td>" +
                escapeHtml(orderSideLabel(row.side)) +
                "</td><td>" +
                escapeHtml(String(row.qty != null ? row.qty : "—")) +
                "</td><td>" +
                escapeHtml(orderStatusLabel(row.status)) +
                "</td><td>" +
                escapeHtml(reasonText) +
                "</td><td>" +
                renderRiskChecks(row) +
                "</td><td>" +
                escapeHtml(SLEEVE_NAMES[row.sleeve] || row.sleeve || "—") +
                "</td></tr>"
              );
            })
            .join("") +
          "</tbody></table>",
        true
      );
    } else if (loadErrors.orders && !(lastOrders || []).length) {
      table =
        '<p class="empty" data-tour="journal-orders-empty">Список ордеров не загрузился — это не «0 ордеров».</p>';
    } else if (!(lastOrders || []).length) {
      table =
        '<p class="empty" data-tour="journal-orders-empty">' +
        "Ордеров ещё нет. Когда риск отклонит вход или сделка пройдёт, строка появится здесь." +
        "</p>";
    } else {
      table =
        '<p class="empty">Нет ордеров по выбранным фильтрам. Сбросьте статус, рукав или тикер.</p>';
    }
    return (
      '<section class="panel" data-tour="journal-orders">' +
      "<h3>Ордера</h3>" +
      "<p data-tour=\"journal-orders-intro\">" +
      "Факт лабораторных заявок. Отказы риска показываются русской фразой — не сырым <code>reject_reason: killed</code>." +
      "</p>" +
      blockErrorHtml("orders") +
      '<div class="filters" data-tour="journal-orders-filters">' +
      '<label class="field compact">статус<select id="order-filter-status">' +
      '<option value="">все</option>' +
      statuses
        .map(function (s) {
          return (
            '<option value="' +
            escapeHtml(s) +
            '"' +
            (orderFilterStatus === s ? " selected" : "") +
            ">" +
            escapeHtml(orderStatusLabel(s)) +
            "</option>"
          );
        })
        .join("") +
      "</select></label>" +
      '<label class="field compact">рукав<select id="order-filter-sleeve">' +
      '<option value="">все</option>' +
      sleeves
        .map(function (s) {
          return (
            '<option value="' +
            escapeHtml(s) +
            '"' +
            (orderFilterSleeve === s ? " selected" : "") +
            ">" +
            escapeHtml(SLEEVE_NAMES[s] || s) +
            "</option>"
          );
        })
        .join("") +
      "</select></label>" +
      '<label class="field compact">тикер' +
      '<input type="text" id="order-filter-ticker" placeholder="SBER" value="' +
      escapeHtml(orderFilterTicker) +
      '"></label>' +
      '<button type="button" class="ghost" id="order-filter-reset">Сбросить</button>' +
      "</div>" +
      table +
      "</section>"
    );
  }

  function ledgerAccountLabel(kind) {
    var key = String(kind || "");
    return LEDGER_ACCOUNT_RU[key] || (key ? "счёт: " + key : "—");
  }

  function ledgerReasonLabel(reason) {
    var key = String(reason || "");
    return LEDGER_REASON_RU[key] || key || "—";
  }

  function renderJournalLedger() {
    var rows = lastLedger || [];
    var depositRows = rows.filter(function (row) {
      return row.reason === "deposit";
    });
    var table = "";
    if (rows.length) {
      table = wrapTableScroll(
        '<table class="data-table" data-tour="journal-ledger-table">' +
          "<thead><tr>" +
          "<th>время</th><th>счёт</th><th>сумма</th><th>причина</th><th>ссылка</th>" +
          "</tr></thead><tbody>" +
          rows
            .map(function (row) {
              var isDeposit = row.reason === "deposit";
              return (
                "<tr" +
                (isDeposit
                  ? ' class="is-deposit" data-tour="journal-deposit-row"'
                  : "") +
                ">" +
                "<td>" +
                formatSignalTime(row.ts) +
                "</td><td>" +
                escapeHtml(ledgerAccountLabel(row.account_kind)) +
                "</td><td>" +
                money(row.amount) +
                "</td><td>" +
                escapeHtml(ledgerReasonLabel(row.reason)) +
                "</td><td>" +
                escapeHtml(row.ref || "—") +
                "</td></tr>"
              );
            })
            .join("") +
          "</tbody></table>"
      );
    } else if (loadErrors.ledger) {
      table =
        blockErrorHtml("ledger") ||
        '<p class="empty">Проводки не загрузились — это не означает, что денежных событий нет.</p>';
    } else {
      table =
        '<p class="empty" data-tour="journal-ledger-empty">' +
        "Проводок ещё нет. После стартового депозита здесь появится пополнение торгового кэша." +
        "</p>";
    }
    var depositHint = depositRows.length
      ? '<p class="source-line" data-tour="journal-deposit-hint">' +
        "Стартовый депозит → торговый кэш: найдите строки с причиной «депозит» (подсвечены). " +
        "Свободный кэш смотрите в <a class=\"panel-link\" href=\"#/portfolio\">Портфеле</a>." +
        "</p>"
      : '<p class="source-line" data-tour="journal-deposit-hint">' +
        "Связь: депозит пополняет торговый кэш. Когда депозит появится, строка будет подсвечена." +
        "</p>";
    return (
      '<section class="panel" data-tour="journal-ledger">' +
      "<h3>Проводки</h3>" +
      "<p data-tour=\"journal-ledger-intro\">" +
      "Денежная история paper-книги. Счета и причины по-русски — без сырого account_kind." +
      "</p>" +
      depositHint +
      table +
      "</section>"
    );
  }

  function renderJournalAudit() {
    var audit = lastAudit || {};
    var auditRows = (audit.events || []).map(function (row) {
      return Object.assign({ lane: "АУДИТ", timeline_at: row.occurred_at }, row);
    });
    var orderRows = (lastOrders || []).map(function (row) {
      return {
        lane: "ОРДЕР",
        timeline_at: row.created_at,
        event_type:
          orderSideLabel(row.side) + " · " + orderStatusLabel(row.status),
        entity_type: row.sleeve || "order",
        entity_id: row.ticker || row.id,
        payload: row.raw || row,
      };
    });
    var ledgerRows = (lastLedger || []).map(function (row) {
      return {
        lane: "ПРОВОДКА",
        timeline_at: row.ts,
        event_type: ledgerReasonLabel(row.reason),
        entity_type: ledgerAccountLabel(row.account_kind),
        entity_id: row.ref || row.id,
        payload: row,
      };
    });
    var rows = auditRows
      .concat(orderRows, ledgerRows)
      .sort(function (a, b) {
        return new Date(a.timeline_at).getTime() - new Date(b.timeline_at).getTime();
      });
    var chainOk = audit.chain_valid === true;
    var events = rows
      .slice()
      .reverse()
      .map(function (row, index) {
        return (
          '<article class="audit-event">' +
          '<div class="audit-event__rail"><span>' +
          escapeHtml(String(rows.length - index).padStart(2, "0")) +
          "</span></div>" +
          '<div class="audit-event__body"><div class="audit-event__head"><strong>' +
          '<span class="audit-lane">' +
          escapeHtml(row.lane) +
          "</span> " +
          escapeHtml(row.event_type || "событие") +
          '</strong><time>' +
          formatSignalTime(row.timeline_at) +
          "</time></div>" +
          '<p><span class="section-kicker">' +
          escapeHtml(row.entity_type || "объект") +
          "</span> " +
          escapeHtml(row.entity_id || "—") +
          "</p>" +
          (row.lane === "АУДИТ"
            ? '<div class="audit-hashes"><code>предыдущий ' +
              escapeHtml(shortId(row.previous_hash)) +
              '</code><code>хеш ' +
              escapeHtml(shortId(row.event_hash)) +
              "</code></div>"
            : "") +
          '<details class="fold tight"><summary>Данные события</summary><pre class="payload">' +
          escapeHtml(JSON.stringify(row.payload || {}, null, 2)) +
          "</pre></details></div></article>"
        );
      })
      .join("");
    return (
      '<section class="panel" data-tour="journal-audit">' +
      '<div class="audit-title"><div><span class="section-kicker">НЕИЗМЕНЯЕМАЯ ИСТОРИЯ</span><h3>Сквозной журнал</h3></div>' +
      '<span class="qualification ' +
      (chainOk ? "is-qualified" : "is-rejected") +
      '">' +
      (chainOk ? "ЦЕПОЧКА ЦЕЛА" : "ЦЕПОЧКА НАРУШЕНА") +
      "</span></div>" +
      "<p>Ордера, проводки и неизменяемые события на одной временной оси. События связаны хешами; исправления выполняются компенсирующими проводками.</p>" +
      (events
        ? '<div class="audit-timeline">' + events + "</div>"
        : '<p class="empty">Событий аудита пока нет.</p>') +
      "</section>"
    );
  }

  function bindJournalControls() {
    byId("page-body")
      .querySelectorAll("[data-journal-tab]")
      .forEach(function (btn) {
        btn.addEventListener("click", function () {
          journalTab = btn.getAttribute("data-journal-tab") || "orders";
          setRouteTab("journal", journalTab);
        });
      });
    var statusEl = byId("order-filter-status");
    var sleeveEl = byId("order-filter-sleeve");
    var tickerEl = byId("order-filter-ticker");
    var resetBtn = byId("order-filter-reset");
    function apply() {
      orderFilterStatus = statusEl ? statusEl.value : "";
      orderFilterSleeve = sleeveEl ? sleeveEl.value : "";
      orderFilterTicker = tickerEl ? tickerEl.value : "";
      renderJournal();
    }
    if (statusEl) statusEl.addEventListener("change", apply);
    if (sleeveEl) sleeveEl.addEventListener("change", apply);
    if (tickerEl) {
      tickerEl.addEventListener("change", apply);
      tickerEl.addEventListener("keydown", function (event) {
        if (event.key === "Enter") apply();
      });
    }
    if (resetBtn) {
      resetBtn.addEventListener("click", function () {
        orderFilterStatus = "";
        orderFilterSleeve = "";
        orderFilterTicker = "";
        renderJournal();
      });
    }
  }

  function renderJournal() {
    var body = byId("page-body");
    var content =
      journalTab === "ledger"
        ? renderJournalLedger()
        : journalTab === "audit"
          ? renderJournalAudit()
          : renderJournalOrders();
    body.innerHTML =
      journalTabsHtml() +
      '<div id="journal-panel" role="tabpanel" aria-labelledby="journal-tab-' +
      journalTab +
      '">' +
      content +
      "</div>";
    bindJournalControls();
  }

  function refreshJournal() {
    routeLoading = true;
    if (currentRoute === "journal") {
      byId("page-body").innerHTML =
        journalTabsHtml() +
        '<div id="journal-panel" role="tabpanel" aria-labelledby="journal-tab-' +
        journalTab +
        '">' +
        skeletonHtml(3) +
        "</div>";
    }
    return Promise.all([
      apiGet("/orders")
        .then(function (data) {
          clearLoadError("orders");
          return data;
        })
        .catch(function (err) {
          setLoadError("orders", err);
          return { orders: lastOrders };
        }),
      apiGet("/ledger")
        .then(function (data) {
          clearLoadError("ledger");
          return data;
        })
        .catch(function (err) {
          setLoadError("ledger", err);
          return { entries: lastLedger };
        }),
      apiGet("/audit/timeline").catch(function () {
        return lastAudit;
      }),
    ]).then(function (parts) {
      if (parts[0] && parts[0].orders) lastOrders = parts[0].orders;
      if (parts[1] && parts[1].entries) lastLedger = parts[1].entries;
      if (parts[2]) lastAudit = parts[2];
      routeLoading = false;
      if (currentRoute === "journal") renderJournal();
      return parts;
    });
  }

  function startJournalTour() {
    setHash("journal");
    journalTab = "orders";
    renderJournal();
    window.setTimeout(function () {
      if (!window.CabinTour) return;
      var hasOrders = (lastOrders || []).length > 0;
      var hasDeposit = (lastLedger || []).some(function (row) {
        return row.reason === "deposit";
      });
      CabinTour.start({
        key: JOURNAL_TOUR_KEY,
        steps: [
          {
            tour: "journal-orders-intro",
            title: "Ордер vs проводка",
            text: "Ордера — заявки и отказы риска. Проводки — денежные движения книги (депозит, сделки, сейф).",
          },
          {
            tour: hasOrders ? "journal-orders-table" : "journal-orders-empty",
            title: "Где искать отказ",
            text: hasOrders
              ? "В колонке «причина» русская фраза, не сырой reject_reason: killed."
              : "Когда риск режет вход, строка появится здесь с понятной причиной.",
          },
          {
            tour: "journal-ledger-intro",
            title: "Проводки и депозит",
            text: "На вкладке «Проводки» ищите причину «депозит» — это стартовое пополнение торгового кэша.",
            onBefore: function () {
              journalTab = "ledger";
              renderJournal();
            },
          },
          {
            tour: hasDeposit
              ? "journal-deposit-row"
              : "journal-deposit-hint",
            title: "Связь с Портфелем",
            text: hasDeposit
              ? "Подсвеченная строка депозита → торговый кэш. Свободный кэш смотрите в Портфеле."
              : "Когда депозит появится, строка будет подсвечена. Кэш — в Портфеле.",
            onBefore: function () {
              journalTab = "ledger";
              renderJournal();
            },
          },
        ],
        onStep: function (step) {
          if (step.onBefore) step.onBefore();
        },
      });
    }, 60);
  }

  function maybeStartJournalTour() {
    if (!authed || !window.CabinTour) return;
    if (CabinTour.wasSeen(JOURNAL_TOUR_KEY)) return;
    window.setTimeout(function () {
      if (
        authed &&
        currentRoute === "journal" &&
        !CabinTour.isActive() &&
        !CabinTour.wasSeen(JOURNAL_TOUR_KEY)
      ) {
        startJournalTour();
      }
    }, 400);
  }

  function startMarketTour() {
    setHash("market");
    marketTab = "universe";
    renderMarket();
    window.setTimeout(function () {
      if (!window.CabinTour) return;
      var hasRows =
        lastUniverse && lastUniverse.members && lastUniverse.members.length;
      CabinTour.start({
        key: MARKET_TOUR_KEY,
        steps: [
          {
            tour: "market-universe-summary",
            title: "Периметр бумаг",
            text: "Сводка показывает, сколько тикеров активно и какой лимит UNIVERSE_MAX.",
          },
          {
            tour: hasRows ? "market-universe-table" : "market-universe-empty",
            title: hasRows ? "Таблица вселенной" : "Пустая вселенная",
            text: hasRows
              ? "Причины на русском: почему бумага в сите или выпала."
              : "Пока сито не наполнило состав, входы будут отклоняться — это ожидаемо.",
          },
          {
            tour: "market-rule-kill",
            title: "Стоп торговли",
            text: "Первая карточка правил — live-статус стопа и кнопки управления. Отказ увидите в Журнале.",
            onBefore: function () {
              marketTab = "rules";
              renderMarket();
            },
          },
          {
            tour: "market-rules-intro",
            title: "Почему ордер режут",
            text: "Ещё шесть карточек: вселенная, доли, дневной убыток, один вход, день отчёта. Не копипаста бэкенд-ТЗ.",
            onBefore: function () {
              marketTab = "rules";
              renderMarket();
            },
          },
        ],
        onStep: function (step) {
          if (step.onBefore) step.onBefore();
        },
      });
    }, 60);
  }

  function maybeStartMarketTour() {
    if (!authed || !window.CabinTour) return;
    if (CabinTour.wasSeen(MARKET_TOUR_KEY)) return;
    window.setTimeout(function () {
      if (
        authed &&
        currentRoute === "market" &&
        !CabinTour.isActive() &&
        !CabinTour.wasSeen(MARKET_TOUR_KEY)
      ) {
        startMarketTour();
      }
    }, 400);
  }

  function startNewsTour() {
    setHash("news");
    newsTab = "feed";
    renderNews();
    window.setTimeout(function () {
      if (!window.CabinTour) return;
      CabinTour.start({
        key: NEWS_TOUR_KEY,
        steps: [
          {
            tour: "news-disclaimer",
            title: "Лента ≠ торговые сигналы",
            text: "Новости не открывают сделки сами. Это внешний информационный контур лаборатории.",
          },
          {
            tour: "news-filters",
            title: "Тикеры и поиск",
            text: "Фильтр по тикеру и поиск по заголовку. Чип тикера в карточке тоже ставит фильтр.",
          },
          {
            tour: "news-tabs",
            title: "Вкладка research",
            text: "«Исследования» — offline-окна доходности по новости. Это не кнопка «покупай».",
            onBefore: function () {
              newsTab = "studies";
              renderNews();
            },
          },
          {
            tour: "news-lookahead",
            title: "Без lookahead",
            text: "Считаем только по уже закрытым дневкам вокруг новости. В будущее относительно события не подглядывают.",
            onBefore: function () {
              newsTab = "studies";
              renderNews();
            },
          },
        ],
        onStep: function (step) {
          if (step.onBefore) step.onBefore();
          if (step.route && authed) setHash(step.route);
        },
      });
    }, 60);
  }

  function maybeStartNewsTour() {
    if (!authed || !window.CabinTour) return;
    if (CabinTour.wasSeen(NEWS_TOUR_KEY)) return;
    window.setTimeout(function () {
      if (
        authed &&
        currentRoute === "news" &&
        !CabinTour.isActive() &&
        !CabinTour.wasSeen(NEWS_TOUR_KEY)
      ) {
        startNewsTour();
      }
    }, 400);
  }

  function startAgentsTour() {
    setHash("agents");
    window.setTimeout(function () {
      if (!window.CabinTour) return;
      var hasCard = proposedList(lastProposals).length > 0;
      CabinTour.start({
        key: AGENTS_TOUR_KEY,
        steps: [
          {
            tour: "agents-banner",
            title: "Агент не торгует сам",
            text: "Баннер показывает, включены ли агенты. Выключены — это нормально, не авария и не «система упала».",
          },
          {
            tour: "agents-waiting",
            title: "Очередь решений",
            text: "Сверху — предложения со статусом «ждёт решения». Сортировка: proposed первыми.",
          },
          {
            tour: hasCard ? "agents-card" : "agents-waiting-empty",
            title: hasCard ? "Карточка без сырых данных" : "Пустая очередь",
            text: hasCard
              ? "Сначала человеческое описание и статус. Сырые детали только под «Подробнее». Принять/Отклонить — с подтверждением."
              : "Пустая очередь при выключенных агентах — ожидаемо. Когда появятся предложения, здесь будут крупные карточки.",
          },
          {
            tour: hasCard ? "agents-actions" : "agents-recent-panel",
            title: hasCard ? "Принять и риск" : "Где смотреть итог",
            text: hasCard
              ? "Если вы приняли, а риск отклонил ордер — кабинет скажет это явно. Успех approve не маскирует отказ риска."
              : "Недавние решения — ниже. Факт ордеров и проводок — в Журнале.",
          },
        ],
      });
    }, 60);
  }

  function maybeStartAgentsTour() {
    if (!authed || !window.CabinTour) return;
    if (CabinTour.wasSeen(AGENTS_TOUR_KEY)) return;
    window.setTimeout(function () {
      if (
        authed &&
        currentRoute === "agents" &&
        !CabinTour.isActive() &&
        !CabinTour.wasSeen(AGENTS_TOUR_KEY)
      ) {
        startAgentsTour();
      }
    }, 400);
  }

  function startStrategiesTour() {
    setHash("strategies");
    window.setTimeout(function () {
      if (!window.CabinTour) return;
      CabinTour.start({
        key: STRATEGIES_TOUR_KEY,
        steps: [
          {
            tour: "strategies-intro",
            title: "Что такое рукав",
            text: "Рукав — отдельная стратегия. Четыре активных: SMA, Дончиан, RSI (дневки) и EMA-скальп (M15).",
          },
          {
            tour: "strategies-table",
            title: "Как читать PnL",
            text: "Колонки: зафиксировано, на бумаге, итог. Код рукава вторичен — ориентируйтесь на название.",
          },
          {
            tour: "strategies-row-sma_cross",
            title: "Открыть карточку",
            text: "Клик по строке или «открыть» ведёт в карточку: PnL, «как устроен» и лента сигналов.",
          },
          {
            tour: "strategies-row-donchian_breakout",
            title: "Дончиан",
            text: "Пробой Дончиана — второй дневной рукав, тот же маршрут /sleeves/{name}.",
          },
          {
            tour: "strategies-row-rsi_reversion",
            title: "RSI-возврат",
            text: "Mean-reversion по RSI(14): покупка в перепроданности, продажа в перекупленности.",
          },
          {
            tour: "strategies-row-ema_scalp",
            title: "Скальп M15",
            text: "EMA-скальп — короткий горизонт. Для прогона нужны CSV в data/candles_m15.",
          },
        ],
      });
    }, 60);
  }

  function startStrategiesCardTour() {
    var sleeveId = strategiesSleeveFromHash() || "sma_cross";
    setHash("strategies/" + sleeveId);
    window.setTimeout(function () {
      if (!window.CabinTour) return;
      CabinTour.start({
        key: STRATEGIES_TOUR_KEY + "-card",
        steps: [
          {
            tour: "strategies-card-title",
            title: "Карточка рукава",
            text: "Здесь деталка выбранного рукава. Все рукава открываются одинаково.",
          },
          {
            tour: "strategies-card-pnl",
            title: "PnL рукава",
            text: "Зафиксировано, на бумаге и итог — paper-цифры этого рукава, не брокерский экран.",
          },
          {
            tour: "strategies-howto",
            title: "Как устроен",
            text: "Короткий статический абзац про логику рукава. У каждого рукава свой текст.",
          },
          {
            tour: "strategies-filters",
            title: "Фильтры",
            text: "Можно сузить ленту по тикеру и типу действия: покупка, продажа, плоско, выход.",
          },
          {
            tour: lastSleeveDetail && (lastSleeveDetail.signals || []).length
              ? "strategies-signals"
              : "strategies-signals-empty",
            title: "Как читать сигнал",
            text: lastSleeveDetail && (lastSleeveDetail.signals || []).length
              ? "Строка: время, тикер и действие по-русски. Технические детали спрятаны под «подробнее»."
              : "Пустая лента зависит от воркера: нет пульса — одно сообщение, воркер жив и тишина — другое.",
          },
        ],
      });
    }, 80);
  }

  function maybeStartStrategiesTour() {
    if (!authed || !window.CabinTour) return;
    if (strategiesSleeveFromHash()) {
      if (CabinTour.wasSeen(STRATEGIES_TOUR_KEY + "-card")) return;
      window.setTimeout(function () {
        if (
          authed &&
          currentRoute === "strategies" &&
          strategiesSleeveFromHash() &&
          !CabinTour.isActive() &&
          !CabinTour.wasSeen(STRATEGIES_TOUR_KEY + "-card")
        ) {
          startStrategiesCardTour();
        }
      }, 400);
      return;
    }
    if (CabinTour.wasSeen(STRATEGIES_TOUR_KEY)) return;
    window.setTimeout(function () {
      if (
        authed &&
        currentRoute === "strategies" &&
        !strategiesSleeveFromHash() &&
        !CabinTour.isActive() &&
        !CabinTour.wasSeen(STRATEGIES_TOUR_KEY)
      ) {
        startStrategiesTour();
      }
    }, 400);
  }

  function startHelpDemoTour() {
    setHash("help");
    window.setTimeout(function () {
      runTour(HELP_TOUR_KEY, [
        {
          tour: "help-map",
          title: "Карта кабинета",
          text: "Одиннадцать разделов с объяснением «зачем». Это карта оператора, а не список изменений.",
        },
        {
          tour: "help-vault",
          title: "Сейф своими словами",
          text: "50% до перекрытия депозита, потом 20%. После раздела «Помощь» и тура Обзора вы должны объяснить сейф без шпаргалки.",
        },
        {
          tour: "help-security",
          title: "Безопасность",
          text: "В браузер — только токен кабины. Токен брокера сюда не вводится.",
        },
        {
          tour: "help-actions",
          title: "Обучение",
          text: "Сброс туров, демо и «Пройти тур Обзора» — чтобы J8 закрыть без созвона.",
        },
        {
          tour: "help-limits",
          title: "Честные ограничения",
          text: "Нет боевого интерфейса, стакана и чата с моделью. Кабинет — операторский контур лаборатории.",
        },
      ]);
    }, 50);
  }

  function maybeStartGateTour() {
    if (authed || !window.CabinTour) return;
    if (CabinTour.wasSeen(GATE_TOUR_KEY)) return;
    window.setTimeout(function () {
      if (!authed && !CabinTour.isActive() && !CabinTour.wasSeen(GATE_TOUR_KEY)) {
        startGateTour();
      }
    }, 300);
  }

  function maybeStartMenuTour() {
    if (!authed || !window.CabinTour) return;
    if (CabinTour.wasSeen(MENU_TOUR_KEY)) return;
    window.setTimeout(function () {
      if (authed && !CabinTour.isActive() && !CabinTour.wasSeen(MENU_TOUR_KEY)) {
        startMenuTour();
      }
    }, 350);
  }

  function bind() {
    var remember = byId("remember-token");
    remember.checked = localStorage.getItem(REMEMBER_KEY) !== "0";
    byId("app-token").value = readStoredToken();

    document.addEventListener("mouseover", function (event) {
      var tip = event.target && event.target.closest
        ? event.target.closest(".whatis")
        : null;
      if (tip) tip.classList.add("is-open");
    });
    document.addEventListener("mouseout", function (event) {
      var tip = event.target && event.target.closest
        ? event.target.closest(".whatis")
        : null;
      if (!tip) return;
      var related = event.relatedTarget;
      if (related && tip.contains(related)) return;
      tip.classList.remove("is-open");
    });
    document.addEventListener("focusin", function (event) {
      var tip = event.target && event.target.closest
        ? event.target.closest(".whatis")
        : null;
      if (tip) tip.classList.add("is-open");
    });
    document.addEventListener("focusout", function (event) {
      var tip = event.target && event.target.closest
        ? event.target.closest(".whatis")
        : null;
      if (tip) tip.classList.remove("is-open");
    });

    byId("gate-form").addEventListener("submit", function (event) {
      event.preventDefault();
      loginWithToken(byId("app-token").value, rememberEnabled());
    });

    byId("gate-tour").addEventListener("click", startGateTour);
    byId("btn-refresh").addEventListener("click", function () {
      refreshStatus();
    });
    byId("btn-kill").addEventListener("click", function () {
      requestKill(true);
    });
    byId("btn-unkill").addEventListener("click", function () {
      requestKill(false);
    });
    byId("banner-unkill").addEventListener("click", function () {
      requestKill(false);
    });
    byId("confirm-cancel").addEventListener("click", function () {
      closeConfirm(false);
    });
    byId("confirm-ok").addEventListener("click", function () {
      closeConfirm(true);
    });
    byId("confirm-modal").addEventListener("click", function (event) {
      if (event.target === byId("confirm-modal")) closeConfirm(false);
    });
    byId("mobile-more-close").addEventListener("click", closeMobileMore);
    byId("mobile-more-backdrop").addEventListener("click", closeMobileMore);
    byId("btn-change-token").addEventListener("click", function () {
      logoutToGate(false);
      showGateError("Вставьте другой токен кабины и войдите снова.");
    });
    byId("btn-tour").addEventListener("click", function () {
      if (!authed) {
        startGateTour();
        return;
      }
      if (currentRoute === "overview") startOverviewTour();
      else if (currentRoute === "portfolio") startPortfolioTour();
      else if (currentRoute === "strategies") {
        if (strategiesSleeveFromHash()) startStrategiesCardTour();
        else startStrategiesTour();
      } else if (currentRoute === "agents") startAgentsTour();
      else if (currentRoute === "news") startNewsTour();
      else if (currentRoute === "market") startMarketTour();
      else if (currentRoute === "journal") startJournalTour();
      else if (currentRoute === "help") startHelpDemoTour();
      else startMenuTour();
    });
    byId("btn-tour-page").addEventListener("click", function () {
      byId("btn-tour").click();
    });
    byId("btn-reset-tour").addEventListener("click", function () {
      if (window.CabinTour) CabinTour.resetAll();
      if (authed) startMenuTour();
      else startGateTour();
    });

    window.addEventListener("hashchange", syncFromHash);
    window.addEventListener("keydown", function (event) {
      var modal = byId("confirm-modal");
      var more = byId("mobile-more");
      if (event.key === "Escape") {
        if (modal && !modal.hidden) {
          event.preventDefault();
          closeConfirm(false);
          return;
        }
        if (more && !more.hidden) {
          event.preventDefault();
          closeMobileMore();
          var moreBtn = byId("mobile-more-btn");
          if (moreBtn) moreBtn.focus();
          return;
        }
      }
      if (modal && !modal.hidden) {
        if (event.key === "Enter") {
          var tag = (event.target && event.target.tagName) || "";
          if (tag !== "BUTTON" && tag !== "A" && tag !== "TEXTAREA") {
            event.preventDefault();
            closeConfirm(true);
          }
          return;
        }
        if (event.key === "Tab") {
          var focusables = modal.querySelectorAll(
            "button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex='-1'])"
          );
          if (!focusables.length) return;
          var first = focusables[0];
          var last = focusables[focusables.length - 1];
          if (event.shiftKey && document.activeElement === first) {
            event.preventDefault();
            last.focus();
          } else if (!event.shiftKey && document.activeElement === last) {
            event.preventDefault();
            first.focus();
          }
        }
      }
    });

    function accessFromQuery() {
      try {
        var q = new URLSearchParams(location.search || "");
        return (q.get("access") || "").trim();
      } catch (err) {
        return "";
      }
    }

    function stripAccessQuery() {
      try {
        if (!location.search || location.search.indexOf("access=") < 0) return;
        var url = location.pathname + (location.hash || "");
        history.replaceState(null, "", url);
      } catch (err) {
        /* ignore */
      }
    }

    var access = accessFromQuery();
    if (access) {
      stripAccessQuery();
      loginWithToken(access, false);
      return;
    }

    var existing = readStoredToken();
    if (existing) {
      verifyToken(existing)
        .then(function (data) {
          setToken(existing, localStorage.getItem(REMEMBER_KEY) !== "0");
          lastStatus = data;
          lastStatusAt = new Date();
          setAuthed(true);
          renderStatus(data, {});
        })
        .catch(function () {
          setAuthed(false);
          showGateError(
            "Сохранённый токен больше не принимается. Вставьте актуальный APP_AUTH_TOKEN."
          );
          maybeStartGateTour();
        });
    } else {
      setAuthed(false);
      maybeStartGateTour();
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", bind);
  } else {
    bind();
  }
})();
