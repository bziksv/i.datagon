#!/usr/bin/env bash
# Дамп Postgres вне webroot. .env не source, URL не в argv.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export PYTHONPATH="${ROOT}${PYTHONPATH:+:$PYTHONPATH}"
export WEBROOT="${WEBROOT:-/var/www/i_datagon_ru_usr/data/www/i.datagon.ru}"
export BACKUP_DIR="${BACKUP_DIR:-/var/www/i_datagon_ru_usr/data/backups}"
export ENV_FILE="${ENV_FILE:-${WEBROOT}/.env}"

umask 077
python3 -m app.ops.pg_backup dump
