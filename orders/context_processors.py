"""Контекст-процессор корзины: делает её доступной во всех шаблонах."""

from __future__ import annotations

from typing import Any

from django.http import HttpRequest

from .cart import Cart


def cart(request: HttpRequest) -> dict[str, Any]:
    current = Cart(request)
    return {"cart": current, "cart_count": len(current), "cart_total": current.total}
