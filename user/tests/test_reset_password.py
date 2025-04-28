from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str


from django.urls import reverse

from rest_framework import status

def test_forgot_password(client, user, mock_password_reset_email_task):
    """
    Test the forgot password functionality.
    """
    url = reverse('forgot-password')
    response = client.post(url, data={'email': user.email}, format='json')
    mock_password_reset_email_task.assert_called_once
    assert response.status_code == status.HTTP_202_ACCEPTED
    assert response.data['status'] == "success"
    assert response.data['code'] == 202
    assert response.data['message'] == "Password reset link will be sent to your email address."


def test_forgot_password_with_invalid_email(client, db_access):
    """
    Test the forgot password functionality with an invalid email.
    """
    url = reverse('forgot-password')
    response = client.post(url, data={'email': 'invalid_email'}, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['status'] == "error"
    assert response.data['message'] == "User with this email does not exist."

def test_forgot_password_without_email(client):
    """
    Test the forgot password functionality without an email.
    """
    url = reverse('forgot-password')
    response = client.post(url, data={}, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['status'] == "error"
    assert response.data['message'] == "Please provide an email address."


def test_reset_password(client, user):
    """
    Test the reset password functionality.
    """
    url = reverse('reset-password-confirm')
    token_generator = PasswordResetTokenGenerator()
    token = token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.email))
    url = f"{url}?uid={uid}&token={token}"
    response = client.post(url, data={
        'new_password': 'NewPassword123#',
        'confirm_password': 'NewPassword123#'
    }, format='json')
    assert response.status_code == status.HTTP_200_OK
    assert response.data['status'] == "success"
    assert response.data['code'] == 200
    assert response.data['message'] == "Password reset successfully."


def test_reset_password_with_invalid_token(client, user):
    """
    Test the reset password functionality with an invalid token.
    """
    url = reverse('reset-password-confirm')
    uid = urlsafe_base64_encode(force_bytes(user.email))
    token_generator = PasswordResetTokenGenerator()
    token = token_generator.make_token(user) + 'invalid'
    url = f"{url}?uid={uid}&token={token}"
    response = client.post(url, data={
        'new_password': 'NewPassword123#',
        'confirm_password': 'NewPassword123#'
    }, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['status'] == "error"
    assert response.data['message'] == "Invalid or expired password reset token."


def test_reset_password_with_invalid_uid(client, user):
    """
    Test the reset password functionality with an invalid uid.
    """
    url = reverse('reset-password-confirm')
    token_generator = PasswordResetTokenGenerator()
    token = token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.email)) + 'invalid'
    url = f"{url}?uid={uid}&token={token}"
    response = client.post(url, data={
        'new_password': 'NewPassword123#',
        'confirm_password': 'NewPassword123#'
    }, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['status'] == "error"
    assert response.data['message'] == "Invalid password reset link."


def test_reset_password_without_uid_and_token(client, user):
    """
    Test the reset password functionality without uid and token.
    """
    url = reverse('reset-password-confirm')
    response = client.post(url, data={
        'new_password': 'NewPassword123#',
        'confirm_password': 'NewPassword123#'
    }, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['status'] == "error"
    assert response.data['message'] == "Invalid password reset link."


def test_reset_password_with_mismatched_passwords(client, user):
    """
    Test the reset password functionality with mismatched passwords.
    """
    url = reverse('reset-password-confirm')
    token_generator = PasswordResetTokenGenerator()
    token = token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.email))
    url = f"{url}?uid={uid}&token={token}"
    response = client.post(url, data={
        'new_password': 'NewPassword123#',
        'confirm_password': 'DifferentPassword123#'
    }, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['status'] == "error"
    assert response.data['message'] == "Passwords do not match."


def test_reset_password_without_new_password(client, user):
    """
    Test the reset password functionality without a new password.
    """
    url = reverse('reset-password-confirm')
    token_generator = PasswordResetTokenGenerator()
    token = token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.email))
    url = f"{url}?uid={uid}&token={token}"
    response = client.post(url, data={
        'confirm_password': 'NewPassword123#'
    }, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['status'] == "error"
    assert response.data['message'] == "Please provide a new password and confirm password."


def test_reset_password_without_confirm_password(client, user):
    """
    Test the reset password functionality without a confirm password.
    """
    url = reverse('reset-password-confirm')
    token_generator = PasswordResetTokenGenerator()
    token = token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.email))
    url = f"{url}?uid={uid}&token={token}"
    response = client.post(url, data={
        'new_password': 'NewPassword123#'
    }, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['status'] == "error"
    assert response.data['message'] == "Please provide a new password and confirm password."