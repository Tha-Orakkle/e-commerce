from django.urls import reverse
import pytest


def test_user_logout_view(client, signed_in_user):
    """
    Test the user logout view
    """
    url = reverse('logout')
    client.cookies['refresh_token'] = signed_in_user['refresh_token']
    client.cookies['access_token'] = signed_in_user['access_token']
    response = client.post(url)
    
    assert response.status_code == 200
    assert response.data['status'] == 'success'
    assert response.data['message'] == 'User logged out successfully.'

    c = response.cookies
    assert c['refresh_token'].value == ''
    assert c['access_token'].value == ''


def test_user_logout_without_token(client):
    """
    Test the user logout view without token
    """
    url = reverse('logout')
    response = client.post(url)
    
    assert response.status_code == 401
    assert response.data['status'] == 'error'
    assert response.data['message'] == 'Authentication credentials were not provided.'