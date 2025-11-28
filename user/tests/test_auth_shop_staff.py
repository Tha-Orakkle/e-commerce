from django.urls import reverse
from rest_framework import status

import uuid

# ==========================================================
# SHOP STFF CREATION TESTS
# ==========================================================
STAFF_CREATION_DATA = {
        'first_name': 'Jane',
        'last_name': 'Doe',
        'telephone': '08121119999',
        'staff_handle': 'staff1',
        'password': 'Password123#',
        'confirm_password': 'Password123#'        
    } 

def get_staff_creation_url(id):
    return reverse(
        'shop-staff-list-create',
        kwargs={'shop_id': id}
)

def test_shop_staff_creation_by_shop_owner(request, client, shopowner):
    """
    Test shop staff creation by shop owner.
    """
    tokens = request.getfixturevalue('signed_in_shopowner')
    url = get_staff_creation_url(shopowner.owned_shop.id)
    client.cookies['access_token']  = tokens['access_token']
    data = STAFF_CREATION_DATA
    res = client.post(url, data, format='json')
    
    assert res.status_code == status.HTTP_201_CREATED
    assert res.data['message'] == "Shop staff member creation successful."
    assert res.data['data'] is not None
    assert res.data['data']['staff_handle'] == data['staff_handle']
    assert res.data['data']['is_staff'] == True
    assert res.data['data']['profile']['first_name'] == data['first_name']
    assert res.data['data']['profile']['last_name'] == data['last_name']

def test_shop_staff_creation_by_shop_owner_without_access_token(client, shopowner):
    """
    Test shop staff creation by shop owner without access token.
    """
    url = get_staff_creation_url(shopowner.owned_shop.id)
    data = STAFF_CREATION_DATA
    res = client.post(url, data, format='json')

    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.data['status'] == "error"
    assert res.data['code'] == "unauthorized"
    assert res.data['message'] == "Authentication credentials were not provided."

def test_shop_staff_creation_by_shop_owner_wit_invalid_access_token(client, shopowner):
    """
    Test shop staff creation by shop owner with invalid token.
    """
    url = get_staff_creation_url(shopowner.owned_shop.id)
    data = STAFF_CREATION_DATA
    client.cookies['access_token'] = "invalid_token"
    res = client.post(url, data, format='json')

    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.data['status'] == "error"
    assert res.data['code'] == "unauthorized"
    print(res.data['message'])
    assert res.data['message'] == "Token is invalid or expired"

def test_shop_staff_creation_by_customer(request, client, dummy_shop):
    """
    Test shop staff creation by a customer.
    """
    tokens = request.getfixturevalue('signed_in_customer')
    url = get_staff_creation_url(dummy_shop.id)
    client.cookies['access_token'] = tokens['access_token']

    res = client.post(url, STAFF_CREATION_DATA, format='json')

    assert res.status_code == status.HTTP_403_FORBIDDEN
    assert res.data['status'] == "error"
    assert res.data['code'] == "forbidden"
    assert res.data['message'] == "You do not have permission to perform this action."

def test_shop_staff_creation_by_non_owner_shop(request, client, dummy_shop):
    """
    Test shop staff creation by a shop owner whose shop is different.
    """
    tokens = request.getfixturevalue('signed_in_shopowner')
    url = get_staff_creation_url(dummy_shop.id)
    client.cookies['access_token'] = tokens['access_token']

    res = client.post(url, STAFF_CREATION_DATA, format='json')

    assert res.status_code == status.HTTP_403_FORBIDDEN
    assert res.data['status'] == "error"
    assert res.data['code'] == "forbidden"
    assert res.data['message'] == "You do not have permission to perform this action."

def test_shop_staff_creation_with_non_existing_shop_id(request, client):
    """
    Test shop staff creation with non-existing shop ID.
    """
    tokens = request.getfixturevalue('signed_in_shopowner')
    url = get_staff_creation_url(uuid.uuid4())
    client.cookies['access_token'] = tokens['access_token']

    res = client.post(url, STAFF_CREATION_DATA, format='json')

    assert res.status_code == status.HTTP_404_NOT_FOUND
    assert res.data['status'] == "error"
    assert res.data['code'] == "not_found"
    assert res.data['message'] == "No shop matching the given ID found."

