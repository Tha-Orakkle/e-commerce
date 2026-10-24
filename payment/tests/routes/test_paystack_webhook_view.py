import hashlib
import hmac
import json

import pytest
from django.urls import reverse
from rest_framework import status

WEBHOOK_SECRET = "test_secret_key"
PAYSTACK_WEBHOOK_URL = reverse("paystack-webhook")
DELAY_PATH = (
    "payment.api.v1.routes.webhook_paystack.verify_payment_task.delay"
)


@pytest.fixture(autouse=True)
def paystack_secret(settings):
    """
    Use a known secret for the duration of each test; pytest-django
    restores the original settings afterwards.
    """
    settings.PAYSTACK = {**settings.PAYSTACK, "SECRET_KEY": WEBHOOK_SECRET}


def signed(payload):
    """
    Return the request body and a valid Paystack signature for it.
    """
    body = json.dumps(payload).encode()
    signature = hmac.new(
        WEBHOOK_SECRET.encode(),
        body,
        hashlib.sha512
    ).hexdigest()
    return body, signature


def post_webhook(client, body, signature):
    return client.post(
        PAYSTACK_WEBHOOK_URL,
        data=body,
        content_type="application/json",
        HTTP_X_PAYSTACK_SIGNATURE=signature
    )


# =================================================
# TEST PAYSTACK WEBHOOK
# =================================================
def test_paystack_webhook_successful(client, mocker):
    """
    Test that a signed charge.success event is accepted and verification
    is queued with the transaction reference.
    """
    mock_verify = mocker.patch(DELAY_PATH)
    payload = {
        "event": "charge.success",
        "data": {"reference": "ref-123"}
    }
    body, signature = signed(payload)

    res = post_webhook(client, body, signature)

    assert res.status_code == status.HTTP_200_OK
    assert res.data["message"] == "Accepted."
    mock_verify.assert_called_once_with(reference="ref-123")


def test_paystack_webhook_with_invalid_signature(client, mocker):
    """
    Test that a webhook with a bad signature is rejected.
    """
    mock_verify = mocker.patch(DELAY_PATH)
    body, _ = signed({"event": "charge.success", "data": {"reference": "x"}})

    res = post_webhook(client, body, "invalid_signature")

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data["status"] == "error"
    assert res.data["code"] == "invalid_signature"
    assert res.data["message"] == "Rejected."
    mock_verify.assert_not_called()


def test_paystack_webhook_with_non_charge_success_event(client, mocker):
    """
    Test that only the charge.success event queues verification.
    """
    mock_verify = mocker.patch(DELAY_PATH)
    payload = {
        "event": "transfer.success",
        "data": {"reference": "ref-123"}
    }
    body, signature = signed(payload)

    res = post_webhook(client, body, signature)

    assert res.status_code == status.HTTP_200_OK
    mock_verify.assert_not_called()
