"""Веб-представления каталога и страницы товара."""

from __future__ import annotations

from typing import Any

from django.db.models import QuerySet
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView, ListView

from orders.cart import Cart
from reviews.forms import ReviewForm
from reviews.models import Review
from reviews.services import user_can_review

from .filters import ProductFilter
from .models import Category, Product

SORT_OPTIONS: dict[str, tuple[str, str]] = {
    "new": ("-created_at", "Сначала новые"),
    "price_asc": ("price", "Цена по возрастанию"),
    "price_desc": ("-price", "Цена по убыванию"),
    "rating": ("-avg_rating", "По рейтингу"),
    "popular": ("-sales_count", "По популярности"),
}


class ProductListView(ListView):
    """Каталог: пагинация, фильтрация по категории/цене, поиск, сортировка."""

    model = Product
    template_name = "products/product_list.html"
    context_object_name = "products"
    paginate_by = 12

    def get_queryset(self) -> QuerySet[Product]:
        base = Product.objects.active().select_related("category").with_stats()
        self.filterset = ProductFilter(self.request.GET, queryset=base)
        qs = self.filterset.qs

        sort_key = self.request.GET.get("sort", "new")
        order_field = SORT_OPTIONS.get(sort_key, SORT_OPTIONS["new"])[0]
        self.active_sort = sort_key if sort_key in SORT_OPTIONS else "new"
        return qs.order_by(order_field, "-id")

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        ctx = super().get_context_data(**kwargs)
        params = self.request.GET.copy()
        params.pop("page", None)
        ctx.update(
            {
                "categories": Category.objects.with_product_counts().order_by("name"),
                "sort_options": SORT_OPTIONS,
                "active_sort": self.active_sort,
                "active_category": self.request.GET.get("category", ""),
                "search_query": self.request.GET.get("search", ""),
                "price_min": self.request.GET.get("price_min", ""),
                "price_max": self.request.GET.get("price_max", ""),
                "querystring": params.urlencode(),
            }
        )
        return ctx


class ProductDetailView(DetailView):
    """Страница товара: описание, рейтинг, отзывы, форма отзыва."""

    model = Product
    template_name = "products/product_detail.html"
    context_object_name = "product"

    def get_queryset(self) -> QuerySet[Product]:
        return Product.objects.active().select_related("category").with_stats()

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        ctx = super().get_context_data(**kwargs)
        product: Product = self.object
        reviews: QuerySet[Review] = product.reviews.select_related("user").order_by("-created_at")
        user = self.request.user
        ctx.update(
            {
                "cart_qty": Cart(self.request).quantity_of(product),
                "reviews": reviews,
                "review_form": ReviewForm() if user.is_authenticated else None,
                "can_review": user_can_review(user, product) if user.is_authenticated else False,
                "already_reviewed": (user.is_authenticated and reviews.filter(user=user).exists()),
                "related_products": (
                    Product.objects.active()
                    .filter(category=product.category)
                    .exclude(pk=product.pk)
                    .with_stats()[:4]
                ),
            }
        )
        return ctx


def get_category_or_404(slug: str) -> Category:
    return get_object_or_404(Category, slug=slug)
