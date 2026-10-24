import uuid
from decimal import Decimal

import pytest
from django.urls import reverse
from rest_framework import status

from order.models import OrderGroupStatus, PaymentMethod
from payment.domain.exceptions import (
    PaymentGatewayConnectionError,
    PaymentGatewayTimeoutError,
)
from payment.models import Payment, PaymentStatus

PAYMENT_PAYLOAD = {"provider": "paystack"}


def initialize_url(group_id):
    return reverse("initialize-payment", args=[group_id])


@pytest.fixture
def digital_group(customer, order_group_factory):
    """
    A pending DIGITAL order group of NGN 1,000.00 owned by the customer,
    with the payment record checkout would have created.
    """
    group = order_group_factory(
        user=customer,
        payment_method=PaymentMethod.DIGITAL,
        total_amount=Decimal("1000.00")
    )
    Payment.objects.create_for_order_group(group)
    return group


def test_initialize_payment_view_without_payment_record_returns_error(
    client,
    customer,
    order_group_factory
):
    """
    Test that the endpoint answers with the standard error envelope
    and a stable error code when the Payment row is missing.
    """
    group = order_group_factory(
        user=customer,
        payment_method=PaymentMethod.DIGITAL
    )

    client.force_authenticate(user=customer)
    url = reverse("initialize-payment", args=[group.id])
    res = client.post(url, data={"provider": "paystack"}, format="json")

    assert res.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert res.data["status"] == "error"
    assert res.data["code"] == "payment_not_found"
    assert res.data["message"] == (
        "No payment record exists for this order group."
    )


# ==========================================================
# REQUEST VALIDATION
# ==========================================================
@pytest.mark.parametrize(
    "payload",
    [
        {"provider": "invalid_provider"},
        {"provider": "paypal"},
        {"provider": 123},
        {"provider": ""},
        {},
    ],
    ids=["invalid", "paypal", "integer", "blank", "missing"]
)
def test_initialize_payment_with_unsupported_provider(
    client, customer, digital_group, payload
):
    """
    Test that an unsupported or missing provider is rejected.
    """
    client.force_authenticate(user=customer)
    res = client.post(
        initialize_url(digital_group.id), data=payload, format="json"
    )

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data["status"] == "error"
    assert res.data["code"] == "unsupported_payment_provider"


def test_initialize_payment_with_provider_that_has_no_gateway(
    client, customer, digital_group
):
    """
    Test that a known provider with no configured gateway is rejected.
    """
    client.force_authenticate(user=customer)
    res = client.post(
        initialize_url(digital_group.id),
        data={"provider": "stripe"},
        format="json"
    )

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data["code"] == "unsupported_payment_provider"


def test_initialize_payment_with_invalid_order_group_id(client, customer):
    """
    Test that a malformed order group id fails.
    """
    client.force_authenticate(user=customer)
    res = client.post(
        initialize_url("invalid-uuid"), data=PAYMENT_PAYLOAD, format="json"
    )

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data["code"] == "invalid_uuid"
    assert res.data["message"] == "Invalid order group id."


def test_initialize_payment_with_non_existent_order_group_id(
    client, customer
):
    """
    Test that an unknown order group returns 404.
    """
    client.force_authenticate(user=customer)
    res = client.post(
        initialize_url(uuid.uuid4()), data=PAYMENT_PAYLOAD, format="json"
    )

    assert res.status_code == status.HTTP_404_NOT_FOUND
    assert res.data["code"] == "not_found"
    assert res.data["message"] == (
        "No order group matching the given ID found."
    )


def test_initialize_payment_for_cash_order_group(
    client, customer, order_group_factory
):
    """
    Test that only DIGITAL order groups can be initialized.
    """
    group = order_group_factory(
        user=customer, payment_method=PaymentMethod.CASH
    )

    client.force_authenticate(user=customer)
    res = client.post(
        initialize_url(group.id), data=PAYMENT_PAYLOAD, format="json"
    )

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data["code"] == "invalid_payment_method"
    assert res.data["message"] == (
        "Payment can only be initialized for order groups with "
        "DIGITAL payment method."
    )


@pytest.mark.parametrize(
    "group_status",
    [s for s, _ in OrderGroupStatus.choices if s != OrderGroupStatus.PENDING]
)
def test_initialize_payment_for_non_pending_order_group(
    client, customer, order_group_factory, group_status
):
    """
    Test that only pending order groups can be paid for.
    """
    group = order_group_factory(
        user=customer,
        payment_method=PaymentMethod.DIGITAL,
        status=group_status
    )

    client.force_authenticate(user=customer)
    res = client.post(
        initialize_url(group.id), data=PAYMENT_PAYLOAD, format="json"
    )

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data["code"] == "invalid_order_group_status"
    assert res.data["message"] == "Only pending order groups can be paid for."


def test_initialize_payment_for_already_paid_order_group(
    client, customer, digital_group
):
    """
    Test that a verified payment cannot be initialized again.
    """
    Payment.objects.filter(order_group=digital_group).update(
        status=PaymentStatus.VERIFIED
    )

    client.force_authenticate(user=customer)
    res = client.post(
        initialize_url(digital_group.id), data=PAYMENT_PAYLOAD, format="json"
    )

    assert res.status_code == status.HTTP_409_CONFLICT
    assert res.data["code"] == "duplicate_transaction"
    assert res.data["message"] == "Payment has already been verified."


