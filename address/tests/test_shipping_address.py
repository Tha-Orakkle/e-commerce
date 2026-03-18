from django.urls import reverse
from rest_framework import status

import pytest
import uuid

from address.models import ShippingAddress

# =============================================================================
# TEST CREATE SHIPPING ADDRESS
# =============================================================================

def create_shipping_address_data(state,
                                 city, telephone='08112223344',
                                 postal_code='100001',
                                 country_code='NG'):
    return {
        'street_address': '123 Main St',
        'postal_code': postal_code,
        'city': city.id,
        'state': state.id,
        'country': country_code,
        'full_name': 'Sheldon Cooper',
        'telephone': telephone
    }


SHIPPING_ADDRESS_LIST_CREATE_URL = reverse('shipping-address-list-create')

def test_create_shipping_address(client, customer, state, city):
    """
    Test creating a shipping address for a user.
    """
    data = create_shipping_address_data(state=state, city=city)
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

@pytest.mark.parametrize(
    'field',
    ['full_name', 'telephone', 'street_address', 'city', 'state', 'country', 'postal_code'],
    ids=['full_name', 'telephone', 'street_address', 'city', 'state', 'country', 'postal_code']
)
def test_required_fields(client, customer, state, city, field):
    """
    Test that street address field is required when creating a shipping address.
    """
    data = create_shipping_address_data(state=state, city=city)
    data.pop(field)  # Remove street_address to simulate missing field
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
    assert field in res.data['errors']
    assert res.data['errors'][field] == ["This field is required."]


# STREET ADDRESS
def test_street_address_too_short(client, customer, country, state, city):
    """
    Test that street address must be at least 5 characters long.
    """
    data = create_shipping_address_data(state=state, city=city)
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
    data = create_shipping_address_data(state=state, city=city)
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
    data = create_shipping_address_data(state=state, city=city)
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
    data = create_shipping_address_data(state=state, city=city)
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
    
    
# TELEPHONE - NIGERIAN

@pytest.mark.parametrize(
    'invalid_telephone',
    ['string', 2134, 122.32, '081292', '0912889899999'],
    ids=['string', 'int', 'float', 'less_than_11_digits',
         'greater_than_11_digits']
)
def test_invalid_telephone(client, customer, country, state, city, invalid_telephone):
    """
    Test that telephone is not valid.
    """
    data = create_shipping_address_data(state=state, city=city)
    data['telephone'] = invalid_telephone
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
    assert 'telephone' in res.data['errors']
    assert res.data['errors']['telephone'] == ["Enter a valid phone number."]
    
    
def test_non_nigerian_telephone(client, customer, country, state, city):
    """
    Test that telephone is a valid Nigerian number.
    """
    data = create_shipping_address_data(state=state, city=city)
    data['telephone'] = '+18446778182'
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
    assert 'telephone' in res.data['errors']
    assert res.data['errors']['telephone'] == ["Enter a valid Nigerian phone number (+234)."]

# POSTAL CODE
# Test for checking country code in the postal code verification
#+ to be implemented on expansion

@pytest.mark.parametrize(
    'invalid_postal_code',
    ['012345', '1001', '12345678'],
    ids=['zero-first-digit', 'short-code', 'long-code'],
)
def test_invalid_nigerian_postal_code(client, customer, state, city, invalid_postal_code):
    """
    Test that only Nigerian postal codes are allowed.
    Instances to test:
        - Must not start with zero
        - Must be 6 digits
    """
    data = create_shipping_address_data(state, city)
    data['postal_code'] = invalid_postal_code
    
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
    assert 'postal_code' in res.data['errors']
    assert res.data['errors']['postal_code'] == ["Invalid postal code format for the given country."]


# FULL NAME
def test_full_name_is_short(client, customer, state, city):
    """
    Test full name is required when creating shipping address.
    """
    data = create_shipping_address_data(state, city)
    data['full_name'] = 'aa' # too short
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
    assert 'full_name' in res.data['errors']
    assert res.data['errors']['full_name'] == ['Ensure this field has at least 3 characters.']

def test_full_name_too_long(client, customer, country, state, city):
    """
    Test that full name must be at most 32 characters long.
    """
    data = create_shipping_address_data(state=state, city=city)
    data['full_name'] = 'A' * 33
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
    assert 'full_name' in res.data['errors']
    assert res.data['errors']['full_name'] == ['Ensure this field has no more than 32 characters.']
    
