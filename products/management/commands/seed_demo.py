"""Наполнение БД демо-данными (категории, товары, отзывы, заказ).

Идемпотентно: повторный запуск не создаёт дубликаты.

    python manage.py seed_demo
    python manage.py seed_demo --flush   # предварительно очистить домен
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import Any

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand
from django.db import transaction

from orders.models import Order, OrderItem
from products.models import Category, Product
from reviews.models import Review
from users.models import User

CATEGORIES = ["Hops", "Malts", "Yeast", "Adjuncts"]

# name, category, price, unit, description, stock, image-file
PRODUCTS: list[tuple[str, str, str, str, str, int, str]] = [
    (
        "Citra Hops",
        "Hops",
        "5.99",
        "за 100 г",
        "Один из самых узнаваемых сортов хмеля: яркий цитрусовый аромат, "
        "грейпфрут, лайм, маракуйя. Идеален для IPA и Pale Ale.",
        120,
        "citra_hops.jpg",
    ),
    (
        "Maris Otter Pale Malt",
        "Malts",
        "2.50",
        "за 1 фунт",
        "Классический английский солод для традиционных элей. "
        "Насыщенный бисквитный вкус и надёжная переработка.",
        300,
        "maris_otter_malt.jpg",
    ),
    (
        "SafAle US-05 Dry Ale Yeast",
        "Yeast",
        "3.25",
        "11.5 г",
        "Чистые дрожжи для американских элей. Нейтральный профиль, "
        "хорошая флокуляция, широкий диапазон температур.",
        200,
        "safale_us05_yeast.jpg",
    ),
    (
        "Cascade Hops",
        "Hops",
        "7.49",
        "за 100 г",
        "Американский хмель с цветочно-цитрусовым характером. Отлично работает в сухом охмелении.",
        90,
        "cascade_hops.jpg",
    ),
    (
        "Caramel Malt 60L",
        "Malts",
        "3.00",
        "за 1 фунт",
        "Карамельный солод для тела и пеностойкости в тёмных сортах. Ноты изюма и карамели.",
        150,
        "caramel_malt.jpg",
    ),
    (
        "Saaz Hops",
        "Hops",
        "4.75",
        "за 100 г",
        "Благородный чешский хмель, незаменим для лагеров и пилзнеров. "
        "Мягкая горечь, пряный аромат.",
        80,
        "saaz_hops.jpg",
    ),
    (
        "Pilsner Malt",
        "Malts",
        "2.20",
        "за 1 фунт",
        "Базовый солод для лагеров и пилзнеров. Светлый цвет, чистый зерновой вкус.",
        400,
        "pilsner_malt.jpg",
    ),
    (
        "Imperial Organic Yeast A07",
        "Yeast",
        "8.99",
        "флакон",
        "Жидкие органические дрожжи для американских элей с цитрусовыми нотами.",
        40,
        "imperial_yeast.jpg",
    ),
    (
        "Centennial Hops",
        "Hops",
        "6.20",
        "за 100 г",
        "Часто называют «супер-каскадом»: цитрус и хвоя, универсальный сорт.",
        75,
        "centennial_hops.jpg",
    ),
    (
        "Mosaic Hops",
        "Hops",
        "9.50",
        "за 100 г",
        "Тропические фрукты, черника, травы. Премиальный сорт для IPA и Pale Ale.",
        60,
        "mosaic_hops.jpg",
    ),
    (
        "West Coast IPA — All-Grain Kit",
        "Adjuncts",
        "60.00",
        "набор",
        "Полный зерновой набор для варки классического West Coast IPA "
        "на 20 литров: солод, хмель, дрожжи, рецепт.",
        25,
        "ipa_kit.jpg",
    ),
    (
        "Unmalted Wheat",
        "Adjuncts",
        "1.80",
        "за 1 фунт",
        "Несоложёная пшеница для бельгийского витбира: мутность и мягкое тело.",
        220,
        "unmalted_wheat.jpg",
    ),
]

REVIEWS: list[tuple[str, int, str]] = [
    ("Citra Hops", 5, "Взрывной цитрусовый аромат, использовал в NEIPA — бомба."),
    ("Citra Hops", 4, "Отличный хмель, но дозировку лучше не превышать."),
    ("Pilsner Malt", 5, "Чистый вкус, стабильный результат от партии к партии."),
    ("SafAle US-05 Dry Ale Yeast", 5, "Прощает ошибки новичка, всегда стабильно."),
    ("West Coast IPA — All-Grain Kit", 4, "Хороший набор для первого all-grain, рецепт понятный."),
]

TEMPLATE_IMG_DIR = settings.BASE_DIR / "_template" / "myshop" / "static" / "img" / "products"
STATIC_IMG_DIR = settings.BASE_DIR / "static" / "img" / "products"


class Command(BaseCommand):
    help = "Заполнить базу демонстрационными данными."

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--flush", action="store_true", help="Очистить домен перед заполнением."
        )

    @transaction.atomic
    def handle(self, *args: Any, **options: Any) -> None:
        if options["flush"]:
            self.stdout.write("Очистка домена…")
            Review.objects.all().delete()
            OrderItem.objects.all().delete()
            Order.objects.all().delete()
            Product.objects.all().delete()
            Category.objects.all().delete()

        cats: dict[str, Category] = {}
        for name in CATEGORIES:
            cats[name], _ = Category.objects.get_or_create(name=name)
        self.stdout.write(self.style.SUCCESS(f"Категорий: {len(cats)}"))

        products: dict[str, Product] = {}
        for name, cat, price, unit, desc, stock, img in PRODUCTS:
            product, created = Product.objects.get_or_create(
                name=name,
                defaults={
                    "category": cats[cat],
                    "price": Decimal(price),
                    "price_unit": unit,
                    "description": desc,
                    "stock": stock,
                    "is_active": True,
                },
            )
            if created:
                self._attach_image(product, img)
            products[name] = product
        self.stdout.write(self.style.SUCCESS(f"Товаров: {len(products)}"))

        # Демо-пользователь + доставленный заказ (нужен для проверки «отзыв после покупки»).
        buyer, created = User.objects.get_or_create(
            email="buyer@example.com",
            defaults={"first_name": "Иван", "phone": "+7 900 000-00-00"},
        )
        if created:
            buyer.set_password("buyerpass123")
            buyer.save()

        order, order_created = Order.objects.get_or_create(
            user=buyer,
            status=Order.Status.DELIVERED,
            defaults={
                "total_price": Decimal("0.00"),
                "shipping_address": "г. Москва, ул. Пивоваров, д. 1",
                "contact_name": "Иван",
                "contact_phone": "+7 900 000-00-00",
                "payment_method": "cod",
            },
        )
        if order_created:
            total = Decimal("0.00")
            for pname in (
                "Citra Hops",
                "Pilsner Malt",
                "SafAle US-05 Dry Ale Yeast",
                "West Coast IPA — All-Grain Kit",
            ):
                p = products[pname]
                item = OrderItem.objects.create(order=order, product=p, quantity=2, price=p.price)
                total += item.subtotal
            order.total_price = total
            order.save(update_fields=["total_price"])

        for pname, rating, comment in REVIEWS:
            Review.objects.get_or_create(
                product=products[pname],
                user=buyer,
                defaults={"rating": rating, "comment": comment},
            )
        self.stdout.write(self.style.SUCCESS("Демо-пользователь buyer@example.com / buyerpass123"))
        self.stdout.write(self.style.SUCCESS("Готово."))

    def _attach_image(self, product: Product, filename: str) -> None:
        for base in (TEMPLATE_IMG_DIR, STATIC_IMG_DIR):
            path: Path = base / filename
            if path.exists():
                with path.open("rb") as fh:
                    product.image.save(filename, File(fh), save=True)
                return
