from django.urls import reverse
from rest_framework import status

import pytest


PAYLOAD = {
    "payment_status": False,
    "status": "PROCESSING",
    "delivery_date": "2026-08-05"
}

# test expected fields and response


def test_update_shop_cash_order_status_from_pending_to_processing_pickup(
    client,
    shopowner,
    populated_order_group_factory
):
    """
    Test updating a shop order status from pending to process.
    Order fulfillment method is PICKUP and payment method is CASH.
    """

    # by default this is a cash pick up transaction
    group = populated_order_group_factory(shop=shopowner.owned_shop)
    order = group.orders.first()

    url = reverse("update-shop-order-status", args=[order.id])
    client.force_authenticate(user=shopowner)
    res = client.post(url, data=PAYLOAD, format="json")

    assert res.status_code == status.HTTP_200_OK
    data = res.data["data"]
    assert data["status"] == "PROCESSING"
    assert data["is_paid"] is False
    assert data["paid_at"] is None
    assert data["processing_at"] is not None
    assert data["shipped_at"] is None
    assert data["completed_at"] is None
    assert data["cancelled_at"] is None
    assert data["is_delivered"] is False
    assert data["is_picked_up"] is False
    assert data["delivery_date"] is None

    payload = {
        **PAYLOAD,
        "payment_status": True
    }
    group = populated_order_group_factory(shop=shopowner.owned_shop)
    order = group.orders.first()

    url = reverse("update-shop-order-status", args=[order.id])
    res = client.post(url, data=payload, format="json")
    assert res.status_code == status.HTTP_200_OK
    data = res.data["data"]
    assert data["status"] == "PROCESSING"
    assert data["is_paid"] is True
    assert data["paid_at"] is not None


@pytest.mark.parametrize(
    "new_status",
    ["SHIPPED", "COMPLETED"],
    ids=["SHIPPED", "COMPLETED"]
)
def test_update_shop_cash_order_status_from_pending_pickup_to_other_statuses(
    client,
    shopowner,
    populated_order_group_factory,
    new_status
):
    """
    Test updating a shop order status from pending to shipped and completed.
    Order fulfillment method is PICKUP and payment method is CASH.
    Transaction fails since only processing orders can be shipped or
    completed. Also, pick up orders cannot be shipped.
    """

    # by default this is a cash pick up transaction
    group = populated_order_group_factory(shop=shopowner.owned_shop)
    order = group.orders.first()
    payload = {
        **PAYLOAD,
        "status": new_status
    }

    url = reverse("update-shop-order-status", args=[order.id])
    client.force_authenticate(user=shopowner)
    res = client.post(url, data=payload, format="json")

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data["status"] == "error"
    assert res.data["code"] == "invalid_status_transition"
    expected_msg = f"Invalid transition from PENDING to {new_status}."
    assert res.data["message"] == expected_msg


def test_update_shop_cash_order_status_from_processing_to_completed_pickup(
    client,
    shopowner,
    order_factory,
    order_group_factory,
):
    """
    Test updating shop order status from processing to conmpleted.
    Payment must have been made.
    """
    group = order_group_factory()
    order = order_factory(
        group=group,
        shop=shopowner.owned_shop,
        status="PROCESSING"
    )

    payload = {
        "status": "COMPLETED",
        "payment_status": True
    }

    url = reverse("update-shop-order-status", args=[order.id])
    client.force_authenticate(user=shopowner)
    res = client.post(url, data=payload, format="json")

    assert res.status_code == status.HTTP_200_OK
    data = res.data["data"]
    assert data["status"] == "COMPLETED"
    assert data["is_paid"] is True
    assert data["paid_at"] is not None
    assert data["shipped_at"] is None
    assert data["completed_at"] is not None
    assert data["cancelled_at"] is None
    assert data["is_delivered"] is False
    assert data["is_picked_up"] is True
    assert data["delivery_date"] is None


