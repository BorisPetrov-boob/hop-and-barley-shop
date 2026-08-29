"""Модели заказа и позиций заказа."""

from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Sum
from django.db.models.functions import Coalesce
from django.utils.translation import gettext_lazy as _

from common.models import TimeStampedModel
from products.models import Product


class PaymentMethod(models.TextChoices):
    CARD = "debit", _("Дебетовая карта")
    WALLET = "wallet", _("Электронный кошелёк")
    COD = "cod", _("Наложенный платёж")


class OrderQuerySet(models.QuerySet["Order"]):
    def for_user(self, user: settings.AUTH_USER_MODEL) -> OrderQuerySet:  # type: ignore[name-defined]
        return self.filter(user=user)

    def with_totals(self) -> OrderQuerySet:
        return self.annotate(
            items_count=Coalesce(Sum("items__quantity"), 0),
        )


class Order(TimeStampedModel):
    """Заказ пользователя. ``total_price`` фиксируется на момент оформления."""

    class Status(models.TextChoices):
        PENDING = "pending", _("Ожидает оплаты")
        PAID = "paid", _("Оплачен")
        SHIPPED = "shipped", _("Отправлен")
        DELIVERED = "delivered", _("Доставлен")
        CANCELLED = "cancelled", _("Отменён")

    #: Статусы, из которых пользователь может сам отменить заказ.
    USER_CANCELLABLE = {Status.PENDING, Status.PAID}

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="orders",
        verbose_name=_("пользователь"),
    )
    status = models.CharField(
        _("статус"), max_length=16, choices=Status.choices, default=Status.PENDING, db_index=True
    )
    total_price = models.DecimalField(
        _("сумма заказа"), max_digits=12, decimal_places=2, default=Decimal("0.00")
    )
    shipping_address = models.TextField(_("адрес доставки"))
    contact_name = models.CharField(_("контактное лицо"), max_length=255)
    contact_phone = models.CharField(_("телефон"), max_length=32)
    contact_email = models.EmailField(_("email"), blank=True)
    payment_method = models.CharField(
        _("способ оплаты"), max_length=16, choices=PaymentMethod.choices, default=PaymentMethod.CARD
    )
    paid_at = models.DateTimeField(_("оплачен"), null=True, blank=True)

    objects = OrderQuerySet.as_manager()

    class Meta:
        verbose_name = _("заказ")
        verbose_name_plural = _("заказы")
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return self.number

    @property
    def number(self) -> str:
        """Человекочитаемый номер заказа."""
        return f"HB-{self.pk:06d}" if self.pk else "HB-—"

    def recalculate_total(self) -> Decimal:
        """Пересчитать ``total_price`` по позициям и сохранить."""
        agg = self.items.aggregate(total=Coalesce(Sum(F("price") * F("quantity")), Decimal("0.00")))
        self.total_price = agg["total"]
        self.save(update_fields=["total_price", "updated_at"])
        return self.total_price

    def can_be_cancelled_by(self, user: settings.AUTH_USER_MODEL) -> bool:  # type: ignore[name-defined]
        return user == self.user and self.status in self.USER_CANCELLABLE


class OrderItem(TimeStampedModel):
    """Позиция заказа со снапшотом цены товара."""

    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="items", verbose_name=_("заказ")
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="order_items",
        verbose_name=_("товар"),
    )
    quantity = models.PositiveIntegerField(_("количество"), validators=[MinValueValidator(1)])
    price = models.DecimalField(_("цена за единицу"), max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = _("позиция заказа")
        verbose_name_plural = _("позиции заказа")
        ordering = ("id",)
        constraints = [
            models.UniqueConstraint(fields=("order", "product"), name="uniq_order_product"),
        ]

    def __str__(self) -> str:
        return f"{self.product} × {self.quantity}"

    @property
    def subtotal(self) -> Decimal:
        return self.price * self.quantity
