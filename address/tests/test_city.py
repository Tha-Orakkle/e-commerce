from django.urls import reverse
from rest_framework import status

import uuid

from address.models import State


def test_get_cities(client, load_locations_to_db, customer):
    """
    Test get cities endpoint.
    """
    client.force_authenticate(user=customer)
    state = State.objects.first()
    url = f"{reverse('cities')}?state={state.id}"
    res = client.get(url)
    assert res.status_code == status.HTTP_200_OK
    assert res.data['status'] == "success"
    assert res.data['messages'] == "Cities retrieved successfully."
    assert 'data' in res.data
    assert isinstance(res.data['data'], list)
    assert len(res.data['data']) > 0
    city = res.data['data'][0]
    assert 'id' in city
    assert 'name' in city


def test_get_cities_invalid_state(client, load_locations_to_db, customer):
    """
    Test get cities endpoint with invalid state ID.
    """
    client.force_authenticate(user=customer)
    url = f"{reverse('cities')}?state=invalid"
    res = client.get(url)
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "invalid_uuid"
    assert res.data['message'] == "Invalid state id."
    

def test_get_cities_nonexistent_state(client, load_locations_to_db, customer):
    """
    Test get cities endpoint with non-existent state ID.
    """
    client.force_authenticate(user=customer)
    url = f"{reverse('cities')}?state={uuid.uuid4()}"
    res = client.get(url)
    assert res.status_code == status.HTTP_404_NOT_FOUND
    assert res.data['status'] == "error"
    assert res.data['code'] == "not_found"
    assert res.data['message'] == "No cities found for the provided state ID."
    

def test_get_cities_missing_state(client, load_locations_to_db, customer):
    """
    Test get cities endpoint without state ID.
    """
    client.force_authenticate(user=customer)
    url = reverse('cities')
    res = client.get(url)
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "missing_state"
    assert res.data['message'] == "State ID is required to retrieve associated cities."


def test_get_cities_by_unauthenticated_user(client, load_locations_to_db):
    """
    Test retrieving cities without authentication.
        - test token is not provided & invalid token
    """
    url = f"{reverse('cities')}?state=12345678-1234-1234-1234-123456789012"
    res = client.get(url)
    
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.data['message'] == "Authentication credentials were not provided."
    
    client.cookies['access_token'] = 'invalidtoken'
    res = client.get(url)
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.data['message'] == "Token is invalid or expired"
    