def test_update_shop_cash_pickup_order_status_from_processing_to_completed_without_payment(
    client,
    shopowner,
    order_factory,
    order_group_factory,
):
    """
    Test updating shop order status from processing to conmpleted.
    Payment must have been made.
    """
    group = order_group_factory()
    order = order_factory(
        group=group,
        shop=shopowner.owned_shop,
        status="PROCESSING"
    )

    payload = {
        **PAYLOAD,
        "status": "COMPLETED",
    }
    url = reverse("update-shop-order-status", args=[order.id])
    client.force_authenticate(user=shopowner)
    res = client.post(url, data=payload, format="json")

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    data = res.data
    assert data["status"] == "error"
    assert data["code"] == "invalid_payment_status"
    expected_msg = "Cash orders must be marked paid before completing."
    assert data["message"] == expected_msg


def test_update_shop_cash_pickup_order_status_from_processing_to_shipped(
    client,
    shopowner,
    order_factory,
    order_group_factory,
):
    """
    Test updating a cash pick-up order to shipped.
    Pick up orders can not be shipped.
    """
    group = order_group_factory()
    order = order_factory(
        group=group,
        shop=shopowner.owned_shop,
        status="PROCESSING"
    )

    payload = {
        "payment_status": True,
        "status": "SHIPPED"
    }

    url = reverse("update-shop-order-status", args=[order.id])
    client.force_authenticate(user=shopowner)
    res = client.post(url, data=payload, format="json")

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data["status"] == "error"
    assert res.data["code"] == "invalid_status_transition"
    expected_msg = "PICKUP orders can not be shipped."
    assert res.data["message"] == expected_msg


@pytest.mark.parametrize(
    "new_status",
    ["PROCESSING", "SHIPPED", "CANCELLED"],
    ids=["PROCESSING", "SHIPPED", "CANCELLED"]
)
def test_update_shop_order_from_completed_to_other_statuses(
    client,
    shopowner,
    order_group_factory,
    order_factory,
    new_status
):
    """
    Test updating completed orders to other statuses fails.
    """
    group = order_group_factory()
    order = order_factory(
        group=group,
        shop=shopowner.owned_shop,
        status="COMPLETED"
    )
    payload = {
        **PAYLOAD,
        "status": new_status
    }

    url = reverse("update-shop-order-status", args=[order.id])
    client.force_authenticate(user=shopowner)
    res = client.post(url, data=payload, format="json")

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data["status"] == "error"
    assert res.data["code"] == "invalid_status_transition"
    expected_msg = f"Invalid transition from COMPLETED to {new_status}."
    assert res.data["message"] == expected_msg


@pytest.mark.parametrize(
    "new_status",
    ["PROCESSING", "SHIPPED", "COMPLETED"],
    ids=["PROCESSING", "SHIPPED", "COMPLETED"]
)
def test_update_shop_order_from_cancelled_to_other_statuses(
    client,
    shopowner,
    order_group_factory,
    order_factory,
    new_status
):
    """
    Test updating cancelled orders to other statuses fails.
    """
    group = order_group_factory()
    order = order_factory(
        group=group,
        shop=shopowner.owned_shop,
        status="CANCELLED"
    )
    payload = {
        **PAYLOAD,
        "status": new_status
    }

    url = reverse("update-shop-order-status", args=[order.id])
    client.force_authenticate(user=shopowner)
    res = client.post(url, data=payload, format="json")

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data["status"] == "error"
    assert res.data["code"] == "invalid_status_transition"
    expected_msg = f"Invalid transition from CANCELLED to {new_status}."
    assert res.data["message"] == expected_msg


