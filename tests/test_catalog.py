"""Каталог: список, фильтры, поиск, сортировка, пагинация, деталь."""

from __future__ import annotations

from decimal import Decimal

import pytest
from django.urls import reverse

from tests.factories import CategoryFactory, ProductFactory

pytestmark = pytest.mark.django_db


def test_product_list_web_ok(client, products):
    resp = client.get(reverse("products:product_list"))
    assert resp.status_code == 200
    assert b"product-card" in resp.content


def test_product_list_pagination(client, products):
    resp = client.get(reverse("products:product_list"))
    assert resp.context["is_paginated"] is True
    assert len(resp.context["products"]) == 12
    resp2 = client.get(reverse("products:product_list"), {"page": 2})
    assert len(resp2.context["products"]) == 3


def test_inactive_product_hidden(client):
    ProductFactory(name="Скрытый", is_active=False)
    resp = client.get(reverse("products:product_list"))
    assert "Скрытый" not in resp.content.decode()


def test_filter_by_category(client):
    hops = CategoryFactory(name="Hops")
    malts = CategoryFactory(name="Malts")
    ProductFactory(name="Citra", category=hops)
    ProductFactory(name="Pilsner", category=malts)
    resp = client.get(reverse("products:product_list"), {"category": "hops"})
    names = [p.name for p in resp.context["products"]]
    assert names == ["Citra"]


def test_filter_by_price_range(client, category):
    ProductFactory(name="Дешёвый", price=Decimal("2.00"), category=category)
    ProductFactory(name="Дорогой", price=Decimal("20.00"), category=category)
    resp = client.get(reverse("products:product_list"), {"price_min": "5", "price_max": "25"})
    names = [p.name for p in resp.context["products"]]
    assert names == ["Дорогой"]


def test_search_by_name_and_description(client, category):
    ProductFactory(name="Mosaic Hops", description="тропический профиль", category=category)
    ProductFactory(name="Saaz", description="благородный", category=category)
    resp = client.get(reverse("products:product_list"), {"search": "тропический"})
    assert [p.name for p in resp.context["products"]] == ["Mosaic Hops"]


def test_sort_by_price(client, category):
    ProductFactory(name="A", price=Decimal("30.00"), category=category)
    ProductFactory(name="B", price=Decimal("10.00"), category=category)
    resp = client.get(reverse("products:product_list"), {"sort": "price_asc"})
    prices = [p.price for p in resp.context["products"]]
    assert prices == sorted(prices)


def test_product_detail_web(client, product):
    resp = client.get(product.get_absolute_url())
    assert resp.status_code == 200
    assert product.name.encode() in resp.content


def test_api_product_list(api_client, products):
    resp = api_client.get("/api/products/")
    assert resp.status_code == 200
    assert resp.data["count"] == 15
    assert len(resp.data["results"]) == 12


def test_api_product_list_filter_search(api_client, category):
    ProductFactory(name="Citra Hops", description="грейпфрут", category=category)
    ProductFactory(name="Saaz", description="пряный", category=category)
    resp = api_client.get("/api/products/", {"search": "грейпфрут"})
    assert [r["name"] for r in resp.data["results"]] == ["Citra Hops"]


def test_api_product_detail(api_client, product):
    resp = api_client.get(f"/api/products/{product.pk}/")
    assert resp.status_code == 200
    assert resp.data["slug"] == product.slug
    assert "description" in resp.data


def test_api_product_ordering(api_client, category):
    ProductFactory(name="A", price=Decimal("30.00"), category=category)
    ProductFactory(name="B", price=Decimal("10.00"), category=category)
    ProductFactory(name="C", price=Decimal("20.00"), category=category)
    resp = api_client.get("/api/products/", {"ordering": "-price"})
    assert resp.status_code == 200
    prices = [float(r["price"]) for r in resp.data["results"]]
    assert prices == sorted(prices, reverse=True)


def test_api_product_filter_by_price(api_client, category):
    ProductFactory(name="Дешёвый", price=Decimal("2.00"), category=category)
    ProductFactory(name="Дорогой", price=Decimal("50.00"), category=category)
    resp = api_client.get("/api/products/", {"price_min": "10", "price_max": "100"})
    assert [r["name"] for r in resp.data["results"]] == ["Дорогой"]
