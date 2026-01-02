from django.urls import reverse
from rest_framework import status

import pytest
import uuid
# GET all -- done
# GET 
# PATCH
# DELETE




# ==========================================================
# GET SHOP STAFF MEMBERS TESTS
# ==========================================================

def test_get_shop_staff_members_by_shopowner(client, shopowner, shop_staff_factory):
    """
    Test geting all shop staff members by shop owner.
    """
    for _ in range(2):
        shop_staff_factory(shopowner=shopowner)
    
    url = reverse('shop-staff-list-create', kwargs={
        'shop_id': shopowner.owned_shop.id
    })
    
    client.force_authenticate(user=shopowner)
    res = client.get(url)
    
    assert res.status_code == status.HTTP_200_OK
    assert res.data['status'] == "success"
    assert res.data['message'] == "Shop staff members retrieved successfully."
    assert res.data['data']['count'] == 2
    assert 'results' in res.data['data']


def test_get_shop_staff_members_by_superuser(client, super_user, shopowner, shop_staff_factory):
    """
    Test geting all shop staff members by a super user.
    """
    for _ in range(2):
        shop_staff_factory(shopowner=shopowner)
    url = reverse('shop-staff-list-create', kwargs={
        'shop_id': shopowner.owned_shop.id
    })    
    client.force_authenticate(user=super_user)
    res = client.get(url)     
    assert res.status_code == status.HTTP_200_OK
    assert res.data['status'] == "success"
    assert res.data['message'] == "Shop staff members retrieved successfully."
    assert res.data['data']['count'] == 2
    assert 'results' in res.data['data']


def test_get_shop_staff_members_by_another_shopowner(client, shopowner_factory, shop_staff_factory):
    """
    Test getting all shop staff members by another shop owner.
    """
    sh1 = shopowner_factory()
    sh2 = shopowner_factory()
    
    for _ in range(2):
        shop_staff_factory(shopowner=sh2)
    url = reverse('shop-staff-list-create', kwargs={
        'shop_id': sh2.owned_shop.id
    })
    client.force_authenticate(user=sh1)
    res = client.get(url)
    assert res.status_code == status.HTTP_403_FORBIDDEN
    assert res.data['status'] == "error"
    assert res.data['code'] == "forbidden"
    assert res.data['message'] == "You do not have permission to perform this action."

    
@pytest.mark.parametrize(
    'user_type',
    ['customer', 'shop_staff'],
    ids=['customer', 'shop_staff']
)
def test_get_shop_staff_members_by_non_shoponwer(client, all_users, user_type, shopowner):
    """
    Test getting all shop staff members by non shop owner.
    """
    user = all_users[user_type]
    url = reverse('shop-staff-list-create', kwargs={
        'shop_id': shopowner.owned_shop.id
    })
    client.force_authenticate(user=user)
    res = client.get(url)

    assert res.status_code == status.HTTP_403_FORBIDDEN
    assert res.data['status'] == "error"
    assert res.data['code'] == "forbidden"
    assert res.data['message'] == "You do not have permission to perform this action."

def test_get_shop_staff_members_with_invalid_shop_id(client, shopowner):
    """
    Test getting shop staff members with invalid shop id.
    """
    url = reverse('shop-staff-list-create', kwargs={
        'shop_id': 'invalid_shop_id'
    })
    client.force_authenticate(user=shopowner)
    res = client.get(url)

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "invalid_uuid"
    assert res.data['message'] == "Invalid shop id."


def test_get_shop_staff_members_with_non_existent_id(client, shopowner):
    """
    Test getting shop staff members with non existent shop id.
    """
    url = reverse('shop-staff-list-create', kwargs={
        'shop_id': uuid.uuid4()
    })
    client.force_authenticate(user=shopowner)
    res = client.get(url)

    assert res.status_code == status.HTTP_404_NOT_FOUND
    assert res.data['status'] == "error"
    assert res.data['code'] == "not_found"
    assert res.data['message'] == "No shop matching the given ID found."


