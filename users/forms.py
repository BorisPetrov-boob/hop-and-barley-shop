"""Формы регистрации, входа и профиля."""

from __future__ import annotations

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.utils.translation import gettext_lazy as _

from .models import Address, User


class RegistrationForm(UserCreationForm):
    """Регистрация нового пользователя по email."""

    email = forms.EmailField(label=_("Email"), required=True)

    class Meta:
        model = User
        fields = ("email", "first_name", "phone")

    def clean_email(self) -> str:
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(_("Пользователь с таким email уже зарегистрирован."))
        return email


class EmailAuthenticationForm(AuthenticationForm):
    """Форма входа: поле логина подписано как «Email»."""

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)  # type: ignore[arg-type]
        self.fields["username"].label = _("Email")
        self.fields["username"].widget = forms.EmailInput(
            attrs={"autofocus": True, "autocomplete": "email"}
        )


class ProfileForm(forms.ModelForm):
    """Редактирование основных данных профиля."""

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email", "phone")

    def clean_email(self) -> str:
        email = self.cleaned_data["email"].lower()
        qs = User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError(_("Этот email уже занят."))
        return email


class AddressForm(forms.ModelForm):
    """Адрес доставки в личном кабинете."""

    class Meta:
        model = Address
        fields = ("full_name", "phone", "city", "street", "postal_code", "is_default")
