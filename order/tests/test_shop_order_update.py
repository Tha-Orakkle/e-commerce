from django.urls import reverse
from django.utils.timezone import now
from rest_framework import status

import pytest

PAYLOAD = {
    "payment_status": False,
    "status": "PROCESSING",
    "delivery_date": "2026-08-05"
}


# ===================================================
# GENERAL TRANSACTIONS TESTS
#  - Cash (Pickup and Delivery)
#  - Digital (Pickup and Delivery)
# ===================================================
def test_update_shop_order_status_response_fields(
    client,
    shopowner,
    populated_order_group_factory
):
    """
    Test updating a shop order status returns the expected fields.
    """
    group = populated_order_group_factory(shop=shopowner.owned_shop)
    order = group.orders.first()

    url = reverse("update-shop-order-status", args=[order.id])
    client.force_authenticate(user=shopowner)
    res = client.post(url, data=PAYLOAD, format="json")

    assert res.status_code == status.HTTP_200_OK
    data = res.data["data"]
    expected_fields = [
        "id",
        "shipping",
        "items",
        "status",
        "total_amount",
        "shop_name",
        "is_paid",
        "paid_at",
        "processing_at",
        "shipped_at",
        "completed_at",
        "created_at",
        "cancelled_at",
        "is_delivered",
        "is_picked_up",
        "delivery_date"
    ]
    for field in expected_fields:
        assert field in data


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


@pytest.mark.parametrize(
    "new_status",
    ["PENDING", "INVALID_STATUS", ""],
    ids=["PENDING", "INVALID_STATUS", "EMPTY_STRING"]
)
def test_update_shop_order_with_invalid_status(
    client,
    shopowner,
    order_group_factory,
    order_factory,
    new_status
):
    """
    Test updating a shop order with an invalid status fails.
    """
    group = order_group_factory()
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
    assert res.data["code"] == "invalid_status"
    assert res.data["message"] == "Invalid status provided."


