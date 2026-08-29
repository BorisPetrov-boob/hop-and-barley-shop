"""Пользователи: регистрация/вход через веб и API (JWT), профиль."""

from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

pytestmark = pytest.mark.django_db
User = get_user_model()


def test_web_registration_logs_in(client):
    resp = client.post(
        reverse("users:register"),
        {
            "email": "new@example.com",
            "first_name": "Ника",
            "phone": "+70000000000",
            "password1": "SuperSecret123",
            "password2": "SuperSecret123",
        },
        follow=True,
    )
    assert resp.status_code == 200
    assert User.objects.filter(email="new@example.com").exists()
    assert resp.context["user"].is_authenticated


def test_web_login_logout(client, user):
    resp = client.post(reverse("users:login"), {"username": user.email, "password": "pass12345"})
    assert resp.status_code == 302
    resp = client.post(reverse("users:logout"))
    assert resp.status_code == 302


def test_api_register_and_jwt_login(api_client):
    reg = api_client.post(
        "/api/users/register/",
        {"email": "api@example.com", "password": "SuperSecret123", "first_name": "Api"},
        format="json",
    )
    assert reg.status_code == 201

    login = api_client.post(
        "/api/users/login/",
        {"email": "api@example.com", "password": "SuperSecret123"},
        format="json",
    )
    assert login.status_code == 200
    assert "access" in login.data and "refresh" in login.data

    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
    me = api_client.get("/api/users/me/")
    assert me.status_code == 200
    assert me.data["email"] == "api@example.com"


def test_api_register_rejects_weak_password(api_client):
    resp = api_client.post(
        "/api/users/register/",
        {"email": "weak@example.com", "password": "123"},
        format="json",
    )
    assert resp.status_code == 400


def test_api_me_requires_auth(api_client):
    assert api_client.get("/api/users/me/").status_code == 401


def test_profile_update_web(client, user):
    client.force_login(user)
    resp = client.post(
        reverse("users:profile"),
        {"first_name": "Ново", "last_name": "Имя", "email": user.email, "phone": "+71112223344"},
        follow=True,
    )
    assert resp.status_code == 200
    user.refresh_from_db()
    assert user.first_name == "Ново"
