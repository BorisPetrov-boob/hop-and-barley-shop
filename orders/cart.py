"""Корзина на сессии Django.

Хранит ``{product_id: {"quantity": int}}`` в ``request.session``.
Данные о товаре (цена, наличие) всегда берутся из БД — в сессии лежит
только количество, поэтому цена не «замораживается» до оформления заказа.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from decimal import Decimal

from django.conf import settings
from django.http import HttpRequest

from products.models import Product


@dataclass(slots=True)
class CartLine:
    """Одна строка корзины с уже подгруженным товаром."""

    product: Product
    quantity: int

    @property
    def unit_price(self) -> Decimal:
        return self.product.price

    @property
    def subtotal(self) -> Decimal:
        return self.product.price * self.quantity

    @property
    def has_enough_stock(self) -> bool:
        return self.quantity <= self.product.stock


class Cart:
    """Обёртка над сессией с бизнес-логикой корзины."""

    def __init__(self, request: HttpRequest) -> None:
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if cart is None:
            cart = self.session[settings.CART_SESSION_ID] = {}
        self._cart: dict[str, dict[str, int]] = cart

    # --- изменение состава -------------------------------------------------
    def add(self, product: Product, quantity: int = 1, *, replace: bool = False) -> None:
        """Добавить товар или изменить его количество.

        ``replace=True`` устанавливает точное количество (используется
        со страницы корзины), иначе количество прибавляется.
        """
        pid = str(product.pk)
        current = self._cart.get(pid, {"quantity": 0})["quantity"]
        new_qty = quantity if replace else current + quantity
        new_qty = max(0, min(new_qty, product.stock))
        if new_qty == 0:
            self.remove(product)
            return
        self._cart[pid] = {"quantity": new_qty}
        self._save()

    def remove(self, product: Product) -> None:
        self._cart.pop(str(product.pk), None)
        self._save()

    def clear(self) -> None:
        self.session.pop(settings.CART_SESSION_ID, None)
        self.session.modified = True

    def _save(self) -> None:
        self.session[settings.CART_SESSION_ID] = self._cart
        self.session.modified = True

    # --- чтение ----------------------------------------------------------
    def _products(self) -> dict[int, Product]:
        ids = [int(pid) for pid in self._cart]
        return {p.pk: p for p in Product.objects.filter(pk__in=ids)}

    def __iter__(self) -> Iterator[CartLine]:
        products = self._products()
        for pid, row in self._cart.items():
            product = products.get(int(pid))
            if product is not None:
                yield CartLine(product=product, quantity=row["quantity"])

    def __len__(self) -> int:
        return sum(row["quantity"] for row in self._cart.values())

    @property
    def total(self) -> Decimal:
        return sum((line.subtotal for line in self), Decimal("0.00"))

    @property
    def is_empty(self) -> bool:
        return not self._cart

    def has_stock_issues(self) -> bool:
        return any(not line.has_enough_stock for line in self)

    def quantity_of(self, product: Product) -> int:
        return self._cart.get(str(product.pk), {"quantity": 0})["quantity"]
