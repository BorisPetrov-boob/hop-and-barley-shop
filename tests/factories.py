"""factory_boy-фабрики для тестов."""

from __future__ import annotations

from decimal import Decimal

import factory
from django.contrib.auth import get_user_model

from orders.models import Order, OrderItem
from products.models import Category, Product
from reviews.models import Review

User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        skip_postgeneration_save = True

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    first_name = "Тест"

    @factory.post_generation
    def password(obj, create, extracted, **kwargs):  # noqa: N805
        obj.set_password(extracted or "pass12345")
        if create:
            obj.save()


class StaffFactory(UserFactory):
    is_staff = True


class CategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Category
        django_get_or_create = ("name",)

    name = factory.Sequence(lambda n: f"Категория {n}")


class ProductFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Product

    name = factory.Sequence(lambda n: f"Товар {n}")
    description = "Описание тестового товара для полнотекстового поиска."
    price = Decimal("9.99")
    price_unit = "за 100 г"
    category = factory.SubFactory(CategoryFactory)
    is_active = True
    stock = 50


class OrderFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Order

    user = factory.SubFactory(UserFactory)
    status = Order.Status.PENDING
    total_price = Decimal("0.00")
    shipping_address = "г. Москва, ул. Пивоваров, 1"
    contact_name = "Тест Тестов"
    contact_phone = "+70000000000"
    payment_method = "debit"


class OrderItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = OrderItem

    order = factory.SubFactory(OrderFactory)
    product = factory.SubFactory(ProductFactory)
    quantity = 1
    price = factory.LazyAttribute(lambda o: o.product.price)


class ReviewFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Review

    product = factory.SubFactory(ProductFactory)
    user = factory.SubFactory(UserFactory)
    rating = 5
    comment = "Отличный товар."
