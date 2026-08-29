"""Веб-URL отзывов."""

from __future__ import annotations

from django.urls import path

from . import views

app_name = "reviews"

urlpatterns = [
    path("product/<slug:slug>/review/", views.add_review, name="add"),
]
