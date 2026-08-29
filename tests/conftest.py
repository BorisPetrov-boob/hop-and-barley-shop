"""Общие фикстуры pytest."""

from __future__ import annotations

from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from orders.models import Order, OrderItem
from tests.factories import (
    CategoryFactory,
    OrderFactory,
    ProductFactory,
    StaffFactory,
    UserFactory,
)


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def user(db):
    return UserFactory()


@pytest.fixture
def staff_user(db):
    return StaffFactory()


@pytest.fixture
def category(db):
    return CategoryFactory(name="Hops")


@pytest.fixture
def product(db, category):
    return ProductFactory(name="Citra Hops", price=Decimal("5.99"), stock=20, category=category)


@pytest.fixture
def products(db, category):
    return [
        ProductFactory(name=f"Хмель {i}", price=Decimal(f"{i + 1}.50"), stock=10, category=category)
        for i in range(15)
    ]


@pytest.fixture
def auth_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def paid_order_with_product(db, user, product):
    """Оплаченный заказ пользователя, содержащий ``product`` (нужен для отзывов)."""
    order = OrderFactory(user=user, status=Order.Status.PAID)
    OrderItem.objects.create(order=order, product=product, quantity=1, price=product.price)
    order.recalculate_total()
    return order