@pytest.mark.parametrize(
    "new_status",
    ["PROCESSING", "SHIPPED", "COMPLETED", "CANCELLED"],
    ids=["PROCESSING", "SHIPPED", "COMPLETED", "CANCELLED"]
)
def test_update_shop_order_with_self_transition(
    client,
    shopowner,
    order_group_factory,
    order_factory,
    new_status
):
    """
    Test updating a shop order with the same status fails.
    """
    group = order_group_factory()
    order = order_factory(
        group=group,
        shop=shopowner.owned_shop,
        status=new_status
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
    expected_msg = f"Order {str(order.id)} is already in {new_status} state."
    assert res.data["message"] == expected_msg


def test_update_shop_order_group_status_to_partially_fulfilled(
    client,
    shopowner,
    order_group_factory,
    order_factory
):
    """
    Test that when the shop order status is updated,
    the order group status is also updated accordingly.
    Order group status is updated to PARTIALLY_FULFILLED when
    one order is PROCESSING, SHIPPED OR COMPLETED.
    """
    group = order_group_factory()
    order1 = order_factory(
        group=group,
        shop=shopowner.owned_shop,
        status="PENDING"
    )
    order2 = order_factory(
        group=group,
        shop=shopowner.owned_shop,
        status="PENDING"
    )

    payload = {
        **PAYLOAD,
        "status": "PROCESSING"
    }
    

    url = reverse("update-shop-order-status", args=[order1.id])
    client.force_authenticate(user=shopowner)
    res = client.post(url, data=payload, format="json")

    assert res.status_code == status.HTTP_200_OK
    group.refresh_from_db()
    assert group.status == "PARTIALLY_FULFILLED"


def test_update_shop_order_group_status_to_fulfilled(
    client,
    shopowner,
    order_group_factory,
    order_factory
):
    """
    Test that when all shop orders in a group are updated to COMPLETED,
    the order group status is also updated to FULFILLED.
    """
    group = order_group_factory()
    order1 = order_factory(
        group=group,
        shop=shopowner.owned_shop,
        status="PROCESSING"
    )
    order2 = order_factory(
        group=group,
        shop=shopowner.owned_shop,
        status="PROCESSING"
    )

    payload = {
        **PAYLOAD,
        "status": "COMPLETED",
        "payment_status": True
    }

    url1 = reverse("update-shop-order-status", args=[order1.id])
    url2 = reverse("update-shop-order-status", args=[order2.id])
    client.force_authenticate(user=shopowner)

    res1 = client.post(url1, data=payload, format="json")
    assert res1.status_code == status.HTTP_200_OK

    res2 = client.post(url2, data=payload, format="json")
    assert res2.status_code == status.HTTP_200_OK

    group.refresh_from_db()
    assert group.status == "FULFILLED"
    assert group.completed_at is not None


# ===================================================
# CASH PAYMENT TRANSACTIONS
# ===================================================
@pytest.mark.parametrize(
    "fulfillment_method",
    ["PICKUP", "DELIVERY"],
    ids=["PICKUP", "DELIVERY"]
)
def test_update_shop_cash_order_status_from_pending_to_processing(
    client,
    shopowner,
    populated_order_group_factory,
    fulfillment_method
):
    """
    Test updating a shop order status from pending to processing.
    """
    group = populated_order_group_factory(
        shop=shopowner.owned_shop,
        fulfillment_method=fulfillment_method
    )
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
def test_update_shop_cash_order_status_from_pending_to_other_statuses(
    client,
    shopowner,
    populated_order_group_factory,
    new_status
):
    """
    Test updating a shop cash delivery order status from pending to
    statuses other than processing fails.
    """
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


def test_update_shop_cash_pickup_order_status_from_processing_to_completed(
    client,
    shopowner,
    order_factory,
    order_group_factory,
):
    """
    Test updating cash pickup order status from processing to completed.
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
    Test updating cash pickup order status from processing to completed.
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


# ===================================================
# DIGITAL PAYMENT TRANSACTIONS
# ===================================================
@pytest.mark.parametrize(
    "old_status, new_status",
    [
        ("PENDING", "PROCESSING"),
        ("PROCESSING", "SHIPPED"),
        ("PROCESSING", "COMPLETED"),
        ("SHIPPED", "COMPLETED")
    ],
    ids=[
        "PENDING_TO_PROCESSING",
        "PROCESSING_TO_SHIPPED",
        "PROCESSING_TO_COMPLETED",
        "SHIPPED_TO_COMPLETED"]
)
def test_update_shop_digital_order_status_without_payment(
    client,
    shopowner,
    order_group_factory,
    order_factory,
    old_status,
    new_status
):
    """
    Test updating a shop digital order status without payment fails.
    """
    f_method = "DELIVERY" if old_status == "SHIPPED" else "PICKUP"
    group = order_group_factory(
        payment_method="DIGITAL",
        fulfillment_method=f_method
    )

    order = order_factory(
        group=group,
        shop=shopowner.owned_shop,
        status=old_status
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
    assert res.data["code"] == "invalid_payment_status"
    expected_msg = "Digital orders must be paid before transition."
    assert res.data["message"] == expected_msg


@pytest.mark.parametrize(
    "fulfillment_method",
    ["PICKUP", "DELIVERY"],
    ids=["PICKUP", "DELIVERY"]
)
def test_update_shop_digital_order_status_from_pending_to_processing(
    client,
    shopowner,
    order_group_factory,
    order_factory,
    fulfillment_method
):
    """
    Test updating a shop digital order status from pending to processing.
    """
    group = order_group_factory(
        fulfillment_method=fulfillment_method,
        payment_method="DIGITAL"
    )
    order = order_factory(
        group=group,
        shop=shopowner.owned_shop,
        is_paid=True,
        paid_at=now()
    )

    url = reverse("update-shop-order-status", args=[order.id])
    client.force_authenticate(user=shopowner)
    res = client.post(url, data=PAYLOAD, format="json")

    assert res.status_code == status.HTTP_200_OK
    data = res.data["data"]
    assert data["status"] == "PROCESSING"
    assert data["is_paid"] is True
    assert data["paid_at"] is not None
    assert data["processing_at"] is not None
    assert data["shipped_at"] is None
    assert data["completed_at"] is None
    assert data["cancelled_at"] is None
    assert data["is_delivered"] is False
    assert data["is_picked_up"] is False
    assert data["delivery_date"] is None


@pytest.mark.parametrize(
    "new_status",
    ["SHIPPED", "COMPLETED"],
    ids=["SHIPPED", "COMPLETED"]
)
def test_update_shop_digital_order_status_from_pending_to_other_statuses(
    client,
    shopowner,
    order_group_factory,
    order_factory,
    new_status
):
    """
    Test updating a shop digital delivery order status from pending to
    statuses other than processing fails.
    """
    group = order_group_factory(
        fulfillment_method="DELIVERY",
        payment_method="DIGITAL"
    )
    order = order_factory(
        group=group,
        shop=shopowner.owned_shop,
        is_paid=True,
        paid_at=now()
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


def test_update_shop_digital_delivery_order_status_from_processing_to_shipped(
    client,
    shopowner,
    order_group_factory,
    order_factory
):
    """
    Test updating a shop digital delivery order status from processing
    to shipped.
    """
    group = order_group_factory(
        fulfillment_method="DELIVERY",
        payment_method="DIGITAL"
    )
    order = order_factory(
        group=group,
        shop=shopowner.owned_shop,
        status="PROCESSING",
        is_paid=True,
        paid_at=now()
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


def test_update_shop_digital_delivery_order_status_from_processing_to_completed(
    client,
    shopowner,
    order_group_factory,
    order_factory
):
    """
    Test updating a shop digital delivery order status from processing
    to completed fails.
    """
    group = order_group_factory(
        fulfillment_method="DELIVERY",
        payment_method="DIGITAL"
    )
    order = order_factory(
        group=group,
        shop=shopowner.owned_shop,
        status="PROCESSING",
        is_paid=True,
        paid_at=now()
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


def test_update_shop_digital_delivery_order_status_from_shipped_to_completed(
    client,
    shopowner,
    order_group_factory,
    order_factory
):
    """
    Test updating a shop digital delivery order status from shipped to completed.
    """
    group = order_group_factory(
        fulfillment_method="DELIVERY",
        payment_method="DIGITAL"
    )
    order = order_factory(
        group=group,
        shop=shopowner.owned_shop,
        status="SHIPPED",
        is_paid=True,
        paid_at=now()
    )
    payload = {
        **PAYLOAD,
        "status": "COMPLETED"
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


@pytest.mark.parametrize(
    "new_status",
    ["PROCESSING", "CANCELLED"],
    ids=["PROCESSING", "CANCELLED"]
)
def test_update_shop_digital_delivery_order_status_from_shipped_to_other_statuses(
    client,
    shopowner,
    order_group_factory,
    order_factory,
    new_status
):
    """
    Test updating a shop digital delivery order status from shipped
    to statuses other than COMPLETED fails.
    """
    group = order_group_factory(
        fulfillment_method="DELIVERY",
        payment_method="DIGITAL"
    )
    order = order_factory(
        group=group,
        shop=shopowner.owned_shop,
        status="SHIPPED",
        is_paid=True,
        paid_at=now()
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
    expected_msg = f"Invalid transition from SHIPPED to {new_status}."
    assert res.data["message"] == expected_msg


def test_update_shop_digital_pickup_order_status_from_processing_to_completed(
    client,
    shopowner,
    order_group_factory,
    order_factory
):
    """
    Test updating a shop digital pick-up order status from processing
    to completed.
    """
    group = order_group_factory(
        fulfillment_method="PICKUP",
        payment_method="DIGITAL",
    )
    order = order_factory(
        group=group,
        shop=shopowner.owned_shop,
        status="PROCESSING",
        is_paid=True,
        paid_at=now()
    )
    payload = {
        **PAYLOAD,
        "status": "COMPLETED"
    }

    url = reverse("update-shop-order-status", args=[order.id])
    client.force_authenticate(user=shopowner)
    res = client.post(url, data=payload, format="json")

    assert res.status_code == status.HTTP_200_OK
    data = res.data["data"]
    assert data["status"] == "COMPLETED"
    assert data["completed_at"] is not None


def test_update_shop_digital_pickup_order_status_from_processing_to_shipped(
    client,
    shopowner,
    order_group_factory,
    order_factory
):
    """
    Test updating a shop digital pick-up order status from processing
    to shipped fails.
    """
    group = order_group_factory(
        fulfillment_method="PICKUP",
        payment_method="DIGITAL",
    )
    order = order_factory(
        group=group,
        shop=shopowner.owned_shop,
        status="PROCESSING",
        is_paid=True,
        paid_at=now()
    )
    payload = {
        **PAYLOAD,
        "status": "SHIPPED"
    }

    url = reverse("update-shop-order-status", args=[order.id])
    client.force_authenticate(user=shopowner)
    res = client.post(url, data=payload, format="json")

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data["status"] == "error"
    assert res.data["code"] == "invalid_status_transition"
    expected_msg = f"PICKUP orders can not be shipped."
    assert res.data["message"] == expected_msg
