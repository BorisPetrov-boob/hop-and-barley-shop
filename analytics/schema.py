"""GraphQL-схема аналитики (бонус).

Единый эндпоинт ``/graphql/``. Все запросы требуют прав персонала
(``is_staff``): аутентификация — сессия Django или JWT (Bearer),
см. :mod:`analytics.views`.

Пример запроса::

    query {
      orderStats { revenue ordersCount averageCheck }
      popularProducts(limit: 5) { name salesCount revenue }
      revenueTrend(days: 14) { date revenue orders }
      lowStockProducts(threshold: 20) { name stock }
      userActivity { totalUsers buyers repeatBuyers repeatRate }
    }
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from typing import Any

import graphene
from django.db.models import Count, DecimalField, ExpressionWrapper, F, Q, Sum
from django.db.models.functions import Coalesce, TruncDate
from django.utils import timezone

from orders.models import Order, OrderItem
from products.models import Product
from users.models import User

SOLD_STATUSES = ("paid", "shipped", "delivered")

_REVENUE = ExpressionWrapper(
    F("quantity") * F("price"), output_field=DecimalField(max_digits=14, decimal_places=2)
)


def _require_staff(info: graphene.ResolveInfo) -> None:
    user = getattr(info.context, "user", None)
    if user is None or not user.is_authenticated or not user.is_staff:
        raise PermissionError("Доступ к аналитике только для персонала (is_staff).")


def _sold_orders(date_from: date | None, date_to: date | None):  # noqa: ANN202
    qs = Order.objects.filter(status__in=SOLD_STATUSES)
    if date_from:
        qs = qs.filter(created_at__date__gte=date_from)
    if date_to:
        qs = qs.filter(created_at__date__lte=date_to)
    return qs


class OrderStatsType(graphene.ObjectType):
    revenue = graphene.Float()
    orders_count = graphene.Int()
    average_check = graphene.Float()
    items_sold = graphene.Int()


class TrendPointType(graphene.ObjectType):
    date = graphene.Date()
    revenue = graphene.Float()
    orders = graphene.Int()


class PopularProductType(graphene.ObjectType):
    id = graphene.ID()
    name = graphene.String()
    sales_count = graphene.Int()
    revenue = graphene.Float()


class LowStockProductType(graphene.ObjectType):
    id = graphene.ID()
    name = graphene.String()
    stock = graphene.Int()


class UserActivityType(graphene.ObjectType):
    total_users = graphene.Int()
    buyers = graphene.Int()
    repeat_buyers = graphene.Int()
    repeat_rate = graphene.Float()


class Query(graphene.ObjectType):
    """Корневой аналитический запрос."""

    order_stats = graphene.Field(
        OrderStatsType,
        date_from=graphene.Date(),
        date_to=graphene.Date(),
        description="Выручка, количество заказов и средний чек за период.",
    )
    revenue_trend = graphene.List(
        TrendPointType,
        days=graphene.Int(default_value=30),
        description="Динамика выручки и числа заказов по дням.",
    )
    popular_products = graphene.List(
        PopularProductType,
        limit=graphene.Int(default_value=10),
        description="Топ товаров по количеству проданных единиц.",
    )
    low_stock_products = graphene.List(
        LowStockProductType,
        threshold=graphene.Int(default_value=10),
        description="Активные товары с остатком не выше порога.",
    )
    user_activity = graphene.Field(
        UserActivityType, description="Активность пользователей и доля повторных покупателей."
    )

    @staticmethod
    def resolve_order_stats(
        root: Any,
        info: graphene.ResolveInfo,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> OrderStatsType:
        _require_staff(info)
        orders = _sold_orders(date_from, date_to)
        agg = orders.aggregate(
            revenue=Coalesce(Sum("total_price"), Decimal("0")),
            orders_count=Count("id"),
        )
        items = OrderItem.objects.filter(order__in=orders).aggregate(
            n=Coalesce(Sum("quantity"), 0)
        )["n"]
        count = agg["orders_count"] or 0
        revenue = float(agg["revenue"] or 0)
        return OrderStatsType(
            revenue=revenue,
            orders_count=count,
            average_check=round(revenue / count, 2) if count else 0.0,
            items_sold=items,
        )

    @staticmethod
    def resolve_revenue_trend(
        root: Any, info: graphene.ResolveInfo, days: int = 30
    ) -> list[TrendPointType]:
        _require_staff(info)
        since = timezone.now().date() - timedelta(days=max(days, 1) - 1)
        rows = (
            Order.objects.filter(status__in=SOLD_STATUSES, created_at__date__gte=since)
            .annotate(day=TruncDate("created_at"))
            .values("day")
            .annotate(revenue=Sum("total_price"), orders=Count("id"))
            .order_by("day")
        )
        return [
            TrendPointType(date=r["day"], revenue=float(r["revenue"] or 0), orders=r["orders"])
            for r in rows
        ]

    @staticmethod
    def resolve_popular_products(
        root: Any, info: graphene.ResolveInfo, limit: int = 10
    ) -> list[PopularProductType]:
        _require_staff(info)
        rows = (
            OrderItem.objects.filter(order__status__in=SOLD_STATUSES)
            .values("product_id", "product__name")
            .annotate(sales_count=Sum("quantity"), revenue=Sum(_REVENUE))
            .order_by("-sales_count")[: max(limit, 1)]
        )
        return [
            PopularProductType(
                id=r["product_id"],
                name=r["product__name"],
                sales_count=r["sales_count"] or 0,
                revenue=float(r["revenue"] or 0),
            )
            for r in rows
        ]

    @staticmethod
    def resolve_low_stock_products(
        root: Any, info: graphene.ResolveInfo, threshold: int = 10
    ) -> list[LowStockProductType]:
        _require_staff(info)
        rows = Product.objects.active().filter(stock__lte=threshold).order_by("stock")
        return [LowStockProductType(id=p.id, name=p.name, stock=p.stock) for p in rows]

    @staticmethod
    def resolve_user_activity(root: Any, info: graphene.ResolveInfo) -> UserActivityType:
        _require_staff(info)
        total = User.objects.count()
        buyer_qs = User.objects.filter(orders__status__in=SOLD_STATUSES).annotate(
            n=Count("orders", filter=Q(orders__status__in=SOLD_STATUSES), distinct=True)
        )
        buyers = buyer_qs.count()
        repeat = buyer_qs.filter(n__gte=2).count()
        return UserActivityType(
            total_users=total,
            buyers=buyers,
            repeat_buyers=repeat,
            repeat_rate=round(repeat / buyers, 3) if buyers else 0.0,
        )


schema = graphene.Schema(query=Query)
