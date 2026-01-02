"""
Test module for the user enpoints
"""
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status

import pytest
import uuid

User = get_user_model()


# =============================================================================
# TEST GET CUSTOMERS
# =============================================================================
USERS_URL = reverse('customer-list')

def test_get_customers_by_superuser(client, super_user, customer_factory):
    """
    Test get all customers by super user.
    """
    for i in range(5):
        customer_factory()
    client.force_authenticate(user=super_user)
    res = client.get(USERS_URL)
    assert res.status_code == status.HTTP_200_OK
    assert res.data['status'] == "success"
    assert res.data['message'] == "Customers retrieved successfully."
    assert res.data['data']['count'] == 5
    assert 'results' in res.data['data']


@pytest.mark.parametrize(
    'user_type',
    ['customer', 'shopowner', 'shop_staff'],
    ids=['customer', 'shopowner', 'shop_staff']
)
def test_get_customers_by_non_superuser(client, all_users, user_type):
    """
    Test get all customers by non super user.
    """
    user = all_users[user_type]
    client.force_authenticate(user=user)
    res = client.get(USERS_URL)

    assert res.status_code == status.HTTP_403_FORBIDDEN
    assert res.data['status'] == "error"
    assert res.data['code'] == "forbidden"
    assert res.data['message'] == "You do not have permission to perform this action."


def test_get_customers_by_unauthenticated_user(client):
    """
    Test get all customers by unauthenticated user.
    """
    res = client.get(USERS_URL)
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.data['status'] == "error"
    assert res.data['code'] == "unauthorized"
    assert res.data['message'] == "Authentication credentials were not provided."

    client.cookies['access_token'] = 'invalid_token'

    res = client.get(USERS_URL)
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.data['status'] == "error"
    assert res.data['code'] == "unauthorized"
    assert res.data['message'] == "Token is invalid or expired"


# =============================================================================
# TEST GET CUSTOMER WITH ID
# =============================================================================

def test_get_customer_with_user_id(client, customer):
    """
    Test get customer with the user's id.
    """
    url = reverse('customer-detail', kwargs={'customer_id': customer.id})
    client.force_authenticate(user=customer)
    res = client.get(url)
    assert res.status_code == status.HTTP_200_OK
    assert res.data['status'] == "success"
    assert res.data['message'] == "Customer retrieved successfully."
    assert res.data['data']
    assert res.data['data']['id'] == str(customer.id)

def test_get_customer_with_user_id_by_another_customer(client, customer, customer_factory):
    """
    Test get customer with the user's id by another customer.
    """
    cus1 = customer_factory()
    url = reverse('customer-detail', kwargs={'customer_id': cus1.id})
    client.force_authenticate(user=customer)
    res = client.get(url)
    assert res.status_code == status.HTTP_403_FORBIDDEN
    assert res.data['status'] == "error"
    assert res.data['code'] == "forbidden"
    assert res.data['message'] == "You do not have permission to perform this action."


@pytest.mark.parametrize(
    'user_type',
    ['shopowner', 'shop_staff'],
    ids=['shopowner', 'shop_staff']
)
def test_get_customer_with_user_id_by_non_customer(client, customer,  all_users, user_type):
    """
    Test get a customer by non customer.
    """
    user = all_users[user_type]

    client.force_authenticate(user=user)
    url = reverse('customer-detail', kwargs={'customer_id': customer.id})
    res = client.get(url)

    assert res.status_code == status.HTTP_403_FORBIDDEN
    assert res.data['status'] == "error"
    assert res.data['code'] == "forbidden"
    assert res.data['message'] == "You do not have permission to perform this action."


def test_get_customer_with_invalid_id(client, customer):
    """
    Test get customer with invalid id.
    """
    url = reverse('customer-detail', kwargs={'customer_id': "45678909876543"})
    client.force_authenticate(user=customer)
    res = client.get(url)
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "invalid_uuid"
    assert res.data['message'] == "Invalid customer id."


