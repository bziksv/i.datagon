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

## HTTPS

Сертификат панели: Let’s Encrypt (`CN=i.datagon.ru`, до 2027-01-09).  
Nginx слушает `155.212.171.103:443`. HTTP → `301` на HTTPS. Renewal Let’s Encrypt идёт через тот же vhost на `:443`.  
Сниппет: `deploy/https-redirect.includes.conf` → `/etc/nginx/fastpanel2-sites/i_datagon_ru_usr/i.datagon.ru.includes`.

## Выкладка

С сервера, от root:

```
/var/www/i_datagon_ru_usr/data/www/i.datagon.ru/deploy/release.sh
```

`git pull` → `alembic upgrade head` → `systemctl restart idatagon-api idatagon-worker`. `.env` не из git.

## Логи

Файлы (хвост 100 строк):

```
tail -n 100 /var/www/i_datagon_ru_usr/data/logs/idatagon-api.log
tail -n 100 /var/www/i_datagon_ru_usr/data/logs/idatagon-worker.log
```

journald (юниты пишут старт/стоп; приложение — в файлы):

```
journalctl -u idatagon-api -n 100
journalctl -u idatagon-worker -n 100
```

## Postgres 5432

Системный PostgreSQL 17: `listen_addresses = localhost`.  
Проверка 2026-10-12: `ss`/`lsof` — только `127.0.0.1:5432`, не `0.0.0.0`.  
`docker-compose.local.yml` на сервере не подключать.
