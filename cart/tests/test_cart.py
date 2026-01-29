from django.urls import reverse
from rest_framework import status

import pytest
import uuid

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


# =============================================================================
# TEST GET A SPECIFIC CART ITEM
# =============================================================================

def test_get_specific_cart_item(client, customer, shopowner, product_factory):
    """
    Test get a specific cart item.
    """

    cart = fill_customer_cart(
        cart=customer.cart,
        shop=shopowner.owned_shop,
        product_factory=product_factory,
        count=2
    )
    item = cart.items.first()

    url = reverse('cart-item-detail', args=[item.id])
    client.force_authenticate(user=customer)
    res = client.get(url)

    assert res.status_code == status.HTTP_200_OK
    assert res.data['message'] == "Cart item retrieved successfully."
    assert 'data' in res.data
    data = res.data['data']
    fields = ['id', 'product_name', 'quantity']
    assert all(f in data for f in fields)
    assert data['id'] == str(item.id)
    assert data['product_name'] == item.product_name
    assert data['quantity'] == item.quantity


def test_get_specific_cart_item_that_does_not_exist(client, customer):
    """
    Test get a specific cart item that does not exist.
    """
    url = reverse('cart-item-detail', args=[uuid.uuid4()])
    client.force_authenticate(user=customer)
    res = client.get(url)

    assert res.status_code == status.HTTP_404_NOT_FOUND
    assert res.data['status'] == "error"
    assert res.data['code'] == "not_found"
    assert res.data['message'] == "No item matching given ID found in cart."
    

def test_get_specific_cart_item_with_invalid_item_id(client, customer):
    """
    Test get a specific cart item with invalid cart item id.
    """
    url = reverse('cart-item-detail', args=['invalid-uuid'])
    client.force_authenticate(user=customer)
    res = client.get(url)
    
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "invalid_uuid"
    assert res.data['message'] == "Invalid cart item id."

    
def test_get_specific_cart_item_by_user_without_cart(client, customer_no_cart):
    """
    Test get a specific cart item for customer with no cart.
    """
    url = reverse('cart-item-detail', args=[uuid.uuid4()])
    client.force_authenticate(user=customer_no_cart)
    res = client.get(url)
    
    assert res.status_code == status.HTTP_404_NOT_FOUND
    assert res.data['status'] == "error"
    assert res.data['code'] == "not_found"
    assert res.data['message'] == "No cart found for the user."


def test_get_specific_cart_item_by_unauthenticated_user(client):
    """
    Test get a specific cart item by unauthenticated user:
        - Test for without token and invalid token
    """
    url = reverse('cart-item-detail', args=[uuid.uuid4()])
    res = client.get(url)
    
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.data['status'] == "error"
    assert res.data['code'] == "unauthorized"
    assert res.data['message'] == "Authentication credentials were not provided."

    client.cookies['access_token'] = "Invalid_access_token2445"
    res = client.get(url)
    
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.data['status'] == "error"
    assert res.data['code'] == "unauthorized"
    assert res.data['message'] == "Token is invalid or expired"


def test_get_specific_cart_item_by_non_customer_user(client, shopowner):
    """
    Test get a specific cart item by non-customer user.
    """
    url = reverse('cart-item-detail', args=[uuid.uuid4()])
    client.force_authenticate(user=shopowner)
    res = client.get(url)
    
    assert res.status_code == status.HTTP_403_FORBIDDEN
    assert res.data['status'] == "error"
    assert res.data['code'] == "forbidden"
    assert res.data['message'] == "You do not have permission to perform this action."


# =============================================================================
# TEST ADD ITEM TO CART
# =============================================================================

def test_add_item_to_cart(client, customer, inventory):
    """
    Test add item to cart.
    """
    url = CART_ITEMS_LIST_URL
    data = {
        'product_id': str(inventory.product.id),
        'quantity': 3
    }
    client.force_authenticate(user=customer)
    res = client.post(url, data=data, format='json')

    assert res.status_code == status.HTTP_200_OK
    assert res.data['message'] == "Item added to cart successfully."
    assert 'data' in res.data
    data = res.data['data']
    assert 'id' in data
    assert 'items' in data
    items = data['items']
    assert len(items) == 1
    item = items[0]
    assert item['product_name'] == inventory.product.name
    assert item['quantity'] == 3
    

