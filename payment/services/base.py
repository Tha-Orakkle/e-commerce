import uuid

from payment.domain.exceptions import DuplicatePaymentError
from payment.models import Payment


class BasePaymentService:
    def __init__(self, user, group):
        self.user = user
        self.group = group

    def _get_or_create_payment(self):
        """
        Get or create payment.
        """
        return Payment.objects.get_or_create(
            order_group=self.group,
            defaults={
                "email": self.user.email,
                "amount": self.group.total_amount * 100,
            }
        )

    def _verify_order_group_payment(self):
        """
        Verify that payment has not been made before.
        Update the payment reference code if the payment obj has
        been created and payment not yet verified.
        """
        payment, created = self._get_or_create_payment()
        if payment.verified:
            raise DuplicatePaymentError()
        if not created:
            payment.reference = uuid.uuid4()
            payment.save(update_fields=["reference"])
        return payment
