# ТЗ i.datagon

Лаборатория аллокации на Тинькофф sandbox: воркер, Postgres, тонкая кабина, рукава стратегий, сейф прибыли, агенты позже.

**Не торговый совет.** Чужие деньги не принимаем. Живой счёт — только отдельным решением после бумаги.

## Паспорт

| Поле | Значение |
|---|---|
| Репозиторий | https://github.com/bziksv/i.datagon |
| Сервер | `155.212.171.103` |
| Путь на сервере | `/var/www/i_datagon_ru_usr/data/www/i.datagon.ru` |
| Домен | `i.datagon.ru` |
| Старт | sandbox T-Invest, вирт. 1 000 000 ₽ |
| Брокер в браузере | нет, токен только на сервере |
| БД | PostgreSQL |
| Стек | Python 3.12, FastAPI, воркер, Docker, тонкая кабина |
| Правило работ | **один пункт = одна итерация, не больше** |

## Как внедряем

1. Берём следующий номер со статусом `todo`.
2. Делаем только его. Без задела «заодно».
3. Проверяем критерий готовности (колонка «Готово когда»).
4. Ставим `done`, в шапке двигаем **Следующая итерация**.
5. Коммит в репозиторий — отдельным шагом, если попросили.

Пропуски запрещены: нельзя делать 040, пока 039 не `done`, если у 040 в зависимостях указан предыдущий блок.

## Не делаем в этом листе

- Живая торговля и боевой токен Тинькоффа
- Приём денег клиентов, PAMM, «сигналы за подписку»
- Агент с инструментом `place_order`
- Свой hex/JS в кабину к API брокера
- MySQL / SQLite как основная БД

## Следующая итерация

**Бэкенд-лист 001–156 закрыт.**  
UI кабинета — отдельный лист: [TZ-CABIN.md](TZ-CABIN.md) (**30 этапов, 01–30 done**, кабинет **v1**).  
Приёмка оператора: [CABIN-ACCEPTANCE.md](CABIN-ACCEPTANCE.md) (J1–J9).  
Финальная фиксация: [CABIN-FINAL.md](CABIN-FINAL.md).  
Персональный контур (фундамент → рекомендации): [TZ-ADVISORY.md](TZ-ADVISORY.md) (блок A+B).
Модернизация финансового контура, бэктеста, риска и кабины:
[TZ-MODERNIZATION.md](TZ-MODERNIZATION.md) (M0–M7).
Тест и рабочая песочница (только «Абс. моментум-4», боевой счёт вне листа):
[TZ-DESKS.md](TZ-DESKS.md).

---

## Модель (чтобы пункты не расползались)

```
кабина  →  FastAPI  →  Postgres
              ↑
           воркер  →  Tinkoff sandbox
              ↑
     рукава / риск / аллокатор / сейф
              ↑
     агенты (только propose + rationale)
```

Счета в нашей книге: `trading_cash`, `vault`. В sandbox «вывод на карту» не обязателен — сейф живёт у нас.

Правило сейфа (код, не модель):

- пока сумма выводов в сейф < стартового депозита: **50%** закрытой прибыли → сейф;
- после перекрытия ввода: **20%** новой закрытой прибыли → сейф;
- бумажная переоценка не считается.

Лимиты по умолчанию (меняются конфигом, не промптом): ≤10% капитала на имя, ≤40% на рукав, kill-switch.

---

## Лист внедрения

Статусы: `todo` · `doing` · `done` · `blocked`

### A. Репозиторий и каркас

| # | Пункт | Готово когда |
|---|---|---|
| 001 | Каркас репозитория: README с паспортом (сервер, путь, домен, ссылка на это ТЗ) | **done** · README.md в корне |
| 002 | `.gitignore`: `.env`, venv, `__pycache__`, `.pytest_cache`, IDE, дампы | **done** · секреты в git не попадают |
| 003 | Python 3.12: `pyproject.toml` с именем `i-datagon` | **done** · `pip install -e .` ставит `i-datagon 0.0.1` |
| 004 | Каталоги `app/`, `worker/`, `tests/`, `deploy/`, `web/` | **done** · пакеты `app`, `worker`; `tests/`, `deploy/`, `web/` |
| 005 | `.env.example` без значений токенов: `DATABASE_URL`, `TINKOFF_SANDBOX_TOKEN`, `APP_AUTH_TOKEN`, `SANDBOX_DEPOSIT` | **done** · токены пустые |
| 006 | Настройки через pydantic-settings, чтение только из env | **done** · без env — `SettingsError` |
| 007 | Логи в stdout: время, уровень, logger, сообщение | **done** · `app/logging.py`, формат asctime level name message |
| 008 | Ruff: lint + format, команда в README | **done** · `ruff check .` зелёный |
| 009 | Pytest подключён, один дымовой тест `test_version` | **done** · 1 passed |
| 010 | Константа версии `0.0.1` в одном месте | **done** · `app.__version__`, тест сверяет с пакетом |

