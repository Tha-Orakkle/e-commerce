from decimal import Decimal

import pytest
from django.urls import reverse
from rest_framework import status

from order.models import FulFillmentMethod, OrderGroup, PaymentMethod
from order.services.checkout import CheckoutService
from order.utils.delivery import calculate_delivery_fee
from payment.models import Payment, PaymentStatus

CHECKOUT_URL = reverse('checkout')


def _checkout(client, customer, address, payment_method, fulfillment_method):
    client.force_authenticate(user=customer)
    return client.post(
        CHECKOUT_URL,
        {
            'shipping_address': address.id,
            'payment_method': payment_method,
            'fulfillment_method': fulfillment_method,
        },
        format='json'
    )


# ==========================================================
# TEST CASES FOR PAYMENT CREATION DURING CHECKOUT
# ==========================================================
@pytest.mark.parametrize(
    "fulfillment_method",
    [FulFillmentMethod.DELIVERY, FulFillmentMethod.PICKUP],
    ids=["delivery", "pickup"]
)
def test_digital_checkout_creates_payment(
    client,
    customer,
    create_cart_items,
    shipping_address_factory,
    shopowner,
    fulfillment_method
):
    """
    Test that a DIGITAL checkout creates a pending payment whose amount
    is the final group total (items plus any delivery fee) in kobo.
    """
    address = shipping_address_factory(user=customer)
    total, _ = create_cart_items(
        customer.cart, shops=[shopowner.owned_shop],
        num_items=1, quantity=10
    )

    res = _checkout(
        client, customer, address,
        PaymentMethod.DIGITAL, fulfillment_method
    )

    assert res.status_code == status.HTTP_201_CREATED
    group = OrderGroup.objects.get(id=res.data['data']['id'])
    payment = Payment.objects.get(order_group=group)

    fee = (
        Decimal(calculate_delivery_fee())
        if fulfillment_method == FulFillmentMethod.DELIVERY
        else Decimal('0.00')
    )
    assert group.total_amount == Decimal(total) + fee
    assert payment.amount == int((Decimal(total) + fee) * 100)
    assert payment.currency == "NGN"
    assert payment.status == PaymentStatus.PENDING
    assert payment.active_transaction is None


def test_cash_checkout_creates_no_payment(
    client,
    customer,
    create_cart_items,
    shipping_address_factory,
    shopowner
):
    """
    Test that a CASH checkout does not create a payment record.
    """
    address = shipping_address_factory(user=customer)
    create_cart_items(
        customer.cart, shops=[shopowner.owned_shop],
        num_items=1, quantity=10
    )

    res = _checkout(
        client, customer, address,
        PaymentMethod.CASH, FulFillmentMethod.DELIVERY
    )

    assert res.status_code == status.HTTP_201_CREATED
    assert Payment.objects.count() == 0


def test_checkout_rolls_back_when_payment_creation_fails(
    mocker,
    customer,
    create_cart_items,
    shipping_address_factory,
    shopowner
):
    """
    Test that a failure creating the payment undoes the whole checkout:
    no order group, cart items kept, and stock untouched.
    """
    address = shipping_address_factory(user=customer)
    _, products = create_cart_items(
        customer.cart, shops=[shopowner.owned_shop],
        num_items=1, quantity=10
    )
    stock_before = products[0].inventory.stock
    cart_count = customer.cart.items.count()

    mocker.patch(
        "payment.models.PaymentManager.create_for_order_group",
        side_effect=RuntimeError("boom")
    )
    service = CheckoutService(
        user=customer,
        cart=customer.cart,
        cart_items=customer.cart.items.select_related(
            "product__inventory", "product__shop"
        ),
        shipping_address=address,
        payment_method=PaymentMethod.DIGITAL,
        fulfillment_method=FulFillmentMethod.DELIVERY,
    )

    with pytest.raises(RuntimeError):
        service.execute()

    products[0].inventory.refresh_from_db()
    assert OrderGroup.objects.count() == 0
    assert Payment.objects.count() == 0
    assert customer.cart.items.count() == cart_count
    assert products[0].inventory.stock == stock_before
