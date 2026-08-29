"""Настройки для запуска тестов.

По умолчанию используется быстрый SQLite в памяти, чтобы тесты можно было
гонять без поднятого PostgreSQL. В CI переменная ``DATABASE_URL`` указывает на
реальный PostgreSQL — тогда тесты идут против него.
"""

from __future__ import annotations

from .base import *  # noqa: F403
from .base import BASE_DIR, env

DEBUG = False
SECRET_KEY = "test-secret-key-not-used-anywhere-but-long-enough-000000"  # noqa: S105

DATABASES = {
    "default": env.db_url("DATABASE_URL", default="sqlite://:memory:"),
}

# Ускоряем хеширование паролей в тестах.
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

STORAGES["staticfiles"]["BACKEND"] = (  # noqa: F405
    "django.contrib.staticfiles.storage.StaticFilesStorage"
)

# Отключаем троттлинг в тестах.
REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"] = []  # noqa: F405
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {}  # noqa: F405

MEDIA_ROOT = BASE_DIR / "test_media"
