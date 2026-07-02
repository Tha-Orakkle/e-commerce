from django.urls import reverse
from rest_framework import status

import pytest
import uuid

from order.models import Order


# ======================================================
# TEST GET ALL SHOP ORDERS
# ======================================================
GET_SHOP_ORDERS_URL = reverse("shop-orders")


def test_get_all_shop_orders_expected_fields(
    client,
    shopowner,
    populated_order_group_factory
):
    """
    Get all orders associated with a shop and the expected fields.
    """
    shop = shopowner.owned_shop
    populated_order_group_factory(shop=shop)

    client.force_authenticate(user=shopowner)
    res = client.get(GET_SHOP_ORDERS_URL)

    assert res.status_code == status.HTTP_200_OK

    assert res.data["status"] == "success"
    expected_msg = "All orders retrieved successfully."
    assert res.data["message"] == expected_msg

    data = res.data["data"]
    expected_data_fields = [
        "count", "next", "previous", "results"]
    assert all(field in data for field in expected_data_fields)

    order = data["results"][0]
    expected_order_fields = [
        "id", "shipping", "items",
        "status", "total_amount",
        "is_paid", "shop_name",
        "is_delivered", "is_picked_up",
        "created_at", "delivery_date",
        "paid_at", "processing_at",
        "shipped_at", "completed_at",
        "cancelled_at"
    ]
    assert all(field in order for field in expected_order_fields)

    shipping = order["shipping"]
    expected_shipping_fields = [
        "full_name", "telephone",
        "street_address", "city",
        "state", "country",
        "postal_code"
    ]
    assert all(field in shipping for field in expected_shipping_fields)

    item = order["items"][0]
    expected_item_fields = [
        "id", "product_name",
        "product_description",
        "quantity", "price"
    ]
    assert all(field in item for field in expected_item_fields)


def test_get_all_shop_orders_count(client,
                                   shopowner_factory,
                                   populated_order_group_factory):
    """
    Test that response only includes all orders and items
    associated to the shop of the signed in user.
    """
    shopowner = shopowner_factory()
    shop1 = shopowner.owned_shop
    shop2 = shopowner_factory().owned_shop

    populated_order_group_factory(
        shop=shop1,
        orders_per_group=6,
        items_per_order=3
    )
    populated_order_group_factory(
        shop=shop2,
        orders_per_group=3,
    )

    assert Order.objects.count() == 9

    client.force_authenticate(user=shopowner)
    res = client.get(GET_SHOP_ORDERS_URL)

    assert res.status_code == status.HTTP_200_OK
    results = res.data["data"]["results"]

    assert len(results) == 6
    assert len(results[0]["items"]) == 3


def test_get_all_shop_orders_pagination(client,
                                        shopowner,
                                        populated_order_group_factory):
    """
    Test that get all shop orders is paginated and
    the the next values and previous values work.
    """
    from rest_framework.settings import reload_api_settings
    from django.conf import settings
    from urllib.parse import urlparse, parse_qs

    settings.REST_FRAMEWORK = {
        **settings.REST_FRAMEWORK,
        "PAGE_SIZE": 5
    }
    reload_api_settings(setting="REST_FRAMEWORK")

    shop = shopowner.owned_shop
    populated_order_group_factory(shop=shop, orders_per_group=8)

    client.force_authenticate(user=shopowner)
    res = client.get(GET_SHOP_ORDERS_URL)

    assert res.status_code == status.HTTP_200_OK
    data = res.data["data"]

    assert data["count"] == 8
    assert len(data["results"]) == 5

    next_url = data["next"]
    assert next_url is not None
    print(urlparse(next_url))

    page = int(parse_qs(urlparse(next_url).query)["page"][0])
    assert page == 2

    res = client.get(next_url)
    data = res.data["data"]

    assert len(data["results"]) == 3

    prev_url = data["previous"]
    assert prev_url is not None
    assert urlparse(prev_url).path == GET_SHOP_ORDERS_URL


def test_get_all_shop_orders_by_superuser(client,
                                          super_user,
                                          populated_order_group_factory):
    """
    Test super user can get all shop orders.
    """
    for _ in range(4):
        populated_order_group_factory()

    client.force_authenticate(user=super_user)
    res = client.get(GET_SHOP_ORDERS_URL)

    assert res.status_code == status.HTTP_200_OK
    assert res.data["status"] == "success"
    assert res.data["message"] == "All orders retrieved successfully."

    results = res.data["data"]["results"]
    assert len(results) == 4