# ==========================================================
# SUCCESSFUL INITIALIZATION
# ==========================================================
def test_initialize_payment_with_paystack(
    client, customer, digital_group, stub_gateway
):
    """
    Test that initialization returns the provider's authorization url
    and sends the payment amount in kobo.
    """
    client.force_authenticate(user=customer)
    res = client.post(
        initialize_url(digital_group.id), data=PAYMENT_PAYLOAD, format="json"
    )

    assert res.status_code == status.HTTP_200_OK
    assert res.data["status"] == "success"
    assert res.data["message"] == "Payment initialized successfully."
    data = res.data["data"]
    assert data["authorization_url"] == (
        stub_gateway.initialize_response["authorization_url"]
    )
    assert data["provider"] == "paystack"
    assert data["reference"]
    call = stub_gateway.initialize_calls[0]
    assert call["amount"] == 100000
    assert call["currency"] == "NGN"
    assert call["email"] == customer.email


@pytest.mark.parametrize(
    "provider",
    ["PAYSTACK", "Paystack", "paystack", "PAyStacK"]
)
def test_initialize_payment_provider_is_case_insensitive(
    client, customer, digital_group, stub_gateway, provider
):
    """
    Test that the provider name is matched regardless of case.
    """
    client.force_authenticate(user=customer)
    res = client.post(
        initialize_url(digital_group.id),
        data={"provider": provider},
        format="json"
    )

    assert res.status_code == status.HTTP_200_OK


def test_initialize_payment_again_reuses_pending_transaction(
    client, customer, digital_group, stub_gateway
):
    """
    Test that initializing again while the first attempt is still
    pending returns the same reference without a second provider
    initialization.
    """
    client.force_authenticate(user=customer)
    url = initialize_url(digital_group.id)

    first = client.post(url, data=PAYMENT_PAYLOAD, format="json")
    reference = first.data["data"]["reference"]
    stub_gateway.verify_response = {
        "status": "pending",
        "reference": reference
    }
    second = client.post(url, data=PAYMENT_PAYLOAD, format="json")

    assert second.status_code == status.HTTP_200_OK
    assert second.data["data"]["reference"] == reference
    assert len(stub_gateway.initialize_calls) == 1


# ==========================================================
# GATEWAY FAILURES
# ==========================================================
def test_initialize_payment_when_gateway_times_out(
    client, customer, digital_group, stub_gateway
):
    """
    Test that a gateway timeout is reported as 504.
    """
    stub_gateway.initialize_error = PaymentGatewayTimeoutError()

    client.force_authenticate(user=customer)
    res = client.post(
        initialize_url(digital_group.id), data=PAYMENT_PAYLOAD, format="json"
    )

    assert res.status_code == status.HTTP_504_GATEWAY_TIMEOUT
    assert res.data["status"] == "error"
    assert res.data["code"] == "payment_gateway_timeout"


def test_initialize_payment_when_gateway_is_unreachable(
    client, customer, digital_group, stub_gateway
):
    """
    Test that a gateway connection failure is reported as 503.
    """
    stub_gateway.initialize_error = PaymentGatewayConnectionError()

    client.force_authenticate(user=customer)
    res = client.post(
        initialize_url(digital_group.id), data=PAYMENT_PAYLOAD, format="json"
    )

    assert res.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert res.data["code"] == "payment_gateway_connection_error"


# ==========================================================
# AUTHORIZATION
# ==========================================================
@pytest.mark.parametrize(
    "user_type",
    ["shopowner", "shop_staff"],
    ids=["shopowner", "shop_staff"]
)
def test_initialize_payment_by_non_customer_user(
    client, all_users, order_group_factory, user_type
):
    """
    Test that non-customers are forbidden.
    """
    group = order_group_factory(payment_method=PaymentMethod.DIGITAL)

    client.force_authenticate(user=all_users[user_type])
    res = client.post(
        initialize_url(group.id), data=PAYMENT_PAYLOAD, format="json"
    )

    assert res.status_code == status.HTTP_403_FORBIDDEN
    assert res.data["code"] == "forbidden"
    assert res.data["message"] == (
        "You do not have permission to perform this action."
    )


def test_initialize_payment_by_different_user(
    client, customer, order_group_factory
):
    """
    Test that another customer's order group looks like it does not exist.
    """
    group = order_group_factory(payment_method=PaymentMethod.DIGITAL)

    client.force_authenticate(user=customer)
    res = client.post(
        initialize_url(group.id), data=PAYMENT_PAYLOAD, format="json"
    )

    assert res.status_code == status.HTTP_404_NOT_FOUND
    assert res.data["code"] == "not_found"


def test_initialize_payment_by_superuser(
    client, super_user, order_group_factory, stub_gateway
):
    """
    Test that a super user can initialize any order group's payment.
    """
    group = order_group_factory(
        payment_method=PaymentMethod.DIGITAL,
        total_amount=Decimal("500.00")
    )
    Payment.objects.create_for_order_group(group)

    client.force_authenticate(user=super_user)
    res = client.post(
        initialize_url(group.id), data=PAYMENT_PAYLOAD, format="json"
    )

    assert res.status_code == status.HTTP_200_OK
    assert res.data["status"] == "success"


def test_initialize_payment_by_unauthenticated_user(client):
    """
    Test that unauthenticated requests are rejected, with and without
    an invalid token.
    """
    url = initialize_url(uuid.uuid4())
    res = client.post(url, data=PAYMENT_PAYLOAD, format="json")

    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.data["code"] == "unauthorized"
    assert res.data["message"] == (
        "Authentication credentials were not provided."
    )

    client.cookies["access_token"] = "invalid_token"
    res = client.post(url, data=PAYMENT_PAYLOAD, format="json")

    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.data["message"] == "Token is invalid or expired"
