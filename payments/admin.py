"""Админка платежей."""

from __future__ import annotations

from django.contrib import admin

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("order", "method", "status", "amount", "transaction_id", "created_at")
    list_filter = ("status", "method", "created_at")
    search_fields = ("order__id", "transaction_id")
    autocomplete_fields = ("order",)
    readonly_fields = ("created_at", "updated_at")
