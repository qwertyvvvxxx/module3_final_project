from django.test import Client

from apps.accounts.models import User
from apps.orders.models import Order, OrderItem


def test_analytics_requires_staff(client: Client, user: User) -> None:
    client.force_login(user)

    assert client.get("/admin/analytics/").status_code == 302


def test_analytics_page_shows_aggregations(client: Client, staff_user: User, product) -> None:
    client.force_login(staff_user)
    order = Order.objects.create(user=staff_user, shipping_address="Kyiv", status="paid")
    OrderItem.objects.create(order=order, product=product, quantity=2, price=product.price)

    response = client.get("/admin/analytics/")

    assert response.status_code == 200
    assert response.context["summary"]["orders_count"] == 1
    assert float(response.context["summary"]["revenue"]) == 11.98
    assert response.context["top_products"][0]["product__name"] == "Citra Hops"
    assert response.context["by_status"][0]["count"] >= 0


def test_admin_index_links_to_analytics(client: Client, staff_user: User) -> None:
    client.force_login(staff_user)

    response = client.get("/admin/")

    assert response.status_code == 200
    assert b"/admin/analytics/" in response.content
