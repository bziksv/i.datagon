# i.datagon

Лаборатория аллокации на Тинькофф sandbox: воркер, Postgres, тонкая кабина, рукава стратегий, сейф прибыли. Агенты подключаются позже и не ставят ордера сами.

Это не торговый совет. Чужие деньги не принимаем.

## Паспорт

| Поле | Значение |
|---|---|
| Репозиторий | https://github.com/bziksv/i.datagon |
| Сервер | `155.212.171.103` |
| Путь на сервере | `/var/www/i_datagon_ru_usr/data/www/i.datagon.ru` |
| Домен | `i.datagon.ru` |
| Старт | T-Invest sandbox, вирт. 1 000 000 ₽ |
| Брокер в браузере | нет, токен только на сервере |
| БД | PostgreSQL |
| Стек | Python 3.12, FastAPI, воркер, Docker, тонкая кабина |

## Команды

```bash
pip install -e ".[dev]"
ruff check .
ruff format .
pytest
```

Локальный контур (с публикацией 5432):

```bash
make up
make logs
make test
make down
```

На сервере: `docker compose -f docker-compose.yml up -d` — без `docker-compose.local.yml`.

## Документы

- Как поднять у себя: [deploy/LOCAL.md](deploy/LOCAL.md)
- Сервер: [deploy/SERVER.md](deploy/SERVER.md)
- Техническое задание и лист внедрения: [TZ.md](TZ.md)
- Правило работ: один пункт ТЗ = одна итерация