def test_add_item_to_cart_with_invalid_quantity(client, customer, inventory):
    """
    Test add item to cart with invalid quantity:
        - negative quantity
        - zero quantity
        - non-integer quantity
    """
    url = CART_ITEMS_LIST_URL
    invalid_quantities = [-5, 0, 'abc', None]
    client.force_authenticate(user=customer)
    
    for qty in invalid_quantities:
        data = {
            'product_id': str(inventory.product.id),
            'quantity': qty
        }
        res = client.post(url, data=data, format='json')
        
        assert res.status_code == status.HTTP_400_BAD_REQUEST
        assert res.data['status'] == "error"
        assert res.data['code'] == "invalid_quantity"
        assert res.data['message'] == "Provide a valid quantity that is greater than 0."


def test_add_item_to_cart_with_quantity_as_string(client, customer, inventory):
    """
    Test add item to cart with quantity as string.
    """
    url = CART_ITEMS_LIST_URL
    data = {
        'product_id': str(inventory.product.id),
        'quantity': '4'
    }
    client.force_authenticate(user=customer)
    res = client.post(url, data=data, format='json')
    
    assert res.status_code == status.HTTP_200_OK
    assert res.data['message'] == "Item added to cart successfully."
    assert 'data' in res.data
    data = res.data['data']
    assert 'id' in data
    assert 'items' in data
    items = data['items']
    assert len(items) == 1
    item = items[0]
    assert item['product_name'] == inventory.product.name
    assert item['quantity'] == 4  # should be converted to integer


def test_add_item_to_cart_with_quantity_as_float(client, customer, inventory):
    """
    Test add item to cart with quantity as float.
    float quantity should be converted to integer by truncating the decimal part.
    """
    url = CART_ITEMS_LIST_URL
    data = {
        'product_id': str(inventory.product.id),
        'quantity': 4.5
    }
    client.force_authenticate(user=customer)
    res = client.post(url, data=data, format='json')

    assert res.status_code == status.HTTP_200_OK
    assert res.data['message'] == "Item added to cart successfully."
    assert 'data' in res.data
    data = res.data['data']
    assert 'id' in data
    assert 'items' in data
    items = data['items']
    assert len(items) == 1
    item = items[0]
    assert item['product_name'] == inventory.product.name
    assert item['quantity'] == 4 # should be truncated to 4


def test_add_item_to_cart_with_quantity_exceeding_stock(client, customer, inventory):
    """
    Test add item to cart with quantity exceeding stock.
    """
    url = CART_ITEMS_LIST_URL
    data = {
        'product_id': str(inventory.product.id),
        'quantity': inventory.stock + 10  # exceeding stock
    }
    client.force_authenticate(user=customer)
    res = client.post(url, data=data, format='json')
    
    assert res.status_code == status.HTTP_200_OK
    assert res.data['message'] == "Item added to cart successfully."
    assert 'data' in res.data
    data = res.data['data']
    assert 'id' in data
    assert 'items' in data
    items = data['items']
    assert len(items) == 1
    item = items[0]
    assert item['product_name'] == inventory.product.name
    assert item['quantity'] == inventory.stock  # should be set to available stock


def test_add_item_to_cart_when_product_is_out_of_stock(client, customer, inventory):
    """
    Test add item to cart when product is out of stock.
    """
    # Set inventory stock to zero
    inventory.subtract(inventory.stock)
    
    url = CART_ITEMS_LIST_URL
    data = {
        'product_id': str(inventory.product.id),
        'quantity': 2
    }
    client.force_authenticate(user=customer)
    res = client.post(url, data=data, format='json')
    
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "out_of_stock"
    assert res.data['message'] == "Product out of stock."


def test_add_item_to_cart_when_item_already_exists_updates_quantity(client, customer, inventory):
    """
    Test add item to cart when item already exists updates quantity.
    """
    # First add item to cart
    cart = customer.cart
    cart.add_to_cart(inventory.product, 2)
    
    url = CART_ITEMS_LIST_URL
    client.force_authenticate(user=customer)
    
    # Add the same item again with different quantity
    data = {
        'product_id': str(inventory.product.id),
        'quantity': 5
    }
    res = client.post(url, data=data, format='json')

    assert res.status_code == status.HTTP_200_OK
    assert res.data['message'] == "Item added to cart successfully."
    assert 'data' in res.data
    data = res.data['data']
    assert 'id' in data
    assert 'items' in data
    items = data['items']
    assert len(items) == 1  # still one item in cart
    item = items[0]
    assert item['product_name'] == inventory.product.name
    assert item['quantity'] == 5  # quantity should be updated to new value

