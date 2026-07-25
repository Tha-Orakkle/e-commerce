from django.urls import reverse
from freezegun import freeze_time
from rest_framework import status

import pytest
import uuid

from order.models import OrderGroupStatus, OrderStatus


def test_cancel_order_group_cash_payment(
    client,
    customer,
    populated_order_group_factory
):
    """
    Test cancelling order group with cash payment method succeeds.
    """
    group = populated_order_group_factory(
        user=customer,
        orders_per_group=3
    )
    url = reverse("cancel-order-group", args=[group.id])
    client.force_authenticate(user=customer)

    assert group.status != OrderGroupStatus.CANCELLED
    assert all(order.status != OrderStatus.CANCELLED
               for order in group.orders.all())

    res = client.post(url)

    assert res.status_code == status.HTTP_200_OK
    assert res.data["status"] == "success"
    expected_msg = ("Order cancelled. A refund will be processed "
                    "shortly if payment was already made.")
    assert res.data["message"] == expected_msg

    group.refresh_from_db()
    assert group.status == OrderGroupStatus.CANCELLED
    assert all(order.status == OrderStatus.CANCELLED
               for order in group.orders.all())


def test_cancel_order_group_digital_payment_made(
    client,
    customer,
    order_group_factory,
    order_factory,
    payment_factory
):
    """
    Test cancelling order group with digital payment method succeeds.
    Testing with payment already made and a refund requested.
    """
    group = order_group_factory(
        user=customer,
        payment_method="DIGITAL",
        total_amount=10000
    )
    payment = payment_factory(
        user=customer,
        group=group,
        verified=True
    )
    for _ in range(3):
        order_factory(group=group)

    url = reverse("cancel-order-group", args=[group.id])
    client.force_authenticate(user=customer)

    assert group.status != OrderGroupStatus.CANCELLED
    assert all(order.status != OrderStatus.CANCELLED
               for order in group.orders.all())
    assert payment.refund_requested is False

    res = client.post(url)
    assert res.status_code == status.HTTP_200_OK
    assert res.data["status"] == "success"
    expected_msg = ("Order cancelled. A refund will be processed "
                    "shortly if payment was already made.")
    assert res.data["message"] == expected_msg
    group.refresh_from_db()
    assert group.status == OrderGroupStatus.CANCELLED
    assert all(order.status == OrderStatus.CANCELLED
               for order in group.orders.all())
    payment.refresh_from_db()
    assert payment.refund_requested is True


def test_cancel_order_group_digital_payment_not_made(
    client,
    customer,
    order_group_factory,
    order_factory,
    payment_factory
):
    """
    Test cancelling order group with digital payment method succeeds.
    Testing with payment not paid, refund is not requested.
    """
    group = order_group_factory(
        user=customer,
        payment_method="DIGITAL",
        total_amount=10000
    )
    payment = payment_factory(
        user=customer,
        group=group,
        verified=False
    )
    for _ in range(3):
        order_factory(group=group)

    url = reverse("cancel-order-group", args=[group.id])
    client.force_authenticate(user=customer)

    assert group.status != OrderGroupStatus.CANCELLED
    assert all(order.status != OrderStatus.CANCELLED
               for order in group.orders.all())
    assert payment.refund_requested is False

    res = client.post(url)
    assert res.status_code == status.HTTP_200_OK
    assert res.data["status"] == "success"

    group.refresh_from_db()
    assert group.status == OrderGroupStatus.CANCELLED
    assert all(order.status == OrderStatus.CANCELLED
               for order in group.orders.all())
    payment.refresh_from_db()
    assert payment.refund_requested is False


@pytest.mark.parametrize(
    "group_status",
    ["PROCESSING", "SHIPPED", "CPOMPLETED", "CANCELLED"],
    ids=["PROCESSING", "SHIPPED", "CPOMPLETED", "CANCELLED"]
)
def test_cancel_non_pending_order_group(
    client,
    customer,
    order_group_factory,
    order_factory,
    group_status
):
    """
    Test cancelling non-pending order groups fails.
    """
    group = order_group_factory(
        user=customer,
        status=group_status
    )
    for _ in range(3):
        order_factory(group=group)

    url = reverse("cancel-order-group", args=[group.id])
    client.force_authenticate(user=customer)

    res = client.post(url)
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data["status"] == "error"
    assert res.data["code"] == "order_already_processed"
    expected_msg = "Only pending order groups can be cancelled."
    assert res.data["message"] == expected_msg
    if group_status != OrderGroupStatus.CANCELLED:
        assert group.status != OrderGroupStatus.CANCELLED
        assert all(order.status != OrderStatus.CANCELLED
                   for order in group.orders.all())