def test_shop_staff_creation_with_invalid_shop_uuid(request, client, shopowner):
    """
    Test shop staff creation with invalid shop UUID.
    """
    tokens = request.getfixturevalue('signed_in_shopowner')
    url = get_staff_creation_url('invalid-uuid')
    client.cookies['access_token'] = tokens['access_token']

    res = client.post(url, STAFF_CREATION_DATA, format='json')

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "invalid_uuid"
    assert res.data['message'] == "Invalid shop id."

def test_shop_staff_creation_by_shop_staff(request, client, shop_staff):
    """
    Test shop staff creation by a shop staff.
    """
    tokens = request.getfixturevalue('signed_in_staff')
    url = get_staff_creation_url(shop_staff.shop.id)
    client.cookies['access_token'] = tokens['access_token']

    res = client.post(url, STAFF_CREATION_DATA, format='json')

    assert res.status_code == status.HTTP_403_FORBIDDEN
    assert res.data['status'] == "error"
    assert res.data['code'] == "forbidden"
    assert res.data['message'] == "You do not have permission to perform this action."

def test_shop_staff_creation_with_existing_staff_handle(request, client, shopowner):
    """
    Test shop staff creation with existing staff handle.
    """
    tokens = request.getfixturevalue('signed_in_shopowner')
    url = get_staff_creation_url(shopowner.owned_shop.id)
    client.cookies['access_token'] = tokens['access_token']
    existing_staff_data = STAFF_CREATION_DATA
    # create the first staff member
    res1 = client.post(url, existing_staff_data, format='json')
    assert res1.status_code == status.HTTP_201_CREATED

    # attempt to create another staff member with same handle
    res2 = client.post(url, existing_staff_data, format='json')

    assert res2.status_code == status.HTTP_400_BAD_REQUEST
    assert res2.data['status'] == "error"
    assert res2.data['code'] == "validation_error"
    assert res2.data['message'] == "Shop staff member creation failed."
    assert res2.data['errors'] is not None
    assert res2.data['errors']['staff_handle'] == ["Staff member with handle already exists."]

def test_shop_staff_creation_with_invalid_staff_handle(request, client, shopowner):
    """
    Test shop staff creation with invalid staff handle.
    """
    tokens = request.getfixturevalue('signed_in_shopowner')
    url = get_staff_creation_url(shopowner.owned_shop.id)
    client.cookies['access_token'] = tokens['access_token']
    invalid_data = STAFF_CREATION_DATA.copy()
    invalid_data['staff_handle'] = 'ab'  # too short

    res = client.post(url, invalid_data, format='json')

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "validation_error"
    assert res.data['message'] == "Shop staff member creation failed."
    assert res.data['errors'] is not None
    assert res.data['errors']['staff_handle'] == ["Ensure this field has at least 3 characters."]

    invalid_data['staff_handle'] = 'a' * 21  # too long
    res = client.post(url, invalid_data, format='json')
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['errors']['staff_handle'] == ["Ensure this field has no more than 20 characters."]

def test_shop_staff_creation_with_missing_data(request, client, shopowner):
    """
    Test shop staff creation with missing data.
    """
    tokens = request.getfixturevalue('signed_in_shopowner')
    url = get_staff_creation_url(shopowner.owned_shop.id)
    client.cookies['access_token'] = tokens['access_token']
    incomplete_data = {} 

    res = client.post(url, incomplete_data, format='json')

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "validation_error"
    assert res.data['message'] == "Shop staff member creation failed."
    assert res.data['errors'] is not None
    assert res.data['errors']['password'] == ["This field is required."]
    assert res.data['errors']['confirm_password'] == ["This field is required."]
    assert res.data['errors']['first_name'] == ["This field is required."]
    assert res.data['errors']['last_name'] == ["This field is required."]
    assert res.data['errors']['telephone'] == ["This field is required."]
    assert res.data['errors']['staff_handle'] == ["This field is required."]

