from decimal import Decimal
from django.urls import reverse
from rest_framework import status

import uuid
import pytest

from order.services.checkout import CheckoutService


def assert_dict_matches(actual, expected):
    for k, v in expected.items():
        assert actual[k] == v


CHECKOUT_URL = reverse('checkout')


def test_checkout_success_single_shop(client,
                                      mocker,
                                      create_cart_items,
                                      customer,
                                      shipping_address_factory,
                                      shopowner):
    """
    Test successful checkout process.
        - Given a customer with items in their cart from a single
        shop and a valid shipping address
    """
    NUM_ITEMS = 1
    ITEM_QUANTITY = 10

    cart = customer.cart

    assert customer.order_groups.count() == 0
    assert cart.items.count() == 0

    address = shipping_address_factory(user=customer)
    total, products = create_cart_items(
        cart, shops=[shopowner.owned_shop],
        num_items=NUM_ITEMS, quantity=ITEM_QUANTITY
    )

    assert cart.items.count() == 1

    payload = {
        'shipping_address': address.id,
        'fulfillment_method': 'DELIVERY',
        'payment_method': 'CASH'
    }
    client.force_authenticate(user=customer)

    init_spy = mocker.spy(CheckoutService, "__init__")
    execute_spy = mocker.spy(CheckoutService, "execute")

    res = client.post(CHECKOUT_URL, payload, format='json')
    data = res.data
    assert 'data' in res.data
    res_data = data['data']

    # response assertions
    assert res.status_code == status.HTTP_201_CREATED
    assert data['status'] == "success"
    assert data['message'] == "Checkout successful. Orders have been created."

    assert customer.order_groups.count() == 1

    # spy assertions
    init_spy.assert_called_once()
    execute_spy.assert_called_once()

    # args = spy.call_args[1]
    expected_args = init_spy.call_args.kwargs
    assert expected_args['user'] == customer
    assert expected_args['shipping_address'] == address
    assert expected_args['fulfillment_method'] == payload['fulfillment_method']
    assert expected_args['payment_method'] == payload['payment_method']
    assert expected_args['cart_items'] is not None
    assert len(expected_args['cart_items']) == cart.items.count()

    # order_group assertions
    assert 'id' in res_data
    fn = customer.profile.first_name
    ln = customer.profile.last_name
    expected_core = {
        'status': 'PENDING',
        'payment_method': payload['payment_method'],
        'fulfillment_method': payload['fulfillment_method'],
        'email': customer.email,
        'full_name': f"{fn} {ln}",
    }
    assert_dict_matches(res_data, expected_core)

    # shipping address assertions
    expected_shipping = {
        'shipping_full_name': address.full_name,
        'shipping_telephone': str(address.telephone),
        'shipping_street_address': address.street_address,
        'shipping_city': address.city.name,
        'shipping_state': address.city.state.name,
        'shipping_country': address.city.state.country.name,
        'shipping_postal_code': address.postal_code
    }
    assert_dict_matches(res_data, expected_shipping)

    # amount assertions
    delivery_fee = Decimal(res_data['delivery_fee'])
    total_amount = Decimal(res_data['total_amount'])
    assert total_amount == Decimal(total) + delivery_fee

    # orders assertions
    assert res_data['orders'] is not None
    assert len(res_data['orders']) == NUM_ITEMS

    order = res_data['orders'][0]
    assert order['id'] is not None
    assert order['created_at'] is not None
    assert Decimal(order['total_amount']) == total

    expected_order = {
        'status': 'PENDING',
        'is_paid': False,
        'is_delivered': False,
        'shop_name': shopowner.owned_shop.name,
        'is_picked_up': False,
        'delivery_date': None,
        'paid_at': None,
        'processing_at': None,
        'shipped_at': None,
        'completed_at': None,
        'cancelled_at': None
    }

    assert_dict_matches(order, expected_order)

    # order shop assertions
    shop = order['shop']
    assert shop['id'] == str(shopowner.owned_shop.id)
    assert shop['name'] == shopowner.owned_shop.name

    # order items assertions
    items = order['items']
    assert items is not None
    assert len(items) == NUM_ITEMS
    item = items[0]
    assert item['id'] is not None
    assert item['quantity'] == ITEM_QUANTITY
    assert item['product_name'] == products[0].name
    assert item['product_description'] == products[0].description
    assert Decimal(item['price']) == Decimal(str(products[0].price))

    # cart assertions
    assert cart.items.count() == 0


