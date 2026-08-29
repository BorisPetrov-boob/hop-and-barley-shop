"""Админка каталога с аннотациями (рейтинг, продажи, выручка)."""

from __future__ import annotations

from typing import Any

from django.contrib import admin
from django.db.models import DecimalField, ExpressionWrapper, F, Q, QuerySet, Sum
from django.db.models.functions import Coalesce
from django.http import HttpRequest
from django.utils.html import format_html

from .models import Category, Product, ProductImage
from .querysets import SOLD_ORDER_STATUSES


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "parent", "product_count", "slug")
    list_filter = ("parent",)
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    autocomplete_fields = ("parent",)

    def get_queryset(self, request: HttpRequest) -> QuerySet[Category]:
        return super().get_queryset(request).with_product_counts()

    @admin.display(description="Товаров", ordering="product_count")
    def product_count(self, obj: Category) -> int:
        return getattr(obj, "product_count", 0)


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


@admin.action(description="Активировать выбранные товары")
def make_active(
    modeladmin: admin.ModelAdmin, request: HttpRequest, queryset: QuerySet[Product]
) -> None:
    updated = queryset.update(is_active=True)
    modeladmin.message_user(request, f"Активировано товаров: {updated}.")


@admin.action(description="Снять с публикации")
def make_inactive(
    modeladmin: admin.ModelAdmin, request: HttpRequest, queryset: QuerySet[Product]
) -> None:
    updated = queryset.update(is_active=False)
    modeladmin.message_user(request, f"Снято с публикации: {updated}.")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "category",
        "price",
        "stock",
        "is_active",
        "sales_count",
        "revenue",
        "avg_rating",
        "created_at",
    )
    list_filter = ("is_active", "category", "created_at")
    list_editable = ("price", "stock", "is_active")
    search_fields = ("name", "description", "slug")
    prepopulated_fields = {"slug": ("name",)}
    autocomplete_fields = ("category",)
    inlines = (ProductImageInline,)
    actions = (make_active, make_inactive)
    date_hierarchy = "created_at"
    readonly_fields = ("preview",)

    def get_queryset(self, request: HttpRequest) -> QuerySet[Product]:
        revenue_expr = ExpressionWrapper(
            F("order_items__quantity") * F("order_items__price"),
            output_field=DecimalField(max_digits=12, decimal_places=2),
        )
        return (
            super()
            .get_queryset(request)
            .select_related("category")
            .with_stats()
            .annotate(
                revenue_total=Coalesce(
                    Sum(
                        revenue_expr,
                        filter=Q(order_items__order__status__in=SOLD_ORDER_STATUSES),
                    ),
                    0,
                    output_field=DecimalField(max_digits=12, decimal_places=2),
                )
            )
        )

    @admin.display(description="Продано, шт.", ordering="sales_count")
    def sales_count(self, obj: Product) -> int:
        return getattr(obj, "sales_count", 0)

    @admin.display(description="Выручка", ordering="revenue_total")
    def revenue(self, obj: Product) -> str:
        return f"{getattr(obj, 'revenue_total', 0):.2f}"

    @admin.display(description="Рейтинг", ordering="avg_rating")
    def avg_rating(self, obj: Product) -> str:
        return f"{getattr(obj, 'avg_rating', 0):.2f}"

    @admin.display(description="Превью")
    def preview(self, obj: Product) -> Any:
        if obj.image:
            return format_html('<img src="{}" style="max-height:160px;">', obj.image.url)
        return "—"


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ("product", "sort_order", "alt")
    autocomplete_fields = ("product",)