def test_update_shop_cash_delivery_order_status_from_pending_to_processing(
    client,
    shopowner,
    order_group_factory,
    order_factory
):
    """
    Test updating a shop order status from pending to process.
    Order fulfillment method is PICKUP and payment method is CASH.
    """
    group = order_group_factory(fulfillment_method="DELIVERY")
    order = order_factory(
        group=group,
        shop=shopowner.owned_shop,
    )

    url = reverse("update-shop-order-status", args=[order.id])
    client.force_authenticate(user=shopowner)
    res = client.post(url, data=PAYLOAD, format="json")

    assert res.status_code == status.HTTP_200_OK
    data = res.data["data"]
    assert data["status"] == "PROCESSING"
    assert data["is_paid"] is False
    assert data["paid_at"] is None
    assert data["processing_at"] is not None
    assert data["shipped_at"] is None
    assert data["completed_at"] is None
    assert data["cancelled_at"] is None
    assert data["is_delivered"] is False
    assert data["is_picked_up"] is False
    assert data["delivery_date"] is None

    payload = {
        **PAYLOAD,
        "payment_status": True
    }
    group = order_group_factory(fulfillment_method="DELIVERY")
    order = order_factory(
        group=group,
        shop=shopowner.owned_shop,
    )

    url = reverse("update-shop-order-status", args=[order.id])
    res = client.post(url, data=payload, format="json")
    assert res.status_code == status.HTTP_200_OK
    data = res.data["data"]
    assert data["status"] == "PROCESSING"
    assert data["is_paid"] is True
    assert data["paid_at"] is not None


@pytest.mark.parametrize(
    "new_status",
    ["SHIPPED", "COMPLETED"],
    ids=["SHIPPED", "COMPLETED"]
)
def test_update_shop_cash_delivery_order_status_from_pending_to_other_statuses(
    client,
    shopowner,
    order_group_factory,
    order_factory,
    new_status
):
    """
    Test updating a shop delivery order status from pending
    to shipped and completed fails.
    """

    group = order_group_factory(fulfillment_method="DELIVERY")
    order = order_factory(
        group=group,
        shop=shopowner.owned_shop,
    )
    payload = {
        **PAYLOAD,
        "status": new_status
    }

    url = reverse("update-shop-order-status", args=[order.id])
    client.force_authenticate(user=shopowner)
    res = client.post(url, data=payload, format="json")

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data["status"] == "error"
    assert res.data["code"] == "invalid_status_transition"
    expected_msg = f"Invalid transition from PENDING to {new_status}."
    assert res.data["message"] == expected_msg


def test_update_shop_cash_delivery_order_status_from_processing_to_shipped(
    client,
    shopowner,
    order_group_factory,
    order_factory
):
    """
    Test updating a shop order status from processing to shipped succeeds.
    """
    group = order_group_factory(fulfillment_method="DELIVERY")
    order = order_factory(
        group=group,
        shop=shopowner.owned_shop,
        status="PROCESSING"
    )
    payload = {
        **PAYLOAD,
        "status": "SHIPPED"
    }

    url = reverse("update-shop-order-status", args=[order.id])
    client.force_authenticate(user=shopowner)
    res = client.post(url, data=payload, format="json")

    assert res.status_code == status.HTTP_200_OK
    data = res.data["data"]
    assert data["status"] == "SHIPPED"
    assert data["is_paid"] is False
    assert data["paid_at"] is None
    assert data["shipped_at"] is not None
    assert data["completed_at"] is None
    assert data["cancelled_at"] is None
    assert data["is_delivered"] is False
    assert data["is_picked_up"] is False
    assert data["delivery_date"] is not None

    payload = {
        **PAYLOAD,
        "payment_status": True,
        "status": "SHIPPED"
    }
    group = order_group_factory(fulfillment_method="DELIVERY")
    order = order_factory(
        group=group,
        shop=shopowner.owned_shop,
        status="PROCESSING"
    )

    url = reverse("update-shop-order-status", args=[order.id])
    res = client.post(url, data=payload, format="json")
    assert res.status_code == status.HTTP_200_OK
    data = res.data["data"]
    assert data["status"] == "SHIPPED"
    assert data["is_paid"] is True
    assert data["paid_at"] is not None


