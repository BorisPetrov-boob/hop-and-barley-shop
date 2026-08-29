"""API каталога: только чтение, доступно без авторизации."""

from __future__ import annotations

from django.db.models import QuerySet
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import permissions, viewsets

from products.filters import ProductFilter
from products.models import Product

from .serializers import ProductDetailSerializer, ProductListSerializer


@extend_schema_view(
    list=extend_schema(
        summary="Список товаров", description="Пагинация, фильтры, поиск, сортировка."
    ),
    retrieve=extend_schema(summary="Товар по id"),
)
class ProductViewSet(viewsets.ReadOnlyModelViewSet[Product]):
    """``/api/products/`` и ``/api/products/{id}/``."""

    permission_classes = (permissions.AllowAny,)
    filterset_class = ProductFilter
    search_fields = ("name", "description")
    ordering_fields = ("price", "created_at", "avg_rating", "sales_count")
    ordering = ("-created_at",)

    def get_queryset(self) -> QuerySet[Product]:
        return (
            Product.objects.active()
            .select_related("category")
            .prefetch_related("images")
            .with_stats()
        )

    def get_serializer_class(self):  # noqa: ANN201
        if self.action == "retrieve":
            return ProductDetailSerializer
        return ProductListSerializer
