"""Веб-обработчик добавления отзыва со страницы товара."""

from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST

from products.models import Product

from .forms import ReviewForm
from .services import user_can_review


@login_required
@require_POST
def add_review(request: HttpRequest, slug: str) -> HttpResponse:
    """Создать отзыв. Доступно только тем, кто купил товар."""
    product = get_object_or_404(Product.objects.active(), slug=slug)

    if not user_can_review(request.user, product):
        messages.error(
            request,
            "Оставить отзыв можно только после покупки товара (и только один раз).",
        )
        return redirect(product.get_absolute_url())

    form = ReviewForm(request.POST)
    if form.is_valid():
        review = form.save(commit=False)
        review.product = product
        review.user = request.user
        review.save()
        messages.success(request, "Спасибо за отзыв!")
    else:
        messages.error(request, "Проверьте форму отзыва.")
    return redirect(product.get_absolute_url())
