from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status

import pytest

User = get_user_model()

# ==========================================================
# CUSTOMER REGISTRATION TESTS
# ==========================================================

CUSTOMER_REGISTRATION_URL = reverse('customer-register')

REG_DATA = {
    'first_name': 'Test',
    'last_name': 'User',
    'telephone': '08121112323',
    'email': 'test-customer@email.com',
    'password': 'Password123#',
    'confirm_password': 'Password123#',
    'already_shopowner': False
}

@pytest.mark.django_db(transaction=True)
def test_customer_registration(mock_verification_email_task,  client, db_access):
    """"
    Test the customer registration process.
    """ 
    data = REG_DATA
    response = client.post(CUSTOMER_REGISTRATION_URL, data, format='json')
    mock_verification_email_task.assert_called_once()
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data['status'] == "success"
    assert response.data['message'] == "Customer registration successful."
    assert response.data['data']['is_customer'] == True
    assert response.data['data']['is_staff'] == False
    assert response.data['data']['is_shopowner'] == False
    assert response.data['data']['profile']['first_name'] == data['first_name']
    assert response.data['data']['profile']['last_name'] == data['last_name']

@pytest.mark.django_db(transaction=True)
def test_customer_registration_for_shopowner(mock_verification_email_task, client, shopowner):
    """
    Test the customer registration process for an existing shop owner.
    """
    data = {**REG_DATA, 'email': shopowner.email, 'already_shopowner': True}
    response = client.post(CUSTOMER_REGISTRATION_URL, data, format='json')
    mock_verification_email_task.assert_called_once()
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data['status'] == "success"
    assert response.data['message'] == "Customer registration successful."
    assert response.data['data']['is_customer'] == True
    assert response.data['data']['is_shopowner'] == True
    assert response.data['data']['is_staff'] == True
    assert response.data['data']['profile']['first_name'] == data['first_name']
    assert response.data['data']['profile']['last_name'] == data['last_name'] 

