from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.urls import reverse
from rest_framework import status

import pytest

# ==========================================================
# RESET PASSWORD TESTS
# ==========================================================
RESET_PASSWORD_URL = reverse('reset-password-confirm')
PASSWORD_RESET_DATA = {
    'new_password': 'NewPassword123#',
    'confirm_password': 'NewPassword123#'
}

def generate_reset_link(user):
    """
    Helper function to generate a password reset link for a user.
    """
    token_generator = PasswordResetTokenGenerator()
    token = token_generator.make_token(user)
    encoded_email = urlsafe_base64_encode(force_bytes(user.email))
    link = f"{RESET_PASSWORD_URL}?uid={encoded_email}&token={token}"
    return link


@pytest.mark.parametrize(
    'user_type',
    ['shopowner', 'customer'],
    ids=['shopowner', 'customer']
)
def test_reset_password(client, all_users, user_type):
    """
    Test the reset password functionality.
    # """
    user = all_users[user_type]
    url = generate_reset_link(user)
    res = client.post(url, data=PASSWORD_RESET_DATA, format='json')
    assert res.status_code == status.HTTP_200_OK
    assert res.data['status'] == "success"
    assert res.data['message'] == "Password has been reset successfully."

@pytest.mark.parametrize(
    'user_type',
    ['shopowner', 'customer'],
    ids=['shopowner', 'customer']
)
def test_reset_password_with_invalid_token(client, all_users, user_type):
    """
    Test the reset password functionality with an invalid token.
    """
    user = all_users[user_type]
    uid = urlsafe_base64_encode(force_bytes(user.email))
    token_generator = PasswordResetTokenGenerator()
    token = token_generator.make_token(user) + 'invalid'
    url = f"{RESET_PASSWORD_URL}?uid={uid}&token={token}"
    res = client.post(url, data={
        'new_password': 'NewPassword123#',
        'confirm_password': 'NewPassword123#'
    }, format='json')
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "reset_failed"
    assert res.data['message'] == "Invalid or expired password reset link."

@pytest.mark.parametrize(
    'user_type',
    ['shopowner', 'customer'],
    ids=['shopowner', 'customer']
)
def test_reset_password_with_invalid_uid(client, all_users, user_type):
    """
    Test the reset password functionality with an invalid uid.
    """
    user = all_users[user_type]
    token_generator = PasswordResetTokenGenerator()
    token = token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.email)) + 'invalid'
    url = f"{RESET_PASSWORD_URL}?uid={uid}&token={token}"
    res = client.post(url, data=PASSWORD_RESET_DATA, format='json')
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "reset_failed"
    assert res.data['message'] == "Invalid or expired password reset link."

@pytest.mark.parametrize(
    'user_type',
    ['shopowner', 'customer'],
    ids=['shopowner', 'customer']
)
def test_reset_password_without_uid_and_token(client, all_users, user_type):
    """
    Test the reset password functionality without uid and token.
    """
    user = all_users[user_type]
    token_generator = PasswordResetTokenGenerator()
    token = token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.email)) + 'invalid'
    
    # Test missing uid (encoded email)
    res = client.post(
        RESET_PASSWORD_URL + f"?token={token}", data=PASSWORD_RESET_DATA, format='json')
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "reset_failed"
    assert res.data['message'] == "Invalid or expired password reset link."
    
    # Test missing token
    res = client.post(
        RESET_PASSWORD_URL + f"?uid={uid}", data=PASSWORD_RESET_DATA, format='json')
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "reset_failed"
    assert res.data['message'] == "Invalid or expired password reset link."
    
    # Test missing both uid and token
    res = client.post(
        RESET_PASSWORD_URL, data=PASSWORD_RESET_DATA, format='json')
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "reset_failed"
    assert res.data['message'] == "Invalid or expired password reset link."

@pytest.mark.parametrize(
    'user_type',
    ['shopowner', 'customer'],
    ids=['shopowner', 'customer']
)
def test_reset_password_with_mismatched_passwords(client, all_users, user_type):
    """
    Test the reset password functionality with mismatched passwords.
    """
    user = all_users[user_type]
    url = generate_reset_link(user)
    res = client.post(url, data={
        'new_password': 'NewPassword123#',
        'confirm_password': 'DifferentPassword123#'
    }, format='json')
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "validation_error"
    assert res.data['message'] == "Password reset failed."
    assert res.data['errors']['non_field_error'] == ["Passwords do not match."]

@pytest.mark.parametrize(
    'user_type',
    ['shopowner', 'customer'],
    ids=['shopowner', 'customer']
)
def test_reset_password_with_missing_passwords(client, all_users, user_type):
    """
    Test the reset password functionality without passwords.
    """
    user = all_users[user_type]
    url = generate_reset_link(user)

    # Test missing new password
    res = client.post(
        url, data={'confirm_password': 'NewPassword123#'},
        format='json')
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "validation_error"
    assert res.data['message'] == "Password reset failed."
    assert res.data['errors']['new_password'] == ["This field is required."]

    # Test missing confirm password
    res = client.post(
        url, data={'new_password': 'NewPassword123#'},
        format='json')
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "validation_error"
    assert res.data['message'] == "Password reset failed."
    assert res.data['errors']['confirm_password'] == ["This field is required."]

@pytest.mark.parametrize(
    'user_type',
    ['shopowner', 'customer'],
    ids=['shopowner', 'customer']
)
def test_reset_password_with_blank_passwords(client, all_users, user_type):
    """
    Test the reset password functionality with blank passwords.
    """
    user = all_users[user_type]
    url = generate_reset_link(user)
    res = client.post(url, data={
        'new_password': '',
        'confirm_password': ''
    }, format='json')
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "validation_error"
    assert res.data['message'] == "Password reset failed."
    assert res.data['errors']['new_password'] == ["This field may not be blank."]
    assert res.data['errors']['confirm_password'] == ["This field may not be blank."]

@pytest.mark.parametrize(
    'user_type',
    ['shopowner', 'customer'],
    ids=['shopowner', 'customer']
)
def test_reset_password_with_weak_password(client, all_users, user_type):
    """
    Test the reset password functionality with a weak password.
    """
    user = all_users[user_type]
    url = generate_reset_link(user)
    res = client.post(url, data={
        'new_password': 'weakpwd',
        'confirm_password': 'weakpwd'
    }, format='json')
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "validation_error"
    assert res.data['message'] == "Password reset failed."
    assert 'new_password' in res.data['errors']
    assert len(res.data['errors']['new_password']) > 0
