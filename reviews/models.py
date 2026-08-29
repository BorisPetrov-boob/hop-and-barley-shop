"""Модель отзыва на товар."""

from __future__ import annotations

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from common.models import TimeStampedModel
from products.models import Product

MIN_RATING = 1
MAX_RATING = 5


class Review(TimeStampedModel):
    """Отзыв пользователя о товаре. Один отзыв на пару (товар, пользователь)."""

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="reviews", verbose_name=_("товар")
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reviews",
        verbose_name=_("автор"),
    )
    rating = models.PositiveSmallIntegerField(
        _("оценка"),
        validators=[MinValueValidator(MIN_RATING), MaxValueValidator(MAX_RATING)],
    )
    comment = models.TextField(_("комментарий"), blank=True)

    class Meta:
        verbose_name = _("отзыв")
        verbose_name_plural = _("отзывы")
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(fields=("product", "user"), name="uniq_review_per_user"),
            models.CheckConstraint(
                condition=models.Q(rating__gte=MIN_RATING, rating__lte=MAX_RATING),
                name="review_rating_range",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.product} — {self.rating}★ от {self.user}"
