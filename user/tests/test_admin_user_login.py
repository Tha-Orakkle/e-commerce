from django.urls import reverse
from rest_framework import status


admin_login_url = reverse('admin-login')

def test_admin_user_login(client, admin_user):
    """
    Test the admin user login process.
    """
    data = {
        'staff_id': admin_user.staff_id,
        'password': 'Password123#'
    }
    response = client.post(admin_login_url, data, format='json')
    assert response.status_code == status.HTTP_200_OK
    assert response.data['message'] == "Admin user logged in successfully."
    assert response.data['data']['staff_id'] == admin_user.staff_id
    assert response.cookies['access_token'].value is not None
    assert response.cookies['refresh_token'].value is not None
    assert response.cookies['access_token']['httponly'] is True
    assert response.cookies['refresh_token']['httponly'] is True


def test_admin_user_login_missing_staff_id(client, admin_user):
    """
    Test the admin user login process with a missing staff_id.
    """
    data = {
        'password': 'Password123#'
    }
    response = client.post(admin_login_url, data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['status'] == "error"
    assert response.data['message'] == "Please provide staff id and password."


def test_admin_user_login_missing_password(client, admin_user):
    """
    Test the admin user login process with a missing password.
    """
    data = {
        'password': 'Password123#'
    }
    response = client.post(admin_login_url, data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['status'] == "error"
    assert response.data['message'] == "Please provide staff id and password."


def test_admin_user_invalid_password(client, admin_user):
    """
    Test the admin user login process with wrong password.
    """
    data = {
        'staff_id': admin_user.staff_id,
        'password': 'Password1234#'
    }
    response = client.post(admin_login_url, data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['status'] == "error"
    assert response.data['message'] == "Invalid login credentials."


def test_admin_user_non_existent_staff_id(client, db_access):
    """
    Test the admin user login process with wrong password.
    """
    data = {
        'staff_id': 'admin-non-existent',
        'password': 'Password123#'
    }
    response = client.post(admin_login_url, data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['status'] == "error"
    assert response.data['message'] == "Invalid login credentials."


def test_admin_user_login_no_remember_me(client, admin_user):
    """
    Test the admin user login process with remember_me set to False.
    """
    data = {
        'staff_id': admin_user.staff_id,
        'password': 'Password123#',
        'remember_me': False
    }
    response = client.post(admin_login_url, data, format='json')
    assert response.status_code == status.HTTP_200_OK
    assert response.data['status'] == "success"
    assert response.data['message'] == "Admin user logged in successfully."
    assert response.cookies['refresh_token']
    assert response.cookies['refresh_token']['max-age'] is not None
    assert response.cookies['refresh_token']['max-age'] == 86400


def test_admin_user_login_remember_me(client, admin_user):
    """"
    Test the admin user login process with remember_me set to True.
    """
    data = {
        'staff_id': admin_user.staff_id,
        'password': 'Password123#',
        'remember_me': True
    }
    response = client.post(admin_login_url, data, format='json')
    assert response.status_code == status.HTTP_200_OK
    assert response.data['status'] == "success"
    assert response.data['message'] == "Admin user logged in successfully."
    assert response.cookies['refresh_token']['max-age'] is not None
    assert response.cookies['refresh_token']['max-age'] == 604800

    