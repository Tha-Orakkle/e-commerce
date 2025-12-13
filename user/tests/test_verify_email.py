from django.urls import reverse
from freezegun import freeze_time
from rest_framework import status

import pytest

from user.utils.email_verification import generate_email_verification_token

# test that email verified successfully
# test that token is not provided in the email verification
# test that the token has expired
# test email already verified

VERIFY_URL = reverse('verify-email')

def test_verify_email_with_valid_token(client, customer):
    """
    Test verify a user's email using valid token.
    """
    user = customer
    token = generate_email_verification_token(user.id)
    
    url = f"{VERIFY_URL}?token={token}"
    res = client.get(url)
    
    user.refresh_from_db()
    
    assert res.status_code == status.HTTP_200_OK
    assert res.data['message'] == "Email verified successfully."
    assert user.is_verified is True
    
    
def test_verify_email_with_invalid_token(client):
    """
    Test verify email endpoint with an invalid token.
    """
    url = f"{VERIFY_URL}?token=invalid_token"
    res = client.get(url)

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['code'] == "verification_error"
    assert res.data['message'] == "Invalid or expired token."

@freeze_time("2025-01-01 12:00:00")
def test_verify_email_with_expired_token(client, customer):

    """
    Test verify email endpoint with an expired token. 
    """
    user = customer
    token = generate_email_verification_token(user.id)
    
    with freeze_time("2025-01-01 15:00:00"):
        url = f"{VERIFY_URL}?token={token}"
        res = client.get(url)

    user.refresh_from_db()

    assert res.status_code  == status.HTTP_400_BAD_REQUEST
    assert res.data['code'] == "verification_error"
    assert res.data['message'] == "Invalid or expired token."
    assert user.is_verified is False
    
    
def test_verify_email_with_already_verified_email(client, customer):
    """
    Test verify email endpoint on an already verified email.
    """
    customer.is_verified = True
    customer.save(update_fields=['is_verified'])
    token = generate_email_verification_token(customer.id)
    
    url = f"{VERIFY_URL}?token={token}"
    res = client.get(url)

    assert res.status_code == status.HTTP_200_OK
    assert res.data['message'] == "Email already verified."
    