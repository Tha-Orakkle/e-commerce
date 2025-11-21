from django.urls import reverse
from rest_framework import status

# ==========================================================
# SHOP STFF CREATION TESTS
# ==========================================================



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
