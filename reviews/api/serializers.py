"""Сериализаторы отзывов."""

from __future__ import annotations

from typing import Any

from rest_framework import serializers

from reviews.models import Review


class ReviewSerializer(serializers.ModelSerializer[Review]):
    """Чтение и создание отзыва (``product`` и ``user`` проставляет view)."""

    user = serializers.CharField(source="user.display_name", read_only=True)

    class Meta:
        model = Review
        fields = ("id", "user", "rating", "comment", "created_at")
        read_only_fields = ("id", "user", "created_at")

    def validate_rating(self, value: int) -> int:
        if not 1 <= value <= 5:
            raise serializers.ValidationError("Оценка должна быть от 1 до 5.")
        return value

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        # Основную проверку «купил / не дублирует» делает view, здесь — на всякий случай.
        return attrs
