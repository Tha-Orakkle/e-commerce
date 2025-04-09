from django.urls import reverse
from rest_framework import status


def test_user_login(client, user):
    """
    Test the user login process.
    """
    url = reverse('login')
    data = {
        'email': user.email,
        'password': 'Password123#',
        'remember_me': True
    }
    response = client.post(url, data, format='json')
    assert response.status_code == status.HTTP_200_OK
    assert response.data['status'] == "success"
    assert response.data['message'] == f"User login successful."
    assert response.data['data']['id'] == str(user.id)
    assert response.data['data']['email'] == user.email
    assert response.cookies['refresh_token']['httponly'] is True
    assert response.cookies['access_token']['httponly'] is True


def test_user_login_missing_email(client):
    """
    Test the user login process with missing email.
    """
    url = reverse('login')
    data = {
        'password': 'password123#'
    }

    response = client.post(url, data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['status'] == "error"
    assert response.data['message'] == "Please provide email and password."


def test_user_login_missing_password(client):
    """
    Test the user login process with missing password.
    """
    url = reverse('login')
    data = {
        'email': 'user@email.com',
    }
    response = client.post(url, data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['status'] == "error"
    assert response.data['message'] == "Please provide email and password."


def test_user_login_invalid_password(client, user):
    """
    Test the user login process with invalid password.
    """
    url = reverse('login')
    data = {
        'email': user.email,
        'password': 'wrong_password'
    }
    response = client.post(url, data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['status'] == "error"
    assert response.data['message'] == "Invalid login credentials."


def test_user_login_invalid_email(client, db_access):
    """"
    Test the user login process with invalid email.
    """
    url = reverse('login')
    data = {
        'email': 'invalid_email',
        'password': 'password123#'
    }
    response = client.post(url, data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['status'] == "error"
    assert response.data['message'] == "Invalid login credentials."


def test_user_login_nonexistent_email(client, db_access):
    """
    Test the user login process with a non-existent email.
    """
    url = reverse('login')
    data = {
        'email': 'nonexistent@email.com',
        'password': 'password123#'
    }
    response = client.post(url, data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['status'] == "error"
    assert response.data['message'] == "Invalid login credentials."


def test_user_login_inactive_user(client, inactive_user):
    """
    Test the user login process with an inactive user.
    """
    url = reverse('login')
    data = {
        'email': inactive_user.email,
        'password': 'Password123#'
    }
    response = client.post(url, data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['status'] == "error"
    assert response.data['message'] == "Invalid login credentials."


def test_user_login_no_remember_me(client, user):
    """
    Test the user login process with remember_me set to False.
    """
    url = reverse('login')
    data = {
        'email': user.email,
        'password': 'Password123#',
        'remember_me': False
    }
    response = client.post(url, data, format='json')
    assert response.status_code == status.HTTP_200_OK
    assert response.data['status'] == "success"
    assert response.data['message'] == f"User login successful."
    assert response.cookies['refresh_token']
    assert response.cookies['refresh_token']['max-age'] is not None
    assert response.cookies['refresh_token']['max-age'] == 86400


def test_user_login_remember_me(client, user):
    """"
    Test the user login process with remember_me set to True.
    """
    url = reverse('login')
    data = {
        'email': user.email,
        'password': 'Password123#',
        'remember_me': True
    }
    response = client.post(url, data, format='json')
    assert response.status_code == status.HTTP_200_OK
    assert response.data['status'] == "success"
    assert response.data['message'] == f"User login successful."
    assert response.cookies['refresh_token']['max-age'] is not None
    assert response.cookies['refresh_token']['max-age'] == 604800
