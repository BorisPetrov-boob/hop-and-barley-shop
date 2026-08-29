"""GraphQL-view с поддержкой JWT и сессионной аутентификации."""

from __future__ import annotations

from django.conf import settings
from django.http import HttpRequest
from django.views.decorators.csrf import csrf_exempt
from graphene_django.views import GraphQLView
from rest_framework_simplejwt.authentication import JWTAuthentication

from .schema import schema


class AuthGraphQLView(GraphQLView):
    """Перед обработкой запроса пытается аутентифицировать пользователя по JWT.

    Если Bearer-токен отсутствует или невалиден — остаётся сессионный
    ``request.user`` (для входа через админку/браузер). Проверку прав
    (``is_staff``) выполняют резолверы схемы.
    """

    def dispatch(self, request: HttpRequest, *args: object, **kwargs: object):  # noqa: ANN201
        if not getattr(request.user, "is_authenticated", False):
            try:
                result = JWTAuthentication().authenticate(request)
            except Exception:  # noqa: BLE001 — невалидный токен не должен ронять view
                result = None
            if result is not None:
                request.user, request.auth = result
        return super().dispatch(request, *args, **kwargs)


analytics_graphql_view = csrf_exempt(
    AuthGraphQLView.as_view(graphiql=settings.DEBUG, schema=schema)
)