def test_get_all_shop_orders_by_customer(client,
                                         customer,
                                         populated_order_group_factory):
    """
    Test get all shop orders by customer fails.
    """
    for _ in range(4):
        populated_order_group_factory()

    client.force_authenticate(user=customer)
    res = client.get(GET_SHOP_ORDERS_URL)

    assert res.status_code == status.HTTP_403_FORBIDDEN
    assert res.data["status"] == "error"
    assert res.data["code"] == "forbidden"
    expected_msg = "You do not have permission to perform this action."
    assert res.data["message"] == expected_msg


def test_get_all_shop_orders_by_unauthenticated_user(
    client,
    populated_order_group_factory
):
    """
    Test getting all shop orders by unauthenticated user fails.
        - Test no token provided and invalid token.
    """
    for _ in range(4):
        populated_order_group_factory()

    res = client.get(GET_SHOP_ORDERS_URL)

    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    expected_msg = "Authentication credentials were not provided."
    assert res.data['message'] == expected_msg

    client.cookies['access_token'] = 'invalidtoken'
    res = client.get(GET_SHOP_ORDERS_URL)
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.data['message'] == "Token is invalid or expired"


@pytest.mark.parametrize(
    "order_status",
    ["pending", "processing", "shipped", "completed", "cancelled"],
    ids=["pending", "processing", "shipped", "completed", "cancelled"]
)
def test_get_all_shop_orders_filtered_by_status(
    client,
    shopowner,
    order_group_factory,
    order_factory,
    order_status
):
    """
    Test getting all shop orders with filters.
    """
    statuses = [
        "PENDING",
        "PROCESSING",
        "SHIPPED",
        "COMPLETED",
        "CANCELLED"
    ]
    shop = shopowner.owned_shop
    for s in statuses:
        group = order_group_factory()
        for _ in range(3):
            order_factory(group=group, shop=shop, status=s)

    url = GET_SHOP_ORDERS_URL + f"?status={order_status}"
    client.force_authenticate(user=shopowner)
    res = client.get(url)

    assert res.status_code == status.HTTP_200_OK
    results = res.data["data"]["results"]

    for order in results:
        assert order["status"] == order_status.upper()


def test_get_all_shop_orders_default_order(
    client,
    shopowner,
    order_group_factory,
    order_factory
):
    """
    Test getting all shop orders with the default order.
    Default order: pending, processing, shipped.
    Other statuses are ordered by the created_at date.
    """
    shop = shopowner.owned_shop
    group = order_group_factory()

    processing_order = order_factory(
        group=group, shop=shop, status="PROCESSING")
    pending_order = order_factory(
        group=group, shop=shop, status="PENDING")
    cancelled_order = order_factory(
        group=group, shop=shop, status="CANCELLED")
    completed_order = order_factory(
        group=group, shop=shop, status="COMPLETED")
    shipped_order = order_factory(
        group=group, shop=shop, status="SHIPPED")

    client.force_authenticate(user=shopowner)
    res = client.get(GET_SHOP_ORDERS_URL)

    assert res.status_code == status.HTTP_200_OK
    results = res.data["data"]["results"]

    returned_ids = [order["id"] for order in results]
    assert returned_ids == [
        str(pending_order.id),
        str(processing_order.id),
        str(shipped_order.id),
        str(cancelled_order.id),
        str(completed_order.id)
    ]


def test_get_all_shop_orders_ordered_by_status(
    client,
    shopowner,
    order_group_factory,
    order_factory
):
    """
    Test getting all shop orders ordered by status.
    """
    shop = shopowner.owned_shop
    group = order_group_factory()

    processing_order = order_factory(
        group=group, shop=shop, status="PROCESSING")
    pending_order = order_factory(
        group=group, shop=shop, status="PENDING")
    cancelled_order = order_factory(
        group=group, shop=shop, status="CANCELLED")
    completed_order = order_factory(
        group=group, shop=shop, status="COMPLETED")
    shipped_order = order_factory(
        group=group, shop=shop, status="SHIPPED")

    url = GET_SHOP_ORDERS_URL + "?ordering=status"
    client.force_authenticate(user=shopowner)
    res = client.get(url)

    assert res.status_code == status.HTTP_200_OK
    results = res.data["data"]["results"]

    returned_ids = [order["id"] for order in results]
    assert returned_ids == [
        str(cancelled_order.id),
        str(completed_order.id),
        str(pending_order.id),
        str(processing_order.id),
        str(shipped_order.id)
    ]

    url = GET_SHOP_ORDERS_URL + "?ordering=-status"
    res = client.get(url)

    assert res.status_code == status.HTTP_200_OK
    results = res.data["data"]["results"]

    returned_ids = [order["id"] for order in results]
    assert returned_ids == [
        str(shipped_order.id),
        str(processing_order.id),
        str(pending_order.id),
        str(completed_order.id),
        str(cancelled_order.id)
    ]


