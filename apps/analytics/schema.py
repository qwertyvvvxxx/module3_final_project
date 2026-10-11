"""GraphQL schema for shop analytics (the optional bonus of the spec, section 3.9).

Queries: orders (revenue, count, average check, daily trends), products (top sellers,
stock levels), users (activity, repeat purchases). The whole schema is staff-only.
"""

from datetime import timedelta
from decimal import Decimal
from typing import Any

import graphene
from django.db.models import Count, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone

from apps.accounts.models import User
from apps.catalog.models import Product
from apps.orders.models import Order, OrderItem


def _require_staff(info: Any) -> None:
    user = info.context.user
    if not (user and user.is_authenticated and user.is_staff):
        raise PermissionError("Аналітика доступна лише співробітникам.")


class RevenuePoint(graphene.ObjectType):
    """One day of the revenue trend."""

    day = graphene.Date(required=True)
    orders = graphene.Int(required=True)
    revenue = graphene.Float(required=True)


class OrderStats(graphene.ObjectType):
    revenue = graphene.Float(required=True)
    count = graphene.Int(required=True)
    average_check = graphene.Float(required=True)
    trends = graphene.List(RevenuePoint, days=graphene.Int(default_value=30))

    def resolve_trends(self, info: Any, days: int) -> list[RevenuePoint]:
        _require_staff(info)
        start = timezone.now() - timedelta(days=days)
        rows = (
            Order.objects.filter(created_at__gte=start)
            .exclude(status=Order.OrderStatus.CANCELLED)
            .annotate(day=TruncDate("created_at"))
            .values("day")
            .annotate(orders=Count("id"), revenue=Sum("total_price"))
            .order_by("day")
        )
        return [
            RevenuePoint(day=row["day"], orders=row["orders"], revenue=float(row["revenue"] or 0))
            for row in rows
        ]


class TopProduct(graphene.ObjectType):
    id = graphene.Int(required=True)
    name = graphene.String(required=True)
    sold_qty = graphene.Int(required=True)
    stock = graphene.Int(required=True)


class ProductStats(graphene.ObjectType):
    top_products = graphene.List(TopProduct, limit=graphene.Int(default_value=10))
    out_of_stock_count = graphene.Int(required=True)

    def resolve_top_products(self, info: Any, limit: int) -> list[TopProduct]:
        _require_staff(info)
        paid = Order.objects.exclude(status=Order.OrderStatus.CANCELLED)
        rows = (
            OrderItem.objects.filter(order__in=paid)
            .values("product_id", "product__name", "product__stock")
            .annotate(sold_qty=Sum("quantity"))
            .order_by("-sold_qty")[:limit]
        )
        return [
            TopProduct(
                id=row["product_id"],
                name=row["product__name"],
                sold_qty=row["sold_qty"],
                stock=row["product__stock"],
            )
            for row in rows
        ]


class UserStats(graphene.ObjectType):
    total = graphene.Int(required=True)
    active_last_30_days = graphene.Int(required=True)
    repeat_customers = graphene.Int(required=True)


class Query(graphene.ObjectType):
    """Analytics root query."""

    order_stats = graphene.Field(OrderStats)
    product_stats = graphene.Field(ProductStats)
    user_stats = graphene.Field(UserStats)

    @staticmethod
    def resolve_order_stats(root: Any, info: Any) -> OrderStats:
        _require_staff(info)
        paid = Order.objects.exclude(status=Order.OrderStatus.CANCELLED)
        revenue = paid.aggregate(total=Sum("total_price"))["total"] or Decimal("0")
        count = paid.count()
        return OrderStats(
            revenue=float(revenue),
            count=count,
            average_check=float(revenue / count) if count else 0.0,
        )

    @staticmethod
    def resolve_product_stats(root: Any, info: Any) -> ProductStats:
        _require_staff(info)
        return ProductStats(out_of_stock_count=Product.objects.active().filter(stock=0).count())

    @staticmethod
    def resolve_user_stats(root: Any, info: Any) -> UserStats:
        _require_staff(info)
        since = timezone.now() - timedelta(days=30)
        repeat = (
            User.objects.filter(orders__isnull=False)
            .annotate(n=Count("orders"))
            .filter(n__gte=2)
            .count()
        )
        return UserStats(
            total=User.objects.count(),
            active_last_30_days=User.objects.filter(last_login__gte=since).count(),
            repeat_customers=repeat,
        )


schema = graphene.Schema(query=Query)
