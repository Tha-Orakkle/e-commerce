from django.urls import reverse
from rest_framework import status

import pytest



# =============================================================================
# LOGOUT TESTS
# =============================================================================

LOGOUT_URL = reverse('logout')

@pytest.mark.parametrize(
    "user_type",
    ['shopowner', 'customer', 'shop_staff'],
    ids=['shopowner', 'customer', 'shop_staff']
)
def test_user_logout_view(client, all_users, user_type):
    """
    Test the user logout view
    """
    user = all_users[user_type]
    client.force_authenticate(user=user)
    res = client.post(LOGOUT_URL)
    
    assert res.status_code == status.HTTP_200_OK
    assert res.data['status'] == 'success'
    assert res.data['message'] == 'Log out successful.'

    c = res.cookies
    assert c['refresh_token'].value == ''
    assert c['access_token'].value == ''


def test_user_logout_fails_without_token(client):
    """
    Test the user logout view without token
    """
    res = client.post(LOGOUT_URL)
    
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.data['status'] == "error"
    assert res.data['message'] == "Authentication credentials were not provided."
    

def test_user_logout_fails_with_invalid_token(client):
    """
    Test the user logout view fails with invalid token
    """
    client.cookies['access_token'] = 'invalid-token'
    res = client.post(LOGOUT_URL)

    
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.data['status'] == 'error'
    assert res.data['message'] == "Token is invalid or expired"