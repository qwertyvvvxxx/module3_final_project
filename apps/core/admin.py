"""Admin extras: the sales analytics page at /admin/analytics/ and the index link."""

from django.contrib.admin.sites import site
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Sum
from django.db.models.functions import TruncDate
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from apps.orders.models import Order, OrderItem

# Show the "Аналітика продажів" button on the admin index page.
site.index_template = "admin/index_with_analytics.html"


@staff_member_required(login_url="admin:login")
def analytics_view(request: HttpRequest) -> HttpResponse:
    """Aggregations for the admin: revenue, top products, orders by status and by day.

    The URL is wired in config/urls.py before the admin include.
    """
    paid = Order.objects.exclude(status=Order.OrderStatus.CANCELLED)
    revenue = paid.aggregate(total=Sum("total_price"))["total"] or 0
    orders_count = paid.count()

    top_products = (
        OrderItem.objects.filter(order__in=paid)
        .values("product__name")
        .annotate(sold_qty=Sum("quantity"))
        .order_by("-sold_qty")[:10]
    )
    by_status = [
        {"label": label, "count": Order.objects.filter(status=value).count()}
        for value, label in Order.OrderStatus.choices
    ]
    by_day = (
        paid.annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(orders=Count("id"), revenue=Sum("total_price"))
        .order_by("-day")[:30]
    )

    context = {
        **site.each_context(request),
        "title": "Аналітика продажів",
        "summary": {
            "revenue": revenue,
            "orders_count": orders_count,
            "average_check": revenue / orders_count if orders_count else 0,
        },
        "top_products": top_products,
        "by_status": by_status,
        "by_day": by_day,
    }
    return render(request, "admin/analytics.html", context)
