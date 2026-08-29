"""Контекст-процессоры каталога (навигация по категориям в шапке/сайдбаре)."""

from __future__ import annotations

from typing import Any

from django.http import HttpRequest

from .models import Category


def catalog_nav(request: HttpRequest) -> dict[str, Any]:
    """Список корневых категорий с числом активных товаров."""
    categories = list(Category.objects.roots().with_product_counts().order_by("name"))
    return {"nav_categories": categories}
