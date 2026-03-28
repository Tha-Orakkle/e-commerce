from decimal import Decimal
from django.urls import reverse
from rest_framework import status

from order.utils.orders import create_orders_from_cart


def assert_dict_matches(actual, expected):
    for k, v in expected.items():
        assert actual[k] == v


CHECKOUT_URL = reverse('checkout')

def test_checkout_success_single_shop(client, mocker, create_cart_items, customer, shipping_address_factory, shopowner):
    """
    Test successful checkout process.
        - Given a customer with items in their cart from a single shop and a valid shipping address
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
    spy = mocker.patch(
        'order.api.v1.routes.checkout.create_orders_from_cart',
        wraps=create_orders_from_cart
    )
    
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
    spy.assert_called_once()

    # args = spy.call_args[1]
    expected_args = spy.call_args.kwargs
    assert expected_args['user'] == customer
    assert expected_args['shipping_address'] == address
    assert expected_args['fulfillment_method'] == payload['fulfillment_method']
    assert expected_args['payment_method'] == payload['payment_method']
    assert expected_args['cart_items'] is not None
    assert len(expected_args['cart_items']) == cart.items.count()
    
    # order_group assertions
    assert 'id' in res_data
    expected_core = {
        'status': 'PENDING',
        'payment_method': payload['payment_method'],
        'fulfillment_method': payload['fulfillment_method'],
        'email': customer.email,
        'full_name': f"{customer.profile.first_name} {customer.profile.last_name}",
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
    
def test_checkout_success_multiple_shops(client, mocker, create_cart_items, customer, shipping_address_factory, shopowner_factory):
    """
    Test successful checkout process with items from multiple shops.
        - Given a customer with items in their cart from multiple shops and a valid shipping address
    """
    NUM_SHOPS = 3
    NUM_ITEMS = 6
    QUANTITY = 10

    cart = customer.cart

    assert customer.order_groups.count() == 0
    assert cart.items.count() == 0

    address = shipping_address_factory(user=customer)
    shops = [shopowner_factory().owned_shop for _ in range(NUM_SHOPS)]
    expected_shop_ids = set(str(shop.id) for shop in shops)
    
    total, _ = create_cart_items(
        cart, shops=shops,
        num_items=NUM_ITEMS, quantity=QUANTITY
    )
    
    for shop in shops:
        assert shop.orders.count() == 0
        assert cart.items.filter(product__shop=shop).count() == NUM_ITEMS // NUM_SHOPS

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
