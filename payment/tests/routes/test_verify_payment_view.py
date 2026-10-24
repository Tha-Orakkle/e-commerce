import uuid
from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils.timezone import now
from rest_framework import status

from payment.models import PaymentStatus, PaymentTransactionStatus


def verify_url(reference):
    return reverse('verify-payment', args=[reference])


@pytest.fixture
def verified_transaction(customer, order_group_factory, payment_factory,
                         payment_transaction_factory):
    """
    A successful transaction on a verified payment of NGN 2,500.00.
    """
    group = order_group_factory(
        user=customer, total_amount=Decimal("2500.00")
    )
    payment = payment_factory(
        group, status=PaymentStatus.VERIFIED, paid_at=now()
    )
    return payment_transaction_factory(
        payment,
        status=PaymentTransactionStatus.SUCCESS,
        paid_at=payment.paid_at
    )


# ==========================================================
# TEST CASES FOR VERIFY PAYMENT VIEW
# ==========================================================
def test_payment_verified(client, customer, verified_transaction):
    """
    Test that a verified payment returns the correct response.
    """
    client.force_authenticate(user=customer)
    res = client.get(verify_url(verified_transaction.reference))

    assert res.status_code == status.HTTP_200_OK
    assert res.data['status'] == "success"
    assert res.data['message'] == "Payment is verified."
    data = res.data['data']
    assert data['reference'] == str(verified_transaction.reference)
    assert data['status'] == PaymentTransactionStatus.SUCCESS
    assert data['payment_status'] == PaymentStatus.VERIFIED
    assert data['verified'] is True
    assert data['amount'] == 2500.0
    assert data['currency'] == "NGN"
    assert data['paid_at'] is not None


def test_payment_not_verified(client, customer, order_group_factory,
                              payment_factory, payment_transaction_factory):
    """
    Test that a pending payment returns the correct response.
    """
    group = order_group_factory(
        user=customer, total_amount=Decimal("1000.00")
    )
    payment = payment_factory(group)
    tx = payment_transaction_factory(payment, active=True)

    client.force_authenticate(user=customer)
    res = client.get(verify_url(tx.reference))

    assert res.status_code == status.HTTP_200_OK
    assert res.data['status'] == "success"
    assert res.data['message'] == "Payment not verified yet."
    data = res.data['data']
    assert data['reference'] == str(tx.reference)
    assert data['status'] == PaymentTransactionStatus.PENDING
    assert data['payment_status'] == PaymentStatus.PENDING
    assert data['verified'] is False
    assert data['amount'] == 1000.0
    assert data['paid_at'] is None


def test_failed_transaction_reports_its_own_status(
    client, customer, order_group_factory, payment_factory,
    payment_transaction_factory
):
    """
    Test that a failed attempt shows FAILED while the payment is
    still unpaid.
    """
    group = order_group_factory(user=customer)
    payment = payment_factory(group)
    tx = payment_transaction_factory(
        payment, status=PaymentTransactionStatus.FAILED
    )

    client.force_authenticate(user=customer)
    res = client.get(verify_url(tx.reference))

    assert res.status_code == status.HTTP_200_OK
    assert res.data['message'] == "Payment not verified yet."
    assert res.data['data']['status'] == PaymentTransactionStatus.FAILED
    assert res.data['data']['payment_status'] == PaymentStatus.PENDING
    assert res.data['data']['verified'] is False


def test_older_transaction_reference_can_be_looked_up(
    client, customer, order_group_factory, payment_factory,
    payment_transaction_factory
):
    """
    Test that the reference of a superseded attempt still resolves and
    reports that attempt's own status.
    """
    group = order_group_factory(user=customer)
    payment = payment_factory(group)
    old_tx = payment_transaction_factory(
        payment, status=PaymentTransactionStatus.EXPIRED
    )
    payment_transaction_factory(payment, active=True)

    client.force_authenticate(user=customer)
    res = client.get(verify_url(old_tx.reference))

    assert res.status_code == status.HTTP_200_OK
    assert res.data['data']['reference'] == str(old_tx.reference)
    assert res.data['data']['status'] == PaymentTransactionStatus.EXPIRED


def test_payment_verified_with_non_uuid_reference(client, customer):
    """
    Test that a non-uuid reference fails.
    """
    client.force_authenticate(user=customer)
    res = client.get(verify_url("non-uuid-reference"))

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "invalid_uuid"
    assert res.data['message'] == "Invalid payment transaction reference id."


def test_payment_verified_with_non_existent_reference(client, customer):
    """
    Test that an unknown reference returns 404.
    """
    client.force_authenticate(user=customer)
    res = client.get(verify_url(uuid.uuid4()))

    assert res.status_code == status.HTTP_404_NOT_FOUND
    assert res.data['status'] == "error"
    assert res.data['code'] == "not_found"
    assert res.data['message'] == (
        "No payment transaction matching the given reference found."
    )


@pytest.mark.parametrize(
    "user_type",
    ["shopowner", "shop_staff"],
    ids=["shopowner", "shop_staff"]
)
def test_payment_verified_by_non_customer_user(client, all_users, user_type):
    """
    Test that a non-customer user is forbidden.
    """
    client.force_authenticate(user=all_users[user_type])
    res = client.get(verify_url(uuid.uuid4()))

    assert res.status_code == status.HTTP_403_FORBIDDEN
    assert res.data['status'] == "error"
    assert res.data['code'] == "forbidden"
    assert res.data['message'] == (
        "You do not have permission to perform this action."
    )


def test_payment_verified_by_different_user(
    client, customer, order_group_factory, payment_factory,
    payment_transaction_factory
):
    """
    Test that another customer's transaction looks like it does not exist.
    """
    group = order_group_factory()
    payment = payment_factory(group, status=PaymentStatus.VERIFIED)
    tx = payment_transaction_factory(
        payment, status=PaymentTransactionStatus.SUCCESS
    )

    client.force_authenticate(user=customer)
    res = client.get(verify_url(tx.reference))

    assert res.status_code == status.HTTP_404_NOT_FOUND
    assert res.data['code'] == "not_found"
    assert res.data['message'] == (
        "No payment transaction matching the given reference found."
    )


def test_payment_verified_by_unauthenticated_user(client):
    """
    Test that unauthenticated requests are rejected.
    """
    url = verify_url(uuid.uuid4())
    res = client.get(url)

    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.data['status'] == "error"
    assert res.data['code'] == "unauthorized"
    assert res.data['message'] == (
        "Authentication credentials were not provided."
    )

    client.cookies["access_token"] = "invalid_token"
    res = client.get(url)

    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.data['code'] == "unauthorized"
    assert res.data["message"] == "Token is invalid or expired"


def test_payment_verified_by_super_user(client, super_user,
                                        order_group_factory, payment_factory,
                                        payment_transaction_factory):
    """
    Test that a super user can see any customer's transaction.
    """
    group = order_group_factory()
    payment = payment_factory(group, status=PaymentStatus.VERIFIED)
    tx = payment_transaction_factory(
        payment, status=PaymentTransactionStatus.SUCCESS
    )

    client.force_authenticate(user=super_user)
    res = client.get(verify_url(tx.reference))

    assert res.status_code == status.HTTP_200_OK
    assert res.data['message'] == "Payment is verified."
    assert res.data['data']['reference'] == str(tx.reference)
    assert res.data['data']['verified'] is True
