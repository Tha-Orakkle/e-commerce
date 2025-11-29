from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
import pytest

from cart.models import Cart
from shop.models import Shop
from user.models import UserProfile



User = get_user_model()

# dummy fixtures
def create_dummy_profile(user):
    """
    Create a dummy user profile.
    """
    return UserProfile.objects.create(
        user=user,
        first_name='John',
        last_name='Doe',
        telephone='08112221111'
    )

@pytest.fixture
def dummy_user(db):
    """
    Create a dummy user.
    """
    user = User.objects.create_user(
        email="dummyuser@email.com",
        password="Password123#",
    )
    create_dummy_profile(user)
    return user

@pytest.fixture
def dummy_shop(db, dummy_user):
    """
    Create a dummy shop.
    """
    return Shop.objects.create(
        name="Dummy Shop",
        description="This is a dummy shop for testing.",
        owner=dummy_user
    )



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
def shopowner(db):
    """
    Creates a shop owner.
    """
    owner = User.objects.create_shopowner(
        email='shopowner@email.com',
        staff_handle='shopowner',
        password='Password123#'
    )
    create_dummy_profile(owner)
    Shop.objects.create(
        name="Playground",
        description="Showcase you talents without fear of being judged.",
        owner=owner
    )
    return owner

@pytest.fixture
def shop_staff(db, shopowner):
    """
    Create a staff for a shop.
    """
    staff = User.objects.create_staff(
        shop=shopowner.owned_shop,
        staff_handle='staff',
        password='Password123#'
    )
    create_dummy_profile(staff)
    return staff

@pytest.fixture
def customer(db):
    """
    Creates a customer.
    """
    customer = User.objects.create_user(
        email="customer@email.com",
        password="Password123#", 
    )
    create_dummy_profile(customer)
    Cart.objects.create(user=customer)

    return customer

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

# to be removed start
@pytest.fixture
def admin_user(db):
    """
    Create an admin user.
    """
    return User.objects.create_staff(
        staff_handle='staff',
        password='Password123#'
    )

@pytest.fixture
def user(db):
    """
    Creates a user
    """
    return User.objects.create_user(
        email="user@email.com",
        password="Password123#", 
    )

# to be removed ends


# SIGNED USERS (SHOP OWNER, SHOP STAFF & CUSTOMER)

@pytest.fixture
def signed_in_superuser(client, super_user):
    """
    Super user sign in.
    Return the refresh token and access token
    For this, su will use the customer-login url.
    """
    url = reverse('customer-login')
    data = {
        'staff_handle': super_user.email,
        'password': 'Password123#'
    }
    response = client.post(url, data, format='json')
    assert response.status_code == 200
    assert 'refresh_token' in response.cookies
    assert 'access_token' in response.cookies
    return {
        'refresh_token': response.cookies['refresh_token'].value,
        'access_token': response.cookies['access_token'].value
    }

@pytest.fixture
def signed_in_shopowner(client, shopowner):
    """
    Staff sign in.
    Return the refresh token and access token
    """
    url = reverse('staff-login')
    data = {
        'shop_code': shopowner.owned_shop.code,
        'staff_handle': shopowner.staff_handle,
        'password': 'Password123#'
    }
    response = client.post(url, data, format='json')
    assert response.status_code == 200
    assert 'refresh_token' in response.cookies
    assert 'access_token' in response.cookies
    return {
        'refresh_token': response.cookies['refresh_token'].value,
        'access_token': response.cookies['access_token'].value
    }

@pytest.fixture
def signed_in_staff(client, shop_staff):
    """
    Staff sign in.
    Return the refresh token and access token
    """
    url = reverse('staff-login')
    data = {
        'shop_code': shop_staff.shop.code,
        'staff_handle': shop_staff.staff_handle,
        'password': 'Password123#'
    }
    response = client.post(url, data, format='json')
    assert response.status_code == 200
    assert 'refresh_token' in response.cookies
    assert 'access_token' in response.cookies
    return {
        'refresh_token': response.cookies['refresh_token'].value,
        'access_token': response.cookies['access_token'].value
    }


@pytest.fixture
def signed_in_customer(client, customer):
    """
    Custoner sign in.
    Return the refresh token and access token
    """
    login_url = reverse('customer-login')
    data = {
        'email': customer.email,
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
    

# to be removed starts
@pytest.fixture
def signed_in_user(client, user):
    """
    Signs in the user
    Return the refresh token and access token
    """
    login_url = reverse('customer-login')
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
def signed_in_admin(client, admin_user):
    """
    Sign in the admin.
    Return the refresh token and access token
    """
    admin_login_url = reverse('staff-login')
    data = {
        'staff_handle': admin_user.handle,
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

# to be removed ends