def test_add_item_to_cart_by_user_without_cart(client, customer_no_cart, inventory):
    """
    Test add item to cart by customer with no cart.
    """
    url = CART_ITEMS_LIST_URL
    data = {
        'product_id': str(inventory.product.id),
        'quantity': 2
    }
    client.force_authenticate(user=customer_no_cart)
    res = client.post(url, data=data, format='json')

    assert res.status_code == status.HTTP_404_NOT_FOUND
    assert res.data['status'] == "error"
    assert res.data['code'] == "not_found"
    assert res.data['message'] == "No cart found for the user."


def test_add_item_to_cart_with_non_existing_product_id(client, customer):
    """
    Test add item to cart with non-existing product
    """
    data = {
        'product_id': str(uuid.uuid4()),
        'quantity': 2
    }
    url = CART_ITEMS_LIST_URL

    client.force_authenticate(user=customer)
    res = client.post(url, data=data, format='json')
    assert res.status_code == status.HTTP_404_NOT_FOUND
    assert res.data['status'] == "error"
    assert res.data['code'] == "not_found"
    assert res.data['message'] == "No product matching the given ID found."


def test_add_item_to_cart_with_invalid_product_id(client, customer):
    """
    Test add item to cart with invalid product id.
    """
    data = {
        'product_id': 'invalid-uuid',
        'quantity': 2
    }
    url = CART_ITEMS_LIST_URL

    client.force_authenticate(user=customer)
    res = client.post(url, data=data, format='json')
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "invalid_uuid"
    assert res.data['message'] == "Invalid product id."


def test_add_item_to_cart_by_unauthenticated_user(client, inventory):
    """
    Test add item to cart by unauthenticated user:
        - Test for without token and invalid token
    """
    url = CART_ITEMS_LIST_URL
    data = {
        'product_id': str(inventory.product.id),
        'quantity': 2
    }
    res = client.post(url, data=data, format='json')

    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.data['status'] == "error"
    assert res.data['code'] == "unauthorized"
    assert res.data['message'] == "Authentication credentials were not provided."

    client.cookies['access_token'] = "Invalid_access_token2445"
    res = client.post(url, data=data, format='json')
    
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.data['status'] == "error"
    assert res.data['code'] == "unauthorized"
    assert res.data['message'] == "Token is invalid or expired"


def test_add_item_to_cart_by_non_customer_user(client, shopowner, inventory):
    """
    Test add item to cart by non-customer user.
    """
    url = CART_ITEMS_LIST_URL
    data = {
        'product_id': str(inventory.product.id),
        'quantity': 2
    }
    client.force_authenticate(user=shopowner)
    res = client.post(url, data=data, format='json')
    assert res.status_code == status.HTTP_403_FORBIDDEN
    assert res.data['status'] == "error"
    assert res.data['code'] == "forbidden"
    assert res.data['message'] == "You do not have permission to perform this action."


# =============================================================================
# TEST UPDATE CART ITEM QUANTITY
# =============================================================================

def test_update_cart_item_quantity(client, customer, inventory):
    """
    Test update cart item quantity.
     - test increment operation
     - test decrement operation
    changes are done by 1 unit
    """
    cart = customer.cart
    cart.add_to_cart(inventory.product, 1)
    item = cart.items.first()

    url = reverse('cart-item-detail', args=[item.id])

    # test increment operation
    payload = {'operation': 'increment'}
    client.force_authenticate(user=customer)
    res = client.post(url, data=payload, format='json')
    
    assert res.status_code == status.HTTP_200_OK
    assert res.data['message'] == "Cart item updated successfully."
    assert 'data' in res.data
    data = res.data['data']
    fields = ['id', 'product_name', 'quantity']
    assert all(f in data for f in fields)
    assert data['id'] == str(item.id)
    assert data['product_name'] == item.product_name
    assert data['quantity'] == item.quantity + 1

    # test decrement operation
    payload = {'operation': 'decrement'}
    res = client.post(url, data=payload, format='json')

    assert res.status_code == status.HTTP_200_OK
    assert res.data['message'] == "Cart item updated successfully."
    assert 'data' in res.data
    data = res.data['data']
    assert all(f in data for f in fields)
    assert data['id'] == str(item.id)
    assert data['product_name'] == item.product_name
    assert data['quantity'] == item.quantity  # back to original quantity (1)
    

def test_decrement_cart_item_quantity_below_zero_removes_item(client, customer, inventory):
    """
    Test decrement cart item quantity below zero removes the item from cart.
    """
    cart = customer.cart
    cart.add_to_cart(inventory.product, 1)
    item = cart.items.first()

    url = reverse('cart-item-detail', args=[item.id])
    
    payload = {'operation': 'decrement'}
    client.force_authenticate(user=customer)

    res = client.post(url, data=payload, format='json')
    assert res.status_code == status.HTTP_200_OK
    assert res.data['status'] == "success"
    assert res.data['message'] == "Cart item updated successfully."
    assert 'data' in res.data
    assert res.data['data'] == {} # item should be removed, so data is empty
    
    # Verify item is removed from cart
    cart.refresh_from_db()
    assert not cart.items.filter(id=item.id).exists()
    assert cart.items.count() == 0


