from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status

import pytest
import uuid

User = get_user_model()

# =============================================================================
# GET SHOP OWNER - TESTS
# =============================================================================

SHOPOWNERS_URL = reverse('shopowner-list') 

def test_get_shop_owners(client, super_user, shopowner_factory):
    """
    Test get all shop owners.
    """
    # Create some shop owners
    for i in range(5):
        shopowner_factory()

    client.force_authenticate(user=super_user)
    res = client.get(SHOPOWNERS_URL)
    
    assert res.status_code == status.HTTP_200_OK
    assert res.data['status'] == "success"
    assert res.data['message'] == "Shop owners retrieved successfully."
    assert res.data['data']['count'] == 5
    assert res.data['data']['previous'] is None
    assert res.data['data']['next'] is None
    assert res.data['data']['results']
    assert res.data['data']['results'][0]['is_shopowner'] is True
    
def test_get_shop_owners_with_no_shopowners(client, super_user):
    """
    Test get all shop owners when there are no shop owners.
    """
    client.force_authenticate(user=super_user)
    res = client.get(SHOPOWNERS_URL)
    
    assert res.status_code == status.HTTP_200_OK
    assert res.data['status'] == "success"
    assert res.data['message'] == "Shop owners retrieved successfully."
    assert res.data['data']['count'] == 0
    assert res.data['data']['previous'] == None
    assert res.data['data']['next'] == None
    assert res.data['data']['results'] == []

@pytest.mark.parametrize(
    'user_type',
    ['customer', 'shopowner'],
    ids=['customer', 'shopowner']
)
def test_get_shop_owners_by_non_superuser(client, all_users, user_type):
    """
    Test get all shop owners by non super user.
    """
    user = all_users[user_type]

    client.force_authenticate(user=user)
    res = client.get(SHOPOWNERS_URL)
    
    assert res.status_code == status.HTTP_403_FORBIDDEN
    assert res.data['status'] == "error"
    assert res.data['code'] == "forbidden"
    assert res.data['message'] == "You do not have permission to perform this action."


def test_get_shop_owners_by_unauthorized_user(client):
    """
    Test get a specific shop owner by unauthorized user.
    """
    res = client.get(SHOPOWNERS_URL)
    
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.data['status'] == "error"
    assert res.data['code'] == "unauthorized"
    assert res.data['message'] == "Authentication credentials were not provided."
    
    client.cookies['access_token'] = "invalid_token"
    res = client.get(SHOPOWNERS_URL)
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.data['message'] == "Token is invalid or expired"


# =============================================================================
# TEST GET SHOP OWNER WITH ID
# =============================================================================
def test_get_shop_owner_by_same_shop_owner(client, shopowner):
    """
    Test get a specific shop owner by same Shop owner.
    """
    url = reverse('shopowner-detail', kwargs={'shopowner_id': shopowner.id})
    client.force_authenticate(user=shopowner)
    res = client.get(url)
    assert res.status_code == status.HTTP_200_OK
    assert res.data['status'] == "success"
    assert res.data['message'] == "Shop owner retrieved successfully."
    assert res.data['data']['id'] == str(shopowner.id)

def test_get_shopowner_by_superuser(client, super_user, shopowner):
    """
    Test get a specific Shop owner by super user.
    """
    url = reverse('shopowner-detail', kwargs={'shopowner_id': shopowner.id})
    client.force_authenticate(user=super_user)
    res = client.get(url)

    assert res.status_code == status.HTTP_200_OK
    assert res.data['status'] == "success"
    assert res.data['message'] == "Shop owner retrieved successfully."
    assert res.data['data']['id'] == str(shopowner.id)

def test_get_shopowner_by_another_shopowner(client, shopowner, shopowner_factory):
    """
    Test get a specific Shop owner by a different Shop owner.
    """
    sh1 = shopowner_factory()
    
    url = reverse('shopowner-detail', kwargs={'shopowner_id': sh1.id})
    client.force_authenticate(user=shopowner)
    res = client.get(url)
    assert res.status_code == status.HTTP_403_FORBIDDEN
    assert res.data['status'] == "error"
    assert res.data['code'] == "forbidden"
    assert res.data['message'] == "You do not have permission to perform this action."

def test_get_shopowner_with_invalid_id(client, shopowner):
    """
    Test get Shop owner with invalid shop owner id.  
    """
    url = reverse('shopowner-detail', kwargs={'shopowner_id': "123-Invalid-id"})
    client.force_authenticate(user=shopowner)
    res = client.get(url)
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "invalid_uuid"
    assert res.data['message'] == "Invalid shop owner id."

def test_get_shopowner_with_non_existent_id(client, super_user):
    """
    Test get shop owner with non-existent user id.
    """
    url = reverse('shopowner-detail', kwargs={'shopowner_id': uuid.uuid4()})
    client.force_authenticate(user=super_user)
    res = client.get(url)
    assert res.status_code == status.HTTP_404_NOT_FOUND
    assert res.data['status'] == "error"
    assert res.data['code'] == "not_found"
    assert res.data['message'] == "No shop owner matching the given given ID found."

@pytest.mark.parametrize(
    'user_type', 
    ['customer', 'shop_staff'],
    ids=['customer', 'shop_staff']
)
def test_get_shopowner_by_non_shopowner(client, shopowner, all_users, user_type):
    """
    Test get shop owner by non shop owner.
    """
    user = all_users[user_type]
    url = reverse('shopowner-detail', kwargs={'shopowner_id': shopowner.id})
    client.force_authenticate(user=user)
    res = client.get(url)
    assert res.status_code == status.HTTP_403_FORBIDDEN
    assert res.data['status'] == "error"
    assert res.data['code'] == "forbidden"
    assert res.data['message'] == "You do not have permission to perform this action."
