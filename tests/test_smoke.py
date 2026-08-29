"""Дымовые тесты: ключевые страницы и эндпоинты отвечают."""

from __future__ import annotations

import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "name",
    ["products:product_list", "users:login", "users:register", "cart:detail"],
)
def test_public_pages_ok(client, name):
    assert client.get(reverse(name)).status_code == 200


def test_account_requires_login(client):
    resp = client.get(reverse("users:account"))
    assert resp.status_code == 302
    assert "/account/login/" in resp.url


def test_checkout_requires_login(client):
    resp = client.get(reverse("checkout:index"))
    assert resp.status_code == 302


def test_api_schema_and_docs(api_client):
    assert api_client.get("/api/schema/").status_code == 200
    assert api_client.get("/api/docs/").status_code == 200


def test_admin_login_page(client):
    assert client.get("/admin/login/").status_code == 200