### B. Docker, локальный контур

| # | Пункт | Готово когда |
|---|---|---|
| 011 | `Dockerfile` API (не root-пользователь в контейнере) | **done** · `USER appuser` uid 1000; `docker` на этой машине нет, сборка на сервере |
| 012 | `.dockerignore` | **done** · без `.git`, `.env`, `.venv`, `tests` |
| 013 | `docker-compose.yml`: сервис `api` | **done** · сервис `api`, порт 8000 |
| 014 | Сервис `postgres:16` в compose, volume, healthcheck | **done** · volume `postgres_data`, `pg_isready` |
| 015 | Сеть compose внутренняя, наружу только api:8000 | **done** · сеть `internal`; 5432 только в `docker-compose.local.yml` |
| 016 | `Makefile` или скрипты: `up`, `down`, `logs`, `test` | **done** · цели в Makefile, описаны в README |
| 017 | `worker` сервис в compose: тот же образ, другая команда | **done** · sleep-loop заглушка |
| 018 | Healthcheck контейнера api на `/health` | **done** · заглушка `app.health_stub`, compose healthcheck |
| 019 | Документ `deploy/LOCAL.md`: как поднять у себя за 10 минут | **done** |
| 020 | Фиксированные версии образов (не `latest` у postgres) | **done** · `postgres:16-alpine` |

### C. База

| # | Пункт | Готово когда |
|---|---|---|
| 021 | Имя БД и роль `idatagon` в init-скрипте postgres | **done** · `deploy/postgres/01-init.sql` |
| 022 | Alembic инициализирован | **done** · `alembic/`, ревизия `0001` baseline; online upgrade — когда поднят compose |
| 023 | Таблица `accounts` (id, kind, broker_account_id, created_at) | **done** · ревизия `0002` |
| 024 | Таблица `instruments` (ticker, figi, uid, lot, currency, class_code) | **done** · `uq_instruments_ticker_class`, ревизия `0003` |
| 025 | Таблица `universe_members` (instrument_id, reason, active, updated_at) | **done** · FK на instruments, ревизия `0004` |
| 026 | Таблица `candles` (instrument_id, tf, ts, o,h,l,c,v) unique(instrument,tf,ts) | **done** · `uq_candles_instrument_tf_ts`, ревизия `0005` |
| 027 | Таблица `orders` (наш uuid, sleeve, ticker, side, qty, type, status, broker_order_id, client_order_id) | **done** · unique `client_order_id`, ревизия `0006` |
| 028 | Таблица `fills` (order_id, qty, price, ts, raw jsonb) | **done** · FK на orders, ревизия `0007` |
| 029 | Таблица `positions` (sleeve, instrument_id, qty, avg_price) | **done** · unique sleeve+instrument, ревизия `0008` |
| 030 | Таблица `ledger_entries` (account_kind, amount, reason, ref, ts) | **done** · amount `numeric(18,2)`, ревизия `0009` |
| 031 | Таблица `equity_snapshots` (ts, trading_cash, vault, positions_value, equity) | **done** · ревизия `0010` |
| 032 | Индексы: candles(ts), orders(status, created_at), ledger(ts) | **done** · ревизия `0011`, у orders появился `created_at` |

### D. API-каркас