# COUNTRY
def test_country_code_too_long(client, customer, state, city):
    """
    Test that the country ISO2 code must not exceed 2 chars. 
    """
    data = create_shipping_address_data(state, city, country_code='UKH')
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
    assert 'country' in res.data['errors']
    assert res.data['errors']['country'] == ['Ensure this field has no more than 2 characters.']

# Uncomment when more countries are permitted

# def test_non_existent_country_code(client, customer, state, city):
#     """
#     Test that request with non-existent country code fails.
#     """
#     data = create_shipping_address_data(state, city, country_code='II')
#     client.force_authenticate(user=customer)
#     res = client.post(
#         SHIPPING_ADDRESS_LIST_CREATE_URL,
#         data=data,
#         format='json'
#     )
    
#     assert res.status_code == status.HTTP_400_BAD_REQUEST
#     assert res.data['status'] == "error"
#     assert res.data['code'] == "validation_error"
#     assert res.data['message'] == "Shipping address creation failed."
#     assert 'errors' in res.data
#     assert 'country' in res.data['errors']
#     assert res.data['errors']['country'] == ['Invalid country.']

    
# STATE
@pytest.mark.parametrize(
    'field',
    ['state', 'city'],
    ids=['state', 'city']
)
def test_state_and_city_is_valid_uuid(client, customer, state, city, field):
    """
    Test that the state and city IDs are valid IDs.
    """
    data = create_shipping_address_data(state, city)
    data[field] = 'invalid_uuid'
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
    assert field in res.data['errors']
    assert res.data['errors'][field] == ['Must be a valid UUID.']

@pytest.mark.parametrize(
    'field, found_in',
    [('state', 'country'), ('city', 'state')],
    ids=['state', 'city']
)
def test_non_existent_state_and_city_ids(client, customer, state, city, field, found_in):
    """
    Test that the state and city IDs match existing state/city.
    """
    data = create_shipping_address_data(state, city)
    data[field] = uuid.uuid4()
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
    assert field in res.data['errors']
    assert res.data['errors'][field] == [f'Invalid {field} for the specified {found_in}.']


@pytest.mark.parametrize(
    'user_type',
    ['shopowner', 'shop_staff'],
    ids=['shopowner', 'shop_staff']
)
def test_shipping_address_creation_by_non_customer(client, all_users, user_type):
    """
    Test that shipping address can only be created by a customer.
    """
    user = all_users[user_type]
    client.force_authenticate(user=user)
    res = client.post(
        SHIPPING_ADDRESS_LIST_CREATE_URL,
        data={},
        format='json'
    )
    assert res.status_code == status.HTTP_403_FORBIDDEN
    assert res.data['status'] == "error"
    assert res.data['code'] == "forbidden"
    assert res.data['message'] == "You do not have permission to perform this action."


def test_shipping_address_creation_by_unauthenticated_user(client):
    """
    Test create shipping address by unauthenticated user fails.
    Test invalid no token passed and invalid token
    """
    res = client.post(
        SHIPPING_ADDRESS_LIST_CREATE_URL,
        data={},
        format='json'
    )
    
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.data['status'] == "error"
    assert res.data['code'] == "unauthorized"
    assert res.data['message'] == "Authentication credentials were not provided."

    client.cookies['access_token'] = "Invalid_access_token2445"
    res = client.post(
        SHIPPING_ADDRESS_LIST_CREATE_URL,
        data={},
        format='json'
    )
    
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.data['status'] == "error"
    assert res.data['code'] == "unauthorized"
    assert res.data['message'] == "Token is invalid or expired"


# =============================================================================
# TEST GET ALL SHIPPING ADDRESSES
# =============================================================================


def test_get_shipping_addresses(client, customer, city, shipping_address_factory):
    """
    Get all shipping addresses for a customer.
    """
    for _ in range(3):
        shipping_address_factory(customer, city)
    
    url = SHIPPING_ADDRESS_LIST_CREATE_URL
    client.force_authenticate(user=customer)
    
    res = client.get(url)

    assert res.status_code == status.HTTP_200_OK
    assert res.data['status'] == "success"
    assert res.data['message'] == "Shipping addresses retrieved successfully."
    assert 'data' in res.data
    assert len(res.data['data']) == 3
    ship_add = res.data['data'][0]
    fields = [
        'id', 'full_name', 'street_address',
        'city', 'state', 'country', 'postal_code',
        'telephone', 'created_at', 'updated_at'
    ]
    assert all(field in ship_add for field in fields)
    assert all(ship_add[field] is not None for field in fields)
    
    