def test_increment_cart_item_quantity_exceeding_stock(client, customer, inventory):
    """
    Test increment cart item quantity exceeding stock.
    """
    cart = customer.cart
    cart.add_to_cart(inventory.product, inventory.stock)

    item = cart.items.first()

    url = reverse('cart-item-detail', args=[item.id])

    # Attempt to increment quantity beyond stock
    payload = {'operation': 'increment'}
    client.force_authenticate(user=customer)
    res = client.post(url, data=payload, format='json')
    
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "insufficient_stock"
    assert res.data['message'] == f"Insufficient stock. Only {item.product.inventory.stock} left."



@pytest.mark.parametrize(
    'operation', 
    ['increment', 'decrement'],
    ids=['increment', 'decrement']
)
def test_update_cart_item_when_product_no_longer_available(client, customer, inventory, operation):
    """
    Test update cart item when product no longer available.
    """
    cart = customer.cart
    cart.add_to_cart(inventory.product, 2)
    item = cart.items.first()

    # Delete the product to simulate unavailability
    inventory.product.delete()

    url = reverse('cart-item-detail', args=[item.id])

    # Attempt to increment quantity
    payload = {'operation': operation}
    client.force_authenticate(user=customer)
    res = client.post(url, data=payload, format='json')
    
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "product_unavailable"
    assert res.data['message'] == "Product no longer available."


@pytest.mark.parametrize(
    'operation', 
    ['increment', 'decrement'],
    ids=['increment', 'decrement']
)
def test_update_cart_item_when_product_is_deactivated(client, customer, inventory, operation):
    """
    Test update cart item when product is deactivated.
    """
    cart = customer.cart
    cart.add_to_cart(inventory.product, 2)
    item = cart.items.first()

    # Deactivate the product
    inventory.product.is_active = False
    inventory.product.save()

    url = reverse('cart-item-detail', args=[item.id])

    # Attempt to increment quantity
    payload = {'operation': operation}
    client.force_authenticate(user=customer)
    res = client.post(url, data=payload, format='json')
    
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "product_unavailable"
    assert res.data['message'] == "Product no longer available."


def test_update_cart_item_quantity_with_invalid_operation(client, customer, inventory):
    """
    Test updating cart item quantity with an invalid operation.
    """
    cart = customer.cart
    cart.add_to_cart(inventory.product, 1)
    
    item = cart.items.first()
    
    url = reverse('cart-item-detail', args=[item.id])
    
    # Attempt to update with an invalid operation
    payload = {'operation': 'invalid_operation'}
    client.force_authenticate(user=customer)
    res = client.post(url, data=payload, format='json')
    
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "invalid_operation"
    assert res.data['message'] == "Provide a valid operation: 'increment' or 'decrement'."


def test_update_cart_item_quantity_by_user_without_cart(client, customer_no_cart, shopowner, product_factory):
    """
    Test update cart item quantity by customer with no cart.
    """
    url = reverse('cart-item-detail', args=[uuid.uuid4()])
    
    payload = {'operation': 'increment'}
    client.force_authenticate(user=customer_no_cart)
    res = client.post(url, data=payload, format='json')
    
    assert res.status_code == status.HTTP_404_NOT_FOUND
    assert res.data['status'] == "error"
    assert res.data['code'] == "not_found"
    assert res.data['message'] == "No cart found for the user."


def test_update_cart_item_quantity_with_non_existing_cart_item_id(client, customer):
    """
    Test update cart item quantity with non-existing cart item id.
    """
    url = reverse('cart-item-detail', args=[uuid.uuid4()])
    
    payload = {'operation': 'increment'}
    client.force_authenticate(user=customer)
    res = client.post(url, data=payload, format='json')
    assert res.status_code == status.HTTP_404_NOT_FOUND
    assert res.data['status'] == "error"
    assert res.data['code'] == "not_found"
    assert res.data['message'] == "No item matching given ID found in cart."


def test_update_cart_item_quantity_with_invalid_cart_item_id(client, customer):
    """
    Test update cart item quantity with invalid cart item id.
    """
    url = reverse('cart-item-detail', args=['invalid-uuid'])
    
    payload = {'operation': 'increment'}
    client.force_authenticate(user=customer)
    res = client.post(url, data=payload, format='json')
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "invalid_uuid"
    assert res.data['message'] == "Invalid cart item id."