def test_checkout_success_multiple_shops(client,
                                         create_cart_items,
                                         customer,
                                         shipping_address_factory,
                                         shopowner_factory):
    """
    Test successful checkout process with items from multiple shops.
        - Given a customer with items in their cart from multiple shops
        and a valid shipping address
    """
    NUM_SHOPS = 3
    NUM_ITEMS = 6
    ITEM_QUANTITY = 10

    cart = customer.cart

    assert customer.order_groups.count() == 0
    assert cart.items.count() == 0

    address = shipping_address_factory(user=customer)
    shops = [shopowner_factory().owned_shop for _ in range(NUM_SHOPS)]
    expected_shop_ids = set(str(shop.id) for shop in shops)

    total, _ = create_cart_items(
        cart, shops=shops,
        num_items=NUM_ITEMS, quantity=ITEM_QUANTITY
    )

    for shop in shops:
        assert shop.orders.count() == 0
        count = cart.items.filter(product__shop=shop).count()
        assert count == NUM_ITEMS // NUM_SHOPS

    assert cart.items.count() == NUM_ITEMS

    payload = {
        'shipping_address': address.id,
        'fulfillment_method': 'DELIVERY',
        'payment_method': 'CASH'
    }
    client.force_authenticate(user=customer)

    res = client.post(CHECKOUT_URL, payload, format='json')
    data = res.data
    assert 'data' in res.data
    res_data = data['data']

    # response assertions
    assert res.status_code == status.HTTP_201_CREATED
    assert data['status'] == "success"
    assert data['message'] == "Checkout successful. Orders have been created."

    assert customer.order_groups.count() == 1
    assert cart.items.count() == 0
    for shop in shops:
        # Each shop should receive the order items combined into one order
        assert shop.orders.count() == 1

    # order_group assertions
    orders = res_data['orders']
    assert len(orders) == NUM_SHOPS
    order_totals_sum = 0
    shop_ids_in_response = set()
    for order in orders:
        items = order['items']
        shop_ids_in_response.add(order['shop']['id'])

        assert len(items) == NUM_ITEMS // NUM_SHOPS

        computed_total = sum(
            Decimal(item['price']) * item['quantity'] for item in items
        )

        assert Decimal(order['total_amount']) == computed_total

        order_totals_sum += computed_total

    assert expected_shop_ids == shop_ids_in_response

    # money assertions
    delivery_fee = Decimal(res_data['delivery_fee'])
    total_amount = Decimal(res_data['total_amount'])
    assert total_amount == Decimal(total) + delivery_fee
    assert total_amount == order_totals_sum + delivery_fee


def test_inventory_is_updated_after_checkout(client,
                                             customer,
                                             shipping_address_factory,
                                             shopowner_factory,
                                             create_cart_items):
    """
    Test that the product inventory is updated correctly after checkout.
        - Given a customer with items in their cart, when they checkout, the
        inventory of the products should be reduced by the quantity ordered.
    """
    ITEM_QUANTITY = 10
    cart = customer.cart
    shops = [shopowner_factory().owned_shop for _ in range(3)]
    _, products = create_cart_items(cart,
                                    shops=shops,
                                    num_items=6,
                                    quantity=ITEM_QUANTITY)
    initial_inventories = {product.id: product.stock for product in products}

    address = shipping_address_factory(user=customer)
    payload = {
        'shipping_address': address.id,
        'fulfillment_method': 'DELIVERY',
        'payment_method': 'CASH'
    }
    client.force_authenticate(user=customer)

    res = client.post(CHECKOUT_URL, payload, format='json')

    # response assertions
    assert res.status_code == status.HTTP_201_CREATED
    assert res.data['status'] == "success"
    msg = res.data['message']
    assert msg == "Checkout successful. Orders have been created."

    # inventory assertions
    for product in products:
        product.refresh_from_db()
        expected_stock = initial_inventories[product.id] - ITEM_QUANTITY
        assert product.stock == expected_stock


