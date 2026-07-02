from django.urls import reverse
from rest_framework import status

import pytest
import uuid

# ======================================================
# TEST GET ORDER GROUP LIST
# ======================================================

GET_ORDER_GROUPS_URL = reverse("order-groups")


def test_get_all_order_groups(client,
                              customer,
                              populated_order_group_factory):
    """
    Test that list of order groups by a customer is retrieved.
    """

    for _ in range(2):
        populated_order_group_factory(user=customer)

    client.force_authenticate(user=customer)

    res = client.get(GET_ORDER_GROUPS_URL)

    assert res.status_code == status.HTTP_200_OK
    assert res.data["message"] == "User order groups retrieved successfully."

    data = res.data["data"]
    assert "count" in data
    assert "next" in data
    assert "previous" in data
    assert "results" in data

    assert data["count"] == 2
    group = data["results"][0]
    expected_fields = [
        "id", "status", "payment_method",
        "total_amount", "fulfillment_method",
        "delivery_fee", "email", "full_name",
        "shipping_full_name", "shipping_telephone",
        "shipping_street_address", "shipping_city",
        "shipping_state", "shipping_country",
        "shipping_postal_code", "created_at",
        "updated_at", "completed_at", "cancelled_at"
    ]
    assert all(field in group for field in expected_fields)


def test_get_all_order_groups_by_customer(client,
                                          customer,
                                          customer_factory,
                                          populated_order_group_factory):
    """
    Test that response includes only order groups
    of the signed in customer.
    """
    customer2 = customer_factory()

    for i in range(4):
        populated_order_group_factory(
            user=customer if i % 2 else customer2
        )

    client.force_authenticate(user=customer)

    res = client.get(GET_ORDER_GROUPS_URL)

    assert res.status_code == status.HTTP_200_OK
    count = res.data["data"]["count"]
    assert count == 2


@pytest.mark.parametrize(
    "user_type",
    ["shopowner", "shop_staff"],
    ids=["shopowner", "shop_staff"],
)
def test_get_all_order_groups_by_non_customer(client, user_type, all_users):
    """
    Test that getting all order group fails is signed in user is
    not a customer.
    """
    user = all_users[user_type]

    client.force_authenticate(user=user)
    res = client.get(GET_ORDER_GROUPS_URL)

    assert res.status_code == status.HTTP_403_FORBIDDEN
    assert res.data["status"] == "error"
    assert res.data["code"] == "forbidden"
    expected_msg = "You do not have permission to perform this action."
    assert res.data["message"] == expected_msg


def test_get_all_order_groups_by_super_user(client,
                                            super_user,
                                            customer_factory,
                                            populated_order_group_factory):
    """
    Test that super user gets all order groups of all customers.
    """
    customer1 = customer_factory()
    customer2 = customer_factory()

    for i in range(4):
        populated_order_group_factory(
            user=customer1 if i % 2 else customer2
        )

    client.force_authenticate(user=super_user)
    res = client.get(GET_ORDER_GROUPS_URL)

    assert res.status_code == status.HTTP_200_OK
    count = res.data["data"]["count"]
    assert count == 4


def test_get_all_order_groups_by_unauthenticated_user(client):
    """
    Test getting all order groups by an unathenticated user fails.
        - Test with invalid access token and without a token
    """

    res = client.get(GET_ORDER_GROUPS_URL)

    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    expected_msg = "Authentication credentials were not provided."
    assert res.data['message'] == expected_msg

    client.cookies['access_token'] = 'invalidtoken'
    res = client.get(GET_ORDER_GROUPS_URL)
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.data['message'] == "Token is invalid or expired"


# ======================================================
# TEST GET AN ORDER GROUP
# ======================================================

