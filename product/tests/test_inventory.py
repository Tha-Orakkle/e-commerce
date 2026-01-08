from django.urls import reverse
from rest_framework import status

import pytest


@pytest.mark.parametrize(
    'user_type',
    ['shop_staff', 'shopowner'],
    ids=['shop_staff', 'shopowner']
)
def test_update_inventory_add_qty(client, all_users, user_type, product, inventory):
    """
    Test updating inventory by adding quantity.
    """
    assert inventory.stock == 20
    
    user = all_users[user_type]
    client.force_authenticate(user=user)
    url = reverse('inventory-update', args=[product.id])
    data = {
        'action': 'add',
        'quantity': 15
    }
    response = client.post(url, data, format='json')
    assert response.status_code == status.HTTP_200_OK
    assert response.data['status'] == 'success'
    assert response.data['message'] == 'Inventory updated successfully.'
    assert response.data['data']['product'] == product.name
    assert response.data['data']['stock'] == 35
    inventory.refresh_from_db()
    assert inventory.stock == 35


@pytest.mark.parametrize(
    'user_type',
    ['shop_staff', 'shopowner'],
    ids=['shop_staff', 'shopowner']
)
def test_update_inventory_sub_qty(client, all_users, user_type, product, inventory):
    """
    Test updating inventory by subtracting quantity.
    """
    assert inventory.stock == 20
    user = all_users[user_type]
    client.force_authenticate(user=user)
    url = reverse('inventory-update', args=[product.id])
    data = {
        'action': 'subtract',
        'quantity': 15
    }
    response = client.post(url, data, format='json')
    assert response.status_code == status.HTTP_200_OK
    assert response.data['status'] == 'success'
    assert response.data['message'] == 'Inventory updated successfully.'
    assert response.data['data']['product'] == product.name
    assert response.data['data']['stock'] == 5
    inventory.refresh_from_db()
    assert inventory.stock == 5


def test_update_inventory_invalid_action(client, shopowner, product, inventory):
    """
    Test updating inventory with invalid action.
    """
    client.force_authenticate(user=shopowner)
    url = reverse('inventory-update', args=[product.id])
    data = {
        'action': 'invalid_action',
        'quantity': 10
    }
    response = client.post(url, data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['code'] == 'invalid_action'
    assert response.data['message'] == "Provide a valid action: 'add' or 'subtract'."
    inventory.refresh_from_db()
    
    assert inventory.stock == 20


def test_update_inventory_insufficient_stock(client, shopowner, product, inventory):
    """
    Test updating inventory by subtracting more than available stock.
    """
    assert inventory.stock == 20
    client.force_authenticate(user=shopowner)
    url = reverse('inventory-update', args=[product.id])
    data = {
        'action': 'subtract',
        'quantity': 25
    }
    response = client.post(url, data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['code'] == 'insufficient_stock'
    detail = f"Insufficient stock to complete this operation. Only {product.inventory.stock} left."
    assert response.data['message'] == detail
    inventory.refresh_from_db()
    assert inventory.stock == 20


def test_update_inventory_with_non_integer_quantity(client, shopowner, product, inventory):
    """
    Test updating inventory with non-integer quantity.
    """
    assert inventory.stock == 20
    client.force_authenticate(user=shopowner)
    url = reverse('inventory-update', args=[product.id])
    data = {
        'action': 'add',
        'quantity': 'ten'
    }
    response = client.post(url, data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['code'] == 'invalid_quantity'
    assert response.data['message'] == "Provide a valid quantity that is greater than 0."
    inventory.refresh_from_db()
    assert inventory.stock == 20


def test_update_inventory_with_negative_quantity(client, shopowner, product, inventory):
    """
    Test updating inventory with negative quantity.
    """
    assert inventory.stock == 20
    client.force_authenticate(user=shopowner)
    url = reverse('inventory-update', args=[product.id])
    data = {
        'action': 'add',
        'quantity': -5
    }
    response = client.post(url, data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['code'] == 'invalid_quantity'
    assert response.data['message'] == "Provide a valid quantity that is greater than 0."
    inventory.refresh_from_db()
    assert product.inventory.stock == 20    

    data['action'] = 'subtract'
    response = client.post(url, data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['code'] == 'invalid_quantity'
    assert response.data['message'] == "Provide a valid quantity that is greater than 0."
    inventory.refresh_from_db()
    assert product.inventory.stock == 20


def test_update_inventory_customer(client, customer, product, inventory):
    """
    Test that unauthorized user cannot update inventory.
    """
    assert inventory.stock == 20
    client.force_authenticate(user=customer)
    url = reverse('inventory-update', args=[product.id])
    data = {
        'action': 'add',
        'quantity': 10
    }
    response = client.post(url, data, format='json')
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.data['status'] == "error"
    assert response.data['code'] == "forbidden"
    assert response.data['message'] == "You do not have permission to perform this action."
    inventory.refresh_from_db()
    assert inventory.stock == 20

 
def test_update_inventory_by_staff_of_different_shop(client, shopowner_factory, product, inventory):
    """
    Test that staff of a different shop cannot update inventory.
    """
    assert inventory.stock == 20
    sh = shopowner_factory()
    client.force_authenticate(user=sh)
    url = reverse('inventory-update', args=[product.id])
    data = {
        'action': 'add',
        'quantity': 10
    }
    response = client.post(url, data, format='json')
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.data['status'] == "error"
    assert response.data['code'] == "forbidden"
    assert response.data['message'] == "You do not have permission to perform this action."
    inventory.refresh_from_db()
    assert product.inventory.stock == 20


def test_update_inventory_by_unauthenticated_user(client, product, inventory):
    """
    Test update product inventory while unauthenticated.
    (without access token or with invalid token).
    """
    assert inventory.stock == 20

    url = reverse('inventory-update', args=[product.id])
    res = client.get(url, {}, format='json')
    
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.data['status'] == "error"
    assert res.data['code'] == "unauthorized"
    assert res.data['message'] == "Authentication credentials were not provided."
    inventory.refresh_from_db()
    assert inventory.stock == 20

    client.cookies['access_token'] = "Invalid_access_token2445"
    res = client.get(url, {}, format='json')
    
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.data['status'] == "error"
    assert res.data['code'] == "unauthorized"
    assert res.data['message'] == "Token is invalid or expired"
    inventory.refresh_from_db()
    assert inventory.stock == 20