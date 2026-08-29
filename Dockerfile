# syntax=docker/dockerfile:1
# --------------------------------------------------------------------------- #
# Образ приложения Hop & Barley. Зависимости ставит uv из uv.lock.
# --------------------------------------------------------------------------- #
FROM python:3.13-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/app/.venv \
    PATH="/app/.venv/bin:$PATH" \
    DJANGO_SETTINGS_MODULE=config.settings.prod

# uv — статический бинарник из официального образа.
COPY --from=ghcr.io/astral-sh/uv:0.9 /uv /uvx /bin/

WORKDIR /app

# Рантайм-библиотека PostgreSQL для psycopg.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq5 \
    && rm -rf /var/lib/apt/lists/*

# 1) Слой зависимостей — кешируется, пока не менялись pyproject.toml / uv.lock.
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# 2) Код приложения.
COPY . .

RUN chmod +x /app/docker/entrypoint.sh \
    && python -m compileall -q config common products orders users reviews payments analytics

EXPOSE 8000
ENTRYPOINT ["/app/docker/entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "60"]