def test_checkout_atomic_rolls_back_on_failure(client,
                                               mocker,
                                               create_cart_items,
                                               customer,
                                               shipping_address_factory,
                                               shopowner_factory):
    """
    Test that the checkout process rolls back if an error occurs
    during order creation.
        - Given a customer with items in their cart, when they
        checkout and an error occurs during order creation,
        no orders should be created and the cart should remain unchanged.
    """
    cart = customer.cart
    address = shipping_address_factory(user=customer)

    shops = [shopowner_factory().owned_shop for _ in range(2)]

    _, products = create_cart_items(cart, shops=shops)
    initial_cart_count = cart.items.count()
    initial_inventories_count = {product.id: product.stock
                                 for product in products}

    assert customer.order_groups.count() == 0

    payload = {
        'shipping_address': address.id,
        'fulfillment_method': 'DELIVERY',
        'payment_method': 'CASH'
    }

    client.force_authenticate(user=customer)

    mocker.patch(
        'order.services.checkout.Inventory.objects.bulk_update',
        side_effect=Exception('DB failure')
    )

    with pytest.raises(Exception):
        client.post(CHECKOUT_URL, data=payload, format='json')

    # Verify rollback
    assert customer.order_groups.count() == 0
    for shop in shops:
        assert shop.orders.count() == 0

    # cart is not cleared
    assert cart.items.count() == initial_cart_count

    # inventory does not change
    for product in products:
        product.refresh_from_db()
        assert product.stock == initial_inventories_count[product.id]


def test_checkout_fails_with_invalid_cart_product_unavailable(
    client,
    customer,
    create_cart_items,
    shopowner,
    shipping_address_factory
):
    """
    Test that checkout fails if the cart contains an unavailable product.
        - Given a customer with an unavailable product in their cart,
        when they checkout, the checkout process should fail with
        an appropriate error message.
    """
    cart = customer.cart
    _, products = create_cart_items(
        cart, shops=[shopowner.owned_shop], num_items=1)

    item = cart.items.first()
    p = products[0]
    p.is_active = False
    p.save(update_fields=['is_active'])

    address = shipping_address_factory(user=customer)

    payload = {
        'shipping_address': address.id,
        'fulfillment_method': 'DELIVERY',
        'payment_method': 'CASH'
    }

    client.force_authenticate(user=customer)

    res = client.post(CHECKOUT_URL, data=payload, format='json')

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['message'] == "Cart contains invalid items."
    assert len(res.data['errors']) == 1
    error = res.data['errors'][0]
    assert error['id'] is not None
    assert error['status'] == 'unavailable'
    assert error['quantity'] == item.quantity
    assert error['issue'] == "Product no longer available"
    assert error['product'] is None


def test_checkout_fails_with_invalid_cart_product_out_of_stock(
    client,
    customer,
    create_cart_items,
    shopowner,
    shipping_address_factory
):
    """
    Test that checkout fails if the cart contains a product
    that is out of stock.
        - Given a customer with a product that is out of stock
        in their cart, when they checkout, the checkout process
        should fail with an appropriate error message.
    """
    cart = customer.cart
    _, products = create_cart_items(
        cart, shops=[shopowner.owned_shop], num_items=1)

    item = cart.items.first()
    p = products[0]
    p.inventory.subtract(qty=p.stock, handle='test')

    address = shipping_address_factory(user=customer)

    payload = {
        'shipping_address': address.id,
        'fulfillment_method': 'DELIVERY',
        'payment_method': 'CASH'
    }

    client.force_authenticate(user=customer)

    res = client.post(CHECKOUT_URL, data=payload, format='json')

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['message'] == "Cart contains invalid items."
    assert len(res.data['errors']) == 1
    error = res.data['errors'][0]
    assert error['id'] is not None
    assert error['status'] == 'out_of_stock'
    assert error['quantity'] == item.quantity
    assert error['issue'] == "Product out of stock"
    assert error['product'] is not None
    err_product = error['product']
    fields = [
        'id', 'name', 'description', 'shop',
        'created_at', 'updated_at'
    ]
    assert all(err_product[f] is not None for f in fields)


