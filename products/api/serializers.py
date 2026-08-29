"""Сериализаторы каталога."""

from __future__ import annotations

from rest_framework import serializers

from products.models import Category, Product, ProductImage


class CategorySerializer(serializers.ModelSerializer[Category]):
    class Meta:
        model = Category
        fields = ("id", "name", "slug", "parent")


class ProductImageSerializer(serializers.ModelSerializer[ProductImage]):
    class Meta:
        model = ProductImage
        fields = ("id", "image", "alt", "sort_order")


class ProductListSerializer(serializers.ModelSerializer[Product]):
    """Компактное представление для списка."""

    category = serializers.SlugRelatedField(slug_field="slug", read_only=True)
    avg_rating = serializers.FloatField(read_only=True)
    review_count = serializers.IntegerField(read_only=True)
    in_stock = serializers.BooleanField(read_only=True)

    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "slug",
            "price",
            "price_unit",
            "category",
            "image",
            "stock",
            "in_stock",
            "avg_rating",
            "review_count",
            "created_at",
        )


class ProductDetailSerializer(ProductListSerializer):
    """Расширенное представление для карточки товара."""

    category = CategorySerializer(read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    sales_count = serializers.IntegerField(read_only=True)

    class Meta(ProductListSerializer.Meta):
        fields = (
            *ProductListSerializer.Meta.fields,
            "description",
            "images",
            "sales_count",
            "updated_at",
        )
