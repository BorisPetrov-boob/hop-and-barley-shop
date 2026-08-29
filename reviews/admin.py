"""Админка отзывов."""

from __future__ import annotations

from django.contrib import admin

from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("product", "user", "rating", "short_comment", "created_at")
    list_filter = ("rating", "created_at")
    search_fields = ("product__name", "user__email", "comment")
    autocomplete_fields = ("product", "user")
    date_hierarchy = "created_at"

    @admin.display(description="Комментарий")
    def short_comment(self, obj: Review) -> str:
        return (obj.comment[:60] + "…") if len(obj.comment) > 60 else obj.comment