def test_checkout_fails_with_invalid_cart_product_insufficient_stock(
    client,
    customer,
    create_cart_items,
    shopowner,
    shipping_address_factory
):
    """
    Test that checkout fails if the cart contains a product with
    insufficient stock.
        - Given a customer with a product with insufficient stock
        in their cart, when they checkout, the checkout process
        should fail with an appropriate error message.
    """
    cart = customer.cart
    _, products = create_cart_items(
        cart, shops=[shopowner.owned_shop], num_items=1)

    item = cart.items.first()
    p = products[0]
    qty = (p.stock - item.quantity) + 1
    p.inventory.subtract(qty=qty, handle='test')

    address = shipping_address_factory(user=customer)

    payload = {
        'shipping_address': address.id,
        'fulfillment_method': 'DELIVERY',
        'payment_method': 'CASH'
    }

    client.force_authenticate(user=customer)

    res = client.post(CHECKOUT_URL, data=payload, format='json')

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['message'] == "Cart contains invalid items."
    assert len(res.data['errors']) == 1
    error = res.data['errors'][0]
    assert error['id'] is not None
    assert error['status'] == 'insufficient_stock'
    assert error['quantity'] == item.quantity
    assert error['issue'] == f"Only {p.stock} left in stock"
    assert error['product'] is not None
    err_product = error['product']
    fields = [
        'id', 'name', 'description', 'shop',
        'created_at', 'updated_at'
    ]
    assert all(err_product[f] is not None for f in fields)


def test_checkout_fails_with_invalid_cart(client,
                                          customer,
                                          create_cart_items,
                                          shipping_address_factory,
                                          shopowner):
    """
    Test that checkout fails with multiple cart item errors
    and response returns only products with issues.
    """
    cart = customer.cart
    address = shipping_address_factory(user=customer)

    _, products = create_cart_items(
        cart, shops=[shopowner.owned_shop], num_items=4)

    # make first product unavailable
    p1 = products[0]
    p1.is_active = False
    p1.save(update_fields=['is_active'])

    # make second product out of stock
    p2 = products[1]
    p2.inventory.subtract(qty=p2.stock, handle='test')

    # make third product insufficient stock
    p3 = products[2]
    qty = (p3.stock - cart.items.filter(product=p3).first().quantity) + 1
    p3.inventory.subtract(qty=qty, handle='test')

    payload = {
        'shipping_address': address.id,
        'fulfillment_method': 'DELIVERY',
        'payment_method': 'CASH'
    }

    client.force_authenticate(user=customer)
    res = client.post(CHECKOUT_URL, data=payload, format='json')

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['message'] == "Cart contains invalid items."
    assert len(res.data['errors']) == 3
    error_statuses = {error['status'] for error in res.data['errors']}
    assert error_statuses == {
        'unavailable',
        'out_of_stock',
        'insufficient_stock'
    }


def test_checkout_fails_with_no_cart_items(client,
                                           customer,
                                           shipping_address_factory):
    """
    Test that checkout fails if the cart has no items.
        - Given a customer with an empty cart, when they checkout,
        the checkout process should fail with an appropriate error message.
    """
    address = shipping_address_factory(user=customer)

    payload = {
        'shipping_address': address.id,
        'fulfillment_method': 'DELIVERY',
        'payment_method': 'CASH'
    }

    client.force_authenticate(user=customer)
    res = client.post(CHECKOUT_URL, data=payload, format='json')

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "empty_cart"
    assert res.data['message'] == "Cart is empty."


def test_checkout_fails_with_no_cart(client,
                                     customer_no_cart,
                                     shipping_address_factory):
    """
    Test that checkout fails if the user has no cart.
        - Given a customer with no cart, when they checkout,
        the checkout process should fail with an appropriate error message.
    """
    address = shipping_address_factory(user=customer_no_cart)

    payload = {
        'shipping_address': address.id,
        'fulfillment_method': 'DELIVERY',
        'payment_method': 'CASH'
    }

    client.force_authenticate(user=customer_no_cart)
    res = client.post(CHECKOUT_URL, data=payload, format='json')

    assert res.status_code == status.HTTP_404_NOT_FOUND
    assert res.data['status'] == "error"
    assert res.data['code'] == "not_found"
    assert res.data['message'] == "No cart found for the user."


