-- Официальный образ уже создаёт POSTGRES_USER / POSTGRES_DB.
-- Скрипт фиксирует роль и права под DATABASE_URL из .env.example.

ALTER ROLE idatagon WITH LOGIN;
GRANT ALL PRIVILEGES ON DATABASE idatagon TO idatagon;
GRANT ALL ON SCHEMA public TO idatagon;
