"""Веб-представления корзины и оформления заказа."""

from __future__ import annotations

from typing import Any

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from products.models import Product

from .cart import Cart
from .forms import CartAddForm, CheckoutForm
from .models import Order
from .services import EmptyCartError, OutOfStockError, create_order_from_cart


def cart_detail(request: HttpRequest) -> HttpResponse:
    """Страница корзины."""
    return render(request, "orders/cart.html", {})


@require_POST
def cart_add(request: HttpRequest, product_id: int) -> HttpResponse:
    """Добавить товар в корзину (или задать точное количество при ``replace``)."""
    product = get_object_or_404(Product.objects.active(), pk=product_id)
    form = CartAddForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Некорректное количество.")
        return redirect(product.get_absolute_url())

    cart = Cart(request)
    quantity = form.cleaned_data["quantity"]
    replace = form.cleaned_data["replace"]

    if product.stock == 0:
        messages.error(request, f"«{product.name}» нет в наличии.")
    else:
        cart.add(product, quantity=quantity, replace=replace)
        if quantity > product.stock:
            messages.warning(
                request, f"На складе только {product.stock} шт. — количество уменьшено."
            )
        else:
            messages.success(request, f"«{product.name}» в корзине.")

    next_url = request.POST.get("next") or request.META.get("HTTP_REFERER")
    return redirect(next_url or reverse("cart:detail"))


@require_POST
def cart_update(request: HttpRequest, product_id: int) -> HttpResponse:
    """Изменить количество позиции со страницы корзины."""
    product = get_object_or_404(Product, pk=product_id)
    cart = Cart(request)
    try:
        quantity = int(request.POST.get("quantity", "1"))
    except ValueError:
        quantity = 1
    cart.add(product, quantity=max(0, quantity), replace=True)
    return redirect("cart:detail")


@require_POST
def cart_remove(request: HttpRequest, product_id: int) -> HttpResponse:
    product = get_object_or_404(Product, pk=product_id)
    Cart(request).remove(product)
    messages.info(request, f"«{product.name}» удалён из корзины.")
    return redirect("cart:detail")


@login_required
def checkout(request: HttpRequest) -> HttpResponse:
    """Оформление заказа: форма доставки + мок-оплата."""
    cart = Cart(request)
    if cart.is_empty:
        messages.info(request, "Корзина пуста.")
        return redirect("products:product_list")

    if request.method == "POST":
        form = CheckoutForm(request.POST)
        if form.is_valid():
            try:
                order = create_order_from_cart(
                    user=request.user, cart=cart, checkout=form.cleaned_data
                )
            except OutOfStockError as exc:
                messages.error(request, str(exc))
                return redirect("cart:detail")
            except EmptyCartError:
                messages.info(request, "Корзина пуста.")
                return redirect("products:product_list")

            from payments.services import process_payment

            process_payment(order)
            messages.success(request, f"Заказ {order.number} оформлен. Мы отправили письмо.")
            return redirect("checkout:success", order_id=order.pk)
    else:
        form = CheckoutForm(initial=CheckoutForm.initial_from_user(request.user))

    context: dict[str, Any] = {"form": form, "cart": cart}
    return render(request, "orders/checkout.html", context)


@login_required
def checkout_success(request: HttpRequest, order_id: int) -> HttpResponse:
    order = get_object_or_404(
        Order.objects.prefetch_related("items__product"), pk=order_id, user=request.user
    )
    return render(request, "orders/checkout_success.html", {"order": order})