def test_get_shipping_addresses_with_no_addresses(client, customer):
    """
    Test retrieving shipping addresses when user has no addresses.
    """
    url = SHIPPING_ADDRESS_LIST_CREATE_URL
    client.force_authenticate(user=customer)
    
    res = client.get(url)

    assert res.status_code == status.HTTP_200_OK
    assert res.data['status'] == "success"
    assert res.data['message'] == "Shipping addresses retrieved successfully."
    assert 'data' in res.data
    assert len(res.data['data']) == 0
    
    
def test_get_shipping_addresses_by_different_user(client, customer_factory, city, shipping_address_factory):
    """
    Test that a user cannot retrieve shipping addresses of another user.
    """
    customer_1 = customer_factory()
    customer_2 = customer_factory()
    for _ in range(2):
        shipping_address_factory(customer_2, city)
    shipping_address_factory(customer_1, city)
    
    assert ShippingAddress.objects.count() == 3
    
    url = SHIPPING_ADDRESS_LIST_CREATE_URL
    client.force_authenticate(user=customer_1)
    
    res = client.get(url)

    assert res.status_code == status.HTTP_200_OK
    assert res.data['status'] == "success"
    assert res.data['message'] == "Shipping addresses retrieved successfully."
    assert 'data' in res.data
    assert len(res.data['data']) == 1
    

def test_get_shipping_addresses_by_superuser(client, customer_factory, super_user, city, shipping_address_factory):
    """
    Test that a superuser can retrieve shipping addresses of all users.
    """
    customer_1 = customer_factory()
    customer_2 = customer_factory()
    for _ in range(2):
        shipping_address_factory(customer_1, city)
        shipping_address_factory(customer_2, city)
    
    assert ShippingAddress.objects.count() == 4
    
    url = SHIPPING_ADDRESS_LIST_CREATE_URL
    client.force_authenticate(user=super_user)
    
    res = client.get(url)

    assert res.status_code == status.HTTP_200_OK
    assert res.data['status'] == "success"
    assert res.data['message'] == "Shipping addresses retrieved successfully."
    assert 'data' in res.data
    assert len(res.data['data']) == 4


def test_get_shiping_addresses_by_unauthenticated_user(client):
    """
    Test retrieving shipping addresses by unauthenticated user fails.
    """
    url = SHIPPING_ADDRESS_LIST_CREATE_URL
    res = client.get(url)
    
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.data['status'] == "error"
    assert res.data['code'] == "unauthorized"
    assert res.data['message'] == "Authentication credentials were not provided."

    client.cookies['access_token'] = "Invalid_access_token2445"
    res = client.get(url)
    
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.data['status'] == "error"
    assert res.data['code'] == "unauthorized"
    assert res.data['message'] == "Token is invalid or expired"


@pytest.mark.parametrize(
    'user_type',
    ['shopowner', 'shop_staff'],
    ids=['shopowner', 'shop_staff']
)
def test_get_shipping_addresses_by_non_customer(client, all_users, user_type):
    """
    Test get shipping addresses by non_customer (shop owner and staff).
    """
    user = all_users[user_type]
    url = SHIPPING_ADDRESS_LIST_CREATE_URL
    client.force_authenticate(user=user)

    res = client.get(url)

    assert res.status_code == status.HTTP_403_FORBIDDEN
    assert res.data['status'] == "error"
    assert res.data['code'] == "forbidden"
    assert res.data['message'] == "You do not have permission to perform this action."    


# =============================================================================
# TEST GET SPECIFIC SHIPPING ADDRESS
# =============================================================================

def test_get_shipping_address_with_id(client, customer, shipping_address_factory):
    """
    Test get specific shipping address by ID.
    """
    address = shipping_address_factory(customer)
    url = reverse('shipping-address-detail', kwargs={'address_id': address.id})
    
    client.force_authenticate(user=customer)
    res = client.get(url)
    assert res.status_code == status.HTTP_200_OK
    assert res.data['status'] == "success"
    assert res.data['message'] == "Shipping address retrieved successfully."
    assert 'data' in res.data
    res_data = res.data['data']
    assert res_data['id'] == str(address.id)
    assert res_data['full_name'] == address.full_name
    assert res_data['street_address'] == address.street_address
    assert res_data['telephone'] == address.telephone
    assert res_data['city'] == address.city.name
    assert res_data['state'] == address.city.state.name
    assert res_data['country'] == address.city.state.country.name
    assert res_data['postal_code'] == address.postal_code
    assert 'created_at' in res_data
    assert 'updated_at' in res_data
    assert 'user' not in res_data
    
    
