(function () {
  "use strict";

  /** Версия UI кабинета (этап 30+). Не путать с version API. */
  var CABIN_UI_VERSION = "v3.0";

  var ROUTES = [
    {
      id: "overview",
      title: "Обзор",
      hint: "Что сейчас важно",
      intro:
        "Сводка лаборатории: живость системы, деньги, решения, которые ждут вас, и состояние рукавов.",
    },
    {
      id: "portfolio",
      title: "Портфель",
      hint: "Где деньги и позиции",
      intro:
        "Paper-книга лаборатории: где лежат деньги и какие позиции открыты. Это не экран приложения брокера.",
    },
    {
      id: "strategies",
      title: "Стратегии",
      hint: "Что делают рукава",
      intro:
        "Сначала деньги и лимиты (Настройки), потом доли рукавов, затем карточка «как торгует». Прогон моделирует paper-сделки по CSV с исполнением на следующем баре и расходами.",
    },
    {
      id: "companies",
      title: "Компании",
      hint: "Фундамент и скор",
      intro:
        "Снимки метрик эмитентов (P/E, P/B, ROE, дивиденды) и прозрачный скор. Не торговый сигнал сам по себе.",
    },
    {
      id: "recommendations",
      title: "Рекомендации",
      hint: "Кандидаты в очередь",
      intro:
        "Топ имён по фундаментальному скору → «В очередь» → вы решаете в Агентах. Аналитика лаборатории, не ИК.",
    },
    {
      id: "agents",
      title: "Агенты",
      hint: "Что решить вам",
      intro:
        "Агенты только предлагают. Сделка или смена весов — после вашего «Принять» и прохождения риск-правил.",
    },
    {
      id: "news",
      title: "Новости",
      hint: "Внешний контур",
      intro:
        "Внешний информационный контур. Новости не открывают сделки сами. Research считается offline.",
    },
    {
      id: "market",
      title: "Рынок",
      hint: "Периметр и правила",
      intro:
        "Периметр торговли: какие бумаги допущены и какие правила режут ордера.",
    },
    {
      id: "journal",
      title: "Журнал",
      hint: "Ордера и проводки",
      intro: "Факт лабораторной истории: ордера и проводки книги.",
    },
    {
      id: "settings",
      title: "Настройки",
      hint: "Депозит и лимиты",
      intro:
        "Капитал лаборатории: депозит (торговый кэш) и максимум на одну бумагу. Бюджеты рукавов — в Стратегиях.",
    },
    {
      id: "help",
      title: "Помощь",
      hint: "Как пользоваться",
      intro:
        "Карта кабинета, легенда статусов, словарь терминов и управление обучением.",
    },
  ];

  /** Основные вкладки на мобиле; остальное — в «Ещё» (G3). */
  var MOBILE_PRIMARY_IDS = [
    "overview",
    "portfolio",
    "recommendations",
    "companies",
    "settings",
  ];
  var MOBILE_MORE_IDS = [
    "strategies",
    "agents",
    "news",
    "market",
    "journal",
    "help",
  ];
  var lastFundamentals = null;
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
  var loadErrors = {};
  var blockLoading = {};
  var routeLoading = false;
  var refreshBusy = false;
  var FETCH_TIMEOUT_MS = 12000;
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
  ];
  var SLEEVE_NAMES = {
    sma_cross: "Пересечение средних",
    donchian_breakout: "Пробой Дончиана",
    rsi_reversion: "RSI-возврат",
    ema_scalp: "EMA-скальп",
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

  function humanBeat(iso) {
    if (!iso) return "пульса ещё не было";
    var beat = new Date(iso);
    if (isNaN(beat.getTime())) return "время пульса неизвестно";
    var sec = Math.max(0, Math.round((Date.now() - beat.getTime()) / 1000));
    if (sec < 60) return "пульс " + sec + " с назад";
    var min = Math.round(sec / 60);
    if (min < 60) return "пульс " + min + " мин назад";
    var hours = Math.round(min / 60);
    return "пульс " + hours + " ч назад";
  }

  function pillHtml(label, value, tone) {
    return (
      '<div class="status-pill">' +
      '<div class="k">' +
      escapeHtml(label) +
      "</div>" +
      '<div class="v"><span class="dot ' +
      tone +
      '"></span><span>' +
      escapeHtml(value) +
      "</span></div></div>"
    );
  }

  function renderStatus(data, meta) {
    var strip = byId("status-strip");
    if (!strip) return;
    var alive = !!(data && data.worker_alive);
    var killed = !!(data && data.killed);
    var agents = !!(data && data.agents_enabled);
    var systemTone = meta && meta.error ? "bad" : "ok";
    var systemText =
      meta && meta.error
        ? meta.error
        : data && data.status === "ok"
          ? "связь есть"
          : "нет ответа";
    var workerTone = alive ? "ok" : "warn";
    var workerText = alive
      ? "в сети · " + humanBeat(data.worker_beat)
      : "нет сигнала · " + humanBeat(data && data.worker_beat);
    var tradeTone = killed ? "bad" : "ok";
    var tradeText = killed
      ? "стоп включён · новые ордера нельзя"
      : "можно выставлять";
    var agentsTone = agents ? "ok" : "warn";
    var agentsText = agents
      ? "включены"
      : "выключены · очередь будет пустой, это нормально";

    strip.innerHTML = [
      pillHtml("Система", systemText, systemTone),
      pillHtml("Воркер", workerText, workerTone),
      pillHtml("Торговля", tradeText, tradeTone),
      pillHtml("Агенты", agentsText, agentsTone),
    ].join("");

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
        el.classList.toggle("active", el.dataset.route === routeId);
      });
    var moreBtn = byId("mobile-more-btn");
    if (moreBtn) {
      var inMore = MOBILE_MORE_IDS.indexOf(routeId) !== -1;
      moreBtn.classList.toggle("active", inMore);
      moreBtn.setAttribute("aria-current", inMore ? "true" : "false");
    }
  }

  function apiPost(path, body) {
    return fetchJson(path, {
      method: "POST",
      body: body === undefined ? undefined : body,
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
    if (ctrl) {
      timer = window.setTimeout(function () {
        try {
          ctrl.abort();
        } catch (e) {}
      }, FETCH_TIMEOUT_MS);
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
          var err = new Error(humanizeHttpError(res.status));
          err.status = res.status;
          throw err;
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
          showGateError("Слишком частые запросы — подождите минуту и попробуйте снова.");
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
    if (!raw) return "overview";
    if (raw === "strategies" || raw.indexOf("strategies/") === 0) {
      return "strategies";
    }
    for (var i = 0; i < ROUTES.length; i++) {
      if (ROUTES[i].id === raw) return raw;
    }
    return "overview";
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

  function renderNav() {
    var nav = byId("nav");
    var mobile = byId("mobile-nav");
    var moreLinks = byId("mobile-more-links");
    nav.innerHTML = '<div class="nav-label">Разделы</div>';
    mobile.innerHTML = "";
    if (moreLinks) moreLinks.innerHTML = "";
    ROUTES.forEach(function (route) {
      var a = document.createElement("a");
      a.href = "#/" + route.id;
      a.dataset.route = route.id;
      a.dataset.tour = "nav-" + route.id;
      a.innerHTML =
        "<span>" +
        route.title +
        '</span><span class="nav-hint">' +
        route.hint +
        "</span>";
      nav.appendChild(a);
    });
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
      return "После «Принять» ордер пройдёт риск-ворота. Если риск пропустит — появится в Журнале; если нет — увидите отказ явно.";
    }
    if (row.kind === "weights") {
      return "После «Принять» новые веса рукавов применятся в аллокаторе. Сами сделки от смены весов не откроются.";
    }
    return "После «Принять» предложение перестанет ждать решения.";
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
        "Paper-forward проверка",
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
          G5: "Live",
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
          ? '<p class="warning-text">Точная equity скрыта: есть устаревшие или отсутствующие цены (' +
            escapeHtml(
              String(quality.stale_marks || 0) +
                " stale, " +
                String(quality.missing_marks || 0) +
                " missing"
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
      money(weekly.pnl) +
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
      '<p data-tour="help-cabin-v1">Кабинет <strong>' +
      escapeHtml(CABIN_UI_VERSION) +
      "</strong> — операторский UI paper/sandbox-лаборатории. " +
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
        "<span><strong>Агенты включены.</strong> Они только предлагают — сделка или веса после вашего решения и риск-правил.</span>" +
        "</div>"
      );
    }
    return (
      '<div class="attention calm" data-tour="agents-banner">' +
      "<span><strong>Агенты выключены.</strong> Это ожидаемо, не авария. Очередь может быть пустой, пока агенты выключены на сервере. Предложения вручную через интерфейс всё ещё видны здесь.</span>" +
      "</div>"
    );
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
          "Принято. Ордер прошёл риск" +
          (order && order.ticker ? " (" + order.ticker + ")" : "") +
          ". Факт смотрите в Журнале.",
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
    var sizing = isOrder
      ? orderSideLabel(payload.side) +
        " " +
        String(payload.qty || "—") +
        " × " +
        String(payload.ticker || "—")
      : (payload.weights || [])
          .map(function (item) {
            return (
              (SLEEVE_NAMES[item.sleeve] || item.sleeve) +
              " " +
              pctLabel(item.weight)
            );
          })
          .join(" · ");
    var invalidation = isOrder
      ? "Стоп " + money(payload.stop) + "; риск-ворота могут отклонить до исполнения."
      : "Не применять, если OOS-квалификация или лимиты капитала изменились.";
    var actions = "";
    if (waiting) {
      actions =
        '<div class="proposal-actions" data-tour="agents-actions">' +
        '<button type="button" class="primary" data-approve="' +
        escapeHtml(row.id) +
        '">Принять</button>' +
        '<button type="button" class="ghost" data-reject="' +
        escapeHtml(row.id) +
        '">Отклонить</button>' +
        "</div>";
    }
    return (
      '<article class="proposal-card large" data-proposal-id="' +
      escapeHtml(row.id) +
      '" data-tour="' +
      (opts && opts.tour ? opts.tour : "agents-card") +
      '">' +
      '<div class="proposal-head">' +
      '<div class="kind">' +
      escapeHtml(proposalKindLabel(row.kind)) +
      '</div><span class="status-chip">' +
      escapeHtml(proposalStatusLabel(row.status)) +
      "</span></div>" +
      '<p class="summary">' +
      escapeHtml(proposalSummary(row)) +
      "</p>" +
      '<div class="decision-flow">' +
      '<div><span>01 / THESIS</span><strong>' +
      escapeHtml(thesis) +
      "</strong></div>" +
      '<div><span>02 / SIZING</span><strong>' +
      escapeHtml(sizing || "—") +
      "</strong></div>" +
      '<div><span>03 / CHECKS</span><strong>Risk policy · лимиты · свежие данные</strong></div>' +
      '<div><span>04 / EFFECT</span><strong>' +
      escapeHtml(proposalWillDo(row)) +
      "</strong></div>" +
      '<div><span>05 / INVALIDATION</span><strong>' +
      escapeHtml(invalidation) +
      "</strong></div></div>" +
      (waiting
        ? '<p class="will-do" data-tour="agents-will-do"><strong>Что будет при «Принять»:</strong> ' +
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
          title: "Принять предложение?",
          text:
            (row ? proposalSummary(row) + ". " : "") +
            "Ордер или веса применятся только если риск-ворота пропустят. Если риск откажет — увидите это явно.",
          okLabel: "Принять",
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
      waitingHtml = waiting
        .map(function (row, i) {
          return proposalCardHtml(row, {
            tour: i === 0 ? "agents-card" : "agents-card-more",
          });
        })
        .join("");
    } else if (loadErrors.proposals) {
      waitingHtml =
        blockErrorHtml("proposals") ||
        '<p class="empty" data-tour="agents-waiting-empty">Очередь не загрузилась — это не пустая очередь.</p>';
    } else if (!agentsOn) {
      waitingHtml =
        '<p class="empty" data-tour="agents-waiting-empty">Очередь пуста: агенты выключены. Это нормально, не ошибка системы.</p>';
    } else {
      waitingHtml =
        '<p class="empty" data-tour="agents-waiting-empty">Сейчас нет предложений, которые ждут решения.</p>';
    }
    var recentHtml = "";
    if (recent.length) {
      recentHtml = wrapTableScroll(
        '<table class="data-table" data-tour="agents-recent">' +
          "<thead><tr><th>тип</th><th>статус</th><th>кратко</th></tr></thead><tbody>" +
          recent
            .map(function (row) {
              return (
                "<tr><td>" +
                escapeHtml(proposalKindLabel(row.kind)) +
                "</td><td>" +
                escapeHtml(proposalStatusLabel(row.status)) +
                "</td><td>" +
                escapeHtml(proposalSummary(row)) +
                "</td></tr>"
              );
            })
            .join("") +
          "</tbody></table>"
      );
    } else {
      recentHtml =
        '<p class="empty">Недавних решений ещё нет. После принятия или отклонения они появятся здесь; факт сделок смотрите в Журнале.</p>';
    }
    body.innerHTML =
      agentsBannerHtml() +
      agentsFlashHtml() +
      '<section class="panel" id="agents-waiting" data-tour="agents-waiting">' +
      "<h3>Ждут решения</h3>" +
      "<p>Сначала предложения со статусом «ждут решения». Краткое описание человеческим языком — технические детали только под «Подробнее».</p>" +
      waitingHtml +
      "</section>" +
      '<section class="panel" data-tour="agents-recent-panel">' +
      "<h3>Недавние решения</h3>" +
      "<p>Принятые, отклонённые и истекшие. Итог ордеров — в <a class=\"panel-link\" href=\"#/journal?tab=orders\">Журнале</a>.</p>" +
      recentHtml +
      "</section>";
    bindAgentsActions();
    if (agentsFocusProposed || hashQuery().tab === "proposed") {
      agentsFocusProposed = false;
      var el = byId("agents-waiting");
      if (el && el.scrollIntoView) {
        window.setTimeout(function () {
          el.scrollIntoView({ behavior: "smooth", block: "start" });
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
    var capital = Number(capitalRub);
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
      '<input type="number" min="1" step="1000" id="' +
      idDeposit +
      '" value="' +
      escapeHtml(String(vals.depositDefault)) +
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
      "<strong>Рамка.</strong> Аналитика paper-лаборатории. Не индивидуальная инвестиционная рекомендация и не услуга ИК. " +
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

  function renderCompanies() {
    var body = byId("page-body");
    var data = lastFundamentals || { items: [], disclaimer: "" };
    var items = data.items || [];
    var table = items.length
      ? wrapTableScroll(
          '<table class="data-table" data-tour="companies-table">' +
            "<thead><tr>" +
            "<th>тикер</th><th>скор</th><th>value</th><th>quality</th><th>div</th>" +
            "<th>P/E</th><th>P/B</th><th>ROE</th><th>див.</th><th>почему</th>" +
            "</tr></thead><tbody>" +
            items
              .map(function (row) {
                var scores = row.scores || {};
                return (
                  "<tr>" +
                  "<td>" +
                  escapeHtml(row.ticker || "—") +
                  "</td><td><strong>" +
                  escapeHtml(String(scores.total != null ? scores.total : "—")) +
                  "</strong></td><td>" +
                  escapeHtml(String(scores.value != null ? scores.value : "—")) +
                  "</td><td>" +
                  escapeHtml(String(scores.quality != null ? scores.quality : "—")) +
                  "</td><td>" +
                  escapeHtml(String(scores.div != null ? scores.div : "—")) +
                  "</td><td>" +
                  escapeHtml(row.pe_ratio_ttm != null ? String(row.pe_ratio_ttm) : "—") +
                  "</td><td>" +
                  escapeHtml(
                    row.price_to_book_ttm != null ? String(row.price_to_book_ttm) : "—"
                  ) +
                  "</td><td>" +
                  escapeHtml(row.roe != null ? String(row.roe) : "—") +
                  "</td><td>" +
                  escapeHtml(
                    row.dividend_yield_ttm != null
                      ? String(row.dividend_yield_ttm)
                      : "—"
                  ) +
                  "</td><td>" +
                  escapeHtml(row.rationale || "") +
                  "</td></tr>"
                );
              })
              .join("") +
            "</tbody></table>",
          true
        )
      : '<p class="empty" data-tour="companies-empty">Снимков ещё нет. Нажмите «Демо-данные» (локально) или «Обновить с брокера».</p>';
    body.innerHTML =
      '<section class="panel" data-tour="companies-panel">' +
      "<h3>Компании</h3>" +
      "<p>Фундаментальные метрики и скор (value / quality / div). " +
      'Кандидаты на вход — в <a class="panel-link" href="#/recommendations">Рекомендациях</a>.</p>' +
      '<div class="panel-actions">' +
      '<button type="button" class="primary" id="companies-demo">Демо-данные</button>' +
      '<button type="button" class="ghost" id="companies-refresh">Обновить с брокера</button>' +
      "</div>" +
      '<p class="source-line" id="companies-status">' +
      escapeHtml(data.disclaimer || "") +
      "</p>" +
      table +
      "</section>";
    var demoBtn = byId("companies-demo");
    var refreshBtn = byId("companies-refresh");
    var status = byId("companies-status");
    if (demoBtn) {
      demoBtn.addEventListener("click", function () {
        demoBtn.disabled = true;
        apiPost("/fundamentals/demo", {})
          .then(function (payload) {
            lastFundamentals = payload;
            if (status) status.textContent = "Загружено демо: " + (payload.count || 0);
            renderCompanies();
          })
          .catch(function (err) {
            if (status) {
              status.textContent = "Демо не загрузилось: " + (err.message || "ошибка");
            }
          })
          .finally(function () {
            demoBtn.disabled = false;
          });
      });
    }
    if (refreshBtn) {
      refreshBtn.addEventListener("click", function () {
        refreshBtn.disabled = true;
        apiPost("/fundamentals/refresh", {})
          .then(function (payload) {
            if (status) {
              status.textContent = "Обновлено записей: " + (payload.upserted || 0);
            }
            return refreshCompanies();
          })
          .catch(function (err) {
            if (status) {
              status.textContent =
                "Брокер недоступен или ошибка: " + (err.message || "ошибка");
            }
          })
          .finally(function () {
            refreshBtn.disabled = false;
          });
      });
    }
  }

  function refreshCompanies() {
    return apiGet("/fundamentals")
      .then(function (data) {
        lastFundamentals = data;
        if (currentRoute === "companies") renderCompanies();
        return data;
      })
      .catch(function (err) {
        lastFundamentals = { items: [], disclaimer: err.message || "" };
        if (currentRoute === "companies") renderCompanies();
        return null;
      });
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
              '<div class="metrics tight">' +
              '<div class="metric hero"><div class="k">скор</div><div class="v">' +
              escapeHtml(String(scores.total != null ? scores.total : "—")) +
              "</div></div>" +
              '<div class="metric"><div class="k">value</div><div class="v">' +
              escapeHtml(String(scores.value != null ? scores.value : "—")) +
              "</div></div>" +
              '<div class="metric"><div class="k">quality</div><div class="v">' +
              escapeHtml(String(scores.quality != null ? scores.quality : "—")) +
              "</div></div>" +
              '<div class="metric"><div class="k">div</div><div class="v">' +
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
      "<p>Топ по фундаментальному скору. «В очередь» создаёт proposal (рукав fund_screener) — сделка только после вашего «Принять» в Агентах.</p>" +
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
              status.textContent =
                "В очереди: " +
                (payload.count || 0) +
                " предложений. Откройте Агенты → Принять/Отклонить.";
            }
            return refreshProposals();
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
        var amount = Number(input && input.value);
        if (!isFinite(amount) || amount <= 0) {
          if (capitalStatus) {
            capitalStatus.textContent = "Укажите депозит больше нуля.";
          }
          return;
        }
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
    var whatIfInput =
      planWhatIfCapital !== ""
        ? planWhatIfCapital
        : String(
            Math.round(
              Number(
                (byPlan[ACTIVE_SLEEVE_IDS[0]] &&
                  byPlan[ACTIVE_SLEEVE_IDS[0]].capital) ||
                  1000000
              )
            )
          );
    var whatIf = whatIfForCapital(whatIfInput);
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
      '<input type="number" min="0" step="1000" id="plan-whatif-capital" value="' +
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
        '<input type="number" min="0" step="1000" data-sleeve-capital="' +
        escapeHtml(id) +
        '" value="' +
        escapeHtml(String(capital)) +
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
      " = equity × " +
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
      "<li><strong>Прогон на истории</strong> — paper-бэктест по CSV: сделки на следующем баре, расходы, PnL и просадка. " +
      "<em>Это модель, не обещание результата и не рекомендация.</em></li>" +
      "</ol></section>"
    );
  }

  function renderStrategiesDesk() {
    var result = lastDeskBacktest;
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
        oos_edge: "OOS-преимущество",
        sample: "Объём выборки",
        drawdown: "Просадка",
        cost_resilience: "Устойчивость к расходам",
        paper_forward: "Paper-forward",
        walk_forward_coverage: "Покрытие walk-forward",
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
      resultHtml =
        '<div class="experiment-report">' +
        '<div class="experiment-report__head"><div><span class="section-kicker">EXPERIMENT ' +
        escapeHtml(shortId(result.experiment_id)) +
        "</span><h4>Strategy evidence report</h4></div>" +
        '<span class="qualification ' +
        (qualified ? "is-qualified" : "is-rejected") +
        '">' +
        (qualified ? "OOS QUALIFIED" : "CASH FALLBACK") +
        "</span></div>" +
        '<div class="callout" data-tour="strategies-desk-verdict"><strong>Paper-бэктест.</strong> ' +
        escapeHtml(verdict) +
        " Сигнал исполняется не раньше открытия следующего бара; учтены комиссия и проскальзывание из конфигурации." +
        "</div>" +
        '<div class="metrics" data-tour="strategies-desk-result">' +
        '<div class="metric hero"><div class="k">чистый PnL</div><div class="v">' +
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
        '<div class="metric"><div class="k">доходность стратегии</div><div class="v">' +
        escapeHtml(
          summary.total_return === null || summary.total_return === undefined
            ? "—"
            : (Number(summary.total_return) * 100).toFixed(2) + "%"
        ) +
        "</div></div>" +
        '<div class="metric"><div class="k">против buy & hold</div><div class="v">' +
        escapeHtml(
          summary.excess_return === null || summary.excess_return === undefined
            ? "—"
            : (Number(summary.excess_return) * 100).toFixed(2) + " п.п."
        ) +
        "</div></div></div>" +
        '<div class="callout"><strong>Вневыборочная проверка.</strong> ' +
        escapeHtml(
          oos.folds
            ? String(oos.folds) +
                " окон, доходность " +
                (Number(oos.total_return) * 100).toFixed(2) +
                "%, преимущество к buy & hold " +
                (Number(oos.excess_return) * 100).toFixed(2) +
                " п.п."
            : "Недостаточно данных для OOS-окна."
        ) +
        "</div>" +
        '<div class="evidence-lanes">' +
        '<div><span>IN-SAMPLE</span><strong>' +
        escapeHtml(String(summary.trades || 0)) +
        ' trades</strong><small>return ' +
        escapeHtml(pctLabel(summary.total_return)) +
        "</small></div>" +
        '<div><span>OUT-OF-SAMPLE</span><strong>' +
        escapeHtml(String(oos.trades || 0)) +
        ' trades / ' +
        escapeHtml(String(oos.folds || 0)) +
        ' folds</strong><small>excess ' +
        escapeHtml(pctLabel(oos.excess_return)) +
        "</small></div>" +
        '<div><span>CAPITAL DECISION</span><strong>' +
        (qualified ? "eligible" : "cash only") +
        "</strong><small>" +
        (qualified
          ? "≥5 OOS trades and positive excess"
          : "qualification gate not passed") +
        "</small></div></div>" +
        evidenceHtml +
        (summary.insufficient_statistics
          ? '<p class="warning-text">Сделок мало: статистики недостаточно для вывода о преимуществе стратегии.</p>'
          : "") +
        (oos.insufficient_statistics
          ? '<p class="warning-text">OOS-сделок мало: стратегия пока не квалифицирована для выделения капитала.</p>'
          : "") +
        '<p class="source-line">файл ' +
        escapeHtml(result.path || "") +
        (result.experiment_id
          ? " · experiment " + escapeHtml(result.experiment_id)
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
        '<p class="empty">Необязательный тест: рукав + тикер CSV → сколько раз стратегия хотела купить/продать. Ордера не ставит.</p>';
    }
    var sleeveOpts = ACTIVE_SLEEVE_IDS.map(function (id) {
      return (
        '<option value="' +
        escapeHtml(id) +
        '">' +
        escapeHtml(SLEEVE_NAMES[id] || id) +
        "</option>"
      );
    }).join("");
    return (
      '<section class="panel" data-tour="strategies-desk">' +
      "<h3>Paper-бэктест на истории</h3>" +
      "<p>" +
      "<strong>Не путать с гарантией прибыли.</strong> Это модель сделок по локальному CSV с next-bar исполнением, комиссией, проскальзыванием и benchmark. " +
      "Депозит и % на бумагу — в " +
      '<a class="panel-link" href="#/settings">Настройках</a>.' +
      "</p>" +
      '<div class="filters" data-tour="strategies-desk-form">' +
      '<label class="field compact">рукав<select id="desk-sleeve">' +
      sleeveOpts +
      "</select></label>" +
      '<label class="field compact">тикер CSV' +
      '<input type="text" id="desk-ticker" value="SBER" placeholder="SBER"></label>' +
      '<button type="button" class="primary" id="desk-run">Прогнать на истории</button>' +
      "</div>" +
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
      "<h3>Четыре рукава</h3>" +
      "<p>" +
      "SMA и Дончиан (дневки), RSI-возврат (дневки), EMA-скальп (M15). " +
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
            "<thead><tr><th>тикер</th><th>qty</th><th>средняя</th><th>на бумаге</th></tr></thead><tbody>" +
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

  function renderStrategies() {
    var body = byId("page-body");
    var sleeveId = strategiesSleeveFromHash();
    if (sleeveId) {
      body.innerHTML = renderStrategiesSleeveCard(sleeveId);
      bindSignalFilters();
      return;
    }
    signalFilterTicker = "";
    signalFilterKind = "";
    body.innerHTML = renderStrategiesCompare();
    body.querySelectorAll("tr[data-href]").forEach(function (row) {
      row.addEventListener("click", function (event) {
        if (event.target && event.target.closest && event.target.closest("a")) {
          return;
        }
        location.hash = row.getAttribute("data-href");
      });
    });
    bindStrategiesLabControls();
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
      capEl.value = String(Math.round((pool * pct) / 100));
    } else {
      var capital = Number(capEl.value);
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
      if (whatIfCap) planWhatIfCapital = whatIfCap.value;
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
    var runBtn = byId("desk-run");
    if (runBtn) {
      runBtn.addEventListener("click", function () {
        var sleeveEl = byId("desk-sleeve");
        var tickerEl = byId("desk-ticker");
        var sleeve = sleeveEl ? sleeveEl.value : "sma_cross";
        var ticker = tickerEl ? tickerEl.value : "SBER";
        runBtn.disabled = true;
        apiPost("/backtests", { sleeve: sleeve, ticker: ticker })
          .then(function (data) {
            lastDeskBacktest = data.result || data;
            if (data.id && lastDeskBacktest) {
              lastDeskBacktest.experiment_id = data.id;
            }
            renderStrategies();
          })
          .catch(function (err) {
            lastDeskBacktest = { error: err.message || "ошибка прогона" };
            renderStrategies();
          })
          .finally(function () {
            runBtn.disabled = false;
          });
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
    return Promise.all([
      listPromise,
      detailPromise,
      allocPromise,
      planPromise,
    ]).then(function () {
      if (currentRoute === "strategies") renderStrategies();
    });
  }

  function whatis(title, text) {
    return (
      '<span class="whatis" title="' +
      escapeHtml(text) +
      '" aria-label="' +
      escapeHtml(title + ": " + text) +
      '">?</span>'
    );
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
      '<div class="tabs" data-tour="portfolio-tabs">' +
      tabs
        .map(function (tab) {
          return (
            '<button type="button" data-tab="' +
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
              escapeHtml(row.mark_quality || "missing") +
              "</span></div>" +
              '<div class="position-card__value">' +
              money(row.market_value) +
              "</div>" +
              '<div class="position-card__pnl ' +
              (pnl > 0 ? "is-positive" : pnl < 0 ? "is-negative" : "") +
              '">Open PnL ' +
              money(row.unrealized_pnl) +
              "</div>" +
              '<dl><div><dt>Qty</dt><dd>' +
              escapeHtml(String(qty)) +
              "</dd></div><div><dt>Cost</dt><dd>" +
              money(row.cost_basis) +
              "</dd></div><div><dt>Mark</dt><dd>" +
              money(row.mark) +
              "</dd></div><div><dt>Weight</dt><dd>" +
              escapeHtml(share) +
              "</dd></div></dl>" +
              '<p class="position-card__source">' +
              escapeHtml(row.mark_source || "no source") +
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
      "<p>Cost → market → PnL с источником и свежестью каждой цены.</p>" +
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
      "Как капитал делится между рукавами. Веса equal-weight; капитал рукава = стоимость счёта × потолок рукава × вес." +
      "</p>" +
      '<div class="metrics">' +
      '<div class="metric" data-tour="portfolio-alloc-equity"><div class="k">стоимость счёта</div><div class="v">' +
      money(alloc.equity) +
      "</div></div>" +
      '<div class="metric" data-tour="portfolio-alloc-share"><div class="k">потолок рукава' +
      whatis(
        "Потолок рукава",
        "Доля equity, в пределах которой рукава делят торговый капитал. Сейчас 40%."
      ) +
      '</div><div class="v">' +
      escapeHtml(pctLabel(alloc.sleeve_share)) +
      "</div></div></div>" +
      table +
      '<details class="fold" data-tour="portfolio-alloc-how">' +
      "<summary>Как считается</summary>" +
      "<p>Два рукава → вес 50/50. Капитал рукава = equity × 0,40 × вес. Это лимит аллокатора, не факт позиций.</p>" +
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
      whatis("Депозит", "Стартовое пополнение лаборатории — цель, которую сейф стремится перекрыть.") +
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
      body.innerHTML = portfolioTabsHtml() + skeletonHtml(3);
      return;
    }
    var content = "";
    if (portfolioTab === "capital") content = renderPortfolioCapital();
    else if (portfolioTab === "positions") content = renderPortfolioPositions();
    else if (portfolioTab === "vault") content = renderPortfolioVault();
    else if (portfolioTab === "allocation") content = renderPortfolioAllocation();
    else content = renderPortfolioDrift();

    body.innerHTML = portfolioTabsHtml() + content;
    body.querySelectorAll(".tabs button").forEach(function (btn) {
      btn.addEventListener("click", function () {
        portfolioTab = btn.getAttribute("data-tab") || "capital";
        renderPortfolio();
      });
    });
    if (portfolioTab === "drift") bindDriftActions();
  }

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
    currentRoute = route.id;

    syncNavActive(route.id);
    closeMobileMore();

    byId("page-title").textContent = route.title;
    byId("page-intro").textContent = route.intro;
    document.title = "i.datagon · " + route.title;

    if (route.id === "overview") {
      renderOverview();
      loadOverviewData(true).then(function () {
        maybeStartOverviewTour();
      });
      return;
    }
    if (route.id === "portfolio") {
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
    if (route.id === "strategies") {
      renderStrategies();
      refreshStrategies().then(function () {
        maybeStartStrategiesTour();
      });
      return;
    }
    if (route.id === "companies") {
      renderCompanies();
      refreshCompanies();
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
    var id = routeFromHash();
    if ((location.hash || "") === "" || location.hash === "#") {
      setHash(id);
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
      '<div class="tabs" data-tour="news-tabs">' +
      tabs
        .map(function (tab) {
          return (
            '<button type="button" data-news-tab="' +
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
          renderNews();
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
    body.innerHTML = newsTabsHtml() + content;
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
      '<div class="tabs" data-tour="market-tabs">' +
      tabs
        .map(function (tab) {
          return (
            '<button type="button" data-market-tab="' +
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
    body.innerHTML = marketTabsHtml() + content;
    body.querySelectorAll("[data-market-tab]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        marketTab = btn.getAttribute("data-market-tab") || "universe";
        renderMarket();
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
      { id: "audit", label: "Audit trail" },
    ];
    return (
      '<div class="tabs" data-tour="journal-tabs">' +
      tabs
        .map(function (tab) {
          return (
            '<button type="button" data-journal-tab="' +
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
        blockErrorHtml("orders") ||
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
      return Object.assign({ lane: "AUDIT", timeline_at: row.occurred_at }, row);
    });
    var orderRows = (lastOrders || []).map(function (row) {
      return {
        lane: "ORDER",
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
        lane: "LEDGER",
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
          escapeHtml(row.event_type || "event") +
          '</strong><time>' +
          formatSignalTime(row.timeline_at) +
          "</time></div>" +
          '<p><span class="section-kicker">' +
          escapeHtml(row.entity_type || "entity") +
          "</span> " +
          escapeHtml(row.entity_id || "—") +
          "</p>" +
          (row.lane === "AUDIT"
            ? '<div class="audit-hashes"><code>prev ' +
              escapeHtml(shortId(row.previous_hash)) +
              '</code><code>hash ' +
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
      '<div class="audit-title"><div><span class="section-kicker">IMMUTABLE EVIDENCE</span><h3>Сквозной audit trail</h3></div>' +
      '<span class="qualification ' +
      (chainOk ? "is-qualified" : "is-rejected") +
      '">' +
      (chainOk ? "CHAIN VALID" : "CHAIN INVALID") +
      "</span></div>" +
      "<p>Ордера, проводки и append-only события на одной временной оси. Audit-события связаны хешами; исправления выполняются компенсирующими проводками.</p>" +
      (events
        ? '<div class="audit-timeline">' + events + "</div>"
        : '<p class="empty">Audit-событий пока нет.</p>') +
      "</section>"
    );
  }

  function bindJournalControls() {
    byId("page-body")
      .querySelectorAll("[data-journal-tab]")
      .forEach(function (btn) {
        btn.addEventListener("click", function () {
          journalTab = btn.getAttribute("data-journal-tab") || "orders";
          renderJournal();
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
    body.innerHTML = journalTabsHtml() + content;
    bindJournalControls();
  }

  function refreshJournal() {
    routeLoading = true;
    if (currentRoute === "journal") {
      byId("page-body").innerHTML = journalTabsHtml() + skeletonHtml(3);
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
            text: "Здесь деталка выбранного рукава. Все четыре рукава открываются одинаково.",
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
          text: "Восемь разделов с «зачем». Это карта оператора, а не список изменений.",
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
