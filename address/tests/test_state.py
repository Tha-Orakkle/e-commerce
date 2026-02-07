from django.urls import reverse
from rest_framework import status

from address.models import State


def test_get_states(client, load_locations_to_db, customer):
    """
    Test retrieving states for a given country.
    """
    client.force_authenticate(user=customer)
    url = f"{reverse('states')}?country=NG"
    res = client.get(url)
    
    assert res.status_code == status.HTTP_200_OK
    assert res.data['status'] == "success"
    assert res.data['message'] == "States retrieved successfully."
    assert len(res.data['data']) == State.objects.filter(country__code='NG').count()
    state = res.data['data'][0]
    assert 'id' in state
    assert 'name' in state
    
    
def test_get_states_without_country_code(client, load_locations_to_db, customer):
    """
    Test retrieving states without providing a country code.
    """
    client.force_authenticate(user=customer)
    url = reverse('states')
    res = client.get(url)
    
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['message'] == "Country code (ISO2) is required to retrieve associated states."
    
    
def test_get_states_with_invalid_country_code(client, load_locations_to_db, customer):
    """
    Test retrieving states with an invalid country code.
    """
    client.force_authenticate(user=customer)
    url = f"{reverse('states')}?country=XX"
    res = client.get(url)
    
    assert res.status_code == status.HTTP_404_NOT_FOUND
    assert res.data['status'] == "error"
    assert res.data['message'] == "No states found for country code: XX"
    
    
def test_get_states_by_unauthenticated_user(client, load_locations_to_db):
    """
    Test retrieving states without authentication.
        - test token is not provided & invalid token
    """
    url = f"{reverse('states')}?country=NG"
    res = client.get(url)
    
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.data['message'] == "Authentication credentials were not provided."
    
    client.cookies['access_token'] = 'invalidtoken'
    res = client.get(url)
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.data['message'] == "Token is invalid or expired"
    