def test_get_shipping_address_by_different_user(client, customer_factory, shipping_address_factory):
    """
    Test that a user cannot retrieve a shipping address of another user.
    """
    customer_1 = customer_factory()
    customer_2 = customer_factory()
    address = shipping_address_factory(customer_2)
    
    url = reverse('shipping-address-detail', kwargs={'address_id': address.id})
    
    client.force_authenticate(user=customer_1)
    res = client.get(url)
    assert res.status_code == status.HTTP_404_NOT_FOUND
    assert res.data['status'] == "error"
    assert res.data['code'] == "not_found"
    assert res.data['message'] == "No shipping address matching the given ID found."
    

def test_get_shipping_address_by_superuser(client, customer_factory, super_user, shipping_address_factory):
    """
    Test that a superuser can retrieve a shipping address of any user.
    """
    customer = customer_factory()
    address = shipping_address_factory(customer)
    
    url = reverse('shipping-address-detail', kwargs={'address_id': address.id})
    
    client.force_authenticate(user=super_user)
    res = client.get(url)
    assert res.status_code == status.HTTP_200_OK
    assert res.data['status'] == "success"
    assert res.data['message'] == "Shipping address retrieved successfully."
    assert 'data' in res.data
    res_data = res.data['data']
    assert res_data['id'] == str(address.id)
    assert res_data['full_name'] == address.full_name
    assert res_data['street_address'] == address.street_address
    assert res_data['telephone'] == address.telephone
    assert res_data['city'] == address.city.name
    assert res_data['state'] == address.city.state.name
    assert res_data['country'] == address.city.state.country.name
    assert res_data['postal_code'] == address.postal_code
    assert 'created_at' in res_data
    assert 'updated_at' in res_data
    assert 'user' in res_data
    assert res_data['user']['id'] == str(customer.id)
    user_fields = [
        'email', 'is_verified', 'staff_handle', 'is_active',
        'is_customer', 'is_shopowner', 'is_staff', 'is_superuser',
        'is_superuser', 'date_joined', 'updated_at', 'profile'
    ]

    assert all(field in res_data['user'] for field in user_fields)
    assert 'password' not in res_data['user']
    
    
def test_get_shipping_address_with_invalid_id(client, customer, shipping_address_factory):
    """
    Test get specific shipping address with invalid ID (uuid) fails.
    """
    shipping_address_factory(customer)
    url = reverse('shipping-address-detail', kwargs={'address_id': 'invalid_uuid'})
    
    client.force_authenticate(user=customer)
    res = client.get(url)
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "invalid_uuid"
    assert res.data['message'] == "Invalid shipping address id."

    
def test_get_shipping_address_by_unauthenticated_user(client, customer, shipping_address_factory):
    """
    Test get specific shipping address by unauthenticated user fails.
    """
    address = shipping_address_factory(customer)
    url = reverse('shipping-address-detail', kwargs={'address_id': address.id})
    
    res = client.get(url)
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.data['status'] == "error"
    assert res.data['code'] == "unauthorized"
    assert res.data['message'] == "Authentication credentials were not provided."

    client.cookies['access_token'] = "Invalid_access_token2445"
    res = client.get(url)
    
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.data['status'] == "error"
    assert res.data['code'] == "unauthorized"
    assert res.data['message'] == "Token is invalid or expired"
    

@pytest.mark.parametrize(
    'user_type',
    ['shopowner', 'shop_staff'],
    ids=['shopowner', 'shop_staff']
)
def test_get_shipping_address_by_non_customer(client, customer_factory, all_users, user_type, shipping_address_factory):
    """
    Test get specific shipping address by non_customer (shop owner and staff).
    """
    user = all_users[user_type]
    address = shipping_address_factory(customer_factory())
    url = reverse('shipping-address-detail', kwargs={'address_id': address.id})
    
    client.force_authenticate(user=user)
    res = client.get(url)
    
    assert res.status_code == status.HTTP_403_FORBIDDEN
    assert res.data['status'] == "error"
    assert res.data['code'] == "forbidden"
    assert res.data['message'] == "You do not have permission to perform this action."


