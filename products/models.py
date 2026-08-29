"""Модели каталога: категории, товары, изображения товаров."""

from __future__ import annotations

from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from common.models import TimeStampedModel

from .querysets import CategoryQuerySet, ProductQuerySet


def _unique_slug(model: type[models.Model], value: str) -> str:
    """Сгенерировать уникальный slug на основе ``value``."""
    base = slugify(value, allow_unicode=False) or "item"
    slug = base
    counter = 2
    while model._default_manager.filter(slug=slug).exists():
        slug = f"{base}-{counter}"
        counter += 1
    return slug


class Category(TimeStampedModel):
    """Категория товаров с поддержкой вложенности (``parent``)."""

    name = models.CharField(_("название"), max_length=128)
    slug = models.SlugField(_("slug"), max_length=140, unique=True, blank=True)
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children",
        verbose_name=_("родительская категория"),
    )

    objects = CategoryQuerySet.as_manager()

    class Meta:
        verbose_name = _("категория")
        verbose_name_plural = _("категории")
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name

    def save(self, *args: object, **kwargs: object) -> None:
        if not self.slug:
            self.slug = _unique_slug(Category, self.name)
        super().save(*args, **kwargs)  # type: ignore[arg-type]

    def get_absolute_url(self) -> str:
        return reverse("products:product_list") + f"?category={self.slug}"


class Product(TimeStampedModel):
    """Товар каталога."""

    name = models.CharField(_("название"), max_length=200)
    slug = models.SlugField(_("slug"), max_length=220, unique=True, blank=True)
    description = models.TextField(_("описание"), blank=True)
    price = models.DecimalField(
        _("цена"),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    price_unit = models.CharField(
        _("единица цены"), max_length=32, blank=True, help_text=_("напр. «за 100 г»")
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="products",
        verbose_name=_("категория"),
    )
    image = models.ImageField(_("изображение"), upload_to="products/", blank=True)
    is_active = models.BooleanField(_("активен"), default=True, db_index=True)
    stock = models.PositiveIntegerField(_("остаток на складе"), default=0)

    objects = ProductQuerySet.as_manager()

    class Meta:
        verbose_name = _("товар")
        verbose_name_plural = _("товары")
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["is_active", "-created_at"]),
            models.Index(fields=["category", "is_active"]),
        ]

    def __str__(self) -> str:
        return self.name

    def save(self, *args: object, **kwargs: object) -> None:
        if not self.slug:
            self.slug = _unique_slug(Product, self.name)
        super().save(*args, **kwargs)  # type: ignore[arg-type]

    def get_absolute_url(self) -> str:
        return reverse("products:product_detail", kwargs={"slug": self.slug})

    @property
    def in_stock(self) -> bool:
        return self.stock > 0

    def can_order(self, quantity: int) -> bool:
        """Достаточно ли остатка для заказа ``quantity`` единиц."""
        return self.is_active and 0 < quantity <= self.stock


class ProductImage(TimeStampedModel):
    """Дополнительное изображение товара (галерея)."""

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="images",
        verbose_name=_("товар"),
    )
    image = models.ImageField(_("изображение"), upload_to="products/gallery/")
    alt = models.CharField(_("alt-текст"), max_length=200, blank=True)
    sort_order = models.PositiveSmallIntegerField(_("порядок"), default=0)

    class Meta:
        verbose_name = _("изображение товара")
        verbose_name_plural = _("изображения товара")
        ordering = ("sort_order", "id")

    def __str__(self) -> str:
        return f"{self.product.name} — изображение #{self.pk}"
