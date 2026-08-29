"""API отзывов: список и создание для конкретного товара."""

from __future__ import annotations

from django.db.models import QuerySet
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied, ValidationError

from products.models import Product
from reviews.models import Review
from reviews.services import has_reviewed, user_can_review

from .serializers import ReviewSerializer


@extend_schema_view(
    get=extend_schema(summary="Отзывы товара"),
    post=extend_schema(summary="Оставить отзыв (JWT, только после покупки)"),
)
class ProductReviewListCreateView(generics.ListCreateAPIView[Review]):
    """``/api/products/{product_id}/reviews/``."""

    serializer_class = ReviewSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_product(self) -> Product:
        return get_object_or_404(Product.objects.active(), pk=self.kwargs["product_id"])

    def get_queryset(self) -> QuerySet[Review]:
        return (
            Review.objects.filter(product_id=self.kwargs["product_id"])
            .select_related("user")
            .order_by("-created_at")
        )

    def perform_create(self, serializer: ReviewSerializer) -> None:
        product = self.get_product()
        user = self.request.user
        if has_reviewed(user, product.pk):
            raise ValidationError("Вы уже оставляли отзыв на этот товар.")
        if not user_can_review(user, product):
            raise PermissionDenied("Оставить отзыв можно только после покупки товара.")
        serializer.save(product=product, user=user)
