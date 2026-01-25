from django.urls import reverse
from rest_framework import status

from cart.tests.fixtures import fill_customer_cart


# =============================================================================
# TEST GET ALL CART ITEMS
# =============================================================================

CART_ITEMS_LIST_URL = reverse('cart-detail')


def test_get_all_cart_items(client, customer, shopowner, product_factory):
    """
    Test get all cart items.
    """

    cart = fill_customer_cart(
        cart=customer.cart,
        shop=shopowner.owned_shop,
        product_factory=product_factory,
        count=2
    )

    client.force_authenticate(user=customer)
    res = client.get(CART_ITEMS_LIST_URL)

    assert res.status_code == status.HTTP_200_OK
    assert res.data['message'] == "Cart retrieved successfully."
    assert 'data' in res.data
    data = res.data['data']
    assert data.get('is_valid') is True
    assert 'items' in data
    items = res.data['data']['items']
    assert cart.items.count() == len(items)
    item = items[0]
    fields = ['id', 'quantity', 'stock', 'status', 'issue', 'product']
    assert all(f in item for f in fields)
    prd_fields = [
        'id', 'name', 'description',
        'price', 'shop', 'images',
        'created_at', 'updated_at'
    ]
    assert all(f in item['product'] for f in prd_fields)
    shop = item['product']['shop']
    assert 'owner' not in shop
    assert 'code' not in shop


def test_get_cart_items_when_some_items_are_invalid_returns_items_with_issues(
        client, customer, shopowner, product_factory):
    """
    Returns all cart items with their respective
    validation issues when the cart contains invalid items.
    """
    cart = fill_customer_cart(
        cart=customer.cart,
        shop=shopowner.owned_shop,
        product_factory=product_factory,
        count=4
    )
    item_1, item_2, item_3, item_4 = cart.items.all()

    # issue 1 - Product no longer available
    item_1.product.delete()

    # issue 2 - Out of stock
    prd = item_2.product
    prd.inventory.subtract(prd.stock)

    # issue 3 - Insufficient stock
    inv = item_3.product.inventory
    x = (inv.stock - item_3.quantity) + (item_3.quantity // 2)
    inv.subtract(x)

    client.force_authenticate(user=customer)
    res = client.get(CART_ITEMS_LIST_URL)

    assert res.status_code == status.HTTP_200_OK
    assert res.data['message'] == "Cart retrieved successfully."

    assert 'data' in res.data
    data = res.data['data']
    assert data['is_valid'] is False
    assert 'items' in data
    items = data['items']

    items_by_id = {i['id']: i for i in items}

    it_1 = items_by_id[item_1.id]
    it_2 = items_by_id[item_2.id]
    it_3 = items_by_id[item_3.id]
    it_4 = items_by_id[item_4.id]

    # test for issue 1
    assert it_1['quantity'] == item_1.quantity
    assert it_1['stock'] == 0
    assert it_1['status'] == "unavailable"
    assert it_1['issue'] == "Product no longer available"
    assert it_1['product'] is None

    # test for issue 2
    assert it_2['quantity'] == item_2.quantity
    assert it_2['stock'] == 0
    assert it_2['status'] == "out_of_stock"
    assert it_2['issue'] == "Product out of stock"
    assert it_2['product'] is not None

    # test for issue 3
    assert inv.stock < item_3.quantity
    assert it_3['quantity'] == item_3.quantity
    assert it_3['stock'] == inv.stock
    assert it_3['status'] == "insufficient_stock"
    assert it_3['issue'] == f"Only {inv.stock} left in stock"
    assert it_3['product'] is not None

    # test for last item - No issue
    assert it_4['quantity'] == item_4.quantity
    assert it_4['stock'] == item_4.product.stock
    assert it_4['status'] == "available"
    assert it_4['issue'] is None
    assert it_4['product'] is not None



def test_get_cart_items_by_user_without_cart(client, customer_no_cart):
    """
    Test get cart items for customer with no cart.
    """
    client.force_authenticate(user=customer_no_cart)
    res = client.get(CART_ITEMS_LIST_URL)
    
    assert res.status_code == status.HTTP_404_NOT_FOUND
    assert res.data['status'] == "error"
    assert res.data['code'] == "not_found"
    assert res.data['message'] == "No cart found for the user."
    
    
def test_get_cart_items_by_unauthenticated_user(client):
    """
    Test get cart items by unauthenticated user:
        - Test for without token and invalid token
    """
    res = client.get(CART_ITEMS_LIST_URL)
    
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.data['status'] == "error"
    assert res.data['code'] == "unauthorized"
    assert res.data['message'] == "Authentication credentials were not provided."

    client.cookies['access_token'] = "Invalid_access_token2445"
    res = client.get(CART_ITEMS_LIST_URL)
    
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.data['status'] == "error"
    assert res.data['code'] == "unauthorized"
    assert res.data['message'] == "Token is invalid or expired"

    
    