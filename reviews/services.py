"""Правила отзывов: оставлять отзыв можно только после покупки товара."""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib.auth.models import AnonymousUser

from orders.models import Order, OrderItem
from products.models import Product

from .models import Review

if TYPE_CHECKING:
    from users.models import User

#: Заказ считается «покупкой», если он оплачен и далее по воронке.
PURCHASED_STATUSES = (Order.Status.PAID, Order.Status.SHIPPED, Order.Status.DELIVERED)


def has_purchased(user: User | AnonymousUser, product_id: int) -> bool:
    """Покупал ли пользователь товар (в оплаченном/доставленном заказе)."""
    if isinstance(user, AnonymousUser) or not user.is_authenticated:
        return False
    return OrderItem.objects.filter(
        order__user=user,
        order__status__in=PURCHASED_STATUSES,
        product_id=product_id,
    ).exists()


def has_reviewed(user: User | AnonymousUser, product_id: int) -> bool:
    if isinstance(user, AnonymousUser) or not user.is_authenticated:
        return False
    return Review.objects.filter(user=user, product_id=product_id).exists()


def user_can_review(user: User | AnonymousUser, product: Product | int) -> bool:
    """Можно ли оставить отзыв: купил и ещё не оставлял."""
    product_id = product.pk if isinstance(product, Product) else product
    return has_purchased(user, product_id) and not has_reviewed(user, product_id)
