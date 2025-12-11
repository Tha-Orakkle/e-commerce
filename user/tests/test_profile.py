from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status

import pytest
import random
import string

from user.models import UserProfile

User = get_user_model()

# test request is from unauthenticated user (not provided and invalid tokens) -- done
# test user has no profile -- done
# test user successfully updates profile (customer, staff and shop owner) -- done
# test profile update with invalid names -- done
# test profile update with invalid telephone -- done
# test profile updatw with missing data -- done


# =================================================================
# PROFILE UPDATE TESTS
# =================================================================

UPDATE_PROFILE_URL = reverse('user-profile')
UPDATE_PROFILE_DATA = {
    'first_name': 'UpdatedFirstName',
    'last_name': 'UpdatedLastName',
    'telephone': '08120002323'
}

# ----
long_name = ''.join(random.choices(string.ascii_letters, k=31))

@pytest.fixture
def updated_user(user):
    user.profile.first_name = 'Jane'
    user.profile.last_name = 'Doe'
    user.profile.telephone = '08129114555'
    user.save()
    return user
# ----



@pytest.mark.parametrize(
    'user_type',
    ['customer', 'shopowner', 'shop_staff'],
    ids=['customer', 'shopowner', 'shop_staff']
)
def test_update_user_profile(client, all_users, user_type):
    """
    Test updating user profile.
    """
    user = all_users[user_type]
    client.force_authenticate(user=user)
    data = UPDATE_PROFILE_DATA.copy()
    res = client.patch(UPDATE_PROFILE_URL, data=data, format='json')
    assert res.status_code == status.HTTP_200_OK
    assert res.data['status'] == "success"
    assert res.data['message'] == "User profile updated successfully."
    assert res.data['data']['first_name'] == data['first_name'].title()
    assert res.data['data']['last_name'] == data['last_name'].title()
    tel1 = "+234" + data['telephone'].lstrip("0").strip()
    tel2 = res.data['data']['telephone'].replace(" ", "")
    assert tel1 == tel2
    
    profile = user.profile
    profile.refresh_from_db()
    
    assert profile.first_name == data['first_name'].title()
    assert profile.last_name == data['last_name'].title()
    assert profile.telephone == data['telephone']


def test_update_user_profile_fails_where_user_has_no_profile(client, customer_factory):
    """
    Test updating user profile when user has no profile.
    """
    cus = customer_factory()
    cus.profile.delete()
    cus.refresh_from_db()
    data = UPDATE_PROFILE_DATA.copy()
    
    client.force_authenticate(user=cus)

    res = client.patch(UPDATE_PROFILE_URL, data=data, format='json')
    print(res.data)
    assert res.status_code == status.HTTP_404_NOT_FOUND
    assert res.data['status'] == "error"
    assert res.data['code'] == "not_found"
    assert res.data['message'] == "User has no profile."


@pytest.mark.parametrize(
    'user_type',
    ['customer', 'shopowner', 'shop_staff'],
    ids=['customer', 'shopowner', 'shop_staff']
)
def test_update_user_profile_fails_with_invalid_first_and_last_name(client, all_users, user_type):
    """
    Test updating user profile with invalid first and last name fails.
    Where names are too short or too long.
    """
    user =  all_users[user_type]
    
    # too short
    data = {
        'first_name': 'J',
        'last_name': 'D'
    }
    client.force_authenticate(user=user)
    
    res = client.patch(UPDATE_PROFILE_URL, data=data, format='json')
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "validation_error"
    assert res.data['message'] == "User profile update failed."
    assert 'last_name' in res.data['errors']
    assert 'first_name' in res.data['errors']
    assert res.data['errors']['first_name'] == ["Ensure this field has at least 2 characters."]
    assert res.data['errors']['last_name'] == ["Ensure this field has at least 2 characters."]
    
    # too long
    data = {
        'first_name': 'J' * 31,
        'last_name': 'D' * 31
    }
    res = client.patch(UPDATE_PROFILE_URL, data=data, format='json')
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['errors']['first_name'] == ["Ensure this field has no more than 30 characters."]
    assert res.data['errors']['last_name'] == ["Ensure this field has no more than 30 characters."]



@pytest.mark.parametrize(
    'user_type',
    ['customer', 'shopowner', 'shop_staff'],
    ids=['customer', 'shopowner', 'shop_staff']
)
def test_update_user_profile_fails_with_invalid_telephone(client, all_users, user_type):
    """
    Test updating user profile with invalid data.
    """
    user = all_users[user_type]
    data = {
        **UPDATE_PROFILE_DATA,
        'telephone': 'invalid_telephone'
    }
    client.force_authenticate(user=user)
    
    res = client.patch(UPDATE_PROFILE_URL, data=data, format='json')
    
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "validation_error"
    assert res.data['message'] == "User profile update failed."
    assert 'telephone' in res.data['errors']
    assert res.data['errors']['telephone'] == ["The phone number entered is not valid."]


@pytest.mark.parametrize(
    'user_type',
    ['customer', 'shopowner', 'shop_staff'],
    ids=['customer', 'shopowner', 'shop_staff']
)
def test_update_user_profile_fails_with_blank_data(client, all_users, user_type):
    """
    Test updating user profile with blank data.
    Only telephone field can be blank.
    """
    user = all_users[user_type]
    data = {
        'first_name': '',
        'last_name': '',
        'telephone': ''
    }
    client.force_authenticate(user=user)

    res = client.patch(UPDATE_PROFILE_URL, data=data, format='json')

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "validation_error"
    assert res.data['message'] == "User profile update failed."
    assert 'first_name' in res.data['errors']
    assert res.data['errors']['first_name'] == ["This field may not be blank."]
    assert 'last_name' in res.data['errors']
    assert res.data['errors']['last_name'] == ["This field may not be blank."]
    assert 'telephone' in res.data['errors']
    assert res.data['errors']['telephone'] == ["This field may not be blank."]

@pytest.mark.parametrize(
    'user_type',
    ['customer', 'shopowner', 'shop_staff'],
    ids=['customer', 'shopowner', 'shop_staff']
)
def test_update_user_profile_with_missing_data(client, all_users, user_type):
    """
    Test updating user profile with missing data.

    """
    user = all_users[user_type]
    client.force_authenticate(user=user)

    res = client.patch(UPDATE_PROFILE_URL, data={}, format='json')
    
    assert res.status_code == status.HTTP_200_OK
    assert res.data['status'] == "success"
    assert res.data['message'] == "User profile updated successfully."

def test_update_user_profile_fails_with_unauthenticated_user(client):
    """
    Test updating user profile with unauthenticated user.
    """
    data = UPDATE_PROFILE_DATA.copy()

    # token not provided
    res = client.patch(UPDATE_PROFILE_URL, data=data, format='json')
    assert res.status_code ==  status.HTTP_401_UNAUTHORIZED
    assert res.data['status'] == "error"
    assert res.data['code'] == "unauthorized"
    assert res.data['message'] == "Authentication credentials were not provided."

    # invalid token were provided
    client.cookies['access_token'] = "invalid_token"
    res = client.patch(UPDATE_PROFILE_URL, data=data, format='json')
    assert res.status_code ==  status.HTTP_401_UNAUTHORIZED
    assert res.data['status'] == "error"
    assert res.data['code'] == "unauthorized"
    assert res.data['message'] == "Token is invalid or expired"
    