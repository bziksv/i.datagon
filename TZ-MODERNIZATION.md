# ТЗ модернизации i.datagon: доказуемый результат и контролируемый риск

Актуально после аудита кабинета **v1.2** и разбора концепции из
[shared chat](https://chatgpt.com/share/6acca314-4d88-83eb-bc8b-e0dc6c846692).

Связанные документы: [TZ.md](TZ.md) · [TZ-CABIN.md](TZ-CABIN.md) ·
[TZ-ADVISORY.md](TZ-ADVISORY.md) · [docs/PRODUCT.md](docs/PRODUCT.md).

## 1. Цель и границы

Цель — превратить paper/sandbox-лабораторию в проверяемую систему управления
капиталом, которая:

- считает финансовый результат после расходов;
- показывает происхождение каждой цифры и каждого решения;
- допускает стратегию к капиталу только после воспроизводимой проверки;
- блокирует увеличение риска при неполных или устаревших данных;
- умеет оставить капитал в кэше, если преимущество не доказано;
- в перспективе готова к автономному исполнению в жёстких лимитах.

Доходность не обещается. Live-торговля, боевой токен и автоматический переход
к реальным деньгам в это ТЗ не входят. Любой live-контур требует отдельного
аудита и явного решения.

## 2. Архитектурные инварианты

1. Стратегия создаёт только торговое намерение; она не отправляет ордер и не
   меняет лимиты.
2. Любое увеличение риска проходит один серверный risk engine.
3. При отсутствии обязательных данных решение — `deny`, а не пропуск проверки.
4. Ордер, исполнение, проводка и позиция — разные сущности.
5. Книга и `PortfolioValuation` — единственный источник финансовых показателей
   для API, UI, отчётов и риска.
6. История не переписывается: исправление выполняется компенсирующей записью.
7. Для каждой цифры доступна цепочка: источник → запись → версия расчёта →
   отображаемое значение.
8. Paper и будущий live-адаптеры разделены; тестовая сборка не содержит
   доступного пути к live.

## 3. Подтверждённые разрывы текущей версии

### P0

- `app/book/portfolio.py` и `app/book/commission.py`: позиция оценивается как
  `qty × avg_price`, то есть по себестоимости, а не по рынку.
- `app/main.py:approve_proposal`: капитал берётся только из ledger cash+vault;
  в `price` передаётся `stop`, а открытая экспозиция имени и рукава не
  рассчитывается.
- `app/risk/gate.py`: проверки цены/equity условны; при неполном контексте часть
  лимитов просто не запускается. `start_equity` по умолчанию равна текущей,
  поэтому дневной убыток может стать нулевым.
- `app/book/orders.py:accept_fill`: после первого fill отклоняется любой
  следующий fill того же ордера; корректные частичные исполнения невозможны.
- `app/strategy/backtest.py` и `app/strategy/desk.py`: прогон считает сигналы,
  но не моделирует сделки, кэш, расходы, PnL и просадку.
- `app/main.py:approve_proposal`: применяется `FakeBroker`, а созданный ордер
  не образует постоянный жизненный цикл в БД.

### P1

- Нет TWR/MWR с учётом внешних денежных потоков.
- Нет единого атрибутирования realized/unrealized PnL по рукавам.
- Нет источника, времени и качества оценочной цены.
- Нет состояния ордера `unknown` и обязательной reconciliation после тайм-аута
  или рестарта.
- Веса рукавов не зависят от out-of-sample, paper-forward, издержек и
  корреляций.
- UI не показывает net PnL, max drawdown, качество данных и полный путь решения.

## 4. Целевая финансовая модель

### 4.1. Оценка

`Equity = trading_cash + vault + market_value + receivables - liabilities`

Для каждой позиции хранятся отдельно:

- количество и средневзвешенная себестоимость;
- рыночная цена, источник, `as_of`, статус свежести;
- market value;
- unrealized PnL;
- realized gross PnL;
- комиссии, сборы, налоги и прочие расходы;
- realized net PnL.

При отсутствии свежей цены equity получает статус `partial`/`stale`; UI не
подменяет неизвестное значение нулём.

### 4.2. Доходность

- Net PnL: изменение equity за вычетом внешних пополнений/изъятий.
- TWR: сравнение стратегий и периодов с разрывом на внешних cash flow.
- MWR/XIRR: результат личного капитала при достаточном наборе датированных
  потоков.
- Drawdown: отклонение equity от предыдущего максимума.
- Метод себестоимости v1: средневзвешенная стоимость, зафиксированная версией
  расчёта.

### 4.3. Контрольный пример

Покупка 100 × 1 000 ₽, комиссия 100 ₽; продажа 100 × 1 030 ₽, комиссия 100 ₽:

- gross PnL = 3 000 ₽;
- costs = 200 ₽;
- realized net PnL = 2 800 ₽.

Результат одинаков в карточке сделки, книге, портфеле, отчёте рукава и
контрольной выгрузке.

## 5. Целевой бэктест

Для `sma_cross`, `donchian_breakout`, `rsi_reversion`, `ema_scalp`:

- последовательный доступ только к уже закрытым барам;
- сигнал на баре `t`, исполнение не раньше доступной цены `t+1`;
- лоты, кэш, размер позиции, стопы и гэпы;
- комиссия, spread и configurable slippage;
- ограничение участия в объёме;
- пропуски и устаревшие данные;
- mark-to-market открытой позиции на конец периода;
- benchmark buy-and-hold на тех же датах и с теми же cash constraints.

Обязательные метрики: net PnL, total return, CAGR, max drawdown, Sharpe,
Sortino, win rate, profit factor, expectancy, turnover, exposure, costs,
benchmark return и excess return.

Контуры проверки: in-sample, out-of-sample, walk-forward, sensitivity к
параметрам и расходам. Эксперимент хранит hash данных, версию кода,
конфигурацию и полный trade ledger.

## 6. Целевая риск-политика

### 6.1. Полный RiskContext

Каждое торговое намерение получает атомарный снимок:

- актуальная цена и stop как разные поля;
- equity, free cash, reserved cash;
- текущие позиции и активные заявки;
- экспозиция имени, рукава, валюты и портфеля;
- start-of-day equity и текущий drawdown;
- свежесть цены/свечей и состояние брокера;
- ликвидность, лот и ожидаемые расходы.

Отсутствие любого обязательного поля блокирует риск-увеличивающую заявку.
Сокращение риска допускается отдельной явно проверяемой политикой.

### 6.2. Размер позиции

`qty_risk = floor((equity × risk_per_trade) /
                  (abs(entry - stop) + unit_costs))`

Финальный qty — минимум ограничений по риску сделки, свободному капиталу,
концентрации имени, бюджету рукава, ликвидности, лотности и портфельному риску.

Черновые значения из концепции (`0.25%` на сделку, `1%` в день, `8%` drawdown,
`10%` на имя, `40%` в рукавах) не активируются автоматически. Они становятся
настройками только после отдельного утверждения и тестов.

### 6.3. Аварийная логика

- kill-switch блокирует новые risk-increasing ордера;
- unknown broker/order state блокирует повторную отправку;
- stale data, потеря связи, max drawdown и дневной лимит дают server-side deny;
- отмена заявок и закрытие позиций — отдельные действия;
- восстановление требует reconciliation и явного resume;
- каждый allow/deny сохраняет код, объяснение и снимок RiskContext.

## 7. Жизненный цикл ордера

`proposed → risk_rejected | risk_approved → submitted →
acknowledged | unknown → partially_filled → filled`

Дополнительные переходы: `cancel_pending → cancelled`; `unknown → reconciled`
с последующим восстановлением фактического состояния.

Требования:

- уникальный `client_order_id`;
- уникальный внешний `execution_id` у fill;
- сумма fills не превышает qty ордера;
- повтор события идемпотентен;
- тайм-аут не означает rejection и не вызывает слепой retry;
- после рестарта незавершённые заявки сверяются с исполнителем;
- ордер и risk decision записываются до внешнего вызова.

## 8. Целевой интерфейс

### Обзор — центр капитала

- equity, net PnL, TWR, max drawdown, free/reserved cash;
- результат и расходы каждого рукава;
- качество и свежесть данных;
- режим PAPER/SANDBOX, разрешение новых заявок, причины блокировки;
- очередь решений и критические расхождения.

### Портфель

Себестоимость и market value раздельно, realized/unrealized PnL, цена и
`as_of`, обязательства, резервы, сейф, reconciliation.

### Стратегии

Backtest/OOS/walk-forward, benchmark, equity/drawdown curves, сделки,
издержки, устойчивость параметров и статус допуска к капиталу.

### Рекомендации и агенты

Тезис, факты и даты, entry/stop/qty, плановый риск, invalidation,
альтернативы, все risk checks и ожидаемое изменение портфеля.

### Рынок и журнал

Качество данных, stale/missing status, ликвидность; сквозной timeline:
signal → proposal → risk decision → order → fills → ledger → PnL.

### Настройки

Версионированные лимиты с датой вступления, автором, причиной и историей.

## 9. План внедрения

Статусы: `todo` · `doing` · `done` · `blocked`.

### M0. Аудит и страховочная сетка

| ID | Задача | Готово когда | Статус |
|---|---|---|---|
| M001 | Карта денежных и торговых путей | Все routes/jobs/functions, меняющие деньги, позиции, ордера и лимиты, перечислены | doing |
| M002 | Characterization tests | Зафиксированы текущие deposit/fill/approve/risk/backtest сценарии | todo |
| M003 | Режим safety | В тестовой/prod paper-конфигурации live недостижим, startup это проверяет | todo |

### M1. Книга, цены и PnL — P0

| ID | Задача | Готово когда | Статус |
|---|---|---|---|
| M101 | `PortfolioValuation` | Один сервис используется portfolio/status/risk/reports | todo |
| M102 | Market marks | Цена имеет source/as_of/quality; stale/missing видны в API | done |
| M103 | Realized/unrealized PnL | Контрольный пример даёт 2 800 ₽ net | done |
| M104 | Денежные потоки и TWR | Deposit не считается прибылью; период разбивается на flows | done |
| M105 | Drawdown и дневной старт | Peak/start-of-day воспроизводимы по snapshots | todo |
| M106 | Расходы и доходы | Commission/fees/tax/dividend раздельны | todo |
| M107 | Версия расчёта | Исторический отчёт воспроизводится той же версией | todo |

### M2. Исполнения — P0

| ID | Задача | Готово когда | Статус |
|---|---|---|---|
| M201 | Идентичность fill | Повтор execution_id no-op, новый partial fill применяется | done |
| M202 | Статусы ордера | Поддержаны partial/cancel_pending/unknown/reconciled | done |
| M203 | Персистентный approve | Risk decision и order записаны до отправки | done |
| M204 | Reconciliation | Рестарт/timeout восстанавливает фактическое состояние без дубля | done |
| M205 | Immutable audit | Коррекция — компенсирующая запись, история не удаляется | todo |

### M3. Risk engine — P0

| ID | Задача | Готово когда | Статус |
|---|---|---|---|
| M301 | Обязательный `RiskContext` | Нет условного пропуска price/equity checks | done |
| M302 | Совокупная экспозиция | Позиции + active orders + partial fills входят в лимиты | done |
| M303 | Risk-based sizing | Qty ограничен entry/stop/costs и всеми hard limits | done |
| M304 | Data/broker health gates | stale/missing/unknown блокируют увеличение риска | done |
| M305 | Portfolio limits | Daily loss, max DD, gross/net exposure, concentration | done |
| M306 | Decision audit | Каждый check имеет code, inputs, allow/deny и explanation | done |
| M307 | Версионированные лимиты | Изменение через единый API и попадает в audit trail | done |

### M4. Доказательный бэктест — P0

| ID | Задача | Готово когда | Статус |
|---|---|---|---|
| M401 | Execution simulator | Next-bar execution, cash, lots, stops, gaps, costs | done |
| M402 | Trade/equity ledger | Каждая метрика раскрывается до сделки и бара | done |
| M403 | Метрики | PnL/CAGR/DD/Sharpe/Sortino/PF/expectancy/turnover/exposure | done |
| M404 | Benchmark | Та же выборка и капитал; показан excess return | done |
| M405 | IS/OOS/walk-forward | Периоды раздельны, future leakage тестируется | done |
| M406 | Reproducible experiments | Data/config/code hashes и результат сохранены | done |
| M407 | Qualification gate | Без достаточной статистики стратегия не получает капитал | done |

### M5. Аллокация — P1

| ID | Задача | Готово когда | Статус |
|---|---|---|---|
| M501 | Strategy evidence score | OOS, paper-forward, costs, DD и uncertainty объяснимы | todo |
| M502 | Correlation/risk budgets | Веса учитывают совокупный риск, а не только equal-weight | todo |
| M503 | Cash fallback | Недоказанный edge даёт 0% стратегии и остаток в cash | done |
| M504 | Режим рекомендаций | Веса меняются только после approve; есть cap/floor/cooldown | todo |

### M6. Кабина и наблюдаемость — P1

| ID | Задача | Готово когда | Статус |
|---|---|---|---|
| M601 | Новый Overview | Net PnL/DD/free cash/data quality/strategy attribution | todo |
| M602 | Portfolio drill-down | Cost/market/PnL/mark freshness по каждой позиции | todo |
| M603 | Strategy report | Backtest/OOS/benchmark/trades/costs/qualification | todo |
| M604 | Decision card | Thesis → sizing → checks → effect → invalidation | todo |
| M605 | Сквозной журнал | Signal-to-ledger timeline и audit настроек | todo |
| M606 | Alerts/metrics | stale data, drift, unknown order, risk halt, worker lag | todo |

### M7. Допуск

| Gate | Условие | Статус |
|---|---|---|
| G1 Учёт | Контрольные кейсы и reconciliation без расхождений | blocked |
| G2 Бэктест | Нет leakage, расходы и benchmark воспроизводимы | blocked |
| G3 Paper-forward | Заранее заданный период на новых данных | blocked |
| G4 Аварийные испытания | Timeout/restart/stale/duplicate/limit tests | blocked |
| G5 Live decision | Отдельный security/legal/execution audit | blocked |

## 10. Новые API-контракты

- `GET /capital/summary` — valuation, PnL, returns, DD, freshness.
- `GET /positions/{id}/valuation` — cost, mark, realized/unrealized, lineage.
- `POST /backtests` / `GET /backtests/{id}` — воспроизводимый experiment.
- `GET /backtests/{id}/trades` — trade ledger.
- `POST /risk/evaluate` — чистая оценка intent без исполнения.
- `GET /risk/decisions/{id}` — полный check trail.
- `GET /data-quality` — freshness/completeness/drift.
- `GET /audit/timeline` — сквозная история объекта.

Существующие endpoints сохраняются на период миграции; новые финансовые поля
не вычисляются независимо в route handlers.

## 11. Definition of Done

Пункт считается `done`, только если:

1. Есть миграция/контракт и обратная совместимость либо план миграции.
2. Есть unit + integration + негативные тесты.
3. Финансовый результат сверяется контрольным расчётом.
4. Ошибка/неполные данные не превращаются в ноль или разрешение.
5. UI показывает источник и время критичных данных.
6. Документация обновлена.
7. Live остаётся выключен.

