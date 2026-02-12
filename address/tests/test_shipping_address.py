from django.urls import reverse
from rest_framework import status

import pytest


# test create shipping address with valid data
# test create shipping address with data
# test creating more than 5 shipping addresses for a user (should fail)





# =============================================================================
# TEST CREATE SHIPPING ADDRESS
# =============================================================================

def create_shipping_address_data(country, state,
                                 city, telephone='08112223344',
                                 postal_code='100001'):
    return {
        'street_address': '123 Main St',
        'postal_code': postal_code,
        'city': city.id,
        'state': state.id,
        'country': country.code,
        'full_name': 'Sheldon Cooper',
        'telephone': telephone
    }


SHIPPING_ADDRESS_LIST_CREATE_URL = reverse('shipping-address-list-create')

def test_create_shipping_address(client, customer, country, state, city):
    """
    Test creating a shipping address for a user.
    """
    data = create_shipping_address_data(country, state, city)
    client.force_authenticate(user=customer)
    res = client.post(
        SHIPPING_ADDRESS_LIST_CREATE_URL,
        data=data,
        format='json'    
    )
    assert res.status_code == status.HTTP_201_CREATED
    assert res.data['message'] == "Shipping address created successfully."
    assert 'data' in res.data
    res_data = res.data['data']
    assert res_data['id'] is not None
    assert res_data['full_name'] == data['full_name']
    assert res_data['street_address'] == data['street_address']
    tel1 = "+234" + data['telephone'].lstrip("0").strip()
    tel2 = res_data['telephone'].replace(" ", "")
    assert tel1 == tel2
    assert res_data['city'] is not None
    assert res_data['state'] is not None
    assert res_data['country'] is not None
    assert res_data['postal_code'] == data['postal_code']
    assert 'created_at' in res_data
    assert 'updated_at' in res_data
    customer.refresh_from_db()
    assert customer.addresses.filter(id=res_data['id']).exists()

# STREET ADDRESS
def test_street_address_field_is_required(client, customer, country, state, city):
    """
    Test that street address field is required when creating a shipping address.
    """
    data = create_shipping_address_data(country, state, city)
    data.pop('street_address')  # Remove street_address to simulate missing field
    client.force_authenticate(user=customer)
    res = client.post(
        SHIPPING_ADDRESS_LIST_CREATE_URL,
        data=data,
        format='json'    
    )
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "validation_error"
    assert res.data['message'] == "Shipping address creation failed."
    assert 'errors' in res.data
    assert 'street_address' in res.data['errors']
    assert res.data['errors']['street_address'] == ["This field is required."]

   
def test_street_address_too_short(client, customer, country, state, city):
    """
    Test that street address must be at least 5 characters long.
    """
    data = create_shipping_address_data(country, state, city)
    data['street_address'] = '123'  # too short, must be at least 5 characters
    client.force_authenticate(user=customer)
    res = client.post(
        SHIPPING_ADDRESS_LIST_CREATE_URL,
        data=data,
        format='json'    
    )
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "validation_error"
    assert res.data['message'] == "Shipping address creation failed."
    assert 'errors' in res.data
    assert 'street_address' in res.data['errors']
    assert res.data['errors']['street_address'] == ['Ensure this field has at least 5 characters.']


def test_street_address_too_long(client, customer, country, state, city):
    """
    Test that street address must be at most 256 characters long.
    """
    data = create_shipping_address_data(country, state, city)
    data['street_address'] = 'A' * 257  # too long, must be at most 256 characters
    client.force_authenticate(user=customer)
    res = client.post(
        SHIPPING_ADDRESS_LIST_CREATE_URL,
        data=data,
        format='json'    
    ) 
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "validation_error"
    assert res.data['message'] == "Shipping address creation failed."
    assert 'errors' in res.data
    assert 'street_address' in res.data['errors']
    assert res.data['errors']['street_address'] == ['Ensure this field has no more than 256 characters.']


@pytest.mark.parametrize(
    'invalid_street_address',
    [True, False, None, [], {}, ()],
    ids=['true_boolean', 'false_boolean', 'null', 'list', 'dict', 'tuple']
)
def test_street_address_not_a_string(client, customer, country, state, city, invalid_street_address):
    """
    Test that street address must be a string.
    """
    data = create_shipping_address_data(country, state, city)
    data['street_address'] = invalid_street_address  # not a string
    client.force_authenticate(user=customer)
    res = client.post(
        SHIPPING_ADDRESS_LIST_CREATE_URL,
        data=data,
        format='json'    
    )
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "validation_error"
    assert res.data['message'] == "Shipping address creation failed."
    assert 'errors' in res.data
    assert 'street_address' in res.data['errors']
    if invalid_street_address is None:
        assert res.data['errors']['street_address'] == ["This field may not be null."]
    else:
        assert res.data['errors']['street_address'] == ["Not a valid string."]
    
    
@pytest.mark.parametrize(
    'blank_street_address',
    ['   ', '\t', '\n', ''],
    ids=['spaces', 'tab', 'newline', 'empty_string']
)
def test_street_address_not_blank(client, customer, country, state, city, blank_street_address):
    """
    Test that street address cannot be blank.
    """
    data = create_shipping_address_data(country, state, city)
    data['street_address'] = blank_street_address  # blank string
    client.force_authenticate(user=customer)
    res = client.post(
        SHIPPING_ADDRESS_LIST_CREATE_URL,
        data=data,
        format='json'    
    )
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "validation_error"
    assert res.data['message'] == "Shipping address creation failed."
    assert 'errors' in res.data
    assert 'street_address' in res.data['errors']
    assert res.data['errors']['street_address'] == ["This field may not be blank."]