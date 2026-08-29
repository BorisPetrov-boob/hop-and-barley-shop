"""FilterSet каталога — общий для веб-интерфейса и REST API.

Сортировкой занимаются:

* в вебе — ``ProductListView`` (параметр ``?sort=new|price_asc|price_desc|rating|popular``);
* в API — DRF ``OrderingFilter`` (``?ordering=price|-price|created_at|avg_rating|sales_count``).

Здесь описаны только фильтры (категория, цена, поиск), чтобы не было двух
конкурирующих обработчиков параметра ``ordering``.
"""

from __future__ import annotations

import django_filters as filters  # type: ignore[import-untyped]

from .models import Category, Product


class ProductFilter(filters.FilterSet):
    """Фильтрация товаров по категории, диапазону цены и полнотекстовому поиску."""

    category = filters.CharFilter(field_name="category__slug", lookup_expr="exact")
    price_min = filters.NumberFilter(field_name="price", lookup_expr="gte")
    price_max = filters.NumberFilter(field_name="price", lookup_expr="lte")
    search = filters.CharFilter(method="filter_search", label="Поиск")

    class Meta:
        model = Product
        fields = ("category", "price_min", "price_max", "search")

    def filter_search(self, queryset, name, value):  # noqa: ANN001, ANN201
        return queryset.search(value)

    @staticmethod
    def category_choices() -> list[Category]:
        return list(Category.objects.with_product_counts().order_by("name"))
