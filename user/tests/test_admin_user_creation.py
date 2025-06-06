from django.urls import reverse
from rest_framework import status


create_admin_url = reverse('create-admin')

def test_admin_user_creation_by_superuser(client, signed_in_superuser):
    """
    Test admin user creation by super user.
    """
    tokens = signed_in_superuser
    data = {
        'staff_id': 'admin-user2',
        'password': 'Password123#',
        'confirm_password': 'Password123#'
    }
    client.cookies['access_token'] == tokens['access_token']
    response = client.post(create_admin_url, data, format='json')
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data['status'] == "success"
    assert response.data['message'] == f"Admin user {data['staff_id']} created successfully."


def test_admin_user_creation_by_non_superuser(client, signed_in_admin):
    """
    Test admin user creation by non super user.
    """
    tokens = signed_in_admin
    data = {
        'staff_id': 'admin-user2',
        'password': 'Password123#',
        'confirm_password': 'Password123#'
    }
    client.cookies['access_token'] == tokens['access_token']
    response = client.post(create_admin_url, data, format='json')
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.data['status'] == "error"
    assert response.data['message'] == "You do not have permission to perform this action."


def test_admin_user_creation_by_without_access_token(client):
    """
    Test admin user creation without super user access token passed.
    """
    data = {
        'staff_id': 'admin-user2',
        'password': 'Password123#',
        'confirm_password': 'Password123#'
    }
    response = client.post(create_admin_url, data, format='json')
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data['status'] == "error"
    assert response.data['message'] == "Authentication credentials were not provided."



def test_admin_user_creation_missing_staff_id(client, signed_in_superuser):
    """
    Test admin user creation by super user process with
    missing staff_id.
    """
    tokens = signed_in_superuser
    data = {
        'password': 'Password123#',
        'confirm_password': 'Password123#'
    }
    client.cookies['access_token'] == tokens['access_token']
    response = client.post(create_admin_url, data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['status'] == 'error'
    assert response.data['message'] == "Please provide staff_id (username) and password for the staff."


def test_admin_user_creation_missing_password(client, signed_in_superuser):
    """
    Test admin user creation by super user process with
    missing password.
    """
    tokens = signed_in_superuser
    data = {
        'staff_id': 'admin-user2',
        'confirm_password': 'Password123#'
    }
    client.cookies['access_token'] == tokens['access_token']
    response = client.post(create_admin_url, data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['status'] == 'error'
    assert response.data['message'] == "Please provide staff_id (username) and password for the staff."



def test_admin_user_creation_mismatching_password(client, signed_in_superuser):
    """
    Test admin user creation by super user process with
    mismatching passwords.
    """
    tokens = signed_in_superuser
    data = {
        'staff_id': 'admin-user2',
        'password': 'Password123#',
        'confirm_password': 'Password1234#'
    }
    client.cookies['access_token'] == tokens['access_token']
    response = client.post(create_admin_url, data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['status'] == 'error'
    assert response.data['message'] == "Password and confirm_password fields do not match."


def test_admin_user_creation_password_length(client, signed_in_superuser):
    """
    Test the user registration process with a short password.
    """
    tokens = signed_in_superuser
    data = {
        'staff_id': 'admin-user2',
        'password': 'passw12',
        'confirm_password': 'passw12'
    }
    client.cookies['access_token'] == tokens['access_token']
    response = client.post(create_admin_url, data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['status'] == 'error'
    assert response.data['message'] == "Password must be at least 8 characters long."



def test_admin_user_creation_existing_staff_id(client, signed_in_superuser, admin_user):
    """
    Test admin user creation by super user process with
    existing staff_id.
    """
    tokens = signed_in_superuser
    data = {
        'staff_id': 'admin-user',
        'password': 'Password123#',
        'confirm_password': 'Password123#'
    }
    client.cookies['access_token'] == tokens['access_token']
    response = client.post(create_admin_url, data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['status'] == 'error'
    assert response.data['message'] == "Admin user with staff id already exists."


def test_admin_user_creation_password_without_digit(client, signed_in_superuser):
    """
    Test the user registration process with a password without digits.
    """
    tokens = signed_in_superuser
    data = {
        'staff_id': 'admin-user2',
        'password': 'Weak_password#',
        'confirm_password': 'Weak_password#'
    }
    client.cookies['access_token'] == tokens['access_token']
    response = client.post(create_admin_url, data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['status'] == 'error'
    assert response.data['message'] == "Password must contain at least one digit."


def test_admin_user_creation_password_without_special_char(client, signed_in_superuser):
    """
    Test the user registration process with a password without special character.
    """
    tokens = signed_in_superuser
    data = {
        'staff_id': 'admin-user2',
        'password': 'Weak_password123',
        'confirm_password': 'Weak_password123'
    }
    client.cookies['access_token'] == tokens['access_token']
    response = client.post(create_admin_url, data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['status'] == 'error'
    assert response.data['message'] == "Password must contain at least one special character."


def test_admin_user_creation_password_without_letters(client, signed_in_superuser):
    """
    Test the user registration process with a password without special character.
    """
    tokens = signed_in_superuser
    data = {
        'staff_id': 'admin-user2',
        'password': '12345678#',
        'confirm_password': '12345678#'
    }
    client.cookies['access_token'] == tokens['access_token']
    response = client.post(create_admin_url, data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['status'] == 'error'
    assert response.data['message'] == "Password must contain at least one letter."
