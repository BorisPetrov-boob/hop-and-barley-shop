# Hop &amp; Barley — интернет-магазин на Django / DRF

Интернет-магазин товаров для домашнего пивоварения (хмель, солод, дрожжи,
наборы). Статический HTML/CSS‑шаблон
[Hop-and-Barley](https://github.com/MagicCodeGit/Hop-and-Barley) превращён
в полноценное приложение:

* **веб‑интерфейс** на Django (шаблоны, сессии, session‑аутентификация);
* **REST API** на DRF с авторизацией по **JWT**;
* **GraphQL**‑эндпоинт для аналитики (бонус);
* инфраструктура: **PostgreSQL + Docker Compose**;
* качество: типизация, линтеры, тесты (**покрытие ~88 %**), CI.

---

## Содержание

* [Стек](#стек)
* [Быстрый старт (Docker)](#быстрый-старт-docker)
* [Локальный запуск (uv)](#локальный-запуск-без-docker-uv)
* [Переменные окружения](#переменные-окружения)
* [Структура проекта](#структура-проекта)
* [Модель данных](#модель-данных)
* [Веб‑интерфейс](#веб-интерфейс)
* [REST API и JWT](#rest-api-и-jwt)
* [GraphQL‑аналитика](#graphql-аналитика-бонус)
* [Админка](#админ-панель)
* [Тесты, линтеры, типы](#тесты-линтеры-типы)
* [CI/CD](#cicd)
* [Git workflow](#git-workflow)
* [Чек‑лист по ТЗ](#чек-лист-по-тз)

---

## Стек

| Область        | Технологии                                                        |
|----------------|-------------------------------------------------------------------|
| Backend        | Python 3.13, Django 5.2 LTS                                       |
| API            | Django REST Framework 3.16, SimpleJWT, drf-spectacular (OpenAPI)  |
| GraphQL        | graphene-django 3.2                                              |
| БД             | PostgreSQL 17 (psycopg 3)                                         |
| Фильтры        | django-filter                                                    |
| Статика        | WhiteNoise                                                       |
| Менеджер пакетов | **uv** (`pyproject.toml` + `uv.lock`)                          |
| Качество       | ruff (линт + формат), mypy + django-stubs, pytest + pytest-django + coverage |
| Инфраструктура | Docker, Docker Compose, GitHub Actions                           |

---

## Быстрый старт (Docker)

Требуется Docker и Docker Compose.

```bash
cp .env.example .env
docker compose up --build
```

Что происходит при старте контейнера `web` (см. `docker/entrypoint.sh`):

1. ожидание готовности PostgreSQL;
2. `migrate`;
3. `collectstatic`;
4. `seed_demo` — демо‑данные (переменная `SEED_DEMO=1`, включена по умолчанию).

После запуска:

| URL                                | Назначение                       |
|------------------------------------|----------------------------------|
| <http://localhost:8000/>           | Каталог (витрина)                |
| <http://localhost:8000/admin/>     | Админка                          |
| <http://localhost:8000/api/docs/>  | Swagger UI                       |
| <http://localhost:8000/api/redoc/> | ReDoc                            |
| <http://localhost:8000/api/schema/>| OpenAPI‑схема (YAML)             |
| <http://localhost:8000/graphql/>   | GraphQL (GraphiQL в DEBUG)       |

Создать суперпользователя:

```bash
docker compose exec web python manage.py createsuperuser
```

Демо‑аккаунт покупателя (создаётся `seed_demo`): `buyer@example.com` / `buyerpass123`
— у него есть доставленный заказ, поэтому на купленные товары можно оставлять отзывы.

---

## Локальный запуск без Docker (uv)

```bash
# 1. установить uv:  https://docs.astral.sh/uv/
uv sync --extra dev                     # создаст .venv и поставит зависимости

# 2. поднять PostgreSQL (или указать свой DATABASE_URL)
docker compose up -d db

# 3. переменные окружения
cp .env.example .env
export DATABASE_URL=postgres://hopbarley:hopbarley@localhost:5432/hopbarley

# 4. миграции + демо-данные
uv run python manage.py migrate
uv run python manage.py seed_demo

# 5. сервер разработки
uv run python manage.py runserver
```

Все частые команды собраны в `Makefile` (`make help`).

> Без PostgreSQL тесты всё равно проходят — они используют SQLite в памяти
> (`config.settings.test`).

---

## Переменные окружения

Читаются через `django-environ`; полный список — в `.env.example`.

| Переменная                | По умолчанию                         | Описание                              |
|---------------------------|-------------------------------------|---------------------------------------|
| `DJANGO_SETTINGS_MODULE`  | `config.settings.dev`               | `dev` / `prod` / `test`               |
| `DJANGO_SECRET_KEY`       | —                                   | обязателен в `prod`                   |
| `DJANGO_DEBUG`            | `0`                                 | режим отладки                         |
| `DJANGO_ALLOWED_HOSTS`    | `localhost,127.0.0.1,0.0.0.0`       | список хостов                         |
| `DATABASE_URL`            | `postgres://…@localhost:5432/hopbarley` | строка подключения к БД           |
| `JWT_ACCESS_MINUTES`      | `30`                                | время жизни access‑токена            |
| `JWT_REFRESH_DAYS`        | `7`                                 | время жизни refresh‑токена           |
| `DJANGO_EMAIL_BACKEND`    | `console`                           | по умолчанию письма печатаются в лог |
| `ORDER_ADMIN_EMAIL`       | `manager@hopbarley.local`           | получатель уведомлений о заказах      |

Настройки разделены: `config/settings/{base,dev,prod,test}.py`.

---

## Структура проекта

```
config/            настройки (base/dev/prod/test), корневые urls, wsgi/asgi
common/            общие абстракции (TimeStampedModel)
users/             кастомный User (логин по email), адреса, регистрация, кабинет
products/          каталог: Category, Product, фильтры, поиск, сортировка
orders/            корзина в сессии, Order/OrderItem, оформление, письма
reviews/           отзывы + правило «только после покупки»
payments/          эмуляция платёжного шлюза (Payment)
analytics/         GraphQL‑схема и резолверы аналитики
templates/         Django‑шаблоны (адаптированный дизайн Hop & Barley)
static/            CSS/JS/картинки из шаблона + app.css
tests/             pytest: каталог, корзина, заказы, отзывы, пользователи, GraphQL
docker/            entrypoint.sh
```

Каждое приложение делит ответственность на слои:
`models.py` → `querysets.py`/`services.py` (бизнес‑логика) → `views.py` (веб)
и `api/` (сериализаторы + вьюхи DRF).

> Приложение GraphQL названо `analytics`, а не `graphql`, чтобы не затенять
> пакет `graphql-core`. Эндпоинт при этом один — `/graphql/`.

---

## Модель данных

| Модель       | Ключевые поля                                                              |
|--------------|---------------------------------------------------------------------------|
| `Category`   | `name`, `slug`, `parent` (self, nullable), `created_at`, `updated_at`     |
| `Product`    | `name`, `slug`, `description`, `price`, `price_unit`, `category` (PROTECT), `image`, `is_active`, `stock`, timestamps |
| `ProductImage` | `product`, `image`, `alt`, `sort_order` — галерея                       |
| `Order`      | `user` (PROTECT), `status` (pending/paid/shipped/delivered/cancelled), `total_price`, `shipping_address`, `contact_*`, `payment_method`, `paid_at`, timestamps |
| `OrderItem`  | `order`, `product` (PROTECT), `quantity`, `price` (снапшот); уникально `(order, product)` |
| `Review`     | `product`, `user`, `rating` 1–5 (CheckConstraint), `comment`; уникально `(product, user)` |
| `Address`    | `user`, `full_name`, `phone`, `city`, `street`, `postal_code`, `is_default` |
| `Payment`    | `order` (OneToOne), `method`, `status`, `amount`, `transaction_id`        |

Агрегаты (`avg_rating`, `review_count`, `sales_count`) считаются в
`ProductQuerySet.with_stats()` одним запросом — используется и в каталоге,
и в API, и в админке.

---

## Веб‑интерфейс

| Маршрут                     | Что делает                                                        |
|-----------------------------|-----------------------------------------------------------------|
| `/`, `/products/`           | каталог: пагинация (12/стр.), фильтр по категории и цене, поиск по названию/описанию, сортировка (новизна/цена/рейтинг/популярность) |
| `/product/<slug>/`          | карточка товара: описание, рейтинг, отзывы, форма отзыва (после покупки), добавление в корзину с выбором количества |
| `/product/<slug>/review/`   | POST — создать отзыв (проверка факта покупки)                    |
| `/cart/`                    | корзина в сессии: изменение количества, удаление, контроль остатка, итог |
| `/checkout/`                | оформление: форма доставки, выбор способа оплаты (мок), создание заказа в транзакции, письма покупателю и администратору |
| `/account/`                 | личный кабинет: история заказов с фильтром по статусу, редактирование профиля, смена пароля, выход |
| `/account/register`, `/account/login`, `/account/logout` | регистрация / вход / выход (session auth) |

Корзина хранит только `product_id → quantity`; цена и наличие всегда берутся
из БД, «замораживается» цена лишь при оформлении (`OrderItem.price`).

---

## REST API и JWT

Базовый префикс — `/api/`. Полная интерактивная документация: **`/api/docs/`**.

### Аутентификация

Внешние клиенты используют JWT (заголовок `Authorization: Bearer <access>`).

```bash
# регистрация
curl -X POST http://localhost:8000/api/users/register/ \
  -H 'Content-Type: application/json' \
  -d '{"email":"alice@example.com","password":"SuperSecret123","first_name":"Alice"}'

# получить пару токенов
curl -X POST http://localhost:8000/api/users/login/ \
  -H 'Content-Type: application/json' \
  -d '{"email":"alice@example.com","password":"SuperSecret123"}'
# → {"access":"<JWT>","refresh":"<JWT>"}

# обновить access по refresh
curl -X POST http://localhost:8000/api/users/token/refresh/ \
  -H 'Content-Type: application/json' \
  -d '{"refresh":"<JWT>"}'
```

`access` живёт 30 минут, `refresh` — 7 дней (настраивается), refresh‑токены
ротируются при обновлении.

### Ресурсы

| Ресурс   | Метод и URL                              | Авторизация  | Описание                                   |
|----------|-----------------------------------------|--------------|--------------------------------------------|
| Товары   | `GET /api/products/`                    | не нужна     | список; `?category=&price_min=&price_max=&search=&ordering=` + пагинация |
| Товары   | `GET /api/products/{id}/`               | не нужна     | детально (описание, галерея, продажи)      |
| Отзывы   | `GET /api/products/{id}/reviews/`       | не нужна     | отзывы товара                              |
| Отзывы   | `POST /api/products/{id}/reviews/`      | JWT          | добавить отзыв (только после покупки)      |
| Заказы   | `POST /api/orders/`                     | JWT          | создать из `items[]` **или** из корзины‑сессии |
| Заказы   | `GET /api/orders/`                      | JWT          | только свои заказы                         |
| Заказы   | `GET /api/orders/{id}/`                 | JWT          | только свой                               |
| Заказы   | `PATCH /api/orders/{id}/` `{"status":"cancelled"}` | JWT | отмена (только `pending`/`paid`), остатки возвращаются |
| Заказы   | `DELETE /api/orders/{id}/`              | JWT          | мягкая отмена по тем же правилам           |
| Корзина  | `GET/POST/PATCH/DELETE /api/cart/`      | сессия/JWT   | содержимое корзины (сессия)                |
| Профиль  | `GET/PATCH /api/users/me/`              | JWT          | текущий пользователь                       |

Пример заказа:

```bash
curl -X POST http://localhost:8000/api/orders/ \
  -H "Authorization: Bearer $ACCESS" -H 'Content-Type: application/json' \
  -d '{
    "shipping_address":"Москва, ул. Хмельная, 3",
    "contact_name":"Alice","contact_phone":"+70000000000",
    "payment_method":"debit",
    "items":[{"product":1,"quantity":2}]
  }'
```

Права: пользователь видит и меняет только свои заказы (`get_queryset`
фильтруется по `request.user`), отзыв можно оставить один раз и только на
купленный товар.

---

## GraphQL‑аналитика (бонус)

Единый эндпоинт **`/graphql/`**. Доступ — только пользователям с `is_staff`
(аутентификация: сессия Django **или** JWT `Bearer`).

```graphql
query {
  orderStats(dateFrom: "2025-01-01") { revenue ordersCount averageCheck itemsSold }
  revenueTrend(days: 14) { date revenue orders }
  popularProducts(limit: 5) { name salesCount revenue }
  lowStockProducts(threshold: 20) { name stock }
  userActivity { totalUsers buyers repeatBuyers repeatRate }
}
```

```bash
curl -X POST http://localhost:8000/graphql/ \
  -H "Authorization: Bearer $STAFF_ACCESS" -H 'Content-Type: application/json' \
  -d '{"query":"{ orderStats { revenue ordersCount } popularProducts(limit:3){ name salesCount } }"}'
```

---

## Админ‑панель

`/admin/` — управление товарами, категориями, заказами, отзывами,
пользователями, платежами. Реализовано:

* **аналитика**: в списке товаров — колонки «продано», «выручка», «рейтинг»
  (аннотации); над списком заказов — сводка «выручка / кол‑во / средний чек»;
* **кастомные actions**: активировать/снять с публикации товары; пометить
  заказы оплаченными; отменить заказы с возвратом остатков;
* поиск, фильтры, `date_hierarchy`, inlines (позиции заказа, галерея товара);
* права: обычные действия под стандартной моделью прав Django.

---

## Тесты, линтеры, типы

```bash
make test        # pytest
make cov         # pytest + отчёт покрытия (term + htmlcov/)
make lint        # ruff check
make fmt         # ruff format + ruff check --fix
make type        # mypy
```

* **pytest-django**, ~50 тестов, покрытие **≈88 %** (`--cov-fail-under=80` в CI).
  Сценарии: каталог (фильтры/поиск/сортировка/пагинация), корзина (в т.ч.
  лимит остатка), оформление заказа (транзакция, списание/возврат остатков,
  письма, «нельзя заказать больше, чем есть»), регистрация/вход (web + JWT),
  отзывы (только после покупки, без дублей), права в API, GraphQL (доступ
  только для staff), management‑команда `seed_demo`.
* **ruff** — линт (правила pycodestyle/pyflakes/bugbear/django/isort/…) и
  форматирование; заменяет flake8/isort/black.
* **mypy** + `django-stubs` + `djangorestframework-stubs`. Бизнес‑логика
  (`services`, `cart`, `querysets`, `models`, `forms`, `schema`) типизирована
  и проверяется; тонкий «клеевой» слой Django/DRF (CBV/ViewSet/urls) исключён
  из строгой проверки — там stubs дают ложные срабатывания (см. комментарий в
  `pyproject.toml`).

Типизация: аннотации во всех функциях бизнес‑логики, докстринги — у публичных
модулей, сервисов и нетривиальных методов.

---

## CI/CD

`.github/workflows/ci.yml` — три задания:

1. **quality** — `ruff check`, `ruff format --check`, `mypy`;
2. **test** — `makemigrations --check` + `pytest` с покрытием против
   **реального PostgreSQL** (service container), порог 80 %;
3. **docker** — сборка образа (`docker/build-push-action`, кеш GHA).

---

## Git workflow

* стабильная ветка — `main`; интеграционная — `develop`; задачи — в
  `feature/*` ветках;
* небольшие осмысленные коммиты (см. `git log`).

---

## Чек‑лист по ТЗ

- [x] Каталог: пагинация, фильтр по категории и цене, поиск, сортировка (CBV, ORM, оптимизация запросов)
- [x] Страница товара: детали, рейтинг, отзывы, отзыв только после покупки, добавление в корзину с количеством
- [x] Корзина в сессии: добавление/удаление/изменение, итог, контроль остатка, Message Framework
- [x] Оформление: форма доставки, выбор оплаты (мок), создание заказа в транзакции, email покупателю и админу
- [x] Личный кабинет: регистрация/вход/выход (session), история заказов с фильтром, профиль, смена пароля, адреса
- [x] Админка: товары/категории/заказы/отзывы/пользователи, агрегаты и аннотации, поиск, фильтры, кастомные actions
- [x] REST API: товары, заказы (CRUD + отмена по правилам), регистрация, JWT‑логин/refresh, корзина, отзывы; пагинация, фильтры, permissions
- [x] Документация API: drf-spectacular — `/api/docs/`, `/api/redoc/`, `/api/schema/`
- [x] Инфраструктура: PostgreSQL, Docker Compose, `pyproject.toml` + `uv.lock`
- [x] Качество: типизация, ruff, mypy, pytest (покрытие ≈88 %)
- [x] Бонусы: GraphQL‑аналитика, CI (линт + типы + тесты на PostgreSQL + сборка образа), менеджер зависимостей **uv**

---

## Лицензия

MIT.
