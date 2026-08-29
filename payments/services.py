"""Эмуляция платёжного шлюза.

`process_payment` создаёт запись :class:`Payment` и, для «мгновенных» способов
оплаты (карта, кошелёк), помечает заказ оплаченным. Наложенный платёж
остаётся в статусе «ожидает».
"""

from __future__ import annotations

import uuid

from django.db import transaction

from orders.models import Order, PaymentMethod
from orders.services import mark_paid

from .models import Payment

INSTANT_METHODS = {PaymentMethod.CARD, PaymentMethod.WALLET}


@transaction.atomic
def process_payment(order: Order) -> Payment:
    """Провести (эмулировать) оплату заказа. Идемпотентно по заказу."""
    payment, _created = Payment.objects.get_or_create(
        order=order,
        defaults={"method": order.payment_method, "amount": order.total_price},
    )
    if payment.status == Payment.Status.SUCCEEDED:
        return payment

    if order.payment_method in INSTANT_METHODS:
        payment.status = Payment.Status.SUCCEEDED
        payment.transaction_id = uuid.uuid4().hex
        payment.save(update_fields=["status", "transaction_id", "updated_at"])
        mark_paid(order)
    else:  # cod — оплата при получении
        payment.status = Payment.Status.PENDING
        payment.save(update_fields=["status", "updated_at"])

    return payment
