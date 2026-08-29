"""QuerySet-ы каталога с агрегатами (рейтинг, продажи) и поиском."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from django.db import models
from django.db.models import Avg, Count, Q, Sum
from django.db.models.functions import Coalesce

if TYPE_CHECKING:
    from .models import Category, Product  # noqa: F401  (используются в строковых аннотациях)

# Статусы заказа, при которых позиции считаются проданными.
SOLD_ORDER_STATUSES = ("paid", "shipped", "delivered")


class CategoryQuerySet(models.QuerySet["Category"]):
    def roots(self) -> CategoryQuerySet:
        return self.filter(parent__isnull=True)

    def with_product_counts(self) -> CategoryQuerySet:
        return self.annotate(
            product_count=Count("products", filter=Q(products__is_active=True), distinct=True)
        )


class ProductQuerySet(models.QuerySet["Product"]):
    """Инкапсулирует часто используемые выборки каталога."""

    def active(self) -> ProductQuerySet:
        return self.filter(is_active=True)

    def in_stock(self) -> ProductQuerySet:
        return self.filter(stock__gt=0)

    def with_stats(self) -> ProductQuerySet:
        """Добавляет ``avg_rating``, ``review_count`` и ``sales_count``.

        Значения считаются одним запросом — используется во всех местах,
        где нужна сортировка по популярности или рейтингу.
        """
        return self.annotate(
            avg_rating=Coalesce(Avg("reviews__rating"), 0.0),
            review_count=Count("reviews", distinct=True),
            sales_count=Coalesce(
                Sum(
                    "order_items__quantity",
                    filter=Q(order_items__order__status__in=SOLD_ORDER_STATUSES),
                ),
                0,
            ),
        )

    def search(self, query: str | None) -> ProductQuerySet:
        if not query:
            return self
        return self.filter(Q(name__icontains=query) | Q(description__icontains=query))

    def price_between(
        self, minimum: Decimal | None = None, maximum: Decimal | None = None
    ) -> ProductQuerySet:
        qs = self
        if minimum is not None:
            qs = qs.filter(price__gte=minimum)
        if maximum is not None:
            qs = qs.filter(price__lte=maximum)
        return qs

    def for_category(self, category: Category | None) -> ProductQuerySet:
        """Товары категории и всех её прямых подкатегорий."""
        if category is None:
            return self
        return self.filter(Q(category=category) | Q(category__parent=category))
