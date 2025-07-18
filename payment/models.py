from django.db import models
from django.conf import settings
from django.urls import reverse

import uuid

from order.models import Order


class Payment(models.Model):
    """
    Payment model.
    """ 
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, null=False)
    reference = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    email = models.EmailField()
    amount = models.PositiveBigIntegerField()
    verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment')

    # to handle cancelled orders
    refund_requested = models.BooleanField(default=False)
    refunded = models.BooleanField(default=False)
    refund_timestamp = models.DateTimeField(null=True)

    def __str__(self):
        return f"<Payment: {self.reference}> {self.verified}"
    
    def to_dict(self):
        return {
            'reference': str(self.reference),
            'email': self.email,
            'amount': float(self.amount),
            'callback_url': f"{settings.BASE_URL}{reverse('temporary-callback')}",
        }
