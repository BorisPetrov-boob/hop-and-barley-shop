"""API заказов и корзины."""

from __future__ import annotations

from django.db.models import QuerySet
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from orders.cart import Cart
from orders.models import Order
from orders.services import cancel_order

from .serializers import (
    CartMutationSerializer,
    CartSerializer,
    OrderCreateSerializer,
    OrderSerializer,
    OrderStatusUpdateSerializer,
)


@extend_schema_view(
    list=extend_schema(summary="Мои заказы"),
    retrieve=extend_schema(summary="Заказ по id (только свой)"),
    create=extend_schema(summary="Создать заказ (из корзины или переданных items)"),
    partial_update=extend_schema(summary="Отмена заказа (status=cancelled)"),
    destroy=extend_schema(summary="Отменить заказ (мягкая отмена, остатки возвращаются)"),
)
class OrderViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet[Order],
):
    """``/api/orders/`` — пользователь видит и меняет только свои заказы."""

    permission_classes = (permissions.IsAuthenticated,)
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self) -> QuerySet[Order]:
        return (
            Order.objects.filter(user=self.request.user)
            .prefetch_related("items__product")
            .order_by("-created_at")
        )

    def get_serializer_class(self):  # noqa: ANN201
        if self.action == "create":
            return OrderCreateSerializer
        if self.action in {"update", "partial_update"}:
            return OrderStatusUpdateSerializer
        return OrderSerializer

    def perform_update(self, serializer: OrderStatusUpdateSerializer) -> None:
        # Валидатор уже проверил правила отмены — возвращаем остатки на склад.
        cancel_order(serializer.instance)

    def destroy(self, request: Request, *args: object, **kwargs: object) -> Response:
        order = self.get_object()
        if not order.can_be_cancelled_by(request.user):
            return Response(
                {"detail": f"Заказ «{order.get_status_display()}» отменить нельзя."},
                status=status.HTTP_409_CONFLICT,
            )
        cancel_order(order)
        return Response(status=status.HTTP_204_NO_CONTENT)


class CartAPIView(APIView):
    """``/api/cart/`` — управление корзиной (сессия; для браузера и session-auth).

    * ``GET``    — содержимое корзины
    * ``POST``   — добавить товар (quantity прибавляется)
    * ``PATCH``  — задать точное количество (quantity=0 удаляет позицию)
    * ``DELETE`` — очистить корзину (или ``?product=<id>`` — убрать одну позицию)
    """

    permission_classes = (permissions.AllowAny,)

    @extend_schema(responses=CartSerializer, summary="Содержимое корзины")
    def get(self, request: Request) -> Response:
        return Response(CartSerializer.from_cart(Cart(request)).data)

    @extend_schema(
        request=CartMutationSerializer, responses=CartSerializer, summary="Добавить в корзину"
    )
    def post(self, request: Request) -> Response:
        return self._mutate(request, replace=False)

    @extend_schema(
        request=CartMutationSerializer, responses=CartSerializer, summary="Задать количество"
    )
    def patch(self, request: Request) -> Response:
        return self._mutate(request, replace=True)

    @extend_schema(
        responses={200: CartSerializer, 204: OpenApiResponse(description="Корзина очищена")},
        summary="Очистить корзину / удалить позицию",
    )
    def delete(self, request: Request) -> Response:
        cart = Cart(request)
        product_id = request.query_params.get("product")
        if product_id:
            from products.models import Product

            product = Product.objects.filter(pk=product_id).first()
            if product:
                cart.remove(product)
            return Response(CartSerializer.from_cart(cart).data)
        cart.clear()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def _mutate(self, request: Request, *, replace: bool) -> Response:
        serializer = CartMutationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cart = Cart(request)
        cart.add(
            serializer.validated_data["product"],
            quantity=serializer.validated_data["quantity"],
            replace=replace,
        )
        return Response(CartSerializer.from_cart(cart).data, status=status.HTTP_200_OK)