# =============================================================================
# TEST DELETE SHIPPING ADDRESS
# =============================================================================

def test_delete_shipping_address(client, customer, shipping_address_factory):
    """
    Test delete specific shipping address by ID.
    """
    address = shipping_address_factory(customer)
    shipping_address_factory(customer)
    
    assert ShippingAddress.objects.filter(id=address.id).exists()
    assert ShippingAddress.objects.count() == 2
    url = reverse('shipping-address-detail', kwargs={'address_id': address.id})
    
    client.force_authenticate(user=customer)
    res = client.delete(url)
    assert res.status_code == status.HTTP_204_NO_CONTENT
    assert not customer.addresses.filter(id=address.id).exists()
    assert ShippingAddress.objects.count() == 1
    

def test_delete_shipping_address_by_different_user(client, customer_factory, shipping_address_factory):
    """
    Test that a user cannot delete a shipping address of another user.
    """
    customer_1 = customer_factory()
    customer_2 = customer_factory()
    address = shipping_address_factory(customer_2)
    
    url = reverse('shipping-address-detail', kwargs={'address_id': address.id})
    
    client.force_authenticate(user=customer_1)
    res = client.delete(url)
    assert res.status_code == status.HTTP_404_NOT_FOUND
    assert res.data['status'] == "error"
    assert res.data['code'] == "not_found"
    assert res.data['message'] == "No shipping address matching given ID found."


def test_delete_shipping_address_by_superuser(client, customer_factory, super_user, shipping_address_factory):
    """
    Test that a superuser can delete a shipping address of any user.
    """
    customer = customer_factory()
    address = shipping_address_factory(customer)

    assert ShippingAddress.objects.filter(id=address.id).exists()
    
    url = reverse('shipping-address-detail', kwargs={'address_id': address.id})
    
    client.force_authenticate(user=super_user)
    res = client.delete(url)
    assert res.status_code == status.HTTP_204_NO_CONTENT
    assert not ShippingAddress.objects.filter(id=address.id).exists()
    
    
def test_delete_shipping_address_with_invalid_id(client, customer):
    """
    Test delete specific shipping address with invalid ID (uuid) fails.
    """
    url = reverse('shipping-address-detail', kwargs={'address_id': 'invalid_uuid'})
    
    client.force_authenticate(user=customer)
    res = client.delete(url)
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "invalid_uuid"
    assert res.data['message'] == "Invalid shipping address id."
    

def test_delete_non_existent_shipping_address(client, customer):
    """
    Test delete specific shipping address with non-existent ID fails.
    """
    url = reverse('shipping-address-detail', kwargs={'address_id': uuid.uuid4()})
    
    client.force_authenticate(user=customer)
    res = client.delete(url)
    assert res.status_code == status.HTTP_404_NOT_FOUND
    assert res.data['status'] == "error"
    assert res.data['code'] == "not_found"
    assert res.data['message'] == "No shipping address matching given ID found."


@pytest.mark.parametrize(
    'user_type',
    ['shopowner', 'shop_staff'],
    ids=['shopowner', 'shop_staff']
)
def test_delete_shipping_address_by_non_customer(client, customer, all_users, user_type, shipping_address_factory):
    """
    Test delete specific shipping address by non_customer (shop owner and staff).
    """
    user = all_users[user_type]
    address = shipping_address_factory(customer)
    url = reverse('shipping-address-detail', kwargs={'address_id': address.id})
    
    client.force_authenticate(user=user)
    res = client.delete(url)
    
    assert res.status_code == status.HTTP_403_FORBIDDEN
    assert res.data['status'] == "error"
    assert res.data['code'] == "forbidden"
    assert res.data['message'] == "You do not have permission to perform this action."


def test_delete_shipping_address_by_unauthenticated_user(client, customer, shipping_address_factory):
    """
    Test delete specific shipping address by unauthenticated user fails.
    """
    address = shipping_address_factory(customer)
    url = reverse('shipping-address-detail', kwargs={'address_id': address.id})
    
    res = client.delete(url)
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.data['status'] == "error"
    assert res.data['code'] == "unauthorized"
    assert res.data['message'] == "Authentication credentials were not provided."

    client.cookies['access_token'] = "Invalid_access_token2445"
    res = client.delete(url)
    
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.data['status'] == "error"
    assert res.data['code'] == "unauthorized"
    assert res.data['message'] == "Token is invalid or expired"