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
    c = response.cookies
    assert c['refresh_token'].value == ''
    assert c['access_token'].value == ''