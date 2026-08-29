#!/usr/bin/env sh
# Точка входа контейнера: ждём БД, применяем миграции, собираем статику.
set -e

echo "→ Ожидание PostgreSQL..."
python << 'PYEOF'
import os
import time
import sys

import psycopg

url = os.environ.get("DATABASE_URL", "")
if not url:
    sys.exit(0)
for attempt in range(30):
    try:
        psycopg.connect(url, connect_timeout=2).close()
        print("  БД доступна.")
        break
    except Exception as exc:  # noqa: BLE001
        print(f"  [{attempt + 1}/30] БД недоступна: {exc}")
        time.sleep(2)
else:
    print("Не удалось подключиться к БД.")
    sys.exit(1)
PYEOF

echo "→ Миграции..."
python manage.py migrate --noinput

echo "→ Сбор статики..."
python manage.py collectstatic --noinput --clear

if [ "${SEED_DEMO:-0}" = "1" ]; then
    echo "→ Демо-данные..."
    python manage.py seed_demo
fi

echo "→ Запуск: $*"
exec "$@"
