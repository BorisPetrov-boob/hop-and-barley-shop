"""Модели пользователя и адресов доставки."""

from __future__ import annotations

from typing import ClassVar

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from common.models import TimeStampedModel

from .managers import UserManager


class User(AbstractUser):
    """Пользователь магазина. Логин — email, поле ``username`` не используется."""

    username = None  # type: ignore[assignment,misc]
    email = models.EmailField(_("email"), unique=True)
    phone = models.CharField(_("телефон"), max_length=32, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: ClassVar[list[str]] = []

    objects = UserManager()  # type: ignore[assignment,misc]

    class Meta:
        verbose_name = _("пользователь")
        verbose_name_plural = _("пользователи")

    def __str__(self) -> str:
        return self.email

    @property
    def display_name(self) -> str:
        """Имя для отображения в шапке / письмах."""
        full = self.get_full_name().strip()
        return full or self.email.split("@", 1)[0]


class Address(TimeStampedModel):
    """Адрес доставки пользователя (опционально, несколько на пользователя)."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="addresses",
        verbose_name=_("пользователь"),
    )
    full_name = models.CharField(_("получатель"), max_length=255)
    phone = models.CharField(_("телефон"), max_length=32)
    city = models.CharField(_("город"), max_length=128)
    street = models.CharField(_("улица, дом, квартира"), max_length=255)
    postal_code = models.CharField(_("индекс"), max_length=16, blank=True)
    is_default = models.BooleanField(_("основной"), default=False)

    class Meta:
        verbose_name = _("адрес доставки")
        verbose_name_plural = _("адреса доставки")
        ordering = ("-is_default", "-created_at")

    def __str__(self) -> str:
        return f"{self.city}, {self.street} ({self.full_name})"

    def as_text(self) -> str:
        """Однострочное представление для снапшота в заказе."""
        parts = [self.full_name, self.phone, self.postal_code, self.city, self.street]
        return ", ".join(p for p in parts if p)

    def save(self, *args: object, **kwargs: object) -> None:
        super().save(*args, **kwargs)  # type: ignore[arg-type]
        if self.is_default:
            Address.objects.filter(user=self.user).exclude(pk=self.pk).update(is_default=False)