def test_get_order_group(client, customer, populated_order_group_factory):
    """
    Test getting a specific order group matching the given
    order group ID. Test that all expected fields are returned.
    """
    group = populated_order_group_factory(user=customer)

    url = reverse("order-group", kwargs={"order_group_id": group.id})
    client.force_authenticate(user=customer)
    res = client.get(url)

    assert res.status_code == status.HTTP_200_OK
    assert res.data["status"] == "success"
    assert res.data["message"] == "Order group retrieved successfully."

    data = res.data["data"]

    # test data contains order group info
    expected_order_group_fields = [
        "id", "status", "orders", "payment_method",
        "total_amount", "fulfillment_method", "delivery_fee",
        "email", "full_name", "shipping_full_name",
        "shipping_telephone", "shipping_street_address",
        "shipping_city", "shipping_state", "shipping_country",
        "shipping_postal_code", "created_at", "updated_at",
        "completed_at", "cancelled_at"
    ]
    assert all(field in data for field in expected_order_group_fields)

    # test group contains order info
    order = data["orders"][0]
    expected_order_fields = [
        "id", "shop", "items",
        "status", "total_amount",
        "is_paid", "shop_name",
        "is_delivered", "is_picked_up",
        "created_at", "delivery_date",
        "paid_at", "processing_at",
        "shipped_at", "completed_at",
        "cancelled_at"
    ]
    assert all(field in order for field in expected_order_fields)

    # test order contains items info
    item = order["items"][0]
    expected_item_fields = [
        "id", "product_name",
        "product_description",
        "quantity", "price"
    ]
    assert all(field in item for field in expected_item_fields)

    # test order contains shop info
    shop = order["shop"]
    assert all(field in shop for field in ["id", "name"])


def test_get_order_group_returns_correct_order_count(
    client,
    customer,
    populated_order_group_factory
):
    """
    Test that getting an order group returns all associated orders
    and order items
    """
    group = populated_order_group_factory(
        user=customer,
        orders_per_group=2,
        items_per_order=3
    )

    url = reverse("order-group", args=[group.id])
    client.force_authenticate(user=customer)
    res = client.get(url)

    assert res.status_code == status.HTTP_200_OK

    data = res.data["data"]
    assert len(data["orders"]) == 2
    assert len(data["orders"][0]["items"]) == 3


def test_get_order_group_by_different_customer(client,
                                               customer_factory,
                                               populated_order_group_factory):
    """
    Test that getting order group by a different customer fails.
    """
    customer1 = customer_factory()
    customer2 = customer_factory()

    group = populated_order_group_factory(user=customer1)

    url = reverse("order-group", args=[group.id])
    client.force_authenticate(user=customer2)
    res = client.get(url)

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
def test_get_order_group_by_non_customer(client,
                                         all_users,
                                         user_type,
                                         populated_order_group_factory):
    """
    Test getting specific order group by a non-customer fails.
    """
    user = all_users[user_type]
    group = populated_order_group_factory()

    url = reverse("order-group", args=[group.id])
    client.force_authenticate(user=user)
    res = client.get(url)

    assert res.status_code == status.HTTP_403_FORBIDDEN
    assert res.data["status"] == "error"
    assert res.data["code"] == "forbidden"
    expected_msg = "You do not have permission to perform this action."
    assert res.data["message"] == expected_msg


def test_get_order_group_by_super_user(client,
                                       super_user,
                                       populated_order_group_factory):
    """
    Test getting specific order group by a super user succeeds.
    """
    group = populated_order_group_factory()

    url = reverse("order-group", args=[group.id])
    client.force_authenticate(user=super_user)
    res = client.get(url)

    assert res.status_code == status.HTTP_200_OK
    assert res.data["status"] == "success"
    assert res.data["message"] == "Order group retrieved successfully."


def test_get_order_group_by_unauthenticated_user(
    client,
    populated_order_group_factory
):
    """
    Test getting order group by unauthenticated user fails.
        - Test with no credentials provided and with invalid
          access token.
    """
    group = populated_order_group_factory()
    url = reverse("order-group", args=[group.id])
    res = client.get(url)

    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.data['status'] == "error"
    assert res.data['code'] == "unauthorized"
    expected_msg = "Authentication credentials were not provided."
    assert res.data['message'] == expected_msg

    client.cookies['access_token'] = "Invalid_access_token2445"
    res = client.get(url)

    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.data['status'] == "error"
    assert res.data['code'] == "unauthorized"
    assert res.data['message'] == "Token is invalid or expired"


def test_get_order_group_with_non_existent_order_id(
    client,
    customer
):
    """
    Test getting order group with non-existent order id.
    """
    url = reverse("order-group", args=[uuid.uuid4()])
    client.force_authenticate(user=customer)
    res = client.get(url)

    assert res.status_code == status.HTTP_404_NOT_FOUND
    assert res.data["status"] == "error"
    assert res.data["code"] == "not_found"
    expected_msg = "No order group matching the given ID found."
    assert res.data["message"] == expected_msg


def test_get_order_group_with_invalid_uuid(
    client,
    customer
):
    """
    Test getting order group with invalid order id.
    """
    url = reverse("order-group", args=["invalid-uuid"])
    client.force_authenticate(user=customer)
    res = client.get(url)

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data["status"] == "error"
    assert res.data["code"] == "invalid_uuid"
    assert res.data["message"] == "Invalid order group id."