# ===================================================
# Test Checkout with incorrect shipping address
# ===================================================
def test_checkout_fails_without_shipping_address(client, customer):
    """
    Test when no shipping address is passed.
    """

    payload = {
        'fulfillment_method': 'DELIVERY',
        'payment_method': 'CASH'
    }

    client.force_authenticate(user=customer)
    res = client.post(CHECKOUT_URL, data=payload, format='json')

    assert res.status_code == status.HTTP_400_BAD_REQUEST

    data = res.data
    assert data['status'] == "error"
    assert data['code'] == "validation_error"
    assert data['message'] == "Checkout failed. Invalid request data."
    assert "errors" in data

    errors = data["errors"]
    assert "shipping_address" in errors
    assert errors["shipping_address"] == ["This field is required."]


@pytest.mark.parametrize(
    "invalid_shipping",
    ["string", "23456", "12332.43", ""],
    ids=["string", "int", "float", "blank"]
)
def test_checkout_fails_with_invalid_shipping_address(client,
                                                      customer,
                                                      invalid_shipping):
    """
    Test that chackout fails when a non-uuid value is
    passed as the shipping adddress.
    """
    payload = {
        "shipping_address": invalid_shipping,
        "fulfillment_method": "DELIVERY",
        "payment_method": "CASH"
    }

    client.force_authenticate(user=customer)

    res = client.post(CHECKOUT_URL, data=payload, format="json")

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    data = res.data
    assert data['status'] == "error"
    assert data['code'] == "validation_error"
    assert data['message'] == "Checkout failed. Invalid request data."
    assert "errors" in data
    errors = data["errors"]
    assert errors["shipping_address"] == ["Must be a valid UUID."]


@pytest.mark.parametrize(
    "invalid_shipping",
    [uuid.uuid4(), True, False],
    ids=["invalid_uuid", "boolean_true", "boolean_true"]
)
def test_checkout_fails_when_shipping_address_non_existent(client,
                                                           customer,
                                                           invalid_shipping):
    """
    Test when the shipping address uuid is not associated with a
    shipping address.
    """
    payload = {
        "shipping_address": invalid_shipping,
        "fulfillment_method": "DELIVERY",
        "payment_method": "CASH"
    }
    client.force_authenticate(user=customer)

    res = client.post(CHECKOUT_URL, data=payload, format="json")

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    data = res.data
    assert data['status'] == "error"
    assert data['code'] == "validation_error"
    assert data['message'] == "Checkout failed. Invalid request data."
    assert "errors" in data
    errors = data["errors"]
    expected_error = [
        "No shipping address matching the given ID found."
    ]
    assert errors["shipping_address"] == expected_error


# ===================================================
# TEST CHECKOUT PAYMENT METHOD INPUTS
# ===================================================
@pytest.mark.parametrize(
    "payment_method",
    ["cash", "digital"],
    ids=["cash", "digital"]
)
def test_checkout_passes_with_lower_case_payment_method(
    client,
    customer,
    shopowner,
    shipping_address_factory,
    create_cart_items,
    payment_method
):
    """
    Test that checkout passes payment_method passed as a lower case.
    """
    cart = customer.cart
    address = shipping_address_factory(user=customer)
    create_cart_items(cart, shops=[shopowner.owned_shop], num_items=1)

    assert cart.items.count() == 1

    payload = {
        "shipping_address": address.id,
        "fulfillment_method": "DELIVERY",
        "payment_method": payment_method
    }
    client.force_authenticate(user=customer)

    res = client.post(CHECKOUT_URL, data=payload, format="json")
    assert res.status_code == status.HTTP_201_CREATED
    data = res.data

    assert data["status"] == "success"
    assert data["data"]["payment_method"] == payment_method.upper()


def test_checkout_fails_without_payment_method(client,
                                               customer,
                                               shipping_address_factory):
    """
    Test when no payment method is passed.
    """

    address = shipping_address_factory(user=customer)

    payload = {
        "shipping_address": address.id,
        "fulfillment_method": "DELIVERY",
    }

    client.force_authenticate(user=customer)
    res = client.post(CHECKOUT_URL, data=payload, format='json')

    assert res.status_code == status.HTTP_400_BAD_REQUEST

    data = res.data
    assert data['status'] == "error"
    assert data['code'] == "validation_error"
    assert data['message'] == "Checkout failed. Invalid request data."
    assert "errors" in data

    errors = data["errors"]
    assert "payment_method" in errors
    assert errors["payment_method"] == ["This field is required."]


