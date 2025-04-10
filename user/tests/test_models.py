"""
Test models for the user app.
These tests cover the User and UserProfile models.
"""
from django.contrib.auth import get_user_model

from user.models import UserProfile


User = get_user_model()

def test_user_creation(user):
    """
    Test the creation of a user.
    """
    assert user.id is not None
    assert type(user.id).__name__ == "UUID"
    assert user.is_active == True
    assert user.is_staff == False
    assert user.is_verified == False
    assert user.is_superuser == False
    assert user.email == "user@email.com"
    assert user.password != "Password123#"
    assert user.check_password("Password123#")

def test_admin_user_creation(admin_user):
    """
    Test the creation of an admin user.
    """
    assert admin_user.id is not None
    assert type(admin_user.id).__name__ == "UUID"
    assert admin_user.is_active == True
    assert admin_user.is_staff == True
    assert admin_user.is_verified == True
    assert admin_user.is_superuser == False
    assert admin_user.staff_id == "admin-user"
    assert admin_user.password != "Password123#"
    assert admin_user.check_password("Password123#")


def test_user_str(user):
    """
    Test the string representation of a user.
    """
    assert str(user) == f"<User: {user.id}> {user.email}"


def test_user_profile_creation(user):
    """
    Test the creation of a user profile.
    """
    assert user.profile is not None
    assert user.profile.first_name == ""
    assert user.profile.last_name == ""
    assert user.profile.telephone == ""
    assert user.profile.user == user


def test_user_profile_str(user):
    """
    Test the string representation of a user profile.
    """
    assert str(user.profile) == f"<UserProfile: {user.profile.id}> {user.email}"


def test_user_profile_deletes_when_user_is_deleted(user):
    """
    Tests that the user profile associated with a user is deleted
    when the user is deleted.
    """
    assert User.objects.count() == 1
    assert UserProfile.objects.count() == 1
    user.delete()
    assert User.objects.count() == 0
    assert UserProfile.objects.count() == 0
