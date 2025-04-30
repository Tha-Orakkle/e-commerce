from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from unittest.mock import patch
import pytest

User = get_user_model()


# CLIENT
@pytest.fixture
def client():
    return APIClient()


# DB ACCESS
@pytest.fixture
def db_access(db):
    """
    Enable database access for tests that require it.
    """
    pass


# USERS
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
def super_user(db):
    """
    Creates an admin user
    """
    return User.objects.create_superuser(
        email='admin_superuser@email.com',
        staff_id='admin-superuser',
        password="Password123#"
    )


@pytest.fixture
def admin_user(db):
    """
    Create an admin user.
    """
    return User.objects.create_staff(
        staff_id='admin-user',
        password='Password123#'
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
    

@pytest.fixture
def signed_in_superuser(client, super_user):
    """
    Sign in the super user.
    Return the refresh token and access token
    """
    admin_login_url = reverse('admin-login')
    data = {
        'staff_id': super_user.staff_id,
        'password': 'Password123#'
    }
    response = client.post(admin_login_url, data, format='json')
    assert response.status_code == 200
    assert 'refresh_token' in response.cookies
    assert 'access_token' in response.cookies
    return {
        'refresh_token': response.cookies['refresh_token'].value,
        'access_token': response.cookies['access_token'].value
    }
    

@pytest.fixture
def signed_in_admin(client, admin_user):
    """
    Sign in the admin.
    Return the refresh token and access token
    """
    admin_login_url = reverse('admin-login')
    data = {
        'staff_id': admin_user.staff_id,
        'password': 'Password123#'
    }
    response = client.post(admin_login_url, data, format='json')
    assert response.status_code == 200
    assert 'refresh_token' in response.cookies
    assert 'access_token' in response.cookies
    return {
        'refresh_token': response.cookies['refresh_token'].value,
        'access_token': response.cookies['access_token'].value
    }


# MOCKED TASKS
@pytest.fixture
def mock_verification_email_task():
    with patch('user.tasks.send_verification_mail_task.delay') as mocked_task:
        yield mocked_task

@pytest.fixture
def mock_password_reset_email_task():
    with patch('user.tasks.send_password_reset_mail_task.delay') as mocked_task:
        yield mocked_task