@pytest.mark.parametrize(
    "blank_payment",
    ["", "   "],
    ids=["blank", "spaced"]
)
def test_checkout_fails_with_blank_payment_method(client,
                                                  customer,
                                                  shipping_address_factory,
                                                  blank_payment):
    """
    Test checkout fails when the payment method passed is blank.
    """

    address = shipping_address_factory(user=customer)

    payload = {
        "shipping_address": address.id,
        "fulfillment_method": "DELIVERY",
        "payment_method": blank_payment
    }

    client.force_authenticate(user=customer)
    res = client.post(CHECKOUT_URL, data=payload, format='json')

    assert res.status_code == status.HTTP_400_BAD_REQUEST

    data = res.data
    assert data['status'] == "error"
    assert data['code'] == "validation_error"
    assert data['message'] == "Checkout failed. Invalid request data."
    assert "errors" in data

    errors = data["errors"]
    assert "payment_method" in errors
    assert errors["payment_method"] == ["This field may not be blank."]


@pytest.mark.parametrize(
    "invalid_payment",
    [True, False],
    ids=["boolean_true", "boolean_false"]
)
def test_checkout_fails_with_boolean_payment_method(
    client,
    customer,
    shipping_address_factory,
    invalid_payment
):
    """
    Test that checkout fails when a boolean datatype is passed
    as payment method.
    """
    address = shipping_address_factory(user=customer)
    payload = {
        "shipping_address": address.id,
        "fulfillment_method": "DELIVERY",
        "payment_method": invalid_payment
    }
    client.force_authenticate(user=customer)

    res = client.post(CHECKOUT_URL, data=payload, format="json")

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    data = res.data
    assert data['status'] == "error"
    assert data['code'] == "validation_error"
    assert data['message'] == "Checkout failed. Invalid request data."
    assert "errors" in data

    errors = data["errors"]
    assert "payment_method" in errors
    assert errors["payment_method"] == ["Not a valid string."]


@pytest.mark.parametrize(
    "invalid_payment",
    [123456, 123.43, "invalid_method"],
    ids=["int", "float", "invalid_method"])
def test_checkout_fails_with_invalid_payment_method(client,
                                                    customer,
                                                    shipping_address_factory,
                                                    invalid_payment):
    """
    Test that checkout fails when invalid data passed as payment method.
    """
    address = shipping_address_factory(user=customer)
    payload = {
        "shipping_address": address.id,
        "fulfillment_method": "DELIVERY",
        "payment_method": invalid_payment
    }
    client.force_authenticate(user=customer)

    res = client.post(CHECKOUT_URL, data=payload, format="json")

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    data = res.data
    assert data['status'] == "error"
    assert data['code'] == "validation_error"
    assert data['message'] == "Checkout failed. Invalid request data."
    assert "errors" in data

    errors = data["errors"]
    assert "payment_method" in errors
    expected_error = [
        "The payment method must be either 'CASH' or 'DIGITAL'."
    ]
    assert errors["payment_method"] == expected_error


# ===================================================
# TEST CHECKOUT FULFILLMENT METHOD INPUTS
# ===================================================
@pytest.mark.parametrize(
    "fulfillment_method",
    ["pickup", "delivery"],
    ids=["pickup", "delivery"]
)
def test_checkout_passes_with_lower_case_fulfillment_method(
    client,
    customer,
    shopowner,
    shipping_address_factory,
    create_cart_items,
    fulfillment_method
):
    """
    Test that checkout passes fulfillment_method passed as a lower case.
    """
    cart = customer.cart
    address = shipping_address_factory(user=customer)
    create_cart_items(cart, shops=[shopowner.owned_shop], num_items=1)

    assert cart.items.count() == 1

    payload = {
        "shipping_address": address.id,
        "fulfillment_method": fulfillment_method,
        "payment_method": "CASH"
    }
    client.force_authenticate(user=customer)

    res = client.post(CHECKOUT_URL, data=payload, format="json")
    assert res.status_code == status.HTTP_201_CREATED
    data = res.data

    assert data["status"] == "success"
    assert data["data"]["fulfillment_method"] == fulfillment_method.upper()