def test_get_customer_with_non_existent_id(client, customer):
    """
    Test get customer with non-existent id.
    """
    url = reverse('customer-detail', kwargs={'customer_id': uuid.uuid4()})
    client.force_authenticate(user=customer)
    res = client.get(url)
    assert res.status_code == status.HTTP_404_NOT_FOUND
    assert res.data['status'] == "error"
    assert res.data['code'] == "not_found"
    assert res.data['message'] == "No customer matching the given ID found."

def test_get_customers_by_unauthenticated_user(client, customer):
    """
    Test get customer by unauthenticated user.
    """
    url = reverse('customer-detail', kwargs={'customer_id': uuid.uuid4()})
    res = client.get(url)
    
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.data['status'] == "error"
    assert res.data['code'] == "unauthorized"
    assert res.data['message'] == "Authentication credentials were not provided."

    client.cookies['access_token'] = 'invalid_token'

    res = client.get(url)
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.data['status'] == "error"
    assert res.data['code'] == "unauthorized"
    assert res.data['message'] == "Token is invalid or expired"


# =============================================================================
# TEST DELETE CUSTOMER
# =============================================================================
def test_delete_customer_by_superuser(client, super_user, customer):
    """
    Test delete customer by super user.
    """
    url  = reverse('customer-detail', kwargs={'customer_id': customer.id})
    client.force_authenticate(user=super_user)
    res = client.delete(url)
    assert res.status_code == status.HTTP_204_NO_CONTENT
    assert not User.objects.filter(email=customer.email).exists()
    
    
def test_delete_customer_by_customer(client, customer):
    """
    Test delete customer by customer.
    """
    url  = reverse('customer-detail', kwargs={'customer_id': customer.id})
    client.force_authenticate(user=customer)
    res = client.delete(url)
    assert res.status_code == status.HTTP_204_NO_CONTENT
    assert not User.objects.filter(email=customer.email).exists()


def test_delete_customer_by_another_customer(client, customer, customer_factory):
    """
    Test delete customer by a different customer.
    """
    cus = customer_factory()
    
    url  = reverse('customer-detail', kwargs={'customer_id': cus.id})
    client.force_authenticate(user=customer)
    res = client.delete(url)
    assert res.status_code == status.HTTP_403_FORBIDDEN
    assert res.data['status'] == "error"
    assert res.data['code'] == "forbidden"
    assert res.data['message'] == "You do not have permission to perform this action."

def test_delete_customer_that_is_also_shopowner(client, customer):
    """
    Test delete a customer that is a shopw owner.
    """
    customer.is_shopowner = True
    customer.save(update_fields=['is_shopowner'])

    client.force_authenticate(user=customer)
    url  = reverse('customer-detail', kwargs={'customer_id': customer.id})
    res = client.delete(url)
    assert res.status_code == status.HTTP_204_NO_CONTENT
    assert User.objects.filter(email=customer.email).exists()

    customer.refresh_from_db()
    assert customer.is_customer is False
    assert not hasattr(customer, 'cart')


def test_delete_user_with_invalid_id(client, customer):
    """
    Test delete user with invalid id.
    """
    url = reverse('customer-detail', kwargs={'customer_id': "45678909876543"})
    client.force_authenticate(user=customer)
    res = client.get(url)
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "invalid_uuid"
    assert res.data['message'] == "Invalid customer id."


def test_delete_user_with_non_existent_id(client, customer):
    """
    Test delete user with non-existent id.
    """
    url = reverse('customer-detail', kwargs={'customer_id': uuid.uuid4()})
    client.force_authenticate(user=customer)
    res = client.delete(url)
    assert res.status_code == status.HTTP_404_NOT_FOUND
    assert res.data['status'] == "error"
    assert res.data['code'] == "not_found"
    assert res.data['message'] == "No customer mactching the given ID found."
