"""Веб-представления личного кабинета (session-аутентификация)."""

from __future__ import annotations

from typing import Any

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordChangeView,
)
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView

from orders.models import Order

from .forms import EmailAuthenticationForm, ProfileForm, RegistrationForm
from .models import User


class RegisterView(CreateView):
    """Регистрация с автоматическим входом после успеха."""

    template_name = "users/register.html"
    form_class = RegistrationForm
    success_url = reverse_lazy("products:product_list")

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        if request.user.is_authenticated:
            return redirect(self.success_url)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form: RegistrationForm) -> HttpResponse:
        response = super().form_valid(form)
        login(self.request, self.object)
        messages.success(self.request, "Добро пожаловать в Hop & Barley!")
        return response


class AppLoginView(LoginView):
    template_name = "users/login.html"
    authentication_form = EmailAuthenticationForm
    redirect_authenticated_user = True


class AppLogoutView(LogoutView):
    next_page = reverse_lazy("products:product_list")


class ProfileUpdateView(UpdateView):
    """Редактирование профиля."""

    template_name = "users/profile_form.html"
    form_class = ProfileForm
    success_url = reverse_lazy("users:account")

    def get_object(self, queryset: QuerySet[User] | None = None) -> User:
        return self.request.user  # type: ignore[return-value]

    def form_valid(self, form: ProfileForm) -> HttpResponse:
        messages.success(self.request, "Профиль обновлён.")
        return super().form_valid(form)


class AppPasswordChangeView(PasswordChangeView):
    template_name = "users/password_change.html"
    success_url = reverse_lazy("users:account")

    def form_valid(self, form: Any) -> HttpResponse:
        messages.success(self.request, "Пароль изменён.")
        return super().form_valid(form)


@login_required
def account_view(request: HttpRequest) -> HttpResponse:
    """Личный кабинет: история заказов + данные профиля.

    Поддерживает фильтрацию заказов по статусу через ``?status=``.
    """
    orders: QuerySet[Order] = (
        Order.objects.filter(user=request.user)
        .prefetch_related("items__product")
        .order_by("-created_at")
    )
    status = request.GET.get("status")
    if status in dict(Order.Status.choices):
        orders = orders.filter(status=status)

    context: dict[str, Any] = {
        "orders": orders,
        "status_choices": Order.Status.choices,
        "active_status": status or "",
        "profile_form": ProfileForm(instance=request.user),
    }
    return render(request, "users/account.html", context)
