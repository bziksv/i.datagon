# Методы nginx

Факт (локально, 2026-10-12):

- Кабина и API: только `GET`, `POST`, `HEAD`, `OPTIONS`.
- `TRACE`, `PUT`, `DELETE`, `PATCH`, `CONNECT` — `405`.
- FastPanel не мешает: в includes уже есть `if {}` (`https-redirect.includes.conf`). Тот же приём в `nginx-i.datagon.ru.snippet.conf`.
- На прод не выкладывалось в этом проходе. После вставки сниппета проверить: `curl -X TRACE -sI https://i.datagon.ru/` → 405.
