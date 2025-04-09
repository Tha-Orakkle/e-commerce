from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
import pytest

User = get_user_model()


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def db_access(db):
    """
    Enable database access for tests that require it.
    """
    pass

@pytest.fixture
def user(db):
    """
    Creates the user
    """
    return User.objects.create_user(
        email="user@email.com",
        password="Password123#",    
    )


@pytest.fixture
def inactive_user(db):
    """
    Creates the inactive user
    """
    return User.objects.create_user(
        email="inactiveuser@email.com",
        password="Password123#",
        is_active=False,
    )


@pytest.fixture
def signed_in_user(client, user):
    """
    Signs in the user
    Return the refresh token and access token
    """
    login_url = reverse('login')
    data = {
        'email': user.email,
        'password': 'Password123#'
    }
    response = client.post(login_url, data, format='json')
    assert response.status_code == 200
    assert 'refresh_token' in response.cookies
    assert 'access_token' in response.cookies
    return {
        'refresh_token': response.cookies['refresh_token'].value,
        'access_token': response.cookies['access_token'].value
    }
    