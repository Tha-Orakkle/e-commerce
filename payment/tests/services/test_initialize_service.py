from decimal import Decimal

import pytest
from rest_framework import status

from order.models import PaymentMethod
from payment.domain.exceptions import PaymentNotFoundError
from payment.gateways.registry import PaymentGatewayRegistry
from payment.models import (
    Payment,
    PaymentProvider,
    PaymentTransaction,
    PaymentTransactionStatus,
)
from payment.services import InitializePaymentService


class FakeGateway:
    """
    In-memory gateway satisfying the PaymentGateway protocol.
    """
    AUTH_URL = "https://checkout.example.com/abc123"

    def __init__(self):
        self.initialize_calls = []

    def initialize_payment(self, *, reference, amount, currency, email,
                           metadata):
        self.initialize_calls.append({
            "reference": reference,
            "amount": amount,
            "currency": currency,
            "email": email,
            "metadata": metadata,
        })
        return {"authorization_url": self.AUTH_URL, "reference": reference}

    def verify_payment(self, *, reference):
        raise AssertionError("verify_payment should not be called here")


@pytest.fixture
def fake_gateway(monkeypatch):
    gateway = FakeGateway()
    monkeypatch.setitem(
        PaymentGatewayRegistry._gateways,
        PaymentProvider.PAYSTACK,
        gateway
    )
    return gateway


# ==========================================================
# MISSING PAYMENT RECORD
# ==========================================================
def test_initialize_service_without_payment_record_raises_clean_error(
    customer,
    order_group_factory
):
    """
    Test that an order group with no Payment row raises PaymentNotFoundError
    rather than leaking Payment.DoesNotExist.
    """
    group = order_group_factory(
        user=customer,
        payment_method=PaymentMethod.DIGITAL
    )
    service = InitializePaymentService(
        gateway_registry=PaymentGatewayRegistry
    )

    with pytest.raises(PaymentNotFoundError) as exc_info:
        service.initialize(order_group=group, provider="paystack")

    assert exc_info.value.code == "payment_not_found"
    assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert PaymentTransaction.objects.count() == 0


# ==========================================================
# HAPPY PATH WITH A PAYMENT CREATED THROUGH THE MANAGER
# ==========================================================
def test_initialize_service_with_existing_payment_creates_transaction(
    customer,
    order_group_factory,
    fake_gateway
):
    """
    Test that a payment created through the manager can be initialized:
    a pending transaction is created, becomes the active one, and the
    gateway receives the kobo amount and currency.
    """
    group = order_group_factory(
        user=customer,
        payment_method=PaymentMethod.DIGITAL,
        total_amount=Decimal("1500.00")
    )
    payment = Payment.objects.create_for_order_group(group)
    service = InitializePaymentService(
        gateway_registry=PaymentGatewayRegistry
    )

    assert payment.active_transaction is None

    result = service.initialize(order_group=group, provider="paystack")

    payment.refresh_from_db()
    tx = payment.active_transaction
    assert tx is not None
    assert tx.status == PaymentTransactionStatus.PENDING
    assert tx.amount == 150000
    assert tx.currency == "NGN"
    assert tx.customer_email == customer.email
    assert result.authorization_url == FakeGateway.AUTH_URL
    assert result.reference == str(tx.reference)

    call = fake_gateway.initialize_calls[0]
    assert call["amount"] == 150000
    assert call["currency"] == "NGN"
    assert call["metadata"] == {
        "order_group_id": str(group.id),
        "payment_id": str(payment.id),
    }
