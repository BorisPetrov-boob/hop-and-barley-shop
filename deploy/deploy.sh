#!/usr/bin/env bash
# Деплой / обновление продакшн-стека. Запускать из любого места.
#   ./deploy/deploy.sh
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

COMPOSE="docker compose -f deploy/docker-compose.prod.yml --env-file .env.prod"

if [ ! -f .env.prod ]; then
  echo "Нет файла .env.prod. Создайте: cp deploy/.env.prod.example .env.prod && \$EDITOR .env.prod" >&2
  exit 1
fi

echo "==> git pull"
git pull --ff-only || echo "(pull пропущен — нет upstream или локальные изменения)"

echo "==> сборка и запуск"
$COMPOSE up -d --build

echo "==> статус"
$COMPOSE ps

echo "==> очистка старых образов"
docker image prune -f >/dev/null || true

echo "==> готово. Логи:  $COMPOSE logs -f web"