def test_get_shop_staff_members_by_unauthenticated_user(client, shopowner):
    """
    Test getting shop staff members by unauthenticated user.
    """
    url = reverse('shop-staff-list-create', kwargs={
        'shop_id': shopowner.owned_shop.id
    })
    
    res = client.get(url)
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.data['status'] == "error"
    assert res.data['code'] == "unauthorized"
    assert res.data['message'] == "Authentication credentials were not provided."
    
    client.cookies['access_token'] = "invalid_token "
    res = client.get(url)
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.data['status'] == "error"
    assert res.data['code'] == "unauthorized"
    assert res.data['message'] == "Token is invalid or expired"
    
    
# ==========================================================
# GET SHOP STAFF MEMBER BY ID TESTS
# ==========================================================

def test_get_shop_staff_member_by_shopowner(client, shopowner, shop_staff):
    """
    Test get a specific shop staff by the shop owner.
    """
    url = reverse('shop-staff-detail', kwargs={
        'shop_id': shop_staff.shop.id,
        'staff_id': shop_staff.id
    })
    client.force_authenticate(user=shopowner)

    res = client.get(url)
    assert res.status_code == status.HTTP_200_OK
    assert res.data['status'] == "success"
    assert res.data['message'] == "Shop staff member retrieved successfully."
    assert res.data['data']['id'] == str(shop_staff.id)
    assert res.data['data']['staff_handle'] == shop_staff.staff_handle
    assert 'profile' in res.data['data']
    
def test_get_shop_staff_member_by_super_user(client, super_user, shop_staff):
    """
    Test get a specific shop staff by a super user.
    """
    url = reverse('shop-staff-detail', kwargs={
        'shop_id': shop_staff.shop.id,
        'staff_id': shop_staff.id
    })
    client.force_authenticate(user=super_user)

    res = client.get(url)
    assert res.status_code == status.HTTP_200_OK
    assert res.data['status'] == "success"
    assert res.data['message'] == "Shop staff member retrieved successfully."
    assert res.data['data']['id'] == str(shop_staff.id)
    assert res.data['data']['staff_handle'] == shop_staff.staff_handle
    assert 'profile' in res.data['data']
    
def test_get_shop_staff_member_by_same_shop_staff(client, shop_staff):
    """
    Test get a specific shop staff by the same staff member.
    """
    url = reverse('shop-staff-detail', kwargs={
        'shop_id': shop_staff.shop.id,
        'staff_id': shop_staff.id
    })
    client.force_authenticate(user=shop_staff)

    res = client.get(url)
    assert res.status_code == status.HTTP_200_OK
    assert res.data['status'] == "success"
    assert res.data['message'] == "Shop staff member retrieved successfully."
    assert res.data['data']['id'] == str(shop_staff.id)
    assert res.data['data']['staff_handle'] == shop_staff.staff_handle
    assert 'profile' in res.data['data']
    
    
def test_get_shop_staff_member_by_another_shopowner(client, shopowner_factory, shop_staff_factory):
    """
    Test getting a specific shop staff member by another shop owner.
    """
    sh1 = shopowner_factory()
    sh2 = shopowner_factory()
    sh_staff = shop_staff_factory(shopowner=sh2)
    
    url = reverse('shop-staff-detail', kwargs={
        'shop_id': sh_staff.shop.id,
        'staff_id': sh_staff.id
    })
    client.force_authenticate(user=sh1)
    res = client.get(url)
    assert res.status_code == status.HTTP_403_FORBIDDEN
    assert res.data['status'] == "error"
    assert res.data['code'] == "forbidden"
    assert res.data['message'] == "You do not have permission to perform this action."
    
def test_get_shop_staff_member_by_another_shop_staff(client, shopowner_factory, shop_staff_factory):
    """
    Test getting a specific shop staff member by another shop staff.
    """
    sh1 = shopowner_factory()
    sh_staff1 = shop_staff_factory(shopowner=sh1)
    sh_staff2 = shop_staff_factory(shopowner=sh1)
    
    url = reverse('shop-staff-detail', kwargs={
        'shop_id': sh_staff2.shop.id,
        'staff_id': sh_staff2.id
    })
    client.force_authenticate(user=sh_staff1)
    res = client.get(url)
    assert res.status_code == status.HTTP_403_FORBIDDEN
    assert res.data['status'] == "error"
    assert res.data['code'] == "forbidden"
    assert res.data['message'] == "You do not have permission to perform this action."
    
