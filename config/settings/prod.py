"""Продакшн-настройки.

По умолчанию рассчитаны на работу за HTTPS-прокси. Для демонстрационного
деплоя по HTTP на голый IP небезопасные-по-HTTP параметры отключаются через
переменные окружения (см. ``deploy/.env.prod.example``):

    DJANGO_SECURE_SSL_REDIRECT=0
    DJANGO_SESSION_COOKIE_SECURE=0
    DJANGO_CSRF_COOKIE_SECURE=0
    DJANGO_SECURE_HSTS_SECONDS=0
"""

from __future__ import annotations

from .base import *  # noqa: F403
from .base import env

DEBUG = False

# Обязательно должны быть заданы через окружение.
SECRET_KEY = env("DJANGO_SECRET_KEY")
ALLOWED_HOSTS = env("DJANGO_ALLOWED_HOSTS")
CSRF_TRUSTED_ORIGINS = env.list("DJANGO_CSRF_TRUSTED_ORIGINS", default=[])

# Приложение работает за обратным прокси (nginx) — доверяем заголовку.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True

# HTTPS / безопасность (по умолчанию — как для деплоя за TLS).
SECURE_SSL_REDIRECT = env.bool("DJANGO_SECURE_SSL_REDIRECT", default=True)
SESSION_COOKIE_SECURE = env.bool("DJANGO_SESSION_COOKIE_SECURE", default=True)
CSRF_COOKIE_SECURE = env.bool("DJANGO_CSRF_COOKIE_SECURE", default=True)
SECURE_HSTS_SECONDS = env.int("DJANGO_SECURE_HSTS_SECONDS", default=2_592_000)
SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool("DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS", default=True)
SECURE_HSTS_PRELOAD = env.bool("DJANGO_SECURE_HSTS_PRELOAD", default=True)
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
