from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from unittest.mock import patch
import pytest


User = get_user_model()
customer_registration_url = reverse('customer-register')
REG_DATA = {
    'first_name': 'Test',
    'last_name': 'User',
    'telephone': '08121112323',
    'email': 'test-user@email.com',
    'password': 'Password123#',
    'confirm_password': 'Password123#',
    'already_shopowner': False
}


def test_customer_registration(mock_verification_email_task,  client, db_access):
    """"
    Test the customer registration process.
    """ 
    data = REG_DATA
    response = client.post(customer_registration_url, data, format='json')
    mock_verification_email_task.assert_called_once
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data['status'] == "success"
    assert response.data['message'] == "Customer registration successful."
    assert response.data['data']['is_customer'] == True
    assert response.data['data']['is_staff'] == False
    assert response.data['data']['is_shopowner'] == False
    assert response.data['data']['profile']['first_name'] == data['first_name']
    assert response.data['data']['profile']['last_name'] == data['last_name']
    

def test_customer_registration_for_shopowner(mock_verification_email_task, client, shopowner):
    """
    Test the customer registration process for an existing shop owner.
    """
    data = {**REG_DATA, 'email': shopowner.email, 'already_shopowner': True}
    response = client.post(customer_registration_url, data, format='json')
    mock_verification_email_task.assert_called_once
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
    response = client.post(customer_registration_url, data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['status'] == "error"
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
    response = client.post(customer_registration_url, data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['status'] == "error"
    assert response.data['message'] == "Customer registration failed."
    assert response.data['errors']['non_field_errors'] == ['Invalid credentials matching any shop owner.']


def test_customer_registration_with_missing_data(client):
    """
    Test the customer registration with missing data.
    """
    data = {}
    response = client.post(customer_registration_url, data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['status'] == "error"
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
    response = client.post(customer_registration_url, data, format='json')
    assert response.data['status'] == "error"
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
    response = client.post(customer_registration_url, data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['status'] == "error"
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
    response = client.post(customer_registration_url, data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['status'] == "error"
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
    response = client.post(customer_registration_url, data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['status'] == 'error'
    assert response.data['message'] == "Customer registration failed."
    pwd_errors = response.data['errors']['password']
    assert "Password must contain at least one letter." in pwd_errors


def test_customer_registration_with_mismatching_password(client, db_access):
    """
    Test the customer registration process with mismatching passwords.
    """
    data = {**REG_DATA, 'confirm_password': 'Password123456#'
    }
    response = client.post(customer_registration_url, data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['status'] == "error"
    assert response.data['message'] == "Customer registration failed."
    assert response.data['errors']['confirm_password'] == ['Passwords do not match.']


def test_user_registration_existing_email(client, customer):
    """
    Test the customer registration process with an
    existing customer email.
    """
    data = {**REG_DATA, 'email': customer.email}
    response = client.post(customer_registration_url, data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['status'] == "error"
    assert response.data['message'] == "Customer registration failed."
    assert response.data['errors']['email'] == ["User with email already exists."]
    assert User.objects.filter(email=customer.email).exists() is True
