from django.urls import reverse
from rest_framework import status

import uuid
import pytest


# ==========================================================
# TEST CASES FOR VERIFY PAYMENT VIEW
# ==========================================================
def test_payment_verified(client,
                          customer,
                          order_group_factory,
                          payment_factory):
    """
    Test that a verified payment returns the correct response.
    """
    group = order_group_factory(user=customer)
    payment = payment_factory(user=customer, group=group, verified=True)

    url = reverse('verify-payment', args=[payment.reference])
    client.force_authenticate(user=customer)
    res = client.get(url)

    assert res.status_code == status.HTTP_200_OK
    data = res.data
    assert data['status'] == "success"
    assert data['message'] == "Payment is verified."
    assert data['data']['reference'] == str(payment.reference)
    assert data['data']['verified'] is True
    assert "paid_at" in data['data']
    assert "amount" in data['data']


def test_payment_not_verified(client,
                              customer,
                              order_group_factory,
                              payment_factory):
    """
    Test that a not verified payment returns the correct response.
    """
    group = order_group_factory(user=customer)
    payment = payment_factory(user=customer, group=group, verified=False)

    url = reverse('verify-payment', args=[payment.reference])
    client.force_authenticate(user=customer)
    res = client.get(url)

    assert res.status_code == status.HTTP_200_OK
    data = res.data
    assert data['status'] == "success"
    assert data['message'] == "Payment not verified yet."
    assert data['data']['reference'] == str(payment.reference)
    assert data['data']['verified'] is False
    assert "paid_at" in data['data']
    assert "amount" in data['data']


def test_payment_verified_with_non_uuid_reference(client, customer):
    """
    Test that a payment verified with a non-uuid reference fails.
    """
    url = reverse('verify-payment', args=["non-uuid-reference"])
    client.force_authenticate(user=customer)
    res = client.get(url)

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    data = res.data
    assert data['status'] == "error"
    assert data['code'] == "invalid_uuid"
    assert data['message'] == "Invalid payment reference id."


def test_payment_verified_with_non_existent_reference(client, customer):
    """
    Test that a payment verified with a non-existent reference fails.
    """
    url = reverse('verify-payment', args=[uuid.uuid4()])
    client.force_authenticate(user=customer)
    res = client.get(url)

    assert res.status_code == status.HTTP_404_NOT_FOUND
    data = res.data
    assert data['status'] == "error"
    assert data['code'] == "not_found"
    assert data['message'] == "No payment matching the given reference found."


@pytest.mark.parametrize(
    "user_type",
    ["shopowner", "shop_staff"],
    ids=["shopowner", "shop_staff"]
)
def test_payment_verified_by_non_customer_user(
    client,
    all_users,
    user_type
):
    """
    Test that a payment verified by a non-customer user fails.
    """
    user = all_users[user_type]
    url = reverse('verify-payment', args=[uuid.uuid4()])
    client.force_authenticate(user=user)
    res = client.get(url)

    assert res.status_code == status.HTTP_403_FORBIDDEN
    data = res.data
    assert data['status'] == "error"
    assert data['code'] == "forbidden"
    expected_msg = "You do not have permission to perform this action."
    assert data['message'] == expected_msg


def test_payment_verified_by_different_user(client,
                                            customer,
                                            order_group_factory,
                                            payment_factory):
    """
    Test that a payment verified by a different user fails.
    """
    group = order_group_factory()
    payment = payment_factory(user=group.user, group=group, verified=True)

    url = reverse('verify-payment', args=[payment.reference])
    client.force_authenticate(user=customer)
    res = client.get(url)

    assert res.status_code == status.HTTP_404_NOT_FOUND
    data = res.data
    assert data['status'] == "error"
    assert data['code'] == "not_found"
    assert data['message'] == "No payment matching the given reference found."


def test_payment_verified_by_unauthenticated_user(client):
    """
    Test that a payment verified by an unauthenticated user fails.
    """
    url = reverse('verify-payment', args=[uuid.uuid4()])
    res = client.get(url)

    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    data = res.data
    assert data['status'] == "error"
    assert data['code'] == "unauthorized"
    expected_msg = "Authentication credentials were not provided."
    assert data['message'] == expected_msg

    client.cookies["access_token"] = "invalid_token"
    res = client.get(url)

    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    data = res.data
    assert data['status'] == "error"
    assert data['code'] == "unauthorized"
    assert data["message"] == "Token is invalid or expired"


def test_payment_verified_by_super_user(client,
                                        super_user,
                                        order_group_factory,
                                        payment_factory):
    """
    Test that a payment verified by a super user succeeds.
    """
    group = order_group_factory()
    payment = payment_factory(user=group.user, group=group, verified=True)

    url = reverse('verify-payment', args=[payment.reference])
    client.force_authenticate(user=super_user)
    res = client.get(url)

    assert res.status_code == status.HTTP_200_OK
    data = res.data
    assert data['status'] == "success"
    assert data['message'] == "Payment is verified."
    assert data['data']['reference'] == str(payment.reference)
    assert data['data']['verified'] is True
