"""Админка заказов с аналитикой (выручка, средний чек)."""

from __future__ import annotations

from django.contrib import admin
from django.db.models import Avg, Count, QuerySet, Sum
from django.http import HttpRequest

from .models import Order, OrderItem
from .services import cancel_order, mark_paid


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    autocomplete_fields = ("product",)
    readonly_fields = ("subtotal",)

    @admin.display(description="Сумма")
    def subtotal(self, obj: OrderItem) -> str:
        return f"{obj.subtotal:.2f}"


@admin.action(description="Пометить как оплаченные")
def action_mark_paid(
    modeladmin: admin.ModelAdmin, request: HttpRequest, qs: QuerySet[Order]
) -> None:
    for order in qs.exclude(status=Order.Status.PAID):
        mark_paid(order)
    modeladmin.message_user(request, "Готово.")


@admin.action(description="Отменить (вернуть остатки)")
def action_cancel(modeladmin: admin.ModelAdmin, request: HttpRequest, qs: QuerySet[Order]) -> None:
    for order in qs:
        cancel_order(order)
    modeladmin.message_user(request, "Заказы отменены, остатки возвращены.")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("number", "user", "status", "total_price", "payment_method", "created_at")
    list_filter = ("status", "payment_method", "created_at")
    search_fields = ("id", "user__email", "contact_name", "contact_phone")
    date_hierarchy = "created_at"
    autocomplete_fields = ("user",)
    inlines = (OrderItemInline,)
    readonly_fields = ("total_price", "created_at", "updated_at", "paid_at", "number")
    actions = (action_mark_paid, action_cancel)

    @admin.display(description="Номер")
    def number(self, obj: Order) -> str:
        return obj.number

    def changelist_view(self, request: HttpRequest, extra_context: dict | None = None):  # noqa: ANN201
        """Сводка по выручке над списком заказов."""
        response = super().changelist_view(request, extra_context=extra_context)
        try:
            qs = response.context_data["cl"].queryset
        except (AttributeError, KeyError):
            return response
        paid = qs.filter(status__in=("paid", "shipped", "delivered"))
        response.context_data["summary"] = paid.aggregate(
            revenue=Sum("total_price"),
            orders=Count("id"),
            avg_check=Avg("total_price"),
        )
        return response


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("order", "product", "quantity", "price")
    search_fields = ("order__id", "product__name")
    autocomplete_fields = ("order", "product")
