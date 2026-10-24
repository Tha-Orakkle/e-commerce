from decimal import Decimal

import pytest

from order.models import OrderGroupStatus
from payment.domain.exceptions import (
    PaymentGatewayTimeoutError,
    PaymentProviderStatusError,
    PaymentReferenceNotFoundError,
    PaymentTransactionStateChangedError,
)
from payment.gateways.registry import PaymentGatewayRegistry
from payment.models import PaymentStatus, PaymentTransactionStatus
from payment.services.verification import PaymentVerificationService

PAID_AT = "2026-10-17T10:00:00.000Z"


def provider_data(tx, **overrides):
    """
    Build a Paystack-style verification payload matching a transaction.
    """
    data = {
        "status": "success",
        "reference": str(tx.reference),
        "amount": tx.amount,
        "currency": tx.currency,
        "channel": "card",
        "paid_at": PAID_AT,
        "gateway_response": "Successful",
        "customer": {"email": tx.customer_email},
        "metadata": {
            "payment_id": str(tx.payment_id),
            "order_group_id": str(tx.payment.order_group_id),
        },
    }
    data.update(overrides)
    return data


@pytest.fixture
def service():
    return PaymentVerificationService(gateway_registry=PaymentGatewayRegistry)


@pytest.fixture
def setup(customer, order_group_factory, order_factory, payment_factory,
          payment_transaction_factory, stub_gateway):
    """
    A pending digital order group with two orders, its payment, and an
    active pending transaction. Returns (group, payment, tx, gateway).
    """
    group = order_group_factory(
        user=customer,
        payment_method="DIGITAL",
        total_amount=Decimal("1500.00")
    )
    order_factory(group=group)
    order_factory(group=group)
    payment = payment_factory(group)
    tx = payment_transaction_factory(payment, active=True)
    return group, payment, tx, stub_gateway


# ==========================================================
# SUCCESS
# ==========================================================
def test_verify_success_marks_everything_paid(service, setup):
    """
    Test that a matching successful payment completes the transaction,
    verifies the payment and marks every order paid.
    """
    group, payment, tx, gateway = setup
    gateway.verify_response = provider_data(tx)

    result = service.verify(transaction_id=tx.id)

    assert result.is_success
    tx.refresh_from_db()
    payment.refresh_from_db()
    assert tx.status == PaymentTransactionStatus.SUCCESS
    assert tx.channel == "card"
    assert tx.verified_at is not None
    assert tx.paid_at is not None
    assert payment.status == PaymentStatus.VERIFIED
    assert payment.active_transaction is None
    assert payment.paid_at is not None
    assert payment.refund_requested is False
    assert all(order.is_paid for order in group.orders.all())
    assert all(order.paid_at is not None for order in group.orders.all())


def test_verify_is_idempotent_for_successful_transaction(service, setup):
    """
    Test that verifying an already successful transaction does not call
    the provider again.
    """
    _, _, tx, gateway = setup
    gateway.verify_response = provider_data(tx)

    service.verify(transaction_id=tx.id)
    result = service.verify(transaction_id=tx.id)

    assert result.is_success
    assert len(gateway.verify_calls) == 1


def test_verify_success_on_cancelled_group_requests_refund(service, setup):
    """
    Test that a payment landing after the group was cancelled is
    recorded, a refund is requested, and the cancelled orders are not
    marked paid.
    """
    group, payment, tx, gateway = setup
    group.status = OrderGroupStatus.CANCELLED
    group.save(update_fields=["status"])
    gateway.verify_response = provider_data(tx)

    result = service.verify(transaction_id=tx.id)

    assert result.is_success
    payment.refresh_from_db()
    assert payment.status == PaymentStatus.VERIFIED
    assert payment.refund_requested is True
    assert not any(order.is_paid for order in group.orders.all())


def test_verify_success_with_stale_active_transaction_raises(
    service, setup, payment_transaction_factory
):
    """
    Test that success on a transaction that is no longer the payment's
    active one is rejected and nothing is marked paid.
    """
    group, payment, tx, gateway = setup
    payment_transaction_factory(payment, active=True)
    gateway.verify_response = provider_data(tx)

    with pytest.raises(PaymentTransactionStateChangedError):
        service.verify(transaction_id=tx.id)

    tx.refresh_from_db()
    payment.refresh_from_db()
    assert tx.status == PaymentTransactionStatus.PENDING
    assert payment.status == PaymentStatus.PENDING
    assert not any(order.is_paid for order in group.orders.all())


