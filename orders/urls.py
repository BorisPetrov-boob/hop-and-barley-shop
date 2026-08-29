"""URL-ы корзины и оформления заказа (веб)."""

from __future__ import annotations

from django.urls import include, path

from . import views

cart_patterns = (
    [
        path("", views.cart_detail, name="detail"),
        path("add/<int:product_id>/", views.cart_add, name="add"),
        path("update/<int:product_id>/", views.cart_update, name="update"),
        path("remove/<int:product_id>/", views.cart_remove, name="remove"),
    ],
    "cart",
)

checkout_patterns = (
    [
        path("", views.checkout, name="index"),
        path("success/<int:order_id>/", views.checkout_success, name="success"),
    ],
    "checkout",
)

urlpatterns = [
    path("cart/", include(cart_patterns)),
    path("checkout/", include(checkout_patterns)),
]
