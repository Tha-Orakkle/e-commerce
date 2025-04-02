from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
import pytest

User = get_user_model()


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def user(db):
    """
    Creates the user
    """
    return User.objects.create_user(
        email="user@email.com",
        password="password123#",    
    )


@pytest.fixture
def inactive_user(db):
    """
    Creates the inactive user
    """
    return User.objects.create_user(
        email="inactiveuser@email.com",
        password="password123#",
        is_active=False,
    )

@pytest.fixture
def db_access(db):
    """
    Enable database access for tests that require it.
    """
    pass