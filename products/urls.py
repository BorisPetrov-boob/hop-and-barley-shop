"""URL-ы каталога (веб)."""

from __future__ import annotations

from django.urls import path

from .views import ProductDetailView, ProductListView

app_name = "products"

urlpatterns = [
    path("", ProductListView.as_view(), name="product_list"),
    path("products/", ProductListView.as_view(), name="product_list_alt"),
    path("product/<slug:slug>/", ProductDetailView.as_view(), name="product_detail"),
]
