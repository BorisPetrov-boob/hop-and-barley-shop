"""Базовые абстрактные модели, переиспользуемые во всех приложениях."""

from __future__ import annotations

from django.db import models


class TimeStampedModel(models.Model):
    """Добавляет поля ``created_at`` / ``updated_at``.

    Используется практически всеми доменными моделями магазина
    (``Category``, ``Product``, ``Order`` и т. д.).
    """

    created_at = models.DateTimeField("создан", auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField("обновлён", auto_now=True)

    class Meta:
        abstract = True
        get_latest_by = "created_at"
        ordering = ("-created_at",)
