# Деплой на Ubuntu-сервер (Docker, HTTP на IP)

Стек: **nginx → gunicorn (Django) → PostgreSQL**, всё в Docker Compose.
Файлы: `deploy/docker-compose.prod.yml`, `deploy/nginx/app.conf`, `deploy/deploy.sh`,
переменные — `.env.prod` (из `deploy/.env.prod.example`).

Ниже — `SERVER_IP` = внешний IP сервера.

---

## 1. Предварительные требования

* Ubuntu 20.04+ с доступом по SSH и `sudo`.
* Открытый порт **80** (для демонстрации достаточно HTTP).
* ~2 ГБ свободной памяти и ~3 ГБ на диске под образы.

## 2. Установка Docker (если ещё нет)

```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker "$USER"
newgrp docker            # или перелогиниться
docker compose version   # проверка
```

## 3. Firewall

```bash
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw --force enable
```

## 4. Получить код

```bash
git clone https://github.com/BorisPetrov-boob/hop-and-barley-shop.git
cd hop-and-barley-shop
```

## 5. Настроить переменные

```bash
cp deploy/.env.prod.example .env.prod
nano .env.prod
```

Обязательно поменять:

| Переменная | Значение |
|---|---|
| `DJANGO_SECRET_KEY` | случайная строка: `python3 -c "import secrets;print(secrets.token_urlsafe(64))"` |
| `DJANGO_ALLOWED_HOSTS` | `SERVER_IP` |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | `http://SERVER_IP` |
| `POSTGRES_PASSWORD` и пароль внутри `DATABASE_URL` | одинаковый сложный пароль |

Для HTTP-деплоя строки `DJANGO_SECURE_SSL_REDIRECT=0`, `DJANGO_SESSION_COOKIE_SECURE=0`,
`DJANGO_CSRF_COOKIE_SECURE=0`, `DJANGO_SECURE_HSTS_SECONDS=0` уже стоят — так и надо.

## 6. Запуск

```bash
./deploy/deploy.sh
```

Скрипт соберёт образ и поднимет `db` + `web` + `nginx`. При первом старте `entrypoint.sh`
внутри `web`: дождётся БД → `migrate` → `collectstatic` → `seed_demo` (`SEED_DEMO=1`) → `gunicorn`.

Проверка:

```bash
curl -I http://SERVER_IP/                       # 200 OK
curl -s http://SERVER_IP/api/products/ | head   # JSON со списком товаров
```

Открыть в браузере: **`http://SERVER_IP/`**

| URL | Что |
|---|---|
| `http://SERVER_IP/` | витрина каталога (12 демо-товаров) |
| `http://SERVER_IP/api/docs/` | Swagger UI |
| `http://SERVER_IP/graphql/` | GraphQL (только для staff) |
| `http://SERVER_IP/admin/` | админка |

## 7. Суперпользователь для админки

```bash
docker compose -f deploy/docker-compose.prod.yml --env-file .env.prod \
  exec web python manage.py createsuperuser
```

Демо-покупатель (создан сидом): `buyer@example.com` / `buyerpass123` — у него есть
доставленный заказ, поэтому видно отзывы после покупки.

## 8. Обновление после `git push`

```bash
./deploy/deploy.sh
```

(миграции применяются автоматически при старте контейнера `web`)

## 9. Полезные команды

```bash
C="docker compose -f deploy/docker-compose.prod.yml --env-file .env.prod"

$C logs -f web            # логи приложения (там же письма — console backend)
$C ps                     # статус контейнеров
$C restart web            # перезапуск приложения
$C down                   # остановить (данные БД в volume сохраняются)
$C down -v                # остановить и УДАЛИТЬ данные БД

# бэкап / restore БД
$C exec db pg_dump -U hopbarley hopbarley > backup_$(date +%F).sql
cat backup_YYYY-MM-DD.sql | $C exec -T db psql -U hopbarley -d hopbarley
```

## 10. Диагностика

| Симптом | Причина / решение |
|---|---|
| `502 Bad Gateway` | `web` ещё стартует или упал — `$C logs web` |
| `Bad Request (400)` | `SERVER_IP` не добавлен в `DJANGO_ALLOWED_HOSTS` в `.env.prod` → поправить, `$C up -d` |
| CSRF-ошибка при входе/формах | добавить `http://SERVER_IP` в `DJANGO_CSRF_TRUSTED_ORIGINS`, пересоздать `web` |
| порт 80 занят | на хосте уже есть nginx/apache — остановить (`sudo systemctl stop nginx`) или сменить порт в compose |
| стили не грузятся | `$C exec web python manage.py collectstatic --noinput`; volume `static` монтируется и в `web`, и в `nginx` |

## 11. Переход на HTTPS (по желанию, если появится домен)

1. Направить домен A-записью на `SERVER_IP`.
2. В `.env.prod`: `DJANGO_ALLOWED_HOSTS=example.com`, `DJANGO_CSRF_TRUSTED_ORIGINS=https://example.com`,
   вернуть `DJANGO_SECURE_SSL_REDIRECT=1`, `DJANGO_SESSION_COOKIE_SECURE=1`,
   `DJANGO_CSRF_COOKIE_SECURE=1`, `DJANGO_SECURE_HSTS_SECONDS=2592000`.
3. Добавить в стек `certbot` (или поставить Caddy/Traefik перед nginx) и `listen 443 ssl` в `app.conf`.
