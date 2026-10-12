# Локальный контур за 10 минут

Нужны: Python 3.12+, Docker (для `make up`), git.

## 1. Код и env

```bash
git clone https://github.com/bziksv/i.datagon.git
cd i.datagon
cp .env.example .env
```

В `.env` пока достаточно пустых токенов, если не ходите в Тинькофф. `DATABASE_URL` для контейнеров можно не трогать: compose сам ставит `postgres` как хост.

## 2. Пакет и проверки без Docker

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
ruff check .
pytest
```

## 3. Поднять api + worker + postgres

```bash
make up
make logs
```

`make up` берёт `docker-compose.yml` и `docker-compose.local.yml` (Postgres на `localhost:5432`).

Проверка api: `http://127.0.0.1:8000/health` — `{"status":"ok"}`.

Остановка: `make down`.

## 4. Если Docker нет

Нужен локальный Postgres (Homebrew / Postgres.app). Один раз:

```bash
createuser -h localhost idatagon
createdb -h localhost -O idatagon idatagon
psql -h localhost -d postgres -c "ALTER USER idatagon WITH PASSWORD 'idatagon';"
cp .env.example .env
# обязательное для кабине:
#   APP_AUTH_TOKEN=local-cabin
# локальные пути (Mac):
#   WORKER_BEAT_PATH=data/logs/idatagon-worker.beat
#   PROPOSALS_PATH=data/proposals.json
#   CANDLE_DIR=data/candles
#   SANDBOX_DEPOSIT=1000000
.venv/bin/python -m app.ops.migrate
mkdir -p data/candles data/logs
# положить дневки TICKER.csv в data/candles (или сгенерировать демо)
.venv/bin/python -m app          # http://127.0.0.1:8000/
# в другом терминале:
.venv/bin/python -m worker
```

В кабине в поле «токен кабины» вставить тот же `APP_AUTH_TOKEN`, затем «Обновить».  
При старте API заливает депозит в ledger; воркер пишет heartbeat и сигналы в БД.

## Не делать

- Не коммитить `.env`
- Не подключать `docker-compose.local.yml` на сервере
- Не писать боевой токен Тинькоффа
