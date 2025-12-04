from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from unittest.mock import patch


from django.urls import reverse

from rest_framework import status


# ==========================================================
# FORGOT PASSWORD TESTS
# ==========================================================
FORGOT_PASSWORD_URL = reverse('forgot-password')


def test_forgot_password_by_existing_user(client, dummy_user):
    """
    Test forgot password for an existing user.
    Test all the way to the task being called.
    """
    with patch(
        'user.api.v1.routes.password.PasswordResetTokenGenerator.make_token',
        return_value='fixed-token') as mock_make_token, \
        patch('user.api.v1.routes.password.urlsafe_base64_encode',
              return_value='encoded-email') as mock_encode, \
        patch('user.api.v1.routes.password.send_password_reset_mail_task.delay') as mock_send:
            
        res = client.post(FORGOT_PASSWORD_URL, data={'email': dummy_user.email}, format='json')
        
        assert res.status_code == status.HTTP_202_ACCEPTED
        assert res.data['status'] == "success"
        assert res.data['message'] == "Password reset link sent."
        mock_make_token.assert_called_once_with(dummy_user)
        mock_encode.assert_called_once_with(force_bytes(dummy_user.email))
        mock_send.assert_called_once()
        called_email, called_link = mock_send.call_args[0]
        assert called_email == dummy_user.email
        assert 'fixed-token' in called_link
        assert 'encoded-email' in called_link
        

def test_forgot_password_with_nonexistent_email(client, db_access):
    """
    Test the forgot password functionality with an email 
    address not associated with a user.
    """
    with patch(
        'user.api.v1.routes.password.PasswordResetTokenGenerator.make_token',
        return_value='fixed-token') as mock_make_token, \
        patch('user.api.v1.routes.password.urlsafe_base64_encode',
              return_value='encoded-email') as mock_encode, \
        patch('user.api.v1.routes.password.send_password_reset_mail_task.delay') as mock_send:
   
        res = client.post(FORGOT_PASSWORD_URL, data={'email': 'non-existent@email.com'}, format='json')
        
        assert res.status_code == status.HTTP_202_ACCEPTED
        assert res.data['status'] == "success"
        assert res.data['message'] == "Password reset link sent."
        mock_make_token.assert_not_called()
        mock_encode.assert_not_called()
        mock_send.assert_not_called()

def test_forgot_password_with_invalid_email(client):
    """
    Test the forgot password functionality with invalid email format.
    """
    url = reverse('forgot-password')
    res = client.post(url, data={'email': 'invalid_email'}, format='json')
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "validation_error"
    assert res.data['message'] == "Could not generate password reset link."
    assert res.data['errors']['email'] == ["Enter a valid email address."]

def test_forgot_password_with_blank_email(client):
    """
    Test the forgot password functionality with blank email value.
    """
    url = reverse('forgot-password')
    res = client.post(url, data={'email': ''}, format='json')
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "validation_error"
    assert res.data['message'] == "Could not generate password reset link."
    assert res.data['errors']['email'] == ["This field may not be blank."]

def test_forgot_password_with_missing_email(client):
    """
    Test the forgot password functionality with invalid email format.
    """
    url = reverse('forgot-password')
    res = client.post(url, data={}, format='json')
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "validation_error"
    assert res.data['message'] == "Could not generate password reset link."
    assert res.data['errors']['email'] == ["This field is required."]


# ==========================================================
# RESET PASSWORD TESTS
# ==========================================================

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
    assert response.data['message'] == "Password reset failed."
    assert response.data['errors']['link'][0] == "Invalid or expired password reset link."

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
    assert response.data['message'] == "Password reset failed."
    assert response.data['errors']['link'][0] == "Invalid or expired password reset link."

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
    assert response.data['message'] == "Password reset failed."
    assert response.data['errors']['link'][0] == "Invalid or expired password reset link."


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
    assert response.data['message'] == "Password reset failed."
    assert response.data['errors']['password'][0] == "Password and confirm password fields do not match."

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
    assert response.data['message'] == "Password reset failed."
    assert response.data['errors']['password'][0] == "Password and confirm password fields are required."


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
    assert response.data['message'] == "Password reset failed."
    assert response.data['errors']['password'][0] == "Password and confirm password fields are required."