| # | Пункт | Готово когда |
|---|---|---|
| 033 | FastAPI factory `create_app()` | **done** · `app/main.py`, импорт без env и без ордеров |
| 034 | `GET /health` → `{status: ok}` | **done** · без БД |
| 035 | `GET /ready` → пинг Postgres | **done** · 503 `not_ready`, если БД недоступна |
| 036 | `GET /version` | **done** · `{"version": app.__version__}` |
| 037 | Единый JSON ошибок: `code`, `message` | **done** · 404 `{"code","message"}`; 422 тот же формат |
| 038 | CORS только localhost + `i.datagon.ru` | **done** · чужой Origin не в allow-list |
| 039 | Session/engine async SQLAlchemy + `get_db` | **done** · `/ready` через `Depends(get_db)` |
| 040 | Заголовок `X-App-Token` = `APP_AUTH_TOKEN` на все кроме health/ready | **done** · `/version` без токена 401 |
| 041 | `/docs` и `/redoc` тоже за токеном или выключены в prod | **done** · `APP_ENV=prod` выключает docs/openapi |
| 042 | Тесты API: health, ready, 401 | **done** · 4 passed |

### E. Деплой на 155.212.171.103

| # | Пункт | Готово когда |
|---|---|---|
| 043 | `deploy/SERVER.md`: IP, путь, домен, что лежит в git а что нет | **done** |
| 044 | Клон/pull репозитория в `/var/www/i_datagon_ru_usr/data/www/i.datagon.ru` | **done** · rsync в путь; GitHub всё ещё пустой |
| 045 | `.env` на сервере создан вручную, не из git | **done** · файл на сервере, chmod 600, не в git |
| 046 | Postgres на сервере (compose или системный) | **done** · системный PG 17, БД `idatagon`; `/ready` после 047 |
| 047 | Systemd или compose-restart для api+worker | **done** · `idatagon-api`/`worker` enabled; `/health` и `/ready` 200 |
| 048 | Nginx: `i.datagon.ru` → api :8000, статика из `web/` | **done** · `/` и `/index.html` 200 из `web/`, `/health` 200 через :8000 |
| 049 | HTTPS (существующий сертификат хостинга / let’s encrypt как есть у панели) | **done** · LE панели до 2027-01-09; HTTP `301` → HTTPS |
| 050 | Скрипт `deploy/release.sh`: git pull, migrate, restart | **done** · pull + alembic + restart; `/health` 200 |
| 051 | Логи api/worker в journald или файлы под путём хостинга | **done** · `tail -n 100` `data/logs/idatagon-{api,worker}.log` |
| 052 | Не слушать 5432 с `0.0.0.0` | **done** · `ss`/`lsof`: только `127.0.0.1:5432` |

### F. Адаптер T-Invest sandbox

| # | Пункт | Готово когда |
|---|---|---|
| 053 | Порт `BrokerPort` (протокол/ABC): account, candles, prices, post_order, cancel, portfolio | **done** · ABC + 6 тестов на `FakeBroker` |
| 054 | Пакет `app/broker/tinkoff.py`, SDK `tinkoff-investments` | **done** · `from app.broker.tinkoff import Client` |
| 055 | Target только `INVEST_GRPC_API_SANDBOX` | **done** · default sandbox; live только `TINKOFF_LIVE=1` / `live=True` |
| 056 | Токен только `TINKOFF_SANDBOX_TOKEN` | **done** · пустой токен → JSON `broker_token`, не traceback |
| 057 | `OpenSandboxAccount` + сохранить `broker_account_id` в `accounts` | **done** · повтор с тем же id не зовёт OpenSandboxAccount |
| 058 | `SandboxPayIn` на 1 000 000 RUB если кэш ниже депозита | **done** · докидывает gap до 1 млн; если уже есть — skip |
| 059 | Получение счетов и портфеля sandbox | **done** · `sandbox_snapshot()` → `{accounts, portfolio}` |
| 060 | Свечи по FIGI/instrument_id, запись в `candles` | **done** · повторный fetch пропускает тот же `instrument_id+tf+ts` |
| 061 | Last prices пачкой | **done** · `last_price_map` / `last_prices_by_ticker` → ticker→price |
| 062 | Поиск инструмента по ticker (MOEX) | **done** · TQBR → `instruments` (ticker/figi/uid/lot) |
| 063 | Статус торгов инструмента | **done** · `worker.market.trading_status_view` / `tradable` |
| 064 | Выставление sandbox-ордера через порт, **без** вызова из стратегии | **done** · `place_order(port, …)` + fake; live `post_sandbox_order` skip |
| 065 | Отмена ордера | **done** · `cancel_order` + `apply_cancel` → `orders.status=cancelled` |
| 066 | Маппинг ticker ↔ figi ↔ uid в `instruments` | **done** · `resolve_mapped_instrument`: повтор без брокера |
| 067 | `raw` jsonb ответа брокера в fills/orders | **done** · `last_order_view` отдаёт `raw`; `orders.raw` 0012 |
| 068 | Клиентский `FakeBroker` для тестов | **done** · `app.broker.fake`; рукав на порте без tinkoff |

