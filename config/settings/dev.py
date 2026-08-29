"""Настройки для локальной разработки."""

from __future__ import annotations

from .base import *  # noqa: F403
from .base import env

DEBUG = True
ALLOWED_HOSTS = ["*"]

INTERNAL_IPS = ["127.0.0.1"]

# В разработке письма печатаются в консоль.
EMAIL_BACKEND = env(
    "DJANGO_EMAIL_BACKEND",
    default="django.core.mail.backends.console.EmailBackend",
)

# Упрощаем хранилище статики, чтобы не требовать collectstatic во время разработки.
STORAGES["staticfiles"]["BACKEND"] = (  # noqa: F405
    "whitenoise.storage.CompressedStaticFilesStorage"
)
