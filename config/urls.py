"""Корневой URL-роутер проекта.

* Веб-интерфейс (session auth) — на верхнем уровне.
* REST API (JWT) — под префиксом ``/api/``.
* GraphQL-аналитика (бонус) — единый эндпоинт ``/graphql/``.
"""

from __future__ import annotations

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from analytics.views import analytics_graphql_view

admin.site.site_header = "Hop & Barley — администрирование"
admin.site.site_title = "Hop & Barley"
admin.site.index_title = "Управление магазином"

api_patterns = [
    path("", include("products.api.urls")),
    path("", include("reviews.api.urls")),
    path("", include("orders.api.urls")),
    path("users/", include("users.api.urls")),
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="api:schema"), name="swagger-ui"),
    path("redoc/", SpectacularRedocView.as_view(url_name="api:schema"), name="redoc"),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    # Веб-интерфейс.
    path("", include("products.urls")),
    path("", include("reviews.urls")),
    path("", include("orders.urls")),
    path("account/", include("users.urls")),
    # REST API.
    path("api/", include((api_patterns, "api"))),
    # GraphQL (бонус).
    path("graphql/", analytics_graphql_view, name="graphql"),
    # favicon и прочее — мягкий редирект на статику.
    path("favicon.ico", RedirectView.as_view(url=settings.STATIC_URL + "img/logo.svg")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
