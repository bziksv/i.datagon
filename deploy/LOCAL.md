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

Каркас ставится и тестируется через venv (шаг 2). Образ и compose на этой машине разработки могут отсутствовать — тогда контур крутится на сервере.

## Не делать

- Не коммитить `.env`
- Не подключать `docker-compose.local.yml` на сервере
- Не писать боевой токен Тинькоффа
