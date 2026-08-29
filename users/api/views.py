"""API-представления пользователей: регистрация, вход (JWT), профиль."""

from __future__ import annotations

from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions
from rest_framework.request import Request
from rest_framework.response import Response

from users.models import User

from .serializers import RegisterSerializer, UserSerializer


class RegisterView(generics.CreateAPIView[User]):
    """Создание нового аккаунта. Авторизация не требуется."""

    serializer_class = RegisterSerializer
    permission_classes = (permissions.AllowAny,)
    queryset = User.objects.all()


class MeView(generics.RetrieveUpdateAPIView[User]):
    """Просмотр и редактирование собственного профиля (JWT)."""

    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self) -> User:
        return self.request.user  # type: ignore[return-value]

    @extend_schema(summary="Текущий пользователь")
    def get(self, request: Request, *args: object, **kwargs: object) -> Response:
        return super().get(request, *args, **kwargs)
