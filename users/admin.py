"""Админка пользователей и адресов."""

from __future__ import annotations

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import Address, User


class AddressInline(admin.TabularInline):
    model = Address
    extra = 0


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    """Админка кастомного пользователя (логин по email)."""

    ordering = ("email",)
    list_display = ("email", "first_name", "last_name", "is_staff", "is_active", "date_joined")
    list_filter = ("is_staff", "is_superuser", "is_active")
    search_fields = ("email", "first_name", "last_name", "phone")
    inlines = (AddressInline,)

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("Личные данные"), {"fields": ("first_name", "last_name", "phone")}),
        (
            _("Права"),
            {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")},
        ),
        (_("Даты"), {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "first_name", "phone", "password1", "password2"),
            },
        ),
    )


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ("user", "city", "street", "is_default", "created_at")
    list_filter = ("is_default", "city")
    search_fields = ("user__email", "city", "street", "full_name")
    autocomplete_fields = ("user",)
