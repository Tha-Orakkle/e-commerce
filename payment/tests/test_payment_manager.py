from decimal import Decimal

import pytest
from django.db import IntegrityError, transaction

from payment.models import Payment, PaymentStatus


# ==========================================================
# TEST CASES FOR Payment.objects.create_for_order_group
# ==========================================================
@pytest.mark.parametrize(
    "total, expected_kobo",
    [
        (Decimal("3000.00"), 300000),
        (Decimal("1234.56"), 123456),
        (Decimal("0.07"), 7),
    ],
    ids=["whole_naira", "naira_and_kobo", "sub_naira"]
)
def test_create_for_order_group_converts_total_to_kobo(
    order_group_factory,
    total,
    expected_kobo
):
    """
    Test that the order group total is snapshotted as integer kobo.
    """
    group = order_group_factory(total_amount=total)

    payment = Payment.objects.create_for_order_group(group)

    payment.refresh_from_db()
    assert payment.amount == expected_kobo
    assert isinstance(payment.amount, int)


def test_create_for_order_group_sets_defaults(order_group_factory):
    """
    Test that a new payment is linked to the group, pending, in NGN,
    and has no active transaction yet.
    """
    group = order_group_factory(total_amount=Decimal("500.00"))

    payment = Payment.objects.create_for_order_group(group)

    payment.refresh_from_db()
    assert payment.order_group_id == group.id
    assert group.payment == payment
    assert payment.currency == "NGN"
    assert payment.status == PaymentStatus.PENDING
    assert payment.active_transaction is None
    assert payment.paid_at is None


def test_create_for_order_group_with_custom_currency(order_group_factory):
    """
    Test that the currency can be overridden.
    """
    group = order_group_factory(total_amount=Decimal("10.00"))

    payment = Payment.objects.create_for_order_group(group, currency="GHS")

    assert payment.currency == "GHS"


def test_create_for_order_group_twice_fails(order_group_factory):
    """
    Test that an order group can only ever have one payment.
    """
    group = order_group_factory(total_amount=Decimal("500.00"))
    Payment.objects.create_for_order_group(group)

    with pytest.raises(IntegrityError), transaction.atomic():
        Payment.objects.create_for_order_group(group)

    assert Payment.objects.filter(order_group=group).count() == 1