def test_cancel_order_group_after_4_hours(
    client,
    customer,
    populated_order_group_factory,
):
    """
    Test cancel order group after 4 hours fails.
    """
    with freeze_time("2026-07-25 01:00:00"):
        group = populated_order_group_factory(
            user=customer,
            orders_per_group=3
        )

    url = reverse("cancel-order-group", args=[group.id])
    client.force_authenticate(user=customer)

    with freeze_time("2026-07-25 05:00:01"):
        res = client.post(url)

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data["status"] == "error"
    assert res.data["code"] == "cancellation_time_expired"
    expected_msg = "Order cannot be cancelled after 4 hours of creation."
    assert res.data["message"] == expected_msg
    assert group.status != OrderGroupStatus.CANCELLED
    assert all(order.status != OrderStatus.CANCELLED
               for order in group.orders.all())


def test_cancel_order_group_rolls_back_on_error(
    client,
    mocker,
    customer,
    populated_order_group_factory
):
    group = populated_order_group_factory(
        user=customer,
        orders_per_group=3
    )
    mocker.patch(
        "order.api.v1.routes.cancel_order.Order.objects.bulk_update",
        side_effect=Exception("DB Failure")
    )

    url = reverse("cancel-order-group", args=[group.id])
    client.force_authenticate(user=customer)

    with pytest.raises(Exception):
        client.post(url)

    group.refresh_from_db()
    assert group.status != OrderGroupStatus.CANCELLED
    assert all(order.status != OrderStatus.CANCELLED
               for order in group.orders.all())


@pytest.mark.django_db(transaction=True)
def test_cancel_order_group_calls_restock_inventory_task(
    client,
    mocker,
    customer,
    populated_order_group_factory,
):
    """
    Test that cancelling order group calls the restock inventory
    task.
    """
    group = populated_order_group_factory(
        user=customer,
        orders_per_group=3
    )
    mock_restock = mocker.patch(
        "order.api.v1.routes.cancel_order.restock_inventory_with_cancelled_order.delay"
    )

    url = reverse("cancel-order-group", args=[group.id])
    client.force_authenticate(user=customer)
    res = client.post(url)

    assert res.status_code == status.HTTP_200_OK
    mock_restock.assert_called_once()


def test_cancel_order_group_with_invalid_uuid(client, customer):
    """
    Test cancelling order with invalid group uuid fails.
    """
    url = reverse("cancel-order-group", args=["invalid_id"])
    client.force_authenticate(user=customer)
    res = client.post(url)

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data["status"] == "error"
    assert res.data["code"] == "invalid_uuid"
    assert res.data["message"] == "Invalid order group id."


def test_cancel_order_group_with_non_existent_id(client, customer):
    """
    Test cancelling order with non-existent group id fails.
    """
    url = reverse("cancel-order-group", args=[uuid.uuid4()])
    client.force_authenticate(user=customer)
    res = client.post(url)

    assert res.status_code == status.HTTP_404_NOT_FOUND
    assert res.data["status"] == "error"
    assert res.data["code"] == "not_found"
    expected_msg = "No order group matching the given ID found."
    assert res.data["message"] == expected_msg


@pytest.mark.parametrize(
    "user_type",
    ["shopowner", "shop_staff"],
    ids=["shopowner", "shop_staff"]
)
def test_cancel_order_group_by_non_customer(
    client,
    all_users,
    user_type
):
    """
    Test that cancel order group by shop owner/staff fails.
    """
    user = all_users[user_type]
    url = reverse("cancel-order-group", args=[uuid.uuid4()])
    client.force_authenticate(user=user)
    res = client.post(url)

    assert res.status_code == status.HTTP_403_FORBIDDEN
    assert res.data["status"] == "error"
    assert res.data["code"] == "forbidden"
    expected_msg = "You do not have permission to perform this action."
    assert res.data["message"] == expected_msg


def test_cancel_order_group_by_superuser(
    client,
    customer,
    super_user,
    populated_order_group_factory
):
    """
    Test cancelling order group by super user succeeds.
    """
    group = populated_order_group_factory(
        user=customer,
        orders_per_group=3
    )
    url = reverse("cancel-order-group", args=[group.id])
    client.force_authenticate(user=super_user)
    res = client.post(url)

    assert res.status_code == status.HTTP_200_OK
    assert res.data["status"] == "success"
    expected_msg = ("Order cancelled. A refund will be processed "
                    "shortly if payment was already made.")
    assert res.data["message"] == expected_msg

    group.refresh_from_db()
    group.status == OrderGroupStatus.CANCELLED
    assert all(order.status == OrderStatus.CANCELLED
               for order in group.orders.all())


def test_cancel_order_group_by_unauthenticated_user(client):
    """
    Test cancelling order group by unauthenticated user fails.
    Test without access token and invaid token.
    """
    url = reverse("cancel-order-group", args=[uuid.uuid4()])
    res = client.post(url)

    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.data["status"] == "error"
    assert res.data["code"] == "unauthorized"
    expected_msg = "Authentication credentials were not provided."
    assert res.data["message"] == expected_msg

    client.cookies["access_token"] = "invalid_token"
    res = client.post(url)

    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.data["status"] == "error"
    assert res.data["code"] == "unauthorized"
    assert res.data["message"] == "Token is invalid or expired"
