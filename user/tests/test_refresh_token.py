from django.urls import reverse
from rest_framework import status


refresh_token_url = reverse('token-refresh')

def test_access_token_refresh(client, signed_in_user):
    """
    Test the access token refresh process.
    """
    client.cookies['refresh_token'] = signed_in_user['refresh_token']
    response = client.post(refresh_token_url, format='json')
    assert response.status_code == status.HTTP_200_OK
    assert response.data['status'] == "success"
    assert response.data['message'] == "Token refreshed successfully"
    assert response.cookies['access_token']['httponly'] is True


def test_access_token_refresh_without_refresh_token(client):
    """
    Test the access token refresh process without passing the refresh token.
    """
    response = client.post(refresh_token_url, format='json')
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data['status'] == 'error'
    assert response.data['message'] == "Refresh token was not provided."


def test_access_token_refresh_with_invalid_refresh_token(client, signed_in_user):
    """
    Test the access token refresh process with an invalid refresh token.
    """
    client.cookies['refresh_token'] = signed_in_user['refresh_token'] + 'invalid'
    response = client.post(refresh_token_url, format='json')
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data['status'] == 'error'
    assert response.data['message'] == "Token is invalid or expired"



    