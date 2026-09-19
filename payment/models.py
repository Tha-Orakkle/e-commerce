from django.db import models
from django.conf import settings
from django.urls import reverse

import uuid

from order.models import OrderGroup


class Payment(models.Model):
    """
    Payment model.
    """ 
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, null=False)
    reference = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    email = models.EmailField()
    amount = models.PositiveBigIntegerField()
    verified = models.BooleanField(default=False)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    order_group = models.OneToOneField(OrderGroup, on_delete=models.CASCADE, related_name='payment')

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


class PaymentProvider(models.TextChoices):
    PAYSTACK = "paystack", "Paystack"
    STRIPE = "stripe", "Stripe"


class PaymentStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    VERIFIED = "VERIFIED", "Verified"


class PaymentTransactionStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    SUCCESS = "SUCCESS", "Success"
    FAILED = "FAILED", "Failed"
    EXPIRED = "EXPIRED", "Expired"


class NewPayment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4(), null=False)
    order_group = models.OneToOneField(
        OrderGroup,
        on_delete=models.PROTECT,
        related_name='new_payment'
    )
    status = models.CharField(
        max_length=10,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING
    )
    active_transaction = models.OneToOneField(
        "PaymentTransaction",
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )
    amount = models.PositiveBigIntegerField()
    currency = models.CharField(max_length=3)
    paid_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # to handle cancelled orders
    refund_requested = models.BooleanField(default=False)
    refunded = models.BooleanField(default=False)
    refund_timestamp = models.DateTimeField(null=True)


class PaymentTransaction(models.Model):
    """
    Payment model. Records all payment transactions.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, null=False)
    payment = models.ForeignKey(
        Payment,
        on_delete=models.PROTECT,
        related_name="transactions"
    )
    reference = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True
    )
    customer_email = models.EmailField()

    provider = models.CharField(
        max_length=10,
        choices=PaymentProvider.choices,
        null=False
    )
    provider_transaction_id = models.CharField(max_length=12)
    channel = models.CharField(max_length=20)
    currency = models.CharField(max_length=3)
    amount = models.PositiveBigIntegerField()

    status = models.CharField(
        max_length=10,
        choices=PaymentTransactionStatus.choices,
        default=PaymentTransactionStatus.PENDING
    )
    paid_at = models.DateTimeField(null=True)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    verified_at = models.DateTimeField(null=True, blank=True)
    verification_failure_code = models.CharField(max_length=64)
    verification_failure_reason = models.CharField(max_length=255)

    metadata = models.JSONField(null=True, blank=True)
    authorization_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
    )

    def __str__(self):
        return f"<Payment: {self.id}> {self.amount} {self.status}"

    def to_dict(self):
        return {
            'reference': str(self.reference),
            'email': self.customer_email,
            'amount': float(self.amount),
            'callback_url': f"{settings.BASE_URL}{
                reverse('temporary-callback')
            }",
        }