def test_checkout_fails_without_fulfillment_method(client,
                                                   customer,
                                                   shipping_address_factory):

    """
    Test when no fulfimment_method is passed.
    """

    address = shipping_address_factory(user=customer)

    payload = {
        "shipping_address": address.id,
        "payment_method": "CASH",
    }

    client.force_authenticate(user=customer)
    res = client.post(CHECKOUT_URL, data=payload, format='json')

    assert res.status_code == status.HTTP_400_BAD_REQUEST

    data = res.data
    assert data['status'] == "error"
    assert data['code'] == "validation_error"
    assert data['message'] == "Checkout failed. Invalid request data."
    assert "errors" in data

    errors = data["errors"]
    assert "fulfillment_method" in errors
    assert errors["fulfillment_method"] == ["This field is required."]


@pytest.mark.parametrize(
    "blank_fulfillment",
    ["", "   "],
    ids=["blank", "spaced"]
)
def test_checkout_fails_with_blank_fulfillment_method(
    client,
    customer,
    shipping_address_factory,
    blank_fulfillment
):
    """
    Test checkout fails when the fulfillment method passed is blank.
    """

    address = shipping_address_factory(user=customer)

    payload = {
        "shipping_address": address.id,
        "fulfillment_method": blank_fulfillment,
        "payment_method": "CASH"
    }

    client.force_authenticate(user=customer)
    res = client.post(CHECKOUT_URL, data=payload, format='json')

    assert res.status_code == status.HTTP_400_BAD_REQUEST

    data = res.data
    assert data['status'] == "error"
    assert data['code'] == "validation_error"
    assert data['message'] == "Checkout failed. Invalid request data."
    assert "errors" in data

    errors = data["errors"]
    assert "fulfillment_method" in errors
    assert errors["fulfillment_method"] == ["This field may not be blank."]


@pytest.mark.parametrize(
    "invalid_fulfillment",
    [True, False],
    ids=["boolean_true", "boolean_false"]
)
def test_checkout_fails_with_boolean_payment_method(
    client,
    customer,
    shipping_address_factory,
    invalid_fulfillment
):
    """
    Test that checkout fails when a boolean datatype is passed
    as fulfillment method.
    """
    address = shipping_address_factory(user=customer)
    payload = {
        "shipping_address": address.id,
        "fulfillment_method": invalid_fulfillment,
        "payment_method": "CASH"
    }
    client.force_authenticate(user=customer)

    res = client.post(CHECKOUT_URL, data=payload, format="json")

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    data = res.data
    assert data['status'] == "error"
    assert data['code'] == "validation_error"
    assert data['message'] == "Checkout failed. Invalid request data."
    assert "errors" in data

    errors = data["errors"]
    assert "fulfillment_method" in errors
    assert errors["fulfillment_method"] == ["Not a valid string."]


@pytest.mark.parametrize(
    "invalid_fulfillment",
    [123456, 123.43, "invalid_method"],
    ids=["int", "float", "invalid_method"])
def test_checkout_fails_with_invalid_fulfillment_method(
    client,
    customer,
    shipping_address_factory,
    invalid_fulfillment
):
    """
    Test that checkout fails when invalid data passed as fulfillment method.
    """
    address = shipping_address_factory(user=customer)
    payload = {
        "shipping_address": address.id,
        "fulfillment_method": invalid_fulfillment,
        "payment_method": "CASH"
    }
    client.force_authenticate(user=customer)

    res = client.post(CHECKOUT_URL, data=payload, format="json")

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    data = res.data
    assert data['status'] == "error"
    assert data['code'] == "validation_error"
    assert data['message'] == "Checkout failed. Invalid request data."
    assert "errors" in data

    errors = data["errors"]
    assert "fulfillment_method" in errors
    expected_error = [
        "The fulfillment method must be either 'PICKUP' or 'DELIVERY'."
    ]
    assert errors["fulfillment_method"] == expected_error
