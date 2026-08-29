"""URL-ы API отзывов (вложены в /api/products/<id>/reviews/)."""

from __future__ import annotations

from django.urls import path

from .views import ProductReviewListCreateView

urlpatterns = [
    path(
        "products/<int:product_id>/reviews/",
        ProductReviewListCreateView.as_view(),
        name="product-reviews",
    ),
]