### G. Книга и журнал

| # | Пункт | Готово когда |
|---|---|---|
| 069 | Открытие внутреннего счёта `trading_cash` | **done** · `account_kind` = `trading_cash` |
| 070 | Проводка депозита 1 млн в ledger | **done** · `apply_deposit` → баланс `1_000_000` |
| 071 | Создание ордера в БД до похода к брокеру | **done** · `draft_order` → нет брокера: `rejected` + reason |
| 072 | `client_order_id` идемпотентный | **done** · повтор: тот же ордер, `accept_fill` не второй fill |
| 073 | Применение fill → position + ledger | **done** · `apply_fill`: qty/avg_price + проводка cash |
| 074 | Пересчёт позиции после частичного fill | **done** · два fill: 4×100 + 6×110 → qty 10, avg 106 |
| 075 | Комиссия: поле и вычет из cash (хотя бы 0) | **done** · `fills.commission` + проводка; equity видит вычет |
| 076 | Снимок equity по расписанию воркера | **done** · `worker.equity.take_snapshot` → строка `equity_snapshots` |
| 077 | `GET /portfolio` | **done** · JSON `cash`, `vault`, `positions`, `equity` |
| 078 | `GET /orders` | **done** · `?status=` фильтрует; JSON `orders` |
| 079 | `GET /ledger` | **done** · лента `entries` новее сверху |
| 080 | Расхождение «наш ledger vs sandbox portfolio» в лог, не молча | **done** · `ALERT drift` в лог если \|Δcash\| > 1 |

### H. Вселенная бумаг

| # | Пункт | Готово когда |
|---|---|---|
| 081 | Джоба: выгрузить акции MOEX в `instruments` | **done** · `run_moex_dump` TQBR → `instruments`, не пусто |
| 082 | Фильтр: инструмент торгуется | **done** · неторгуемые `universe_members.active=false` |
| 083 | Фильтр: лотность и валюта RUB | **done** · не RUB или lot < 1 → `active=false` |
| 084 | Фильтр ликвидности (оборот/спред — порог в конфиге) | **done** · оборот/спред из конфига; неликвид `active=false` |
| 085 | Конфиг `UNIVERSE_MAX` (старт 15, потом поднять) | **done** · потолок 15; лишние `active=false` |
| 086 | Причина включения в `universe_members.reason` | **done** · `reason` объясняет вход или отсев |
| 087 | `GET /universe` | **done** · JSON `members` только `active=true` |
| 088 | Запрет ордера вне вселенной в risk (заглушка функции) | **done** · `gate_universe`: тикер не из сита → `rejected` |

### I. Первый рукав стратегии (без ИИ)

| # | Пункт | Готово когда |
|---|---|---|
| 089 | Интерфейс `Strategy`: `on_bar(ctx) -> Signal \| None` | **done** · `IdleStrategy` + `FlatStrategy` через `dispatch` |
| 090 | Рукав `sma_cross` (дневки, быстрая/медленная SMA) | **done** · `SmaCrossStrategy` → buy/sell/flat |
| 091 | Параметры рукава в конфиге, не в промпте | **done** · `SMA_FAST`/`SLOW` + `config/sleeves.yaml` |
| 092 | Размер позиции: доля от капитала рукава | **done** · 1 млн → 10% имени = 100k |
| 093 | Стоп в правиле (фиксированный ATR или %) | **done** · 5% стоп → `kind=exit` |
| 094 | Таблица `signals` (sleeve, ticker, ts, kind, payload) | **done** · ревизия `0014`, пишется при решении |
| 095 | Воркер: закрытие дневного бара → `on_bar` | **done** · `on_daily_close` после 15:50 UTC |
| 096 | Ордер только после risk gate | **done** · deny `gate_universe` → нет `post_order` |
| 097 | Фикстуры свечей, бэктест-на-столе одного тикера | **done** · CSV SBER, `replay` без брокера |
| 098 | `GET /sleeves/sma_cross` : последние сигналы и PnL рукава | **done** · signals + pnl для кабины |