def test_get_all_shop_orders_ordered_by_created_at(
    client,
    shopowner,
    order_group_factory,
    order_factory
):
    """
    Test getting all orders ordered by dated created.
    """
    shop = shopowner.owned_shop
    group = order_group_factory()

    order1 = order_factory(group=group, shop=shop)
    order2 = order_factory(group=group, shop=shop)
    order3 = order_factory(group=group, shop=shop)

    url = GET_SHOP_ORDERS_URL + "?ordering=created_at"
    client.force_authenticate(user=shopowner)
    res = client.get(url)

    assert res.status_code == status.HTTP_200_OK
    results = res.data["data"]["results"]

    returned_ids = [order["id"] for order in results]
    assert returned_ids == [
        str(order1.id),
        str(order2.id),
        str(order3.id)
    ]

    url = GET_SHOP_ORDERS_URL + "?ordering=-created_at"
    client.force_authenticate(user=shopowner)
    res = client.get(url)

    assert res.status_code == status.HTTP_200_OK
    results = res.data["data"]["results"]

    returned_ids = [order["id"] for order in results]
    assert returned_ids == [
        str(order3.id),
        str(order2.id),
        str(order1.id)
    ]


def test_get_all_shop_orders_ordered_and_filtered(
    client,
    shopowner,
    order_group_factory,
    order_factory
):
    """
    Test getting all shop orders are ordered and filtered
    by the query string passed. Testing both funtionality.
    """
    shop = shopowner.owned_shop
    group = order_group_factory()

    order1 = order_factory(group=group, shop=shop, status="PENDING")
    order_factory(group=group, shop=shop, status="PROCESSING")
    order2 = order_factory(group=group, shop=shop, status="PENDING")

    url = GET_SHOP_ORDERS_URL + "?status=pending&ordering=-created_at"

    client.force_authenticate(user=shopowner)
    res = client.get(url)

    assert res.status_code == status.HTTP_200_OK
    results = res.data["data"]["results"]
    returned_ids = [order["id"] for order in results]

    assert returned_ids == [str(order2.id), str(order1.id)]


def test_get_all_shop_orders_ordered_by_multiple_parameters(
    client,
    shopowner,
    order_group_factory,
    order_factory
):
    """
    Test getting all shop orders with more than one ordering
    values.
    """
    shop = shopowner.owned_shop
    group = order_group_factory()

    order1 = order_factory(group=group, shop=shop, status="SHIPPED")
    order2 = order_factory(group=group, shop=shop, status="PROCESSING")
    order3 = order_factory(group=group, shop=shop, status="PENDING")
    order4 = order_factory(group=group, shop=shop, status="PENDING")
    order5 = order_factory(group=group, shop=shop, status="PROCESSING")

    url = GET_SHOP_ORDERS_URL + "?ordering=status,created_at"
    client.force_authenticate(user=shopowner)
    res = client.get(url)

    assert res.status_code == status.HTTP_200_OK
    results = res.data["data"]["results"]
    returned_ids = [order["id"] for order in results]
    assert returned_ids == [
        str(order3.id),
        str(order4.id),
        str(order2.id),
        str(order5.id),
        str(order1.id)
    ]


def test_get_all_shop_orders_ordered_by_invalid_ordering_parameter(
    client,
    shopowner,
    order_group_factory,
    order_factory
):
    """
    Test getting shop orders with invalid ordering query parameter.
    Test that it resolves to default.
    """

    shop = shopowner.owned_shop
    group = order_group_factory()

    order1 = order_factory(group=group, shop=shop, status="SHIPPED")
    order2 = order_factory(group=group, shop=shop, status="PENDING")
    order3 = order_factory(group=group, shop=shop, status="PROCESSING")

    url = GET_SHOP_ORDERS_URL + "?ordering=invalid"
    client.force_authenticate(user=shopowner)
    res = client.get(url)

    assert res.status_code == status.HTTP_200_OK
    results = res.data["data"]["results"]
    returned_ids = [order["id"] for order in results]
    assert returned_ids == [
        str(order2.id),
        str(order3.id),
        str(order1.id)
    ]


