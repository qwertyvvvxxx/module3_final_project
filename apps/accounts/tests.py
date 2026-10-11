import pytest
from django.test import Client
from django.urls import reverse

from apps.accounts.models import User
from apps.orders.models import Order


@pytest.mark.parametrize("login", ["alice@example.com", "ALICE@example.com", "alice"])
def test_login_by_email_or_username(client: Client, user: User, login: str) -> None:
    response = client.post(
        reverse("accounts:login"), {"username": login, "password": "secret-pass-123"}
    )

    assert response.status_code == 302
    assert client.session["_auth_user_id"] == str(user.pk)


def test_login_with_wrong_password(client: Client, user: User) -> None:
    response = client.post(reverse("accounts:login"), {"username": "alice", "password": "nope"})

    assert response.status_code == 200
    assert "_auth_user_id" not in client.session


def test_register_logs_in(client: Client, db) -> None:
    client.post(
        reverse("accounts:register"), {"email": "New@Example.com", "password": "Very-secret-777"}
    )

    assert User.objects.get().email == "new@example.com"
    assert "_auth_user_id" in client.session


def test_account_page_saves_profile(client: Client, user: User) -> None:
    client.force_login(user)

    client.post(
        reverse("accounts:profile"),
        {
            "last_name": "Шевченко",
            "first_name": "Аліса",
            "middle_name": "Петрівна",
            "email": "alice@example.com",
            "phone": "+380991112233",
        },
    )

    user.refresh_from_db()
    assert user.get_full_name() == "Шевченко Аліса Петрівна"
    assert user.phone == "+380991112233"


PROFILE = {
    "last_name": "Шевченко",
    "first_name": "Аліса",
    "email": "alice@example.com",
    "phone": "0991112233",
}
DELIVERY = {
    "city_name": "Київ (Київська обл.)",
    "city_ref": "city-kyiv",
    "delivery_type": "branch",
    "warehouse_name": "Відділення №1",
    "warehouse_ref": "wh-1",
}


def test_account_saves_nova_poshta_delivery(client: Client, user: User, nova_poshta) -> None:
    client.force_login(user)

    client.post(reverse("accounts:profile"), PROFILE | DELIVERY)

    user.refresh_from_db()
    assert (user.np_city_ref, user.np_warehouse_ref) == ("city-kyiv", "wh-1")
    # the branch name is taken from the API, not from the browser
    assert user.np_warehouse_name == "Відділення №1: вул. Пирогівський шлях, 135"
    assert user.phone == "+380991112233"


def test_delivery_is_optional_in_account(client: Client, user: User) -> None:
    client.force_login(user)

    response = client.post(reverse("accounts:profile"), PROFILE)

    assert response.status_code == 302
    user.refresh_from_db()
    assert user.np_warehouse_ref == ""


def test_city_without_branch_is_an_error(client: Client, user: User, nova_poshta) -> None:
    client.force_login(user)

    response = client.post(
        reverse("accounts:profile"),
        PROFILE | DELIVERY | {"warehouse_ref": "", "warehouse_name": ""},
    )

    assert "warehouse_name" in response.context["form"].errors


# --- Order history filters -----------------------------------------------------------


def make_order(user: User, status: str) -> Order:
    return Order.objects.create(user=user, shipping_address="Kyiv", status=status)


def test_order_history_filters_by_status(client: Client, user: User) -> None:
    client.force_login(user)
    make_order(user, "paid")
    pending = make_order(user, "pending")

    response = client.get(reverse("accounts:profile"), {"status": "pending"})

    assert list(response.context["orders_page"]) == [pending]


def test_order_history_ignores_unknown_status(client: Client, user: User) -> None:
    client.force_login(user)
    order = make_order(user, "paid")

    response = client.get(reverse("accounts:profile"), {"status": "hack"})

    assert list(response.context["orders_page"]) == [order]
    assert response.context["selected_status"] == ""


# --- Password change -----------------------------------------------------------------


def test_password_change(client: Client, user: User) -> None:
    client.force_login(user)

    response = client.post(
        reverse("accounts:password_change"),
        {
            "old_password": "secret-pass-123",
            "new_password1": "New-strong-pass-456",
            "new_password2": "New-strong-pass-456",
        },
    )

    assert response.status_code == 302
    user.refresh_from_db()
    assert user.check_password("New-strong-pass-456")


def test_password_change_requires_old_password(client: Client, user: User) -> None:
    client.force_login(user)

    response = client.post(
        reverse("accounts:password_change"),
        {
            "old_password": "wrong",
            "new_password1": "New-strong-pass-456",
            "new_password2": "New-strong-pass-456",
        },
    )

    assert response.status_code == 200
    assert "old_password" in response.context["form"].errors
    user.refresh_from_db()
    assert user.check_password("secret-pass-123")
