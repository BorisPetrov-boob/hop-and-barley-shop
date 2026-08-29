"""URL-ы личного кабинета."""

from __future__ import annotations

from django.urls import path

from . import views

app_name = "users"

urlpatterns = [
    path("", views.account_view, name="account"),
    path("register/", views.RegisterView.as_view(), name="register"),
    path("login/", views.AppLoginView.as_view(), name="login"),
    path("logout/", views.AppLogoutView.as_view(), name="logout"),
    path("profile/", views.ProfileUpdateView.as_view(), name="profile"),
    path("password/", views.AppPasswordChangeView.as_view(), name="password_change"),
]
