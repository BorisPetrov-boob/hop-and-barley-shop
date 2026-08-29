"""Модель платежа (эмуляция платёжного шлюза)."""

from __future__ import annotations

from django.db import models
from django.utils.translation import gettext_lazy as _

from common.models import TimeStampedModel
from orders.models import Order, PaymentMethod


class Payment(TimeStampedModel):
    """Запись о попытке оплаты заказа. Реальный шлюз не подключён — статус
    выставляется мок-сервисом :func:`payments.services.process_payment`.
    """

    class Status(models.TextChoices):
        PENDING = "pending", _("Ожидает")
        SUCCEEDED = "succeeded", _("Успешно")
        FAILED = "failed", _("Отклонено")

    order = models.OneToOneField(
        Order, on_delete=models.CASCADE, related_name="payment", verbose_name=_("заказ")
    )
    method = models.CharField(_("способ"), max_length=16, choices=PaymentMethod.choices)
    status = models.CharField(
        _("статус"), max_length=16, choices=Status.choices, default=Status.PENDING
    )
    amount = models.DecimalField(_("сумма"), max_digits=12, decimal_places=2)
    transaction_id = models.CharField(_("id транзакции"), max_length=64, blank=True)
    error_message = models.CharField(_("ошибка"), max_length=255, blank=True)

    class Meta:
        verbose_name = _("платёж")
        verbose_name_plural = _("платежи")
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.order.number} — {self.get_status_display()} ({self.amount})"
