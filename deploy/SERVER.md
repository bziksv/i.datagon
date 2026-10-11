# Сервер

Документ совпадает с паспортом в README.

| Поле | Значение |
|---|---|
| IP | `155.212.171.103` |
| Домен | `i.datagon.ru` |
| Путь | `/var/www/i_datagon_ru_usr/data/www/i.datagon.ru` |
| Репозиторий | https://github.com/bziksv/i.datagon |

## Что в git

- код (`app/`, `worker/`, `tests/`, `web/`)
- `Dockerfile`, `docker-compose.yml`, `docker-compose.local.yml`
- `alembic/`, `deploy/postgres/01-init.sql`
- `.env.example`, это руководство

## Чего в git нет

- `.env` (токены, `APP_AUTH_TOKEN`, боевые пароли)
- volume Postgres
- дампы, логи, `.venv`

На сервере `.env` создаётся вручную из `.env.example`.  
`APP_ENV=prod`.  
`docker-compose.local.yml` на сервере не подключать — порт 5432 наружу не публиковать.

Выкладка кода и systemd — следующие пункты ТЗ (044+).
