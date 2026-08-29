"""Форма отзыва."""

from __future__ import annotations

from django import forms

from .models import MAX_RATING, MIN_RATING, Review


class ReviewForm(forms.ModelForm):
    """Оценка (1–5) и текстовый комментарий."""

    rating = forms.TypedChoiceField(
        label="Оценка",
        coerce=int,
        choices=[(i, f"{i} ★") for i in range(MIN_RATING, MAX_RATING + 1)],
        widget=forms.RadioSelect,
    )

    class Meta:
        model = Review
        fields = ("rating", "comment")
        widgets = {
            "comment": forms.Textarea(attrs={"rows": 4, "placeholder": "Ваши впечатления…"}),
        }
