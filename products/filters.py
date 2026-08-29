"""FilterSet каталога — общий для веб-интерфейса и REST API."""

from __future__ import annotations

import django_filters as filters

from .models import Category, Product

ORDERING_FIELDS = (
    ("created_at", "new"),
    ("-created_at", "-new"),
    ("price", "price_asc"),
    ("-price", "price_desc"),
    ("avg_rating", "rating"),
    ("-avg_rating", "-rating"),
    ("sales_count", "popular"),
    ("-sales_count", "-popular"),
)


class ProductFilter(filters.FilterSet):
    """Фильтрация товаров по категории, цене и полнотекстовому поиску."""

    category = filters.CharFilter(field_name="category__slug", lookup_expr="exact")
    price_min = filters.NumberFilter(field_name="price", lookup_expr="gte")
    price_max = filters.NumberFilter(field_name="price", lookup_expr="lte")
    search = filters.CharFilter(method="filter_search", label="Поиск")
    ordering = filters.OrderingFilter(fields=ORDERING_FIELDS)

    class Meta:
        model = Product
        fields = ("category", "price_min", "price_max", "search")

    def filter_search(self, queryset, name, value):  # noqa: ANN001, ANN201
        return queryset.search(value)

    @property
    def qs(self):  # noqa: ANN201
        # Гарантируем, что аннотации для сортировки по рейтингу/популярности есть.
        parent = super().qs
        return parent

    @staticmethod
    def category_choices() -> list[Category]:
        return list(Category.objects.with_product_counts().order_by("name"))
