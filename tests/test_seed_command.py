"""Проверка management-команды seed_demo."""

from __future__ import annotations

import pytest
from django.core.management import call_command

from orders.models import Order
from products.models import Category, Product
from reviews.models import Review

pytestmark = pytest.mark.django_db


def test_seed_demo_is_idempotent():
    call_command("seed_demo")
    call_command("seed_demo")  # второй раз — без дубликатов

    assert Category.objects.count() == 4
    assert Product.objects.count() == 12
    assert Order.objects.filter(status=Order.Status.DELIVERED).count() == 1
    assert Review.objects.count() >= 4


def test_seed_demo_flush():
    call_command("seed_demo")
    call_command("seed_demo", "--flush")
    assert Product.objects.count() == 12
