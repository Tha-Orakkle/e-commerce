from django.urls import reverse
from rest_framework import status

from order.models import PaymentMethod


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
