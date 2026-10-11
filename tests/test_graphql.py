import json

import pytest
from django.test import Client

from apps.accounts.models import User
from apps.catalog.models import Category, Product
from apps.orders.models import Order, OrderItem

ORDER_STATS_QUERY = """
query {
  orderStats {
    revenue
    count
    averageCheck
    trends(days: 7) { day orders revenue }
  }
}
"""

PRODUCT_STATS_QUERY = """
query {
  productStats {
    outOfStockCount
    topProducts(limit: 5) { name soldQty stock }
  }
}
"""

USER_STATS_QUERY = """
query {
  userStats {
    total
    activeLast30Days
    repeatCustomers
  }
}
"""


def gql(client: Client, query: str) -> dict:
    response = client.post(
        "/graphql/", data=json.dumps({"query": query}), content_type="application/json"
    )
    return response.json()


def test_graphql_requires_staff(client: Client, user: User) -> None:
    client.force_login(user)

    body = gql(client, ORDER_STATS_QUERY)

    assert "errors" in body
    assert "співробітників" in body["errors"][0]["message"]


def test_anonymous_cannot_query_graphql(client: Client) -> None:
    body = gql(client, ORDER_STATS_QUERY)

    assert "errors" in body


def test_order_stats(client: Client, staff_user: User, product: Product) -> None:
    client.force_login(staff_user)
    order = Order.objects.create(user=staff_user, shipping_address="Kyiv", status="paid")
    OrderItem.objects.create(order=order, product=product, quantity=2, price=product.price)

    body = gql(client, ORDER_STATS_QUERY)

    stats = body["data"]["orderStats"]
    assert stats["count"] == 1
    assert stats["revenue"] == pytest.approx(11.98)
    assert stats["averageCheck"] == pytest.approx(11.98)


def test_product_stats(client: Client, staff_user: User, category: Category) -> None:
    client.force_login(staff_user)
    product = Product.objects.create(
        category=category, name="Saaz Hops", slug="saaz-hops", price=3, stock=0
    )
    order = Order.objects.create(user=staff_user, shipping_address="Kyiv", status="paid")
    OrderItem.objects.create(order=order, product=product, quantity=4, price=product.price)

    body = gql(client, PRODUCT_STATS_QUERY)

    stats = body["data"]["productStats"]
    assert stats["outOfStockCount"] == 1  # Saaz Hops has stock=0
    assert stats["topProducts"][0]["name"] == "Saaz Hops"
    assert stats["topProducts"][0]["soldQty"] == 4


def test_user_stats(client: Client, staff_user: User, user: User) -> None:
    client.force_login(staff_user)
    for _ in range(2):
        Order.objects.create(user=user, shipping_address="Kyiv", status="delivered")

    body = gql(client, USER_STATS_QUERY)

    stats = body["data"]["userStats"]
    assert stats["total"] == 2
    assert stats["repeatCustomers"] == 1