def test_update_shop_cash_delivery_order_status_from_processing_to_completed(
    client,
    shopowner,
    order_group_factory,
    order_factory
):
    """
    Test updating a shop cash delivery order from processing to completed
    fails.
    Delivery orders must be shipped before completed.
    """

    group = order_group_factory(fulfillment_method="DELIVERY")
    order = order_factory(
        group=group,
        shop=shopowner.owned_shop,
        status="PROCESSING"
    )
    payload = {
        **PAYLOAD,
        "status": "COMPLETED"
    }

    url = reverse("update-shop-order-status", args=[order.id])
    client.force_authenticate(user=shopowner)
    res = client.post(url, data=payload, format="json")

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data["status"] == "error"
    assert res.data["code"] == "invalid_status_transition"
    expected_msg = f"Invalid transition from PROCESSING to COMPLETED."
    assert res.data["message"] == expected_msg


def test_shop_cash_delivery_order_status_from_shipped_to_completed(
    client,
    shopowner,
    order_group_factory,
    order_factory
):
    """
    Test updating cash delivery order status from shipped to completed.
    Payment status updated to true.
    """
    group = order_group_factory(fulfillment_method="DELIVERY")
    order = order_factory(
        group=group,
        shop=shopowner.owned_shop,
        status="SHIPPED"
    )
    payload = {
        **PAYLOAD,
        "status": "COMPLETED",
        "payment_status": True
    }

    url = reverse("update-shop-order-status", args=[order.id])
    client.force_authenticate(user=shopowner)
    res = client.post(url, data=payload, format="json")

    assert res.status_code == status.HTTP_200_OK
    data = res.data["data"]
    assert data["status"] == "COMPLETED"
    assert data["is_paid"] is True
    assert data["paid_at"] is not None
    assert data["completed_at"] is not None
    assert data["cancelled_at"] is None
    assert data["is_delivered"] is True
    assert data["is_picked_up"] is False


def test_shop_cash_delivery_order_status_from_shipped_to_completed_without_payment(
    client,
    shopowner,
    order_group_factory,
    order_factory
):
    """
    Test updating cash delivery order status from shipped to completed fails.
    Payment status must be true.
    """
    group = order_group_factory(fulfillment_method="DELIVERY")
    order = order_factory(
        group=group,
        shop=shopowner.owned_shop,
        status="SHIPPED"
    )
    payload = {
        **PAYLOAD,
        "status": "COMPLETED",
    }

    url = reverse("update-shop-order-status", args=[order.id])
    client.force_authenticate(user=shopowner)
    res = client.post(url, data=payload, format="json")

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data["status"] == "error"
    assert res.data["code"] == "invalid_payment_status"
    expected_msg = "Cash orders must be marked paid before completing."
    assert res.data["message"] == expected_msg


@pytest.mark.parametrize(
    "new_status",
    ["PROCESSING", "CANCELLED"],
    ids=["PROCESSING", "CANCELLED"]
)
def test_update_shop_cash_delivery_order_status_from_shipped_to_other_statuses(
    client,
    shopowner,
    order_group_factory,
    order_factory,
    new_status
):
    """
    Test updating cash delivery order status from shipped to
    other statuses fails.
    """
    group = order_group_factory(fulfillment_method="DELIVERY")
    order = order_factory(
        group=group,
        shop=shopowner.owned_shop,
        status="SHIPPED"
    )

    payload = {
        **PAYLOAD,
        "status": new_status,
        "payment_status": True
    }

    url = reverse("update-shop-order-status", args=[order.id])
    client.force_authenticate(user=shopowner)
    res = client.post(url, data=payload, format="json")

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data["status"] == "error"
    assert res.data["code"] == "invalid_status_transition"
    expected_msg = f"Invalid transition from SHIPPED to {new_status}."
    assert res.data["message"] == expected_msg
