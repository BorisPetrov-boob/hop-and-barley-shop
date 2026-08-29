"""Сериализаторы заказов и корзины."""

from __future__ import annotations

from typing import Any

from rest_framework import serializers

from orders.cart import Cart
from orders.models import Order, OrderItem
from orders.services import EmptyCartError, LineInput, OutOfStockError, create_order
from products.models import Product


class OrderItemSerializer(serializers.ModelSerializer[OrderItem]):
    product_name = serializers.CharField(source="product.name", read_only=True)
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = OrderItem
        fields = ("product", "product_name", "quantity", "price", "subtotal")
        read_only_fields = ("price",)


class OrderSerializer(serializers.ModelSerializer[Order]):
    """Чтение заказа."""

    items = OrderItemSerializer(many=True, read_only=True)
    number = serializers.CharField(read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Order
        fields = (
            "id",
            "number",
            "status",
            "status_display",
            "total_price",
            "shipping_address",
            "contact_name",
            "contact_phone",
            "contact_email",
            "payment_method",
            "paid_at",
            "created_at",
            "items",
        )
        read_only_fields = fields


class OrderLineInputSerializer(serializers.Serializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.active())
    quantity = serializers.IntegerField(min_value=1, max_value=999)


class OrderCreateSerializer(serializers.ModelSerializer[Order]):
    """Создание заказа: из переданных ``items`` либо из корзины-сессии."""

    items = OrderLineInputSerializer(many=True, required=False)

    class Meta:
        model = Order
        fields = (
            "id",
            "shipping_address",
            "contact_name",
            "contact_phone",
            "contact_email",
            "payment_method",
            "items",
        )

    def _lines_from_cart(self) -> list[LineInput]:
        request = self.context["request"]
        cart = Cart(request)
        if cart.is_empty:
            raise serializers.ValidationError("Корзина пуста и список items не передан.")
        return [LineInput(line.product.pk, line.quantity) for line in cart]

    def create(self, validated_data: dict[str, Any]) -> Order:
        raw_items = validated_data.pop("items", None)
        if raw_items:
            lines = [LineInput(i["product"].pk, i["quantity"]) for i in raw_items]
        else:
            lines = self._lines_from_cart()

        request = self.context["request"]
        try:
            order = create_order(
                user=request.user,
                lines=lines,
                shipping_address=validated_data["shipping_address"],
                contact_name=validated_data["contact_name"],
                contact_phone=validated_data["contact_phone"],
                contact_email=validated_data.get("contact_email", ""),
                payment_method=validated_data.get("payment_method", "debit"),
            )
        except EmptyCartError as exc:
            raise serializers.ValidationError("Нельзя создать пустой заказ.") from exc
        except OutOfStockError as exc:
            raise serializers.ValidationError({"items": str(exc)}) from exc

        if not raw_items:
            Cart(request).clear()
        return order

    def to_representation(self, instance: Order) -> dict[str, Any]:
        return OrderSerializer(instance, context=self.context).data


class OrderStatusUpdateSerializer(serializers.ModelSerializer[Order]):
    """Пользователь может только отменить свой заказ (по правилам модели)."""

    class Meta:
        model = Order
        fields = ("id", "status")

    def validate_status(self, value: str) -> str:
        if value != Order.Status.CANCELLED:
            raise serializers.ValidationError(
                "Через API допустима только отмена заказа (status=cancelled)."
            )
        if not self.instance.can_be_cancelled_by(self.context["request"].user):
            raise serializers.ValidationError(
                f"Заказ в статусе «{self.instance.get_status_display()}» отменить нельзя."
            )
        return value


class CartLineSerializer(serializers.Serializer):
    product = serializers.IntegerField(source="product.id")
    name = serializers.CharField(source="product.name")
    price = serializers.DecimalField(source="unit_price", max_digits=10, decimal_places=2)
    quantity = serializers.IntegerField()
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2)
    has_enough_stock = serializers.BooleanField()


class CartSerializer(serializers.Serializer):
    """Ожидает dict ``{"items": [...CartLine], "total": Decimal, "count": int}``."""

    items = CartLineSerializer(many=True)
    total = serializers.DecimalField(max_digits=12, decimal_places=2)
    count = serializers.IntegerField()

    @classmethod
    def from_cart(cls, cart: Cart) -> CartSerializer:
        return cls({"items": list(cart), "total": cart.total, "count": len(cart)})


class CartMutationSerializer(serializers.Serializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.active())
    quantity = serializers.IntegerField(min_value=0, max_value=999, default=1)
