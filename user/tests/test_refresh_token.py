from django.urls import reverse
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

import pytest

# ==========================================================
# RESET PASSWORD TESTS
# ==========================================================
REFRESH_TOKEN_URL = reverse('token-refresh')


@pytest.mark.parametrize(
    "user_type",
    ['shopowner', 'customer', 'shop_staff'],
    ids=['shopowner', 'customer', 'shop_staff']
)
def test_access_token_refresh(client, all_users, user_type):
    """
    Test the access token refresh process.
    """
    user = all_users[user_type]
    refresh = RefreshToken.for_user(user)
    client.cookies['refresh_token']  = str(refresh)
    
    res = client.post(REFRESH_TOKEN_URL, format='json')
    assert res.status_code == status.HTTP_200_OK
    assert res.data['status'] == "success"
    assert res.data['message'] == "Token refreshed successfully"
    assert res.cookies['access_token']['httponly'] is True
    assert res.cookies['access_token'].value != str(refresh.access_token)


def test_access_token_refresh_without_refresh_token(client):
    """
    Test the access token refresh process without passing the refresh token.
    """
    res = client.post(REFRESH_TOKEN_URL, format='json')
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == 'error'
    assert res.data['message'] == "Refresh token was not provided."


def test_access_token_refresh_with_invalid_refresh_token(client):
    """
    Test the access token refresh process with an invalid refresh token.
    """
    client.cookies['refresh_token'] = 'invalid_token'
    res = client.post(REFRESH_TOKEN_URL, format='json')
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == 'error'
    assert res.data['message'] == "Token is invalid or expired"