def test_shop_staff_creation_with_invalid_first_and_last_name(request, client, shopowner):
    """
    Test shop staff creation with invalid first name and last name.
    """
    tokens = request.getfixturevalue('signed_in_shopowner')
    url = get_staff_creation_url(shopowner.owned_shop.id)
    client.cookies['access_token'] = tokens['access_token']
    invalid_data = STAFF_CREATION_DATA.copy()
    invalid_data['first_name'] = 'J'  # too short
    invalid_data['last_name'] = 'D'   # too short

    res = client.post(url, invalid_data, format='json')

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "validation_error"
    assert res.data['message'] == "Shop staff member creation failed."
    assert res.data['errors'] is not None
    assert res.data['errors']['first_name'] == ["Ensure this field has at least 2 characters."]
    assert res.data['errors']['last_name'] == ["Ensure this field has at least 2 characters."]

    invalid_data['first_name'] = 'J' * 31  # too long
    invalid_data['last_name'] = 'D' * 31   # too long
    res = client.post(url, invalid_data, format='json')
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['errors']['first_name'] == ["Ensure this field has no more than 30 characters."]
    assert res.data['errors']['last_name'] == ["Ensure this field has no more than 30 characters."]

def test_shop_staff_creation_with_invalid_telephone(request, client, shopowner):
    """
    Test shop staff creation with invalid telephone number.
    """
    tokens = request.getfixturevalue('signed_in_shopowner')
    url = get_staff_creation_url(shopowner.owned_shop.id)
    client.cookies['access_token'] = tokens['access_token']
    invalid_data = STAFF_CREATION_DATA.copy()
    invalid_data['telephone'] = 'invalid_phone'

    res = client.post(url, invalid_data, format='json')

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "validation_error"
    assert res.data['message'] == "Shop staff member creation failed."
    assert res.data['errors'] is not None
    assert res.data['errors']['telephone'] == ["Enter a valid phone number."]

def test_shop_staff_creation_with_invalid_passwords(request, client, shopowner):
    """
    Test shop staff creation with invalid passwords.
    """
    tokens = request.getfixturevalue('signed_in_shopowner')
    url = get_staff_creation_url(shopowner.owned_shop.id)
    client.cookies['access_token'] = tokens['access_token']
    invalid_data = STAFF_CREATION_DATA.copy()
    invalid_data['password'] = 'short'
    invalid_data['confirm_password'] = 'short'

    res = client.post(url, invalid_data, format='json')

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "validation_error"
    assert res.data['message'] == "Shop staff member creation failed."
    assert res.data['errors'] is not None
    assert 'password' in res.data['errors']

    # Test non-matching passwords
    invalid_data['password'] = 'Password123#'
    invalid_data['confirm_password'] = 'Password1234#'

    res = client.post(url, invalid_data, format='json')

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "validation_error"
    assert res.data['message'] == "Shop staff member creation failed."
    assert res.data['errors'] is not None
    assert res.data['errors']['confirm_password'] == ["Passwords do not match."]

# ==========================================================
# SHOP OWNER AND STFF LOGIN TESTS
# ==========================================================

STAFF_LOGIN_URL = reverse('staff-login')

def test_staff_login_as_shopowner(client, shopowner):
    """
    Test staff login as a shop owner.
    """
    data = {
        'shop_code': shopowner.owned_shop.code,
        'staff_handle': shopowner.staff_handle,
        'password': 'Password123#',
        'remember_me': True
    }
    res = client.post(STAFF_LOGIN_URL, data, format='json')

    assert res.status_code == status.HTTP_200_OK
    assert res.data['status'] == "success"
    assert res.data['message'] == "Log in successful."
    assert res.data['data'] is not None
    assert res.data['data']['id'] == str(shopowner.id)
    assert res.cookies.get('access_token') is not None
    assert res.cookies.get('refresh_token') is not None
    assert res.cookies['refresh_token']['max-age'] == 604800

def test_staff_login_as_shop_staff(client, shop_staff):
    """
    Test staff login as a shop staff.
    """
    data = {
        'shop_code': shop_staff.shop.code,
        'staff_handle': shop_staff.staff_handle,
        'password': 'Password123#',
        'remember_me': True
    }
    res = client.post(STAFF_LOGIN_URL, data, format='json')

    assert res.status_code == status.HTTP_200_OK
    assert res.data['status'] == "success"
    assert res.data['message'] == "Log in successful."
    assert res.data['data'] is not None
    assert res.data['data']['id'] == str(shop_staff.id)
    assert res.cookies.get('access_token') is not None
    assert res.cookies.get('refresh_token') is not None
    assert res.cookies['refresh_token']['max-age'] == 604800

