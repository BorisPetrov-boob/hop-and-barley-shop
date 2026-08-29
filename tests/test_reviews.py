"""Отзывы: только после покупки, без дублей, через веб и API."""

from __future__ import annotations

import pytest
from django.urls import reverse

from reviews.models import Review
from reviews.services import user_can_review
from tests.factories import OrderItemFactory, ReviewFactory

pytestmark = pytest.mark.django_db


def test_cannot_review_without_purchase(user, product):
    assert user_can_review(user, product) is False


def test_can_review_after_purchase(paid_order_with_product, user, product):
    assert user_can_review(user, product) is True


def test_web_review_rejected_without_purchase(client, user, product):
    client.force_login(user)
    resp = client.post(
        reverse("reviews:add", args=[product.slug]),
        {"rating": 5, "comment": "Класс"},
        follow=True,
    )
    assert resp.status_code == 200
    assert Review.objects.count() == 0


def test_web_review_created_after_purchase(client, paid_order_with_product, user, product):
    client.force_login(user)
    client.post(
        reverse("reviews:add", args=[product.slug]),
        {"rating": 4, "comment": "Хорошо"},
    )
    review = Review.objects.get()
    assert review.rating == 4
    assert review.user == user


def test_duplicate_review_blocked(client, paid_order_with_product, user, product):
    ReviewFactory(product=product, user=user)
    client.force_login(user)
    client.post(
        reverse("reviews:add", args=[product.slug]),
        {"rating": 1, "comment": "Другой"},
    )
    assert Review.objects.filter(product=product, user=user).count() == 1


def test_api_review_list_public(api_client, product):
    ReviewFactory(product=product, rating=3)
    resp = api_client.get(f"/api/products/{product.pk}/reviews/")
    assert resp.status_code == 200
    assert resp.data["results"][0]["rating"] == 3


def test_api_review_create_requires_purchase(auth_client, user, product):
    resp = auth_client.post(
        f"/api/products/{product.pk}/reviews/", {"rating": 5, "comment": "x"}, format="json"
    )
    assert resp.status_code == 403

    OrderItemFactory.create(order__user=user, order__status="paid", product=product)
    resp = auth_client.post(
        f"/api/products/{product.pk}/reviews/", {"rating": 5, "comment": "ok"}, format="json"
    )
    assert resp.status_code == 201
