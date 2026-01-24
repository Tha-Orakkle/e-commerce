from django.urls import reverse
from rest_framework import status

import pytest

from product.tests.fixtures import create_fake_images, create_fake_files


# =============================================================================
# TESTS FOR SHOP OWNER REGISTRATION
# =============================================================================
SHOP_OWNER_REGISTER_URL = reverse('shopowner-register')
SHOP_OWNER_REGISTER_DATA = {
    'email': 'shopowner@email.com',
    'staff_handle': 'staffhandle123',
    'first_name': 'John',
    'last_name': 'Doe',
    'telephone': '+2348012345678',
    'password': 'Password123#',
    'confirm_password': 'Password123#',
    'shop_name': 'My Shop',
    'shop_description': 'A description of my shop.',
    'shop_logo': create_fake_images(1)[0],
    'already_customer': False
}


def test_shop_owner_registration(mock_verification_email_task, client, db_access):
    """Test shop owner registration."""
    res = client.post(SHOP_OWNER_REGISTER_URL, SHOP_OWNER_REGISTER_DATA, format='multipart')
    
    assert res.status_code == status.HTTP_201_CREATED
    assert res.data['status'] == "success"
    assert res.data['message'] == "Shop owner registration successful."
    assert 'data' in res.data
    mock_verification_email_task.assert_called_once
    assert res.data['data']['name'] == SHOP_OWNER_REGISTER_DATA['shop_name']
    assert 'code' in res.data['data']
    assert res.data['data']['code'].startswith('SH')
    assert 'owner' in res.data['data']
    assert res.data['data']['owner']['email'] == SHOP_OWNER_REGISTER_DATA['email']
    assert res.data['data']['owner']['id'] is not None
    assert res.data['data']['owner']['is_active'] is True
    assert res.data['data']['owner']['is_staff'] is True
    assert res.data['data']['owner']['is_shopowner'] is True
    assert res.data['data']['owner']['is_superuser'] is False
    assert res.data['data']['owner']['is_verified'] is False
    assert res.data['data']['owner']['is_customer'] is False
    assert 'profile' in res.data['data']['owner']
    assert res.data['data']['owner']['profile']['id'] is not None
    assert res.data['data']['owner']['profile']['first_name'] == SHOP_OWNER_REGISTER_DATA['first_name']
    assert res.data['data']['owner']['profile']['last_name'] == SHOP_OWNER_REGISTER_DATA['last_name']
    assert 'passord' not in res.data['data']
    assert 'passord' not in res.data['data']['owner']
    assert 'passord' not in res.data['data']['owner']['profile']
    assert res.data['data']['logo'] is not None
    assert res.data['data']['logo'].startswith('/media/shp')

@pytest.mark.django_db(transaction=True)
def test_shop_owner_registration_with_existing_customer(mock_verification_email_task, client, customer):
    """Test shop owner registration by an existing customer."""
    data = {
        **SHOP_OWNER_REGISTER_DATA,
        'email': customer.email,
        'shop_logo': create_fake_images(1)[0],
        'already_customer': True
    }
    res = client.post(SHOP_OWNER_REGISTER_URL, data, format='multipart')
    print(res.data)
    assert res.status_code == status.HTTP_201_CREATED
    assert res.data['status'] == "success"
    assert res.data['message'] == "Shop owner registration successful."
    mock_verification_email_task.assert_called_once()
    assert 'data' in res.data
    assert res.data['data']['name'] == data['shop_name']
    assert res.data['data']['owner']['email'] == customer.email
    assert res.data['data']['owner']['is_shopowner'] is True

@pytest.mark.django_db(transaction=True)
def test_shop_owner_registration_by_verified_customer(mock_verification_email_task, client, customer):
    """Test shop owner registration by customer with verified email"""
    customer.is_verified = True
    customer.save(update_fields=['is_verified'])
    data = {
        **SHOP_OWNER_REGISTER_DATA,
        'email': customer.email,
        'shop_logo': create_fake_images(1)[0],
        'already_customer': True
    }
    res = client.post(SHOP_OWNER_REGISTER_URL, data, format='multipart')

    assert res.status_code == status.HTTP_201_CREATED
    assert res.data['status'] == "success"
    assert res.data['message'] == "Shop owner registration successful."
    mock_verification_email_task.assert_not_called()