def test_customer_registration_for_shopowner_with_invalid_password(client, shopowner):
    """
    Test the customer registration process for an existing shop owner
    with an invalid password.
    """
    data = {
        **REG_DATA,
        'email': shopowner.email,
        'password': 'Password12345#',
        'confirm_password': 'Password12345#',
        'already_shopowner': True
    }
    response = client.post(CUSTOMER_REGISTRATION_URL, data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['status'] == "error"
    assert response.data['code'] == "invalid_credentials"
    assert response.data['message'] == "Customer registration failed."
    assert response.data['errors']['non_field_errors'] == ['Invalid credentials matching any shop owner.']

def test_customer_registration_for_shopowner_with_invalid_email(client, shopowner):
    """
    Test the customer registration process for an existing shop owner
    where the shop owner with email dooes not exist.
    """
    data = {
        **REG_DATA,
        'email': 'test-shopowner@email.com',
        'already_shopowner': True
    }
    response = client.post(CUSTOMER_REGISTRATION_URL, data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['status'] == "error"
    assert response.data['code'] == "invalid_credentials"
    assert response.data['message'] == "Customer registration failed."
    assert response.data['errors']['non_field_errors'] == ['Invalid credentials matching any shop owner.']

def test_customer_registration_with_missing_data(client):
    """
    Test the customer registration with missing data.
    """
    data = {}
    response = client.post(CUSTOMER_REGISTRATION_URL, data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['status'] == "error"
    assert response.data['code'] == "validation_error" 
    assert response.data['message'] == "Customer registration failed."
    assert response.data['errors']['email'] == ["This field is required."]
    assert response.data['errors']['first_name'] == ["This field is required."]
    assert response.data['errors']['last_name'] == ["This field is required."]
    assert response.data['errors']['password'] == ["This field is required."]
    assert response.data['errors']['confirm_password'] == ["This field is required."]

def test_customer_registration_blank_data_values(client):
    """
    Test the customer registration with blank data values.
    """
    data = {
        'first_name': '',
        'last_name': '',
        'telephone': '',
        'email': '',
        'password': '',
        'confirm_password': ''
    }
    response = client.post(CUSTOMER_REGISTRATION_URL, data, format='json')
    assert response.data['status'] == "error"
    assert response.data['code'] == "validation_error"
    assert response.data['message'] == "Customer registration failed."
    assert response.data['errors']['email'] == ["This field may not be blank."]
    assert response.data['errors']['first_name'] == ["This field may not be blank."]
    assert response.data['errors']['last_name'] == ["This field may not be blank."]
    assert response.data['errors']['password'] == ["This field may not be blank."]
    assert response.data['errors']['confirm_password'] == ["This field may not be blank."]

def test_customer_registration_with_invalid_email_address(client):
    """
    Test the customer registration process with invalid email address.
    """
    data = {**REG_DATA, 'email': 'invalid_email'}
    response = client.post(CUSTOMER_REGISTRATION_URL, data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['status'] == "error"
    assert response.data['code'] == "validation_error"
    assert response.data['message'] == "Customer registration failed."
    assert response.data['errors']['email'] == ["Enter a valid email address."]

def test_customer_registration_with_weak_password(client, db_access):
    """
    Test the customer registration process with weak password.
    """
    data = {**REG_DATA, 'password': 'weak'}
    errors = [    
        'Password must be at least 8 characters long.',
        'Password must contain at least one digit.',
        'Password must contain at least one letter.',
        'Password must contain at least one uppercase letter.',
        'Password must contain at least one lowercase letter.',
        'Password must contain at least one special character.'
    ]
    response = client.post(CUSTOMER_REGISTRATION_URL, data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['status'] == "error"
    assert response.data['code'] == "validation_error"
    assert response.data['message'] == "Customer registration failed."
    pwd_errors = response.data['errors']['password']
    assert all(error in errors for error in pwd_errors)

def test_customer_regitration_password_without_letters(client, db_access):
    """
    Test the customer registration process with a password without letters.
    """
    data = {**REG_DATA,
        'password': '12345678#',
        'confirm_password': '12345678#'
    }
    response = client.post(CUSTOMER_REGISTRATION_URL, data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['status'] == 'error'
    assert response.data['code'] == "validation_error"
    assert response.data['message'] == "Customer registration failed."
    pwd_errors = response.data['errors']['password']
    assert "Password must contain at least one letter." in pwd_errors

def test_customer_registration_with_mismatching_password(client, db_access):
    """
    Test the customer registration process with mismatching passwords.
    """
    data = {**REG_DATA, 'confirm_password': 'Password123456#'
    }
    response = client.post(CUSTOMER_REGISTRATION_URL, data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['status'] == "error"
    assert response.data['code'] == "validation_error"
    assert response.data['message'] == "Customer registration failed."
    assert response.data['errors']['confirm_password'] == ['Passwords do not match.']

def test_customer_registration_existing_email(client, customer):
    """
    Test the customer registration process with an
    existing customer email.
    """
    data = {**REG_DATA, 'email': customer.email}
    response = client.post(CUSTOMER_REGISTRATION_URL, data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['status'] == "error"
    assert response.data['code'] == "validation_error"
    assert response.data['message'] == "Customer registration failed."
    assert response.data['errors']['email'] == ["User with email already exists."]
    assert User.objects.filter(email=customer.email).exists() is True

# ==========================================================
# CUSTOMER LOGIN TESTS
# ==========================================================
CUSTOMER_LOGIN_URL = reverse('customer-login')

def test_customer_login(client, customer):
    """
    Test the customer login process.
    """
    data = {
        'email': customer.email,
        'password': 'Password123#',
        'remember_me': True
    }
    response = client.post(CUSTOMER_LOGIN_URL, data, format='json')
    assert response.status_code == status.HTTP_200_OK
    assert response.data['status'] == "success"
    assert response.data['message'] == f"Log in successful."
    assert response.data['data']['id'] == str(customer.id)
    assert response.data['data']['email'] == customer.email
    assert response.cookies['access_token']['httponly'] is True
    assert response.cookies['refresh_token']['httponly'] is True
    assert response.cookies['refresh_token']['max-age'] is not None
    assert response.cookies['refresh_token']['max-age'] == 604800

def test_customer_login_as_shopowner_and_customer(client, shopowner):
    """
    Test customer login as a user who is a customer and a shop owner.
    """
    shopowner.is_customer = True
    shopowner.save(update_fields=['is_customer'])
    data = {
        'email': shopowner.email,
        'password': 'Password123#',
        'remember_me': True
    }
    res = client.post(CUSTOMER_LOGIN_URL, data, format='json')
    assert res.status_code == status.HTTP_200_OK
    assert res.data['status'] == "success"
    assert res.data['message'] == f"Log in successful."
    assert res.data['data']['id'] == str(shopowner.id)
    assert res.data['data']['email'] == shopowner.email
    assert res.cookies['access_token']['httponly'] is True
    assert res.cookies['refresh_token']['httponly'] is True
    assert res.cookies['refresh_token']['max-age'] is not None
    assert res.cookies['refresh_token']['max-age'] == 604800

def test_customer_login_false_remember_me(client, customer):
    """
    Test customer login with false remember me.
    Refresh token expires after one day.
    """
    data = {
        'email': customer.email,
        'password': 'Password123#',
        'remember_me': False
    }
    response = client.post(CUSTOMER_LOGIN_URL, data, format='json')
    assert response.status_code == status.HTTP_200_OK
    assert response.data['status'] == 'success'
    assert response.cookies['refresh_token'] is not None
    assert response.cookies['refresh_token']['max-age'] == 86400

def test_customer_login_as_shopowner(client, shopowner):
    """
    Test customer login as shop owner.
    """
    data = {
        'email': shopowner.email,
        'password': 'Password123#',
        'remember_me': True
    }
    response = client.post(CUSTOMER_LOGIN_URL, data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['status'] == "error"
    assert response.data['code'] == "invalid_credentials"
    assert response.data['message'] == "Log in failed."
    assert response.data['errors'] is not None
    assert response.data['errors']['non_field_errors'] == ["Invalid login credentials were provided."]

def test_customer_login_missing_email(client):
    """
    Test the customer login process with missing email.
    """
    data = {
        'password': 'password123#',
        'remember_me': True
    }

    response = client.post(CUSTOMER_LOGIN_URL, data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['status'] == "error"
    assert response.data['message'] == "Log in failed."
    assert response.data['code'] == "validation_error"
    assert response.data['errors'] is not None
    assert response.data['errors']['email'] == ['This field is required.']

def test_customer_login_missing_password(client):
    """
    Test customer login process with missing password.
    """
    data = {
        'email': 'customer@email.com',
        'remember_me': True
    }
    response = client.post(CUSTOMER_LOGIN_URL, data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['status'] == "error"
    assert response.data['message'] == "Log in failed."
    assert response.data['code'] == "validation_error"
    assert response.data['errors'] is not None
    assert response.data['errors']['password'] == ['This field is required.']

def test_customer_login_invalid_password(client, customer):
    """
    Test customer login process with invalid password.
    """
    data = {
        'email': customer.email,
        'password': 'wrong_password',
        'remember_me': False
    }
    response = client.post(CUSTOMER_LOGIN_URL, data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['status'] == "error"
    assert response.data['code'] == "invalid_credentials"
    assert response.data['message'] == "Log in failed."
    assert response.data['errors'] is not None
    assert response.data['errors']['non_field_errors'] == ["Invalid login credentials were provided."]

def test_customer_login_invalid_email(client, db_access):
    """"
    Test customer login process with invalid email.
    """
    data = {
        'email': 'invalid_email',
        'password': 'password123#'
    }
    response = client.post(CUSTOMER_LOGIN_URL, data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['status'] == "error"
    assert response.data['code'] == "invalid_credentials"
    assert response.data['message'] == "Log in failed."
    assert response.data['errors'] is not None
    assert response.data['errors']['non_field_errors'] == ["Invalid login credentials were provided."]

def test_customer_login_nonexistent_email(client, db_access):
    """
    Test customer login process with a non-existent email.
    """
    data = {
        'email': 'nonexistent@email.com',
        'password': 'password123#'
    }
    response = client.post(CUSTOMER_LOGIN_URL, data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['status'] == "error"
    assert response.data['code'] == "invalid_credentials"
    assert response.data['message'] == "Log in failed."
    assert response.data['errors'] is not None
    assert response.data['errors']['non_field_errors'] == ["Invalid login credentials were provided."]
