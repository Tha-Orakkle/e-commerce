from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
import pytest

from cart.models import Cart
from shop.models import Shop
from user.models import UserProfile

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


# FACTORIES
@pytest.fixture
def profile_factory():
    """
    Factory to create user profiles.
    """
    def create_profile(user, first_name=None, last_name=None, telephone=None):
        first_name = first_name or 'John'
        last_name = last_name or 'Doe'
        telephone = telephone or '08112221111'
        return UserProfile.objects.create(
            user=user,
            first_name=first_name,
            last_name=last_name,
            telephone=telephone
        )
    return create_profile


@pytest.fixture
def customer_factory(db, profile_factory):
    """
    Factory to create customers.
    """
    def create_customer():
        count = User.objects.filter(is_customer=True, is_superuser=False).count() + 1
        customer = User.objects.create_user(
            email=f"customer{count}@email.com",
            password="Password123#",
        )
        profile_factory(customer)
        Cart.objects.create(user=customer)
        return customer
    return create_customer


@pytest.fixture
def shopowner_factory(db, profile_factory):
    """
    Factory to create shop owners.
    """
    def create_shopowner():
        count = User.objects.filter(is_shopowner=True, is_superuser=False).count() + 1
        owner = User.objects.create_shopowner(
            email=f"shopowner{count}@email.com",
            staff_handle=f"shopowner{count}",
            password="Password123#"
        )
        profile_factory(owner)
        Shop.objects.create(
            name=f"Shop {count}",
            description=f"Shop {count} created by shopowner factory.",
            owner=owner
        )
        return owner
    return create_shopowner


@pytest.fixture
def shop_staff_factory(db, profile_factory):
    """
    Factory to create shop staff.
    """
    def create_shop_staff(shopowner):
        count = User.objects.filter(is_staff=True, is_superuser=False).count() + 1
        staff = User.objects.create_staff(
            shop=shopowner.owned_shop,
            staff_handle=f"staff{count}",
            password="Password123#"
        )
        profile_factory(staff)
        return staff
    return create_shop_staff


# USERS (SUPER USER, SHOP OWNER, SHOP STAFF AND CUSTOMER)
@pytest.fixture
def super_user(db):
    """
    Creates an admin user
    """
    return User.objects.create_superuser(
        email='superuser@email.com',
        staff_handle='superuser',
        password="Password123#"
    )


@pytest.fixture
def shopowner(shopowner_factory):
    """
    Creates a shop owner.
    """
    return shopowner_factory()


@pytest.fixture
def shop_staff(db, shopowner, shop_staff_factory):
    """
    Create a staff for a shop.
    """
    return shop_staff_factory(shopowner=shopowner)


@pytest.fixture
def customer(customer_factory):
    """
    Creates a customer.
    """
    return customer_factory()


@pytest.fixture
def all_users(super_user, shopowner, shop_staff, customer):
    """
    Returns all user types as a dict.
    """
    return {
        'super_user': super_user,
        'shopowner': shopowner,
        'shop_staff': shop_staff,
        'customer': customer,
    }