def test_shop_owner_registration_with_nonexisting_customer_and_already_customer_true(client, db_access):
    """Test shop owner registration with non-existing customer but already_customer is True."""
    invalid_data = {
        **SHOP_OWNER_REGISTER_DATA,
        'shop_logo': create_fake_images(1)[0],
        'already_customer': True
    }

    res = client.post(SHOP_OWNER_REGISTER_URL, invalid_data, format='multipart')
    
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['message'] == "Shop owner registration failed."
    assert 'errors' in res.data
    assert res.data['errors']['non_field_errors'] == ['Invalid credentials matching any customer.']

def test_shop_owner_registration_as_existing_customer_with_wrong_password(client, customer):
    """Test shop owner registration as a customer with the wrong password"""
    data = {
        **SHOP_OWNER_REGISTER_DATA,
        'email': customer.email,
        'password': 'Wrong_Password',
        'confirm_password': 'Wrong_Password',
        'shop_logo': create_fake_images(1)[0],
        'already_customer': True
    }

    res = client.post(SHOP_OWNER_REGISTER_URL, data, format='multipart')

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['message'] == "Shop owner registration failed."
    assert 'errors' in res.data
    assert res.data['errors']['non_field_errors'] == ['Invalid credentials matching any customer.']

def test_shop_owner_registration_with_existing_email_but_already_customer_false(client, db_access, customer):
    """Test shop owner registration with an existing email but already_customer is False."""
    data = {
        **SHOP_OWNER_REGISTER_DATA,
        'email': customer.email,
        'shop_logo': create_fake_images(1)[0],
        'already_customer': False
    }
    res = client.post(SHOP_OWNER_REGISTER_URL, data, format='multipart')

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['message'] == "Shop owner registration failed."
    assert 'errors' in res.data
    assert res.data['errors']['email'] == ['User with email already exists.']


def test_shop_owner_registration_by_existing_customer_already_shopowner(client, shopowner):
    """Test shop owner registration with an existing email of a shop owner."""
    data = {
        **SHOP_OWNER_REGISTER_DATA,
        'email': shopowner.email,
        'shop_logo': create_fake_images(1)[0],
        'already_customer': True
    }
    res = client.post(SHOP_OWNER_REGISTER_URL, data, format='multipart')

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['message'] == "Shop owner registration failed."
    assert 'errors' in res.data
    assert res.data['errors']['email'] == ['Shop owner with email already exists.']


def test_shop_owner_registration_with_missing_data(client, db_access):
    """Test shop owner registration with missing data."""
    missing_data = {}
    res = client.post(SHOP_OWNER_REGISTER_URL, missing_data, format='multipart')

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['message'] == "Shop owner registration failed."
    assert res.data['code'] == "validation_error"
    assert 'errors' in res.data
    expected_error_fields = [
        'email', 'staff_handle', 'first_name', 'last_name', 'telephone',
        'password', 'confirm_password', 'shop_name'
    ]
    assert all(res.data['errors'][field] == ['This field is required.'] for field in expected_error_fields)


