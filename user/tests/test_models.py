"""
Test models for the user app.
These tests cover the User and UserProfile models.
"""
from django.contrib.auth import get_user_model

import pytest

from user.models import UserProfile


User = get_user_model()

def test_customer_creation(customer):
    """
    Test customer creation.
    """
    assert customer.id is not None
    assert type(customer.id).__name__ == "UUID"
    assert customer.is_active == True
    assert customer.is_customer == True
    assert customer.is_staff == False
    assert customer.is_verified == False
    assert customer.is_superuser == False
    assert customer.email == "customer1@email.com"
    assert customer.password != "Password123#"
    assert customer.check_password("Password123#")


def test_shop_owner_creation(shopowner):
    """
    Test shop owner creation.
    """
    assert shopowner.id is not None
    assert type(shopowner.id).__name__ == "UUID"
    assert shopowner.is_active == True
    assert shopowner.is_customer == False
    assert shopowner.is_shopowner == True
    assert shopowner.is_staff == True
    assert shopowner.is_verified == False
    assert shopowner.is_superuser == False
    assert shopowner.email == "shopowner1@email.com"
    assert shopowner.staff_handle == "shopowner1"
    assert shopowner.password != "Password123#"
    assert shopowner.check_password("Password123#")


def test_shop_staff_creation(shop_staff):
    """
    Test shop staff creation.
    """
    assert shop_staff.id is not None
    assert type(shop_staff.id).__name__ == "UUID"
    assert shop_staff.is_active == True
    assert shop_staff.is_customer == False
    assert shop_staff.is_shopowner == False
    assert shop_staff.is_staff == True
    assert shop_staff.is_verified == True
    assert shop_staff.is_superuser == False
    assert shop_staff.email == None
    assert shop_staff.staff_handle is not None
    assert shop_staff.staff_handle != ""
    assert shop_staff.password != "Password123#"
    assert shop_staff.check_password("Password123#")


@pytest.mark.parametrize(
    'user_type',
    ['shopowner', 'shop_staff', 'customer'],
    ids=['shopowner', 'shop_staff', 'customer']
)
def test_user_str_representation(all_users, user_type):
    """
    Test the string representation of a user.
    """
    user = all_users[user_type]
    assert str(user) == f"<User: {user.id}> {user.email or user.staff_handle} ({user_type.capitalize()})"


@pytest.mark.parametrize(
    'user_type',
    ['shopowner', 'shop_staff', 'customer'],
    ids=['shopowner', 'shop_staff', 'customer']
)
def test_user_profile_creation(all_users, user_type):
    """
    Test that user profile is created.
    """
    user = all_users[user_type]
    assert user.profile is not None


@pytest.mark.parametrize(
    'user_type',
    ['shopowner', 'shop_staff', 'customer'],
    ids=['shopowner', 'shop_staff', 'customer']
)
def test_user_profile_str_representation(all_users, user_type):
    """
    Test the string representation of a user profile.
    """
    user = all_users[user_type]
    profile = user.profile
    assert str(profile) == f"<UserProfile: {profile.id}> \n\t FIRST NAME: {profile.first_name} \n\t LAST NAME: {profile.last_name} \n\t TELEPHONE: {profile.telephone}"


@pytest.mark.parametrize(
    'factory_name',
    ['shop_staff_factory', 'shopowner_factory', 'customer_factory'],
    ids=['shop_staff', 'shopowner', 'customer']
)
def test_user_profile_deletes_when_user_is_deleted(request, factory_name):
    """
    Tests that the user profile associated with a user is deleted
    when the user is deleted.
    """
    factory = request.getfixturevalue(factory_name)
    
    if factory_name == 'shop_staff_factory':
        shopowner = request.getfixturevalue('shopowner')
        user = factory(shopowner=shopowner)
    else:
        user = factory()

    user_count = User.objects.count()
    profile_count = UserProfile.objects.count()
    
    user.delete()
    assert User.objects.count() == (user_count - 1)
    assert UserProfile.objects.count() == (profile_count - 1)