# ======================================================
# TEST GET A SPECIFIC SHOP ORDER
# ======================================================
@pytest.mark.parametrize(
    "user_type",
    ["shopowner", "shop_staff"],
    ids=["shopowner", "shop_staff"]
)
def test_get_shop_order(client,
                        populated_order_group_factory,
                        user_type,
                        all_users):
    """
    Test getting a specific shop order.
    """
    user = all_users[user_type]
    if user.shop:
        shop = user.shop
    else:
        shop = user.owned_shop

    group = populated_order_group_factory(shop=shop)

    order = group.orders.first()

    url = reverse("shop-order", args=[order.id])
    client.force_authenticate(user=user)
    res = client.get(url)

    assert res.status_code == status.HTTP_200_OK
    assert res.data["status"] == "success"
    assert res.data["message"] == "Order retrieved successfully."

    data = res.data["data"]
    expected_fields = [
        "id", "shipping", "items",
        "status", "total_amount",
        "is_paid", "shop_name",
        "is_delivered", "is_picked_up",
        "created_at", "delivery_date",
        "paid_at", "processing_at",
        "shipped_at", "completed_at",
        "cancelled_at"
    ]
    assert all(field in data for field in expected_fields)

    shipping = data["shipping"]
    expected_shipping_fields = [
        "full_name", "telephone",
        "street_address", "city",
        "state", "country",
        "postal_code"
    ]
    assert all(field in shipping for field in expected_shipping_fields)

    items = data["items"][0]
    expected_item_fields = [
        "id", "product_name",
        "product_description",
        "quantity", "price"
    ]
    assert all(field in items for field in expected_item_fields)


def test_get_shop_order_counts(client,
                               shopowner,
                               populated_order_group_factory):
    """
    Test the order has all the order items
    """
    shop = shopowner.owned_shop
    group = populated_order_group_factory(shop=shop,
                                          items_per_order=5)

    order = group.orders.first()

    url = reverse("shop-order", args=[order.id])
    client.force_authenticate(user=shopowner)
    res = client.get(url)

    assert res.status_code == status.HTTP_200_OK
    assert res.data["status"] == "success"
    assert res.data["message"] == "Order retrieved successfully."

    data = res.data["data"]
    assert len(data["items"]) == 5


def test_get_shop_order_by_customer(client,
                                    customer,
                                    shopowner_factory,
                                    populated_order_group_factory):
    """
    test customer cannot get shop order.
    """
    shop = shopowner_factory().owned_shop
    group = populated_order_group_factory(shop=shop)
    order = group.orders.first()

    url = reverse("shop-order", args=[order.id])
    client.force_authenticate(user=customer)
    res = client.get(url)

    assert res.status_code == status.HTTP_403_FORBIDDEN

    data = res.data
    assert data["status"] == "error"
    assert data["code"] == "forbidden"
    expected_msg = "You do not have permission to perform this action."
    assert data["message"] == expected_msg


@pytest.mark.parametrize(
    "user_type",
    ["shopowner", "shop_staff"],
    ids=["shopowner", "shop_staff"]
)
def test_get_shop_order_by_different_shop_staff(
    client,
    shopowner_factory,
    populated_order_group_factory,
    all_users,
    user_type
):
    """
    Test getting shop order by a different shopowner or
    shop staff.
    """
    shop = shopowner_factory().owned_shop
    user = all_users[user_type]
    group = populated_order_group_factory(shop=shop)
    order = group.orders.first()

    url = reverse("shop-order", args=[order.id])
    client.force_authenticate(user=user)
    res = client.get(url)

    assert res.status_code == status.HTTP_404_NOT_FOUND
    assert res.data["status"] == "error"
    assert res.data["code"] == "not_found"
    assert res.data["message"] == "No order matching the given ID found."


def test_get_shop_order_with_non_existent_order_id(
    client,
    shopowner
):
    """
    Test getting shop order with non-existent order id.
    """
    url = reverse("shop-order", args=[uuid.uuid4()])
    client.force_authenticate(user=shopowner)
    res = client.get(url)

    assert res.status_code == status.HTTP_404_NOT_FOUND
    assert res.data["status"] == "error"
    assert res.data["code"] == "not_found"
    assert res.data["message"] == "No order matching the given ID found."


def test_get_shop_order_with_invalid_uuid(
    client,
    shopowner
):
    """
    Test getting shop order with invalid order id.
    """
    url = reverse("shop-order", args=["invalid-uuid"])
    client.force_authenticate(user=shopowner)
    res = client.get(url)

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data["status"] == "error"
    assert res.data["code"] == "invalid_uuid"
    assert res.data["message"] == "Invalid order id."


def test_get_shop_order_by_unauthenticated_user(
    client,
    populated_order_group_factory
):
    """
    Test getting shop order by unauthenticated user fails.
        - Test with no credentials provided and with invalid
          access token.
    """
    group = populated_order_group_factory()
    order = group.orders.first()
    url = reverse("shop-order", args=[order.id])
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