def test_get_shop_staff_member_with_invalid_ids(client, shopowner, shop_staff):
    """
    Test getting a specific shop staff member with invalid shop and staff ids.
    """
    url = reverse('shop-staff-detail', kwargs={
        'shop_id': 'invalid_shop_id',
        'staff_id': shop_staff.id
    })
    client.force_authenticate(user=shopowner)
    res = client.get(url)

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "invalid_uuid"
    assert res.data['message'] == "Invalid shop id."

    url = reverse('shop-staff-detail', kwargs={
        'shop_id': shop_staff.shop.id,
        'staff_id': 'invalid_staff_id'
    })
    res = client.get(url)

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "invalid_uuid"
    assert res.data['message'] == "Invalid staff id."


def test_get_shop_staff_member_with_non_existent_ids(client, shopowner, shop_staff):
    """
    Test getting specific shop staff member with non existent shop and staff ids.
    """
    url = reverse('shop-staff-detail', kwargs={
        'shop_id': uuid.uuid4(),
        'staff_id': shop_staff.id
    })
    client.force_authenticate(user=shopowner)
    res = client.get(url)

    assert res.status_code == status.HTTP_404_NOT_FOUND
    assert res.data['status'] == "error"
    assert res.data['code'] == "not_found"
    assert res.data['message'] == "No shop matching the given ID found."

    url = reverse('shop-staff-detail', kwargs={
        'shop_id': shop_staff.shop.id,
        'staff_id': uuid.uuid4()
    })
    res = client.get(url)

    assert res.status_code == status.HTTP_404_NOT_FOUND
    assert res.data['status'] == "error"
    assert res.data['code'] == "not_found"
    assert res.data['message'] == "No staff member matching the given ID found."


def test_get_shop_staff_member_by_unauthenticated_user(client, shop_staff):
    """
    Test getting specific shop staff member by unauthenticated user.
    """
    url = reverse('shop-staff-detail', kwargs={
        'shop_id': shop_staff.shop.id,
        'staff_id': shop_staff.id
    })
    
    res = client.get(url)
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.data['status'] == "error"
    assert res.data['code'] == "unauthorized"
    assert res.data['message'] == "Authentication credentials were not provided."
    
    client.cookies['access_token'] = "invalid_token "
    res = client.get(url)
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.data['status'] == "error"
    assert res.data['code'] == "unauthorized"
    assert res.data['message'] == "Token is invalid or expired"


# ==========================================================
# UPDATE SHOP STAFF MEMBER HANDLE BY SHOP OWNER TESTS
# ==========================================================

UPDATE_DATA = {'staff_handle': 'new_handle'}


@pytest.mark.parametrize(
    'user_type',
    ['shopowner', 'super_user'],
    ids=['shopowner', 'super_user']
)
def test_update_shop_staff(client, all_users, user_type, shop_staff):
    """
    Test updating a specific shop staff.
    """
    user = all_users[user_type]
    url = reverse('shop-staff-detail', kwargs={
        'shop_id': shop_staff.shop.id,
        'staff_id': shop_staff.id
    })
    client.force_authenticate(user=user)
    res = client.patch(url, data=UPDATE_DATA, format='json')
    assert res.status_code == status.HTTP_200_OK
    assert res.data['status'] == "success"
    assert res.data['message'] == "Staff member updated successfully."
    assert res.data['data']['staff_handle'] == UPDATE_DATA['staff_handle']
    
    shop_staff.refresh_from_db()
    assert shop_staff.staff_handle == UPDATE_DATA['staff_handle']
    
@pytest.mark.parametrize(
    'user_type',
    ['customer', 'shop_staff'],
    ids=['customer', 'shop_staff']
)
def test_update_shop_staff_by_non_shopowner(client, all_users, user_type, shop_staff):
    """
    Test updating a specific shop staff by a non shopowner.
    """
    user = all_users[user_type]
    old_handle = shop_staff.staff_handle
    url = reverse('shop-staff-detail', kwargs={
        'shop_id': shop_staff.shop.id,
        'staff_id': shop_staff.id
    })
    client.force_authenticate(user=user)
    res = client.patch(url, data=UPDATE_DATA, format='json')
    assert res.status_code == status.HTTP_403_FORBIDDEN
    assert res.data['status'] == "error"
    assert res.data['code'] == "forbidden"
    assert res.data['message'] == "You do not have permission to perform this action."
    shop_staff.refresh_from_db()
    assert shop_staff.staff_handle == old_handle 


