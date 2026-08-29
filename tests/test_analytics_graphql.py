"""GraphQL-аналитика: доступ только для персонала, корректные агрегаты."""

from __future__ import annotations

import json

import pytest

from orders.models import Order
from orders.services import LineInput, create_order
from tests.factories import ProductFactory

pytestmark = pytest.mark.django_db

QUERY = """
query {
  orderStats { revenue ordersCount averageCheck itemsSold }
  popularProducts(limit: 3) { name salesCount }
  lowStockProducts(threshold: 5) { name stock }
  userActivity { totalUsers buyers repeatBuyers }
}
"""


def _post(client, token_user=None):
    if token_user is not None:
        client.force_login(token_user)
    return client.post(
        "/graphql/", data=json.dumps({"query": QUERY}), content_type="application/json"
    )


def test_graphql_requires_staff(client, user):
    resp = _post(client, user)
    body = resp.json()
    assert body.get("errors")
    assert "персонал" in body["errors"][0]["message"]


def test_graphql_stats_for_staff(client, staff_user, user):
    product = ProductFactory(price="10.00", stock=100)
    order = create_order(
        user=user,
        lines=[LineInput(product.pk, 2)],
        shipping_address="Москва",
        contact_name="Иван",
        contact_phone="+70000000000",
    )
    order.status = Order.Status.PAID
    order.save()

    resp = _post(client, staff_user)
    data = resp.json()["data"]
    assert data["orderStats"]["ordersCount"] == 1
    assert data["orderStats"]["revenue"] == pytest.approx(20.0)
    assert data["orderStats"]["itemsSold"] == 2
    assert data["popularProducts"][0]["name"] == product.name
    assert data["userActivity"]["buyers"] == 1
