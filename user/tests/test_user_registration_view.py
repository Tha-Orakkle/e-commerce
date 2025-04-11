from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from unittest.mock import patch
import pytest


User = get_user_model()

def test_user_registration(mock_verification_email_task,  client, db_access):
    """"
    Test the user registration process.
    """
    url = reverse('register')
    data = {
        'email': 'user2@email.com',
        'password': 'Password123#',
        'confirm_password': 'Password123#'
    }
    response = client.post(url, data, format='json')
    mock_verification_email_task.assert_called_once
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data['status'] == "success"
    assert response.data['message'] == f"User {data['email']} created successfully."


def test_user_registration_missing_email(client):
    """
    Test the user registration process with missing email.
    """
    url = reverse('register')
    data = {
        'password': 'Password123#',
        'confirm_password': 'Password123#'
    }
    response = client.post(url, data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['status'] == "error"
    assert response.data['message'] == "Please provide email and password."


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
    assert response.data['status'] == "error"
    assert response.data['message'] == "Please provide email and password."


def test_user_registration_password_mismatch(client):
    """
    Test the user registration process with mismatching passwords.
    """
    url = reverse('register')
    data = {
        'email': 'user@email.com',
        'password': 'password123#',
        'confirm_password': 'password1234#'
    }
    response = client.post(url, data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['status'] == "error"
    assert response.data['message'] == "Password and confirm_password fields do not match."


def test_user_registration_invalid_email(client):
    """
    Test the user registration process with invalid email.
    """
    url = reverse('register')
    data = {
        'email': 'invalid_email',
        'password': 'Password123#',
        'confirm_password': 'Password123#'
    }
    response = client.post(url, data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['status'] == "error"
    assert response.data['message'] == "The email address is invalid."


def test_user_registration_existing_email(client, user):
    """
    Test the user registration process with an existing email.
    """
    url = reverse('register')
    data = {
        'email': user.email,
        'password': 'Password123#',
        'confirm_password': 'Password123#'
    }
    response = client.post(url, data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['status'] == "error"
    assert response.data['message'] == "User with email already exists."
    assert User.objects.filter(email=user.email).exists() is True


def test_user_regitration_password_length(client):
    """
    Test the user registration process with a short password.
    """
    url = reverse('register')
    data = {
        'email': 'user2@email.com',
        'password': 'passw12',
        'confirm_password': 'passw12'
    }
    response = client.post(url, data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['status'] == 'error'
    assert response.data['message'] == "Password must be at least 8 characters long."



def test_user_regitration_password_without_digit(client):
    """
    Test the user registration process with a password without digits.
    """
    url = reverse('register')
    data = {
        'email': 'user2@email.com',
        'password': 'Weak_password#',
        'confirm_password': 'Weak_password#'
    }
    response = client.post(url, data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['status'] == 'error'
    assert response.data['message'] == "Password must contain at least one digit."


def test_user_regitration_password_without_special_char(client):
    """
    Test the user registration process with a password without special character.
    """
    url = reverse('register')
    data = {
        'email': 'user2@email.com',
        'password': 'Weak_password123',
        'confirm_password': 'Weak_password123'
    }
    response = client.post(url, data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['status'] == 'error'
    assert response.data['message'] == "Password must contain at least one special character."

def test_user_regitration_password_without_letters(client):
    """
    Test the user registration process with a password without letters.
    """
    url = reverse('register')
    data = {
        'email': 'user2@email.com',
        'password': '12345678#',
        'confirm_password': '12345678#'
    }
    response = client.post(url, data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['status'] == 'error'
    assert response.data['message'] == "Password must contain at least one letter."
