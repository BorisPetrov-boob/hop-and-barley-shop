"""Роутер API заказов и корзины."""

from __future__ import annotations

from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import CartAPIView, OrderViewSet

router = DefaultRouter()
router.register("orders", OrderViewSet, basename="order")

urlpatterns = [
    path("cart/", CartAPIView.as_view(), name="cart"),
    *router.urls,
]
