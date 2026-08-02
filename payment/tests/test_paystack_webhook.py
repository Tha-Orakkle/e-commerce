from django.conf import settings
from django.urls import reverse
from rest_framework import status
from rest_framework.settings import reload_api_settings

import hashlib
import hmac
import json


# =================================================
# HELPER FUNCTION
# =================================================
def paystack_signature(payload):
    """
    Helper function to generate a valid Paystack signature
    for testing.
    """
    body = json.dumps(payload).encode()

    signature = hmac.new(
        settings.PAYSTACK_SECRET_KEY.encode(),
        body,
        hashlib.sha512
    ).hexdigest()

    return body, signature


# =================================================
# TEST PAYSTACK WEBHOOK
# =================================================
PAYSTACK_WEBHOOK_URL = reverse("paystack-webhook")


def test_paystack_webhook_successful(client, mocker):
    """
    Test successful paystack webook call.
        - test response
        - that verify_paystack_payement task is called
    """
    mock_verify = mocker.patch(
        "payment.api.v1.routes.webhook_paystack.verify_paystack_payment.delay"
    )
    payload = {
        "event": "charge.success",
        "data": {}
    }
    settings.PAYSTACK_SECRET_KEY = "test_secret_key"
    reload_api_settings(setting="PAYSTACK_SECRET_KEY")

    body, signature = paystack_signature(payload)

    res = client.post(
        PAYSTACK_WEBHOOK_URL,
        data=body,
        content_type="application/json",
        HTTP_X_PAYSTACK_SIGNATURE=signature
    )

    assert res.status_code == status.HTTP_200_OK
    assert res.data["message"] == "Webhook processed successfully."
    mock_verify.assert_called_once_with(
        data=payload["data"]
    )


def test_paystack_webhook_with_invalid_signature(client, mocker):
    """
    Test that paystack webhook fails when signature is invalid.
    """
    mock_verify = mocker.patch(
        "payment.api.v1.routes.webhook_paystack.verify_paystack_payment.delay"
    )
    payload = {}
    settings.PAYSTACK_SECRET_KEY = "test_secret_key"
    reload_api_settings(setting="PAYSTACK_SECRET_KEY")

    body, _ = paystack_signature(payload)

    res = client.post(
        PAYSTACK_WEBHOOK_URL,
        data=body,
        content_type="application/json",
        HTTP_X_PAYSTACK_SIGNATURE="invalid_signature"
    )

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data["status"] == "error"
    assert res.data["code"] == "invalid_signature"
    assert res.data["message"] == "Invalid signature."
    mock_verify.assert_not_called()


def test_paystack_webhook_with_non_charge_success_event(client, mocker):
    """
    Test that paystack webhook only handles the charge.success event.
    """
    mock_verify = mocker.patch(
        "payment.api.v1.routes.webhook_paystack.verify_paystack_payment.delay"
    )
    payload = {
        "event": "transfer.success",
        "data": {}
    }
    settings.PAYSTACK_SECRET_KEY = "test_secret_key"
    reload_api_settings(setting="PAYSTACK_SECRET_KEY")

    body, signature = paystack_signature(payload)

    res = client.post(
        PAYSTACK_WEBHOOK_URL,
        data=body,
        content_type="application/json",
        HTTP_X_PAYSTACK_SIGNATURE=signature
    )

    assert res.status_code == status.HTTP_200_OK
    mock_verify.assert_not_called()
