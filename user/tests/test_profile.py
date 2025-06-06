from django.urls import reverse
from rest_framework import status

import pytest
import random
import string


long_name = ''.join(random.choices(string.ascii_letters, k=31))
user_profile_url = reverse('user-profile')

@pytest.fixture
def updated_user(user):
    user.profile.first_name = 'Jane'
    user.profile.last_name = 'Doe'
    user.profile.telephone = '08129114555'
    user.save()
    return user


def test_put_user_profile(client, signed_in_user):
    """
    Test updating user profile.
    """
    data = {
        'first_name': 'UpdatedFirstName',
        'last_name': 'UpdatedLastName',
        'telephone': '08120002323'
    }
    client.cookies['access_token'] = signed_in_user['access_token']
    response = client.put(user_profile_url, data=data, format='multipart')
    assert response.status_code == status.HTTP_200_OK
    assert response.data['code'] == 200
    assert response.data['status'] == "success"
    assert response.data['message'] == "User profile updated successfully."
    assert response.data['data']['first_name'] == "Updatedfirstname"
    assert response.data['data']['last_name'] == "Updatedlastname"
    assert response.data['data']['telephone'] == "+234 812 000 2323"


def test_put_user_profile_not_found(client, user, signed_in_user):
    """
    Test updating user profile when user profile is not found.
    """
    user.profile.delete()
    data = {
        'first_name': 'UpdatedFirstName',
        'last_name': 'UpdatedLastName',
        'telephone': '08120002323'
    }
    client.cookies['access_token'] = signed_in_user['access_token']
    response = client.put(user_profile_url, data=data, format='json')
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.data['code'] == 404
    assert response.data['status'] == "error"
    assert response.data['message'] == "User has no profile."


def test_put_user_profile_invalid_data(client, updated_user, signed_in_user):
    """
    Test updating user profile with invalid data.
    """
    data = {
        'first_name': 'A',
        'last_name': 'B',
        'telephone': 'invalid_telephone'
    }
    client.cookies['access_token'] == signed_in_user['access_token']
    response = client.put(user_profile_url, data=data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['code'] == 400
    assert response.data['status'] == "error"
    assert response.data['message'] == "User profile update failed."
    assert 'first_name' in response.data['errors']
    assert response.data['errors']['first_name'] == ["Ensure this field has at least 2 characters."]
    assert 'last_name' in response.data['errors']
    assert response.data['errors']['last_name'] == ["Ensure this field has at least 2 characters."]
    assert 'telephone' in response.data['errors']
    assert response.data['errors']['telephone'] == ["The phone number entered is not valid."]
    

def test_put_user_profile_invalid_data_more(client, updated_user, signed_in_user):
    """
    Test updating user profile with more invalid data.
    """
    data = {
        'first_name': '',
        'last_name': '',
        'telephone': '366738738937'
    }
    client.cookies['access_token'] == signed_in_user['access_token']
    response = client.put(user_profile_url, data=data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['code'] == 400
    assert response.data['status'] == "error"
    assert response.data['message'] == "User profile update failed."
    assert 'first_name' in response.data['errors']
    assert response.data['errors']['first_name'] == ["This field may not be blank."]
    assert 'last_name' in response.data['errors']
    assert response.data['errors']['last_name'] == ["This field may not be blank."]
    assert 'telephone' in response.data['errors']
    assert response.data['errors']['telephone'] == ["The phone number entered is not valid."]


def test_put_user_profile_long_first_and_last_name(client, updated_user, signed_in_user):
    """
    Test updating user profile with invalid long first and last name.
    """
    data = {
        'first_name': long_name,
        'last_name': long_name
    }
    client.cookies['access_token'] == signed_in_user['access_token']
    response = client.put(user_profile_url, data=data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['code'] == 400
    assert response.data['status'] == "error"
    assert response.data['message'] == "User profile update failed."
    assert 'first_name' in response.data['errors']
    assert response.data['errors']['first_name'] == ["Ensure this field has no more than 30 characters."]
    assert 'last_name' in response.data['errors']
    assert response.data['errors']['last_name'] == ["Ensure this field has no more than 30 characters."]


def test_put_user_unauthenticated(client):
    """
    Test updating user profile without authentication.
    """
    data = {
        'first_name': 'Dave',
        'last_name': 'Chapelle',
        'telephone': '08131112222'
    }
    response = client.put(user_profile_url, data=data, format='json')
    assert response.status_code ==  status.HTTP_401_UNAUTHORIZED
    assert response.data['code'] == 401
    assert response.data['status'] == "error"
    assert response.data['message'] == "Authentication credentials were not provided."

    