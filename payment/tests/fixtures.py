from datetime import timedelta

import pytest
from django.utils.timezone import now

from payment.gateways.registry import PaymentGatewayRegistry
from payment.models import (
    Payment,
    PaymentProvider,
    PaymentTransaction,
)


@pytest.fixture
def payment_factory():
    """
    Factory to create payment instances for an order group.
    The amount defaults to the group total in kobo.
    """
    def create_payment(group, **kwargs):
        kwargs.setdefault("amount", int(group.total_amount * 100))
        kwargs.setdefault("currency", "NGN")
        return Payment.objects.create(order_group=group, **kwargs)

    return create_payment


@pytest.fixture
def payment_transaction_factory():
    """
    Factory to create payment transactions for a payment.
    Pass active=True to make it the payment's active transaction.
    """
    def create_transaction(payment, active=False, **kwargs):
        kwargs.setdefault("provider", PaymentProvider.PAYSTACK)
        kwargs.setdefault("customer_email", payment.order_group.user.email)
        kwargs.setdefault("currency", payment.currency)
        kwargs.setdefault("amount", payment.amount)
        kwargs.setdefault("expires_at", now() + timedelta(minutes=30))
        tx = PaymentTransaction.objects.create(payment=payment, **kwargs)
        if active:
            payment.active_transaction = tx
            payment.save(update_fields=["active_transaction", "updated_at"])
        return tx

    return create_transaction


class StubGateway:
    """
    Configurable in-memory gateway satisfying the PaymentGateway protocol.
    Set the *_response or *_error attributes to drive each scenario.
    """

    def __init__(self):
        self.initialize_calls = []
        self.verify_calls = []
        self.initialize_response = {
            "authorization_url": "https://checkout.example.com/stub"
        }
        self.initialize_error = None
        self.verify_response = None
        self.verify_error = None

    def initialize_payment(self, *, reference, amount, currency, email,
                           metadata):
        self.initialize_calls.append({
            "reference": reference,
            "amount": amount,
            "currency": currency,
            "email": email,
            "metadata": metadata,
        })
        if self.initialize_error:
            raise self.initialize_error
        return {**self.initialize_response, "reference": reference}

    def verify_payment(self, *, reference):
        self.verify_calls.append(reference)
        if self.verify_error:
            raise self.verify_error
        return self.verify_response


@pytest.fixture
def stub_gateway(monkeypatch):
    """
    Register a StubGateway as the Paystack gateway for the test.
    """
    gateway = StubGateway()
    monkeypatch.setitem(
        PaymentGatewayRegistry._gateways,
        PaymentProvider.PAYSTACK,
        gateway
    )
    return gateway
