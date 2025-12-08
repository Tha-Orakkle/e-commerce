from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status

import uuid

User = get_user_model()

# =============================================================================
# TEST GET SHOP OWNERS
# =============================================================================

def test_get_shop_owners(client, signed_in_superuser):
    """
    Test get all shop owners.
    """
    # Create some shop owners
    for i in range(3):
        User.objects.create_shopowner(
            email=f"{'shopowner'+str(i)}@example.com",
            staff_handle=f"shopowner{i}",
            password="Password123#"
        )
    url = reverse('shopowner-list')
    client.cookies['access_token'] = signed_in_superuser['access_token']
    res = client.get(url)
    
    assert res.status_code == status.HTTP_200_OK
    assert res.data['status'] == "success"
    assert res.data['message'] == "Shop owners retrieved successfully."
    assert res.data['data']['count'] == 3
    assert res.data['data']['previous'] == None
    assert res.data['data']['next'] == None
    assert res.data['data']['results']
    assert res.data['data']['results'][0]['is_shopowner'] == True
    
def test_get_shop_owners_with_no_shopowners(client, signed_in_superuser):
    """
    Test get all shop owners when there are no shop owners.
    """
    url = reverse('shopowner-list')
    client.cookies['access_token'] = signed_in_superuser['access_token']
    res = client.get(url)
    
    assert res.status_code == status.HTTP_200_OK
    assert res.data['status'] == "success"
    assert res.data['message'] == "Shop owners retrieved successfully."
    assert res.data['data']['count'] == 0
    assert res.data['data']['previous'] == None
    assert res.data['data']['next'] == None
    assert res.data['data']['results'] == []

def test_get_shop_owners_by_non_superuser(client, signed_in_customer):
    """
    Test get all shop owners by non super user.
    """
    url = reverse('shopowner-list')
    client.cookies['access_token'] = signed_in_customer['access_token']
    res = client.get(url)
    
    assert res.status_code == status.HTTP_403_FORBIDDEN
    assert res.data['status'] == "error"
    assert res.data['code'] == "forbidden"
    assert res.data['message'] == "You do not have permission to perform this action."

def test_get_shop_owners_by_unauthorized_user(client):
    """
    Test get a specific shop owner by unauthorized user.
    """
    url = reverse('shopowner-list')
    res = client.get(url)
    
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.data['status'] == "error"
    assert res.data['code'] == "unauthorized"
    assert res.data['message'] == "Authentication credentials were not provided."
    
    client.cookies['access_token'] = "invalid_token"
    res = client.get(url)
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.data['message'] == "Token is invalid or expired"


# =============================================================================
# TEST GET SHOP OWNER WITH ID
# =============================================================================
def test_get_shop_owner_by_same_shop_owner(client, shopowner, signed_in_shopowner):
    """
    Test get a specific shop owner by same Shop owner.
    """
    url = reverse('shopowner-detail', kwargs={'shopowner_id': shopowner.id})
    client.cookies['access_token'] == signed_in_shopowner['access_token']
    res = client.get(url)
    assert res.status_code == status.HTTP_200_OK
    assert res.data['status'] == "success"
    assert res.data['message'] == "Shop owner retrieved successfully."
    assert res.data['data']['id'] == str(shopowner.id)

def test_get_shopowner_by_superuser(client, shopowner, signed_in_superuser):
    """
    Test get a specific Shop owner by super user.
    """
    url = reverse('shopowner-detail', kwargs={'shopowner_id': shopowner.id})
    client.cookies['access_token'] == signed_in_superuser['access_token']
    res = client.get(url)
    assert res.status_code == status.HTTP_200_OK
    assert res.data['status'] == "success"
    assert res.data['message'] == "Shop owner retrieved successfully."
    assert res.data['data']['id'] == str(shopowner.id)

def test_get_shopowner_by_another_shopowner(client, shopowner, signed_in_shopowner):
    """
    Test get a specific Shop owner by a different non superuser Shop owner.
    """
    admin = User.objects.create_shopowner(
        email="anothershopowner@email.com",
        staff_handle='another-shopowner',
        password='Password123#'
    )
    url = reverse('shopowner-detail', kwargs={'shopowner_id': admin.id})
    client.cookies['access_token'] = signed_in_shopowner['access_token']
    res = client.get(url)
    assert res.status_code == status.HTTP_403_FORBIDDEN
    assert res.data['status'] == "error"
    assert res.data['code'] == "forbidden"
    assert res.data['message'] == "You do not have permission to perform this action."

def test_get_shopowner_with_invalid_id(client, signed_in_superuser):
    """
    Test get Shop owner with invalid shop owner id.  
    """
    url = reverse('shopowner-detail', kwargs={'shopowner_id': "123-Invalid-id"})
    client.cookies['access_token'] = signed_in_superuser['access_token']
    res = client.get(url)
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "invalid_uuid"
    assert res.data['message'] == "Invalid shop owner id."

def test_get_shopowner_with_non_existent_id(client, signed_in_superuser):
    """
    Test get shop owner with non-existent user id.
    """
    url = reverse('shopowner-detail', kwargs={'shopowner_id': uuid.uuid4()})
    client.cookies['access_token'] = signed_in_superuser['access_token']
    res = client.get(url)
    assert res.status_code == status.HTTP_404_NOT_FOUND
    assert res.data['status'] == "error"
    assert res.data['code'] == "not_found"
    assert res.data['message'] == "No shop owner matching the given given ID found."

def test_get_shopowner_by_non_shopowner(request, client, shopowner):
    """
    Test get shop owner by non shop owner.
    """
    tokens = request.getfixturevalue('signed_in_customer')
    url = reverse('shopowner-detail', kwargs={'shopowner_id': shopowner.id})
    client.cookies['access_token'] == tokens['access_token']
    res = client.get(url)
    assert res.status_code == status.HTTP_403_FORBIDDEN
    assert res.data['status'] == "error"
    assert res.data['code'] == "forbidden"
    assert res.data['message'] == "You do not have permission to perform this action."

    tokens = request.getfixturevalue('signed_in_staff')
    client.cookies['access_token'] == tokens['access_token']
    res = client.get(url)
    assert res.status_code == status.HTTP_403_FORBIDDEN
    assert res.data['status'] == "error"
    assert res.data['code'] == "forbidden"
    assert res.data['message'] == "You do not have permission to perform this action."