# ==========================================================
# INCONSISTENT PROVIDER DATA
# ==========================================================
@pytest.mark.parametrize(
    "field, override",
    [
        ("amount", {"amount": 1}),
        ("currency", {"currency": "USD"}),
        ("customer", {"customer": {"email": "someone@else.com"}}),
        ("metadata", {"metadata": {"payment_id": "x", "order_group_id": "y"}}),
        ("reference", {"reference": "not-the-reference"}),
    ],
    ids=["amount", "currency", "customer", "metadata", "reference"]
)
def test_verify_marks_inconsistent_data(service, setup, field, override):
    """
    Test that any mismatch between provider data and our records marks
    the transaction INCONSISTENT and leaves orders unpaid.
    """
    group, payment, tx, gateway = setup
    gateway.verify_response = provider_data(tx, **override)

    result = service.verify(transaction_id=tx.id)

    assert result.is_inconsistent
    tx.refresh_from_db()
    payment.refresh_from_db()
    assert tx.status == PaymentTransactionStatus.INCONSISTENT
    assert tx.verification_failure_reason
    assert payment.status == PaymentStatus.PENDING
    assert not any(order.is_paid for order in group.orders.all())


# ==========================================================
# OTHER PROVIDER STATUSES
# ==========================================================
@pytest.mark.parametrize(
    "provider_status",
    ["pending", "processing", "ongoing", "queued"]
)
def test_verify_pending_statuses_leave_transaction_pending(
    service, setup, provider_status
):
    """
    Test that in-flight provider statuses keep the transaction pending.
    """
    _, _, tx, gateway = setup
    gateway.verify_response = provider_data(tx, status=provider_status)

    result = service.verify(transaction_id=tx.id)

    assert result.is_pending
    tx.refresh_from_db()
    assert tx.status == PaymentTransactionStatus.PENDING
    assert tx.provider_status == provider_status


@pytest.mark.parametrize("provider_status", ["failed", "abandoned"])
def test_verify_failed_statuses_mark_transaction_failed(
    service, setup, provider_status
):
    """
    Test that failed or abandoned payments mark the transaction FAILED
    and record the provider's reason.
    """
    group, payment, tx, gateway = setup
    gateway.verify_response = provider_data(
        tx, status=provider_status, gateway_response="Insufficient Funds"
    )

    result = service.verify(transaction_id=tx.id)

    assert result.is_failed
    tx.refresh_from_db()
    payment.refresh_from_db()
    assert tx.status == PaymentTransactionStatus.FAILED
    assert tx.verification_failure_reason == "Insufficient Funds"
    assert payment.status == PaymentStatus.PENDING
    assert not any(order.is_paid for order in group.orders.all())


def test_verify_reversed_marks_transaction_reversed(service, setup):
    """
    Test that a reversed provider status marks the transaction REVERSED.
    """
    _, _, tx, gateway = setup
    gateway.verify_response = provider_data(tx, status="reversed")

    result = service.verify(transaction_id=tx.id)

    assert result.is_reversed
    tx.refresh_from_db()
    assert tx.status == PaymentTransactionStatus.REVERSED


def test_handle_reversed_keeps_an_already_successful_transaction(
    service, setup
):
    """
    Regression: a SUCCESS transaction must be returned untouched rather
    than overwritten as REVERSED.
    """
    _, _, tx, _ = setup
    tx.status = PaymentTransactionStatus.SUCCESS
    tx.save(update_fields=["status"])

    result = service._handle_reversed(
        transaction_id=str(tx.id),
        provider_data={"status": "reversed"}
    )

    assert result.is_success
    tx.refresh_from_db()
    assert tx.status == PaymentTransactionStatus.SUCCESS


def test_verify_unrecognised_status_raises(service, setup):
    """
    Test that an unknown provider status is an error, not a silent pass.
    """
    _, _, tx, gateway = setup
    gateway.verify_response = provider_data(tx, status="mystery")

    with pytest.raises(PaymentProviderStatusError):
        service.verify(transaction_id=tx.id)


# ==========================================================
# GATEWAY ERRORS
# ==========================================================
def test_verify_reference_not_found_marks_initialization_failed(
    service, setup
):
    """
    Regression: an unknown reference must record INITIALIZATION_FAILED
    with a reason instead of crashing.
    """
    _, _, tx, gateway = setup
    gateway.verify_error = PaymentReferenceNotFoundError("not found")

    result = service.verify(transaction_id=tx.id)

    assert result.is_reference_not_found
    tx.refresh_from_db()
    assert tx.status == PaymentTransactionStatus.INITIALIZATION_FAILED
    assert tx.verification_failure_reason == (
        "The payment provider could not locate the transaction reference"
    )


def test_verify_propagates_gateway_errors(service, setup):
    """
    Test that retryable gateway errors reach the caller so Celery can
    retry, leaving the transaction untouched.
    """
    _, _, tx, gateway = setup
    gateway.verify_error = PaymentGatewayTimeoutError()

    with pytest.raises(PaymentGatewayTimeoutError):
        service.verify(transaction_id=tx.id)

    tx.refresh_from_db()
    assert tx.status == PaymentTransactionStatus.PENDING