def test_update_cart_item_quantity_by_unauthenticated_user(client):
    """
    Test update cart item quantity by unauthenticated user:
        - Test for without token and invalid token
    """
    url = reverse('cart-item-detail', args=[uuid.uuid4()])
    
    payload = {'operation': 'increment'}
    res = client.post(url, data=payload, format='json')
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.data['status'] == "error"
    assert res.data['code'] == "unauthorized"
    assert res.data['message'] == "Authentication credentials were not provided."

    client.cookies['access_token'] = "Invalid_access_token2445"
    res = client.post(url, data=payload, format='json')
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.data['status'] == "error"
    assert res.data['code'] == "unauthorized"
    assert res.data['message'] == "Token is invalid or expired"


def test_update_cart_item_quantity_by_non_customer_user(client, shopowner):
    """
    Test update cart item quantity by non-customer user.
    """
    url = reverse('cart-item-detail', args=[uuid.uuid4()])
    
    payload = {'operation': 'increment'}
    client.force_authenticate(user=shopowner)
    res = client.post(url, data=payload, format='json')
    assert res.status_code == status.HTTP_403_FORBIDDEN
    assert res.data['status'] == "error"
    assert res.data['code'] == "forbidden"
    assert res.data['message'] == "You do not have permission to perform this action."
    

# =============================================================================
# TEST DELETE CART ITEM QUANTITY
# =============================================================================

def test_delete_cart_item(client, customer, inventory):
    """
    Test delete cart item.
    """

    cart = customer.cart
    cart.add_to_cart(inventory.product, 2)
    item_id = cart.items.first().id

    assert cart.items.count() == 1

    url = reverse('cart-item-detail', args=[item_id])
    client.force_authenticate(user=customer)
    res = client.delete(url)

    assert res.status_code == status.HTTP_204_NO_CONTENT

    # Verify item is removed from cart
    cart.refresh_from_db()

    assert not cart.items.filter(id=item_id).exists()
    assert cart.items.count() == 0
    
    
def test_delete_cart_item_that_does_not_exist(client, customer):
    """
    Test delete cart item that does not exist.
    """
    url = reverse('cart-item-detail', args=[uuid.uuid4()])
    client.force_authenticate(user=customer)
    res = client.delete(url)

    assert res.status_code == status.HTTP_404_NOT_FOUND
    assert res.data['status'] == "error"
    assert res.data['code'] == "not_found"
    assert res.data['message'] == "No item matching given ID found in cart."


def test_delete_cart_item_with_invalid_cart_item_id(client, customer):
    """
    Test delete cart item with invalid cart item id.
    """
    url = reverse('cart-item-detail', args=['invalid-uuid'])
    client.force_authenticate(user=customer)
    res = client.delete(url)

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "invalid_uuid"
    assert res.data['message'] == "Invalid cart item id."


def test_delete_cart_item_by_user_without_cart(client, customer_no_cart):
    """
    Test delete cart item by customer with no cart.
    """
    url = reverse('cart-item-detail', args=[uuid.uuid4()])
    client.force_authenticate(user=customer_no_cart)
    res = client.delete(url)

    assert res.status_code == status.HTTP_404_NOT_FOUND
    assert res.data['status'] == "error"
    assert res.data['code'] == "not_found"
    assert res.data['message'] == "No cart found for the user."

    
def test_delete_cart_item_by_unauthenticated_user(client):
    """
    Test delete cart item by unauthenticated user:
        - Test for without token and invalid token
    """
    url = reverse('cart-item-detail', args=[uuid.uuid4()])
    res = client.delete(url)

    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.data['status'] == "error"
    assert res.data['code'] == "unauthorized"
    assert res.data['message'] == "Authentication credentials were not provided."

    client.cookies['access_token'] = "Invalid_access_token2445"
    res = client.delete(url)

    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.data['status'] == "error"
    assert res.data['code'] == "unauthorized"
    assert res.data['message'] == "Token is invalid or expired"


def test_delete_cart_item_by_non_customer_user(client, shopowner):
    """
    Test delete cart item by non-customer user.
    """
    url = reverse('cart-item-detail', args=[uuid.uuid4()])
    client.force_authenticate(user=shopowner)
    res = client.delete(url)

    assert res.status_code == status.HTTP_403_FORBIDDEN
    assert res.data['status'] == "error"
    assert res.data['code'] == "forbidden"
    assert res.data['message'] == "You do not have permission to perform this action."
