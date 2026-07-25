import pytest

from payment.models import Payment


@pytest.fixture
def payment_factory():
    """
    Factory to create payment instances.
    """
    def create_payment(user, group, **kwargs):
        user = user
        group = group
        return Payment.objects.create(
            email=user.email,
            amount=group.total_amount * 100, # convert to kobo
            order_group=group,
            **kwargs
        )

    return create_payment
