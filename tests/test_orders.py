"""Оформление заказа: транзакция, остатки, письма, правила отмены."""

from __future__ import annotations

import pytest
from django.core import mail
from django.urls import reverse

from orders.models import Order
from orders.services import (
    EmptyCartError,
    LineInput,
    OutOfStockError,
    cancel_order,
    create_order,
)
from tests.factories import ProductFactory

pytestmark = pytest.mark.django_db

CHECKOUT_DATA = {
    "full_name": "Иван Пивоваров",
    "phone": "+70000000000",
    "email": "ivan@example.com",
    "city": "Москва",
    "address": "ул. Хмельная, 3",
    "payment_method": "debit",
}


def test_create_order_decrements_stock_and_sends_emails(
    user, product, django_capture_on_commit_callbacks
):
    product.stock = 10
    product.save()
    with django_capture_on_commit_callbacks(execute=True):
        order = create_order(
            user=user,
            lines=[LineInput(product.pk, 3)],
            shipping_address="Москва",
            contact_name="Иван",
            contact_phone="+70000000000",
            contact_email="ivan@example.com",
        )
    product.refresh_from_db()
    assert product.stock == 7
    assert order.total_price == product.price * 3
    assert order.items.count() == 1
    # два письма: покупателю и администратору
    assert len(mail.outbox) == 2


def test_create_order_out_of_stock(user, product):
    product.stock = 2
    product.save()
    with pytest.raises(OutOfStockError):
        create_order(
            user=user,
            lines=[LineInput(product.pk, 5)],
            shipping_address="Москва",
            contact_name="Иван",
            contact_phone="+70000000000",
        )
    assert Order.objects.count() == 0
    product.refresh_from_db()
    assert product.stock == 2


def test_create_order_empty(user):
    with pytest.raises(EmptyCartError):
        create_order(user=user, lines=[], shipping_address="x", contact_name="x", contact_phone="x")


def test_checkout_web_flow(client, user, product):
    client.force_login(user)
    client.post(reverse("cart:add", args=[product.pk]), {"quantity": 2})
    resp = client.post(reverse("checkout:index"), CHECKOUT_DATA, follow=True)
    assert resp.status_code == 200
    order = Order.objects.get(user=user)
    assert order.items.count() == 1
    # мгновенная оплата картой → статус paid
    assert order.status == Order.Status.PAID
    assert hasattr(order, "payment")


def test_cancel_order_restores_stock(user, product):
    product.stock = 10
    product.save()
    order = create_order(
        user=user,
        lines=[LineInput(product.pk, 4)],
        shipping_address="Москва",
        contact_name="Иван",
        contact_phone="+70000000000",
    )
    cancel_order(order)
    product.refresh_from_db()
    assert product.stock == 10
    assert order.status == Order.Status.CANCELLED


def test_api_order_create_from_items(auth_client, product):
    payload = {
        "shipping_address": "Москва, Хмельная 3",
        "contact_name": "Иван",
        "contact_phone": "+70000000000",
        "payment_method": "debit",
        "items": [{"product": product.pk, "quantity": 2}],
    }
    resp = auth_client.post("/api/orders/", payload, format="json")
    assert resp.status_code == 201
    assert resp.data["items"][0]["quantity"] == 2


def test_api_orders_scoped_to_user(auth_client, user, django_user_model):
    other = django_user_model.objects.create_user(email="other@example.com", password="x")
    ProductFactory(name="p", stock=5)
    Order.objects.create(user=other, shipping_address="x", contact_name="x", contact_phone="x")
    resp = auth_client.get("/api/orders/")
    assert resp.data["count"] == 0


def test_api_order_cancel_rules(auth_client, user, product):
    order = create_order(
        user=user,
        lines=[LineInput(product.pk, 1)],
        shipping_address="Москва",
        contact_name="Иван",
        contact_phone="+70000000000",
    )
    order.status = Order.Status.DELIVERED
    order.save()
    resp = auth_client.delete(f"/api/orders/{order.pk}/")
    assert resp.status_code == 409

    order.status = Order.Status.PENDING
    order.save()
    resp = auth_client.patch(f"/api/orders/{order.pk}/", {"status": "cancelled"}, format="json")
    assert resp.status_code == 200
    order.refresh_from_db()
    assert order.status == Order.Status.CANCELLED