def test_shop_owner_registration_with_invalid_first_and_last_name(client, db_access):
    """
    Test shop owner registration with invalid data.
    """
    invalid_data = {
        **SHOP_OWNER_REGISTER_DATA,
        'first_name': 'J',
        'last_name': 'D',
        'shop_logo': create_fake_images(1)[0]
    }

    res = client.post(SHOP_OWNER_REGISTER_URL, invalid_data, format='multipart')
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "validation_error"
    assert res.data['message'] == "Shop owner registration failed."
    assert res.data['errors'] is not None
    assert res.data['errors']['first_name'] == ["Ensure this field has at least 2 characters."]
    assert res.data['errors']['last_name'] == ["Ensure this field has at least 2 characters."]

    invalid_data['first_name'] = 'J' * 31  # too long
    invalid_data['last_name'] = 'D' * 31   # too long
    invalid_data['shop_logo'] = create_fake_images(1)[0]

    res = client.post(SHOP_OWNER_REGISTER_URL, invalid_data, format='multipart')
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['errors']['first_name'] == ["Ensure this field has no more than 30 characters."]
    assert res.data['errors']['last_name'] == ["Ensure this field has no more than 30 characters."]

    

def test_shop_owner_registration_with_invalid_telephone(client, db_access):
    """
    Test shop owner registration with invalid telephone number.
    """
    invalid_data = {
        **SHOP_OWNER_REGISTER_DATA,
        'telephone': 'invalid_phone',
        'shop_logo': create_fake_images(1)[0]
    }
    res = client.post(SHOP_OWNER_REGISTER_URL, invalid_data, format='multipart')

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "validation_error"
    assert res.data['message'] == "Shop owner registration failed."
    assert res.data['errors'] is not None
    assert res.data['errors']['telephone'] == ["Enter a valid phone number."]


def test_shop_owner_registration_with_invalid_passwords(client, db_access):
    """
    Test shop owner registration with invalid passwords.
    """
    # weak password
    invalid_data = {
        **SHOP_OWNER_REGISTER_DATA,
        'password': 'weak',
        'confirm_password': 'weak',
        'shop_logo': create_fake_images(1)[0]
    }
    res = client.post(SHOP_OWNER_REGISTER_URL, invalid_data, format='multipart')

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "validation_error"
    assert res.data['message'] == "Shop owner registration failed."
    assert res.data['errors'] is not None
    assert 'password' in res.data['errors']

    # mismatched passwords
    invalid_data = {
        **SHOP_OWNER_REGISTER_DATA,
        'password': 'Password123#',
        'confirm_password': 'Password1234#',
        'shop_logo': create_fake_images(1)[0]
    }
    res = client.post(SHOP_OWNER_REGISTER_URL, invalid_data, format='multipart')

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "validation_error"
    assert res.data['message'] == "Shop owner registration failed."
    assert res.data['errors'] is not None
    assert res.data['errors']['confirm_password'] == ["Passwords do not match."]


def test_shop_owner_registration_with_missing_shop_logo(client, db_access):
    """
    Test shop owner registration without shop logo.
    """
    data = SHOP_OWNER_REGISTER_DATA.copy()
    del data['shop_logo']
    
    res = client.post(SHOP_OWNER_REGISTER_URL, data, format='multipart')
    
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['code'] == "validation_error"
    assert res.data['message'] == "Shop owner registration failed."
    assert res.data['errors'] is not None
    assert res.data['errors']['shop_logo'] == ["No file was submitted."]
    
def test_shop_owner_registration_with_invalid_with_invalid_shop_logo(client, db_access):
    """
    Test shop owner registration with non-file and non-image shop logo.
    """
    data = SHOP_OWNER_REGISTER_DATA.copy()
    data['shop_logo'] = "Non-file shop logo"
    
    res = client.post(SHOP_OWNER_REGISTER_URL, data, format='multipart')
    
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['code'] == "validation_error"
    assert res.data['message'] == "Shop owner registration failed."
    assert res.data['errors'] is not None
    assert res.data['errors']['shop_logo'] == ["The submitted data was not a file. Check the encoding type on the form."]
    
    data['shop_logo'] = create_fake_files(1)[0]

    res = client.post(SHOP_OWNER_REGISTER_URL, data, format='multipart')

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['code'] == "validation_error"
    assert res.data['message'] == "Shop owner registration failed."
    assert res.data['errors'] is not None
    assert res.data['errors']['shop_logo'] == ["Upload a valid image. The file you uploaded was either not an image or a corrupted image."]
