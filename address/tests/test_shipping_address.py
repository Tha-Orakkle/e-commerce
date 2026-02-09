from django.urls import reverse
from rest_framework import status


SHIPPING_ADDRESS_LIST_CREATE_URL = reverse('shipping-address-list-create')

def test_create_shipping_address(client, customer, create_shipping_address_data):
    """
    Test creating a shipping address for a user.
    """
    client.force_authenticate(user=customer)
    res = client.post(
        SHIPPING_ADDRESS_LIST_CREATE_URL,
        data=create_shipping_address_data,
        format='json'    
    )
    assert res.status_code == status.HTTP_201_CREATED
    assert res.data['message'] == "Shipping address created successfully."
    assert 'data' in res.data
    data = res.data['data']
    assert data['id'] is not None
    assert data['full_name'] == create_shipping_address_data['full_name']
    assert data['street_address'] == create_shipping_address_data['street_address']
    tel1 = "+234" + create_shipping_address_data['telephone'].lstrip("0").strip()
    tel2 = data['telephone'].replace(" ", "")
    assert tel1 == tel2
    assert data['city'] is not None
    assert data['state'] is not None
    assert data['country'] is not None
    assert data['postal_code'] == create_shipping_address_data['postal_code']
    assert 'created_at' in data
    assert 'updated_at' in data
    customer.refresh_from_db()
    assert customer.addresses.filter(id=data['id']).exists()
    