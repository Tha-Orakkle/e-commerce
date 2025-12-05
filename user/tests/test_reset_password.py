from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.urls import reverse
from rest_framework import status


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


def test_reset_password(client, customer):
    """
    Test the reset password functionality.
    # """
    url = generate_reset_link(customer)
    res = client.post(url, data=PASSWORD_RESET_DATA, format='json')
    assert res.status_code == status.HTTP_200_OK
    assert res.data['status'] == "success"
    assert res.data['message'] == "Password has been reset successfully."

def test_reset_password_with_invalid_token(client, customer):
    """
    Test the reset password functionality with an invalid token.
    """
    uid = urlsafe_base64_encode(force_bytes(customer.email))
    token_generator = PasswordResetTokenGenerator()
    token = token_generator.make_token(customer) + 'invalid'
    url = f"{RESET_PASSWORD_URL}?uid={uid}&token={token}"
    res = client.post(url, data={
        'new_password': 'NewPassword123#',
        'confirm_password': 'NewPassword123#'
    }, format='json')
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "reset_failed"
    assert res.data['message'] == "Invalid or expired password reset link."

def test_reset_password_with_invalid_uid(client, customer):
    """
    Test the reset password functionality with an invalid uid.
    """
    token_generator = PasswordResetTokenGenerator()
    token = token_generator.make_token(customer)
    uid = urlsafe_base64_encode(force_bytes(customer.email)) + 'invalid'
    url = f"{RESET_PASSWORD_URL}?uid={uid}&token={token}"
    res = client.post(url, data=PASSWORD_RESET_DATA, format='json')
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "reset_failed"
    assert res.data['message'] == "Invalid or expired password reset link."

def test_reset_password_without_uid_and_token(client, customer):
    """
    Test the reset password functionality without uid and token.
    """
    token_generator = PasswordResetTokenGenerator()
    token = token_generator.make_token(customer)
    uid = urlsafe_base64_encode(force_bytes(customer.email)) + 'invalid'
    
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

def test_reset_password_with_mismatched_passwords(client, customer):
    """
    Test the reset password functionality with mismatched passwords.
    """
    url = generate_reset_link(customer)
    res = client.post(url, data={
        'new_password': 'NewPassword123#',
        'confirm_password': 'DifferentPassword123#'
    }, format='json')
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "validation_error"
    assert res.data['message'] == "Password reset failed."
    assert res.data['errors']['non_field_error'] == ["Passwords do not match."]

def test_reset_password_with_missing_passwords(client, customer):
    """
    Test the reset password functionality without passwords.
    """
    url = generate_reset_link(customer)

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

def test_reset_password_with_blank_passwords(client, customer):
    """
    Test the reset password functionality with blank passwords.
    """
    url = generate_reset_link(customer)
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

def test_reset_password_with_weak_password(client, customer):
    """
    Test the reset password functionality with a weak password.
    """
    url = generate_reset_link(customer)
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
