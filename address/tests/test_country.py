from django.urls import reverse
from rest_framework import status

from address.models import Country


def test_get_countries(client, load_locations_to_db, customer):
    """
    Test get countries endpoint.
    """
    url = reverse('countries')
    client.force_authenticate(user=customer)
    res = client.get(url)
    assert res.status_code == status.HTTP_200_OK
    assert res.data['message'] == "Countries retrieved successfully."
    assert 'data' in res.data
    assert len(res.data['data']) == Country.objects.count()
    country = res.data['data'][0]
    assert 'id' in country
    assert 'name' in country
    assert 'code' in country
    assert len(country['code']) == 2
    assert country['code'].isupper()


def test_get_countries_by_unauthenticated_user(client, load_locations_to_db):
    """
    Test retrieving countries without authentication.
        - test token is not provided & invalid token
    """
    url = reverse('countries')
    res = client.get(url)
    
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.data['message'] == "Authentication credentials were not provided."
    
    client.cookies['access_token'] = 'invalidtoken'
    res = client.get(url)
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.data['message'] == "Token is invalid or expired"
    