def test_update_shop_staff_by_another_shopowner(client, shopowner_factory, shop_staff_factory):
    """
    Test updating specific shop staff member handle by another shop owner.
    """
    sh1 = shopowner_factory()
    sh2 = shopowner_factory()
    sh_staff = shop_staff_factory(shopowner=sh2)
    old_handle = sh_staff.staff_handle
    
    url = reverse('shop-staff-detail', kwargs={
        'shop_id': sh_staff.shop.id,
        'staff_id': sh_staff.id
    })
    client.force_authenticate(user=sh1)
    res = client.patch(url, data=UPDATE_DATA, format='json')
    assert res.status_code == status.HTTP_403_FORBIDDEN
    assert res.data['status'] == "error"
    assert res.data['code'] == "forbidden"
    assert res.data['message'] == "You do not have permission to perform this action."
    sh_staff.refresh_from_db()
    assert sh_staff.staff_handle == old_handle 

def test_update_shop_staff_member_with_invalid_ids(client, shopowner, shop_staff):
    """
    Test updating specific shop staff member handle with invalid shop and staff ids.
    """
    old_handle = shop_staff.staff_handle
    url = reverse('shop-staff-detail', kwargs={
        'shop_id': 'invalid_shop_id',
        'staff_id': shop_staff.id
    })
    client.force_authenticate(user=shopowner)
    res = client.patch(url, data=UPDATE_DATA, format='json')

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "invalid_uuid"
    assert res.data['message'] == "Invalid shop id."
    shop_staff.refresh_from_db()
    assert shop_staff.staff_handle == old_handle 

    url = reverse('shop-staff-detail', kwargs={
        'shop_id': shop_staff.shop.id,
        'staff_id': 'invalid_staff_id'
    })
    res = client.patch(url, data=UPDATE_DATA, format='json')

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "invalid_uuid"
    assert res.data['message'] == "Invalid staff id."
    shop_staff.refresh_from_db()
    assert shop_staff.staff_handle == old_handle 

def test_update_shop_staff_member_with_non_existent_ids(client, shopowner, shop_staff):
    """
    Test updating specific shop staff member with non existent shop and staff ids.
    """
    old_handle = shop_staff.staff_handle
    url = reverse('shop-staff-detail', kwargs={
        'shop_id': uuid.uuid4(),
        'staff_id': shop_staff.id
    })
    client.force_authenticate(user=shopowner)
    res = client.patch(url, data=UPDATE_DATA, format='json')

    assert res.status_code == status.HTTP_404_NOT_FOUND
    assert res.data['status'] == "error"
    assert res.data['code'] == "not_found"
    assert res.data['message'] == "No shop matching the given ID found."
    shop_staff.refresh_from_db()
    assert shop_staff.staff_handle == old_handle 
    
    url = reverse('shop-staff-detail', kwargs={
        'shop_id': shop_staff.shop.id,
        'staff_id': uuid.uuid4()
    })
    res = client.patch(url, data=UPDATE_DATA, format='json')

    assert res.status_code == status.HTTP_404_NOT_FOUND
    assert res.data['status'] == "error"
    assert res.data['code'] == "not_found"
    assert res.data['message'] == "No staff member matching the given ID found."
    shop_staff.refresh_from_db()
    assert shop_staff.staff_handle == old_handle 

def test_update_shop_staff_member_by_unauthenticated_user(client, shop_staff):
    """
    Test updating specific shop staff member by unauthenticated user.
    """
    old_handle = shop_staff.staff_handle

    url = reverse('shop-staff-detail', kwargs={
        'shop_id': shop_staff.shop.id,
        'staff_id': shop_staff.id
    })
    res = client.patch(url, data=UPDATE_DATA, format='json')    
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.data['status'] == "error"
    assert res.data['code'] == "unauthorized"
    assert res.data['message'] == "Authentication credentials were not provided."
    shop_staff.refresh_from_db()
    assert shop_staff.staff_handle == old_handle 
    
    client.cookies['access_token'] = "invalid_token "
    res = client.patch(url, data=UPDATE_DATA, format='json')
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.data['status'] == "error"
    assert res.data['code'] == "unauthorized"
    assert res.data['message'] == "Token is invalid or expired"

    shop_staff.refresh_from_db()
    assert shop_staff.staff_handle == old_handle 

def test_updating_shop_staff_with_missing_staff_handle_data(client, shopowner, shop_staff):
    """
    Test updating specific shop staff member handle with missing data.
    """
    old_handle = shop_staff.staff_handle
    url = reverse('shop-staff-detail', kwargs={
        'shop_id': shop_staff.shop.id,
        'staff_id': shop_staff.id
    })
    client.force_authenticate(user=shopowner)
    res = client.patch(url, data={}, format='json')
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "validation_error"
    assert res.data['message'] == "Staff member update failed."
    assert 'staff_handle' in res.data['errors']
    assert res.data['errors']['staff_handle'] == ["This field is required."]
    shop_staff.refresh_from_db()
    assert shop_staff.staff_handle == old_handle 

def test_updating_shop_staff_with_blank_staff_handle_data(client, shopowner, shop_staff):
    """
    Test updating specific shop staff member handle with blank data.
    """
    old_handle = shop_staff.staff_handle

    url = reverse('shop-staff-detail', kwargs={
        'shop_id': shop_staff.shop.id,
        'staff_id': shop_staff.id
    })
    client.force_authenticate(user=shopowner)
    res = client.patch(url, data={'staff_handle': ''}, format='json')
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "validation_error"
    assert res.data['message'] == "Staff member update failed."
    assert 'staff_handle' in res.data['errors']
    assert res.data['errors']['staff_handle'] == ["This field may not be blank."]
    shop_staff.refresh_from_db()
    assert shop_staff.staff_handle == old_handle
    
    
def test_updating_shop_staff_with_invalid_staff_handle_data(client, shopowner, shop_staff):
    """
    Test updating specific shop staff member handle with invalid data.
    """
    old_handle = shop_staff.staff_handle
    url = reverse('shop-staff-detail', kwargs={
        'shop_id': shop_staff.shop.id,
        'staff_id': shop_staff.id
    })
    client.force_authenticate(user=shopowner)
    data = {'staff_handle': 'J'}  # too short
    res = client.patch(url, data=data, format='json')
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "validation_error"
    assert res.data['message'] == "Staff member update failed."
    assert 'staff_handle' in res.data['errors']
    assert res.data['errors']['staff_handle'] == ["Ensure this field has at least 3 characters."]
    
    shop_staff.refresh_from_db()
    assert shop_staff.staff_handle == old_handle 

    data = {'staff_handle': 'J' * 21}  # too long
    res = client.patch(url, data=data, format='json')
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "validation_error"
    assert res.data['message'] == "Staff member update failed."
    assert 'staff_handle' in res.data['errors']
    assert res.data['errors']['staff_handle'] == ["Ensure this field has no more than 20 characters."]

    shop_staff.refresh_from_db()
    assert shop_staff.staff_handle == old_handle 

def test_updating_shop_staff_with_existing_staff_handle(client, shopowner, shop_staff_factory):
    """
    Test updating staff member with already existing staff handle.
    """
    sh_staff1 = shop_staff_factory(shopowner=shopowner)
    sh_staff2 = shop_staff_factory(shopowner=shopowner)
    old_handle = sh_staff1.staff_handle
    url = reverse('shop-staff-detail', kwargs={
        'shop_id': sh_staff1.shop.id,
        'staff_id': sh_staff1.id
    })
    client.force_authenticate(user=shopowner)
    data = {'staff_handle': sh_staff2.staff_handle}

    res = client.patch(url, data=data, format='json')
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "validation_error"
    assert res.data['message'] == "Staff member update failed."
    assert res.data['errors']['staff_handle'] == ["Staff member with staff handle already exists."]

    sh_staff1.refresh_from_db()
    assert sh_staff1.staff_handle == old_handle 

# ==========================================================
# DELETE STAFF MEMBER BY ID TESTS
# ==========================================================

