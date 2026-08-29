"""Формы корзины и оформления заказа."""

from __future__ import annotations

from django import forms
from django.contrib.auth.models import AbstractUser, AnonymousUser
from django.utils.translation import gettext_lazy as _

from .models import PaymentMethod


class CartAddForm(forms.Form):
    """Добавление товара в корзину со страницы товара/каталога."""

    quantity = forms.IntegerField(min_value=1, max_value=999, initial=1)
    replace = forms.BooleanField(required=False, initial=False, widget=forms.HiddenInput)


class CartUpdateForm(forms.Form):
    """Изменение количества конкретной позиции на странице корзины."""

    product_id = forms.IntegerField(widget=forms.HiddenInput)
    quantity = forms.IntegerField(min_value=0, max_value=999)


class CheckoutForm(forms.Form):
    """Данные доставки и способ оплаты."""

    full_name = forms.CharField(label=_("ФИО"), max_length=255)
    phone = forms.CharField(label=_("Телефон"), max_length=32)
    email = forms.EmailField(label=_("Email"), required=False)
    city = forms.CharField(label=_("Город"), max_length=128)
    address = forms.CharField(label=_("Адрес доставки"), widget=forms.Textarea(attrs={"rows": 3}))
    payment_method = forms.ChoiceField(
        label=_("Способ оплаты"),
        choices=PaymentMethod.choices,
        widget=forms.RadioSelect,
        initial=PaymentMethod.CARD,
    )

    def build_shipping_address(self) -> str:
        data = self.cleaned_data
        return f"{data['city']}, {data['address']}"

    @classmethod
    def initial_from_user(cls, user: AbstractUser | AnonymousUser) -> dict[str, str]:
        if isinstance(user, AnonymousUser) or not user.is_authenticated:
            return {}
        return {
            "full_name": user.get_full_name(),
            "email": getattr(user, "email", ""),
            "phone": getattr(user, "phone", ""),
        }
