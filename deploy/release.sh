#!/usr/bin/env bash
# git pull → alembic от пользователя сайта → restart. .env не source от root.
set -euo pipefail

SITE="${SITE:-/var/www/i_datagon_ru_usr/data/www/i.datagon.ru}"
SITE_USER="${SITE_USER:-i_datagon_ru_usr}"
GIT="git -c safe.directory=${SITE}"

cd "$SITE"
test -f .env
test -x .venv/bin/alembic

echo "==> git pull"
$GIT pull --ff-only origin main
$GIT log -1 --oneline

chown -R "${SITE_USER}:${SITE_USER}" "$SITE"
chmod 600 "$SITE/.env"

echo "==> migrate"
as_site() {
  if [[ "$(id -u)" -eq 0 ]]; then
    runuser -u "$SITE_USER" -- "$@"
  else
    "$@"
  fi
}
as_site env SITE="$SITE" PYTHONPATH="$SITE" "$SITE/.venv/bin/python" -m app.ops.migrate

echo "==> restart"
systemctl restart idatagon-api idatagon-worker
systemctl is-active idatagon-api idatagon-worker
for i in 1 2 3 4 5 6 7 8; do
    if curl -sf -o /dev/null http://127.0.0.1:8000/health; then
        echo "ok $($GIT rev-parse --short HEAD)"
        exit 0
    fi
    sleep 0.5
done
echo "api did not answer /health" >&2
exit 1