def test_staff_login_false_remember_me(client, shop_staff):
    """
    Test staff login with false remember me.
    Refresh token expires after one day.
    """
    data = {
        'shop_code': shop_staff.shop.code,
        'staff_handle': shop_staff.staff_handle,
        'password': 'Password123#',
        'remember_me': False
    }
    res = client.post(STAFF_LOGIN_URL, data, format='json')

    assert res.status_code == status.HTTP_200_OK
    assert res.data['status'] == "success"
    assert res.data['message'] == "Log in successful."
    assert res.data['data'] is not None
    assert res.cookies.get('access_token') is not None
    assert res.cookies.get('refresh_token') is not None
    assert res.cookies['refresh_token']['max-age'] == 86400

def test_staff_login_with_invalid_shop_code(client, shop_staff):
    """
    Test staff login using invalid shop code.
    """
    data = {
        'shop_code': 'SH_invalid_code',
        'staff_handle': shop_staff.staff_handle,
        'password': 'Password123#',
        'remember_me': True
    }
    res = client.post(STAFF_LOGIN_URL, data, format='json')

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['message'] == "Log in failed."
    assert res.data['code'] == "invalid_credentials"
    assert res.data['errors'] is not None
    assert res.data['errors']['non_field_errors'] == ["Invalid login credentials were provided."]
    assert res.cookies.get('access_token') is None
    assert res.cookies.get('refresh_token') is None

def test_staff_login_with_invalid_staff_handle(client, shop_staff):
    """
    Test staff login using invalid staff handle.
    """
    data = {
        'shop_code': shop_staff.shop.code,
        'staff_handle': 'invalid_handle',
        'password': 'Password123#',
        'remember_me': True
    }
    res = client.post(STAFF_LOGIN_URL, data, format='json')

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['message'] == "Log in failed."
    assert res.data['code'] == "invalid_credentials"
    assert res.data['errors'] is not None
    assert res.data['errors']['non_field_errors'] == ["Invalid login credentials were provided."]
    assert res.cookies.get('access_token') is None
    assert res.cookies.get('refresh_token') is None

def test_staff_login_with_invalid_password(client, shop_staff):
    """
    Test staff login using invalid password.
    """
    data = {
        'shop_code': shop_staff.shop.code,
        'staff_handle': shop_staff.staff_handle,
        'password': 'invalid_password',
        'remember_me': True
    }
    res = client.post(STAFF_LOGIN_URL, data, format='json')

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['message'] == "Log in failed."
    assert res.data['code'] == "invalid_credentials"
    assert res.data['errors'] is not None
    assert res.data['errors']['non_field_errors'] == ["Invalid login credentials were provided."]
    assert res.cookies.get('access_token') is None
    assert res.cookies.get('refresh_token') is None

def test_staff_login_with_missing_shop_code(client, shop_staff):
    """
    Test staff login with missing staff code.
    """
    data = {
        'staff_handle': shop_staff.staff_handle,
        'password': 'Password123#',
        'remember_me': True
    }
    res = client.post(STAFF_LOGIN_URL, data, format='json')

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['message'] == "Log in failed."
    assert res.data['code'] == "validation_error"
    assert res.data['errors'] is not None
    assert res.data['errors']['shop_code'] == ["This field is required."]
    assert res.cookies.get('access_token') is None
    assert res.cookies.get('refresh_token') is None    

def test_staff_login_with_missing_staff_handle(client, shop_staff):
    """
    Test staff login with missing staff handle.
    """
    data = {
        'shop_code': shop_staff.shop.code,
        'password': 'Password123#',
        'remember_me': True
    }
    res = client.post(STAFF_LOGIN_URL, data, format='json')

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['message'] == "Log in failed."
    assert res.data['code'] == "validation_error"
    assert res.data['errors'] is not None
    assert res.data['errors']['staff_handle'] == ["This field is required."]
    assert res.cookies.get('access_token') is None
    assert res.cookies.get('refresh_token') is None

def test_staff_login_with_missing_password(client, shop_staff):
    """
    Test staff login with missing password.
    """
    data = {
        'shop_code': shop_staff.shop.code,
        'staff_handle': shop_staff.staff_handle,
        'remember_me': True
    }
    res = client.post(STAFF_LOGIN_URL, data, format='json')

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['message'] == "Log in failed."
    assert res.data['code'] == "validation_error"
    assert res.data['errors'] is not None
    assert res.data['errors']['password'] == ["This field is required."]
    assert res.cookies.get('access_token') is None
    assert res.cookies.get('refresh_token') is None
