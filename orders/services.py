"""Бизнес-логика заказов: создание из корзины, письма, отмена."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.template.loader import render_to_string
from django.utils import timezone

from products.models import Product

from .models import Order, OrderItem

if TYPE_CHECKING:
    from users.models import User

    from .cart import Cart


class OutOfStockError(Exception):
    """Недостаточно товара на складе для оформления заказа."""

    def __init__(self, product: Product, requested: int, available: int) -> None:
        self.product = product
        self.requested = requested
        self.available = available
        super().__init__(f"«{product.name}»: запрошено {requested}, доступно {available}.")


class EmptyCartError(Exception):
    """Попытка оформить пустой заказ."""


@dataclass(frozen=True, slots=True)
class LineInput:
    product_id: int
    quantity: int


@transaction.atomic
def create_order(
    *,
    user: User,
    lines: list[LineInput],
    shipping_address: str,
    contact_name: str,
    contact_phone: str,
    contact_email: str = "",
    payment_method: str = "debit",
) -> Order:
    """Создать заказ, списав остатки под блокировкой строк товаров.

    Бросает :class:`EmptyCartError` или :class:`OutOfStockError`.
    Письма отправляются после успешного коммита транзакции.
    """
    if not lines:
        raise EmptyCartError

    product_ids = [line.product_id for line in lines]
    locked = Product.objects.select_for_update().filter(pk__in=product_ids, is_active=True)
    products = {p.pk: p for p in locked}

    order = Order.objects.create(
        user=user,
        status=Order.Status.PENDING,
        shipping_address=shipping_address,
        contact_name=contact_name,
        contact_phone=contact_phone,
        contact_email=contact_email,
        payment_method=payment_method,
    )

    total = Decimal("0.00")
    items: list[OrderItem] = []
    for line in lines:
        product = products.get(line.product_id)
        if product is None:
            raise OutOfStockError(Product(name=f"#{line.product_id}"), line.quantity, 0)
        if line.quantity > product.stock:
            raise OutOfStockError(product, line.quantity, product.stock)
        items.append(
            OrderItem(order=order, product=product, quantity=line.quantity, price=product.price)
        )
        total += product.price * line.quantity

    OrderItem.objects.bulk_create(items)
    Product.objects.bulk_update(
        [_decremented(products[line.product_id], line.quantity) for line in lines],
        ["stock"],
    )

    order.total_price = total
    order.save(update_fields=["total_price", "updated_at"])

    transaction.on_commit(lambda: send_order_emails(order.pk))
    return order


def _decremented(product: Product, qty: int) -> Product:
    product.stock -= qty
    return product


def create_order_from_cart(
    *, user: User, cart: Cart, checkout: dict[str, str]
) -> Order:
    """Адаптер: превратить корзину-сессию в заказ."""
    if cart.is_empty:
        raise EmptyCartError
    lines = [LineInput(product_id=line.product.pk, quantity=line.quantity) for line in cart]
    order = create_order(
        user=user,
        lines=lines,
        shipping_address=f"{checkout['city']}, {checkout['address']}",
        contact_name=checkout["full_name"],
        contact_phone=checkout["phone"],
        contact_email=checkout.get("email", ""),
        payment_method=checkout.get("payment_method", "debit"),
    )
    cart.clear()
    return order


def mark_paid(order: Order) -> None:
    """Пометить заказ оплаченным (используется мок-платежом)."""
    order.status = Order.Status.PAID
    order.paid_at = timezone.now()
    order.save(update_fields=["status", "paid_at", "updated_at"])


@transaction.atomic
def cancel_order(order: Order) -> Order:
    """Отменить заказ и вернуть остатки на склад."""
    if order.status == Order.Status.CANCELLED:
        return order
    for item in order.items.select_related("product").select_for_update():
        Product.objects.filter(pk=item.product_id).update(stock=_stock_plus(item))
    order.status = Order.Status.CANCELLED
    order.save(update_fields=["status", "updated_at"])
    return order


def _stock_plus(item: OrderItem):  # noqa: ANN201
    from django.db.models import F

    return F("stock") + item.quantity


def send_order_emails(order_id: int) -> None:
    """Отправить письма покупателю и администратору."""
    try:
        order = (
            Order.objects.prefetch_related("items__product").select_related("user").get(pk=order_id)
        )
    except Order.DoesNotExist:  # pragma: no cover
        return

    ctx = {"order": order, "items": list(order.items.all())}
    customer_email = order.contact_email or order.user.email

    send_mail(
        subject=f"Заказ {order.number} принят",
        message=render_to_string("emails/order_confirmation.txt", ctx),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[customer_email],
        fail_silently=True,
    )
    send_mail(
        subject=f"Новый заказ {order.number}",
        message=render_to_string("emails/order_admin_notification.txt", ctx),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[settings.ORDER_ADMIN_EMAIL],
        fail_silently=True,
    )
