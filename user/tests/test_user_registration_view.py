from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from unittest.mock import patch
import pytest


User = get_user_model()

@patch('user.tasks.send_verification_mail_task.delay')
def test_user_registration(mock_test,  client, db_access):
    """"
    Test the user registration process.
    """
    url = reverse('register')
    data = {
        'email': 'user2@email.com',
        'password': 'password123#',
        'confirm_password': 'password123#'
    }
    response = client.post(url, data, format='json')
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data['success'] == f"User {data['email']} created successfully"


def test_user_registration_missing_email(client):
    """
    Test the user registration process with missing email.
    """
    url = reverse('register')
    data = {
        'password': 'password123#',
        'confirm_password': 'password123#'
    }
    response = client.post(url, data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['error'] == "Please provide email and password."


def test_user_registration_missing_password(client):
    """
    Test the user registration process with missing password.
    """
    url = reverse('register')
    data = {
        'email': 'user2@email.com',
        'confirm_password': 'password123#'
    }
    response = client.post(url, data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['error'] == "Please provide email and password."


def test_user_registration_password_mismatch(client):
    url = reverse('register')
    data = {
        'email': 'user@email.com',
        'password': 'password123#',
        'confirm_password': 'password1234#'
    }
    response = client.post(url, data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['error'] == "Passwords do not match."


def test_user_registration_invalid_email(client):
    """
    Test the user registration process with invalid email.
    """
    url = reverse('register')
    data = {
        'email': 'invalid_email',
        'password': 'password123#',
        'confirm_password': 'password123#'
    }
    response = client.post(url, data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['error'] == "The email address is invalid."


def test_user_registration_existing_email(client, user):
    """
    Test the user registration process with an existing email.
    """
    url = reverse('register')
    data = {
        'email': user.email,
        'password': 'password123#',
        'confirm_password': 'password123#'
    }
    response = client.post(url, data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['error'] == "User with email already exists."
    assert User.objects.filter(email=user.email).exists() is True
