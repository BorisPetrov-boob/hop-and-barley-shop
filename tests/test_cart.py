"""Корзина на сессии: добавление, изменение, удаление, лимит остатка."""

from __future__ import annotations

import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db


def test_add_to_cart(client, product):
    resp = client.post(reverse("cart:add", args=[product.pk]), {"quantity": 3}, follow=True)
    assert resp.status_code == 200
    assert resp.context["cart_count"] == 3


def test_add_respects_stock(client, product):
    product.stock = 5
    product.save()
    client.post(reverse("cart:add", args=[product.pk]), {"quantity": 99})
    resp = client.get(reverse("cart:detail"))
    line = next(iter(resp.context["cart"]))
    assert line.quantity == 5


def test_update_quantity_zero_removes(client, product):
    client.post(reverse("cart:add", args=[product.pk]), {"quantity": 2})
    client.post(reverse("cart:update", args=[product.pk]), {"quantity": 0})
    resp = client.get(reverse("cart:detail"))
    assert resp.context["cart"].is_empty


def test_remove_from_cart(client, product):
    client.post(reverse("cart:add", args=[product.pk]), {"quantity": 2})
    client.post(reverse("cart:remove", args=[product.pk]))
    resp = client.get(reverse("cart:detail"))
    assert resp.context["cart"].is_empty


def test_cart_total(client, category):
    from tests.factories import ProductFactory

    p1 = ProductFactory(price="2.00", stock=10, category=category)
    p2 = ProductFactory(price="3.50", stock=10, category=category)
    client.post(reverse("cart:add", args=[p1.pk]), {"quantity": 2})
    client.post(reverse("cart:add", args=[p2.pk]), {"quantity": 1})
    resp = client.get(reverse("cart:detail"))
    assert resp.context["cart"].total == pytest.approx(7.50)


def test_cart_api_roundtrip(api_client, product):
    add = api_client.post("/api/cart/", {"product": product.pk, "quantity": 2}, format="json")
    assert add.status_code == 200
    assert add.data["count"] == 2
    patch = api_client.patch("/api/cart/", {"product": product.pk, "quantity": 1}, format="json")
    assert patch.data["count"] == 1
    api_client.delete("/api/cart/")
    get = api_client.get("/api/cart/")
    assert get.data["count"] == 0