@pytest.mark.parametrize(
    'user_type',
    ['shopowner', 'super_user'],
    ids=['shopowner', 'super_user']
)
def test_delete_shop_staff(client, all_users, user_type, shop_staff):
    """
    Test deleting shop staff.
    """
    user = all_users[user_type]
    url = reverse('shop-staff-detail', kwargs={
        'shop_id': shop_staff.shop.id,
        'staff_id': shop_staff.id
    })
    client.force_authenticate(user=user)

    res = client.delete(url)
    assert res.status_code == status.HTTP_204_NO_CONTENT
    
    
def test_delete_shop_staff_by_shop_staff(client, shop_staff):
    """
    Test deleting shop staff member by the shop staff.
    """
    url = reverse('shop-staff-detail', kwargs={
        'shop_id': shop_staff.shop.id,
        'staff_id': shop_staff.id
    })
    client.force_authenticate(user=shop_staff)

    res = client.delete(url)
    assert res.status_code == status.HTTP_403_FORBIDDEN
    
def test_delete_shop_staff_by_customer(client, customer, shop_staff):
    """
    Test deleting shop staff member by a customer.
    """
    url = reverse('shop-staff-detail', kwargs={
        'shop_id': shop_staff.shop.id,
        'staff_id': shop_staff.id
    })
    client.force_authenticate(user=customer)

    res = client.delete(url)
    assert res.status_code == status.HTTP_403_FORBIDDEN

    
def test_delete_shop_staff_by_another_shopowner(client, shop_staff, shopowner_factory):
    """
    Test deleting shop staff member by a shop owner.
    """
    sh1 = shopowner_factory()

    url = reverse('shop-staff-detail', kwargs={
        'shop_id': shop_staff.shop.id,
        'staff_id': shop_staff.id
    })
    client.force_authenticate(user=sh1)

    res = client.delete(url)
    assert res.status_code == status.HTTP_403_FORBIDDEN


def test_delete_shop_staff_with_invalid_ids(client, shopowner, shop_staff):
    """
    Test deleting shop staff member with invalid shop and staff ids.
    """
    url = reverse('shop-staff-detail', kwargs={
        'shop_id': 'invalid_shop_id',
        'staff_id': shop_staff.id
    })
    client.force_authenticate(user=shopowner)
    res = client.delete(url)

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "invalid_uuid"
    assert res.data['message'] == "Invalid shop id."

    url = reverse('shop-staff-detail', kwargs={
        'shop_id': shop_staff.shop.id,
        'staff_id': 'invalid_staff_id'
    })
    res = client.delete(url)

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "invalid_uuid"
    assert res.data['message'] == "Invalid staff id."
    

def test_delete_shop_staff_member_with_non_existent_ids(client, shopowner, shop_staff):
    """
    Test deleting specific shop staff member with non existent shop and staff ids.
    """
    url = reverse('shop-staff-detail', kwargs={
        'shop_id': uuid.uuid4(),
        'staff_id': shop_staff.id
    })
    client.force_authenticate(user=shopowner)
    res = client.get(url)

    assert res.status_code == status.HTTP_404_NOT_FOUND
    assert res.data['status'] == "error"
    assert res.data['code'] == "not_found"
    assert res.data['message'] == "No shop matching the given ID found."

    url = reverse('shop-staff-detail', kwargs={
        'shop_id': shop_staff.shop.id,
        'staff_id': uuid.uuid4()
    })
    res = client.delete(url)

    assert res.status_code == status.HTTP_404_NOT_FOUND
    assert res.data['status'] == "error"
    assert res.data['code'] == "not_found"
    assert res.data['message'] == "No staff member matching the given ID found."


def test_get_shop_staff_member_by_unauthenticated_user(client, shop_staff):
    """
    Test getting specific shop staff member by unauthenticated user.
    """
    url = reverse('shop-staff-detail', kwargs={
        'shop_id': shop_staff.shop.id,
        'staff_id': shop_staff.id
    })
    
    res = client.delete(url)
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.data['status'] == "error"
    assert res.data['code'] == "unauthorized"
    assert res.data['message'] == "Authentication credentials were not provided."
    
    client.cookies['access_token'] = "invalid_token "
    res = client.delete(url)
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.data['status'] == "error"
    assert res.data['code'] == "unauthorized"
    assert res.data['message'] == "Token is invalid or expired"