### J. Риск, аллокатор, сейф

| # | Пункт | Готово когда |
|---|---|---|
| 099 | Risk: тикер ∈ universe | **done** · `gate_ticker` только active universe |
| 100 | Risk: вес имени ≤ 10% equity | **done** · 400×250 на 1 млн ок, 401 — deny |
| 101 | Risk: вес рукава ≤ 40% equity | **done** · 1600×250 на 1 млн ок, 1601 — deny |
| 102 | Risk: дневной убыток ≤ порога → новые входы запрещены | **done** · 4% > 3% → buy deny, sell ок |
| 103 | Risk: один вход на тикер на бар | **done** · второй buy того же тикера — deny |
| 104 | Kill-switch в БД/флаг: все новые ордера deny | **done** · `POST /kill` `/unkill`, флаг `flags` |
| 105 | Аллокатор: пока один рукав = 100% в пределах 101 | **done** · sma_cross = 400k на 1 млн |
| 106 | Сейф: 50% realized PnL, пока vault < депозита | **done** · 10+20+40k → vault 35k |
| 107 | Сейф: 20% realized PnL после перекрытия ввода | **done** · после 1 млн → 20% от 100k = 20k |
| 108 | Сейф не трогает нереализованную переоценку | **done** · mark 100→110, vault тот же |
| 109 | `GET /vault` : депозит, накоплено, фаза 50/20, осталось до перекрытия | **done** · deposit/accumulated/phase/remaining |
| 110 | Аллокатор equal-weight на N рукавов (заготовка, N=1) | **done** · N=1 → 1, N=2 → 0.5/0.5 |

### K. Тонкая кабина

| # | Пункт | Готово когда |
|---|---|---|
| 111 | Статика `web/index.html` + минимум CSS, без SPA-сборки | **done** · один HTML+CSS, без сборки |
| 112 | Экран портфеля: cash, vault, equity, позиции | **done** · кабина читает `/portfolio` |
| 113 | Экран рукавов и сигналов | **done** · кабина читает `/sleeves/sma_cross` |
| 114 | Экран журнала ордеров и ledger | **done** · кабина читает `/orders` и `/ledger` |
| 115 | Кнопка kill-switch | **done** · кнопка Kill → `POST /kill` |
| 116 | Токен кабины: prompt/local field, не хардкод в репо | **done** · поле + localStorage, в репо пусто |
| 117 | В JS нет URL и токена Тинькоффа | **done** · grep `web/` чистый |
| 118 | Кабина отдаётся с того же домена, CORS не нужен для неё | **done** · `/` с API, fetch относительный |

### L. Второй контур данных и рукавов

| # | Пункт | Готово когда |
|---|---|---|
| 119 | Фундамент: вызов GetAssetFundamentals, таблица `fundamentals` | **done** · снимок по тикеру, ревизия `0016` |
| 120 | Сито вселенной может учитывать фундамент (флаг, default off) | **done** · `UNIVERSE_FUNDAMENTALS=0` |
| 121 | Рукав 2: `donchian_breakout` или mean-reversion — один, на выбор | **done** · `donchian_breakout` свои сигналы |
| 122 | Параллельный прогон двух рукавов на одних свечах | **done** · `sma_cross` + `donchian_breakout` |
| 123 | Аллокатор equal-weight 50/50 с потолком 101 | **done** · `GET /allocation` 0.5/0.5 × 200k |
| 124 | `GET /sleeves` сводка PnL всех рукавов | **done** · сводка + таблица в кабине |
| 125 | Недельный paper-отчёт в таблицу `reports` | **done** · по snapshots, ревизия `0017` |
| 126 | Расширение `UNIVERSE_MAX` (конфиг), не снятие сита | **done** · конфиг 30, сито на месте |

### M. Агенты (только после журнала)

| # | Пункт | Готово когда |
|---|---|---|
| 127 | Таблица `agent_runs` (role, input, output, ts) | **done** · промпт без токенов, ревизия `0018` |
| 128 | Таблица `agent_proposals` (kind, payload jsonb, status) | **done** · 4 статуса, ревизия `0019` |
| 129 | JSON-схема `propose_order`: ticker, side, qty, stop, reason, sleeve | **done** · pydantic, иначе 422 |
| 130 | JSON-схема `propose_weights`: список sleeve→weight, сумма 1 | **done** · сумма 1, иначе 422 |
| 131 | Агент `analyst`: rationale по уже существующему signal, **ордер не создаёт** | **done** · только текст в `agent_runs` |
| 132 | Агент `allocator_advisor`: пишет `propose_weights`, не меняет веса сам | **done** · proposal, веса не трогает |
| 133 | Инструменты модели: `get_bars`, `get_positions`, `propose_*`. Нет `place_order` | **done** · grep `app/agent` чистый |
| 134 | `POST /proposals/{id}/approve` → риск → ордер/веса | **done** · без approve ордер/веса не едут |
| 135 | `POST /proposals/{id}/reject` | **done** · статус rejected |
| 136 | Экран кабины: предложения агента, да/нет | **done** · Да/Нет на токене кабины |
| 137 | Лимит частоты агента (раз на бар / раз в N минут) | **done** · раз на бар и раз в 15 мин |
| 138 | Выключатель `AGENTS_ENABLED=false` по умолчанию | **done** · `AGENTS_ENABLED=0`, агенты молчат |

### N. Новости и research

| # | Пункт | Готово когда |
|---|---|---|
| 139 | Таблица `news_events` (ts, source, title, url, tickers[], raw) | **done** · unique url и source+id |
| 140 | Ingest одного RSS (конфиг URL) | **done** · `NEWS_RSS_URL`, джоба кладёт строки |
| 141 | Грубая привязка новости к ticker (словарь имён) | **done** · словарь имён, miss в лог |
| 142 | Research-job: окно доходности T−1…T+N по свечам | **done** · `news_studies`, окно T−1…T+N |
| 143 | Запрет lookahead: новость с ts ≥ бара не попадает в фичи этого бара | **done** · тест: ts ≥ бара нет в фичах |
| 144 | Агент `news_researcher` только offline, пишет study, не proposal ордера | **done** · study offline, нет пути в ордер |
| 145 | Вeto-правило без ИИ: «день отчёта / флаг в календаре — не входить» | **done** · buy в день отчёта reject |
| 146 | Календарь отчётов — таблица, ручное наполнение на старте | **done** · SBER/GAZP/LKOH в `earnings_days` |

### O. Эксплуатация и безопасность

| # | Пункт | Готово когда |
|---|---|---|
| 147 | Бэкап Postgres: скрипт + cron, файл вне webroot | **done** · дамп вне webroot, restore на копии ок |
| 148 | Ротация логов | **done** · daily, 7 копий, copytruncate, maxsize 50M |
| 149 | Секреты не в access-логах nginx | **done** · combined, без заголовка токена |
| 150 | Rate limit на API кабины | **done** · 120/мин на IP, 429 |
| 151 | `GET /admin/drift` сверка книги и sandbox | **done** · только с `X-App-Token` |
| 152 | Документ инцидента: что делать если ушёл боевой токен | **done** · `deploy/INCIDENT-LIVE-TOKEN.md` |
| 153 | Чеклист «ещё не live»: 10 пунктов, все красные | **done** · `deploy/NOT-LIVE.md`, все RED |
| 154 | Метрика простая: счётчик ордеров, last worker beat в `/ready` | **done** · `orders`, `worker_beat`, `worker_alive` |
| 155 | Telegram optional: только алерт kill/drift, не торговля | **done** · `TELEGRAM_ENABLED=0`, только kill/drift |
| 156 | Запрет TRACE/лишних методов на nginx если панель не мешает | **done** · TRACE/лишние → 405, факт в `deploy/NGINX-METHODS.md` |

---

## Порядок фаз (не прыгать)

| Фаза | Пункты | Смысл |
|---|---|---|
| A–B | 001–020 | Каркас и Docker |
| C–D | 021–042 | БД и API |
| E | 043–052 | Сервер 155.212.171.103 |
| F–G | 053–080 | Sandbox и книга |
| H–I | 081–098 | Вселенная и один рукав без ИИ |
| J–K | 099–118 | Риск, сейф, кабина |
| L | 119–126 | Второй рукав |
| M–N | 127–146 | Агенты и новости |
| O | 147–156 | Эксплуатация |

ИИ не начинается раньше **127**, и только если 089–118 уже `done`.

## Итерация прямо сейчас

Следующий проход: нет. Осталось **0** из 156.
