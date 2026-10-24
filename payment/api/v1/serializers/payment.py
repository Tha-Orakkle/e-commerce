from drf_spectacular.utils import OpenApiTypes, extend_schema_field
from rest_framework import serializers

from payment.models import PaymentStatus, PaymentTransaction


class PaymentStatusSerializer(serializers.ModelSerializer):
    """
    Read-only status of a payment transaction together with the state of
    the payment it belongs to.

    `status` is the state of this transaction attempt, while
    `payment_status` is the state of the overall payment. `verified`
    is derived from the payment status and kept for clients that
    relied on it.
    """
    payment_status = serializers.CharField(
        source="payment.status",
        read_only=True
    )
    amount = serializers.SerializerMethodField()
    currency = serializers.CharField(
        source="payment.currency",
        read_only=True
    )
    paid_at = serializers.DateTimeField(
        source="payment.paid_at",
        read_only=True
    )
    verified = serializers.SerializerMethodField()

    class Meta:
        model = PaymentTransaction
        fields = [  # noqa: RUF012
            "reference",
            "status",
            "payment_status",
            "amount",
            "currency",
            "paid_at",
            "verified",
        ]
        read_only_fields = fields

    @extend_schema_field(OpenApiTypes.FLOAT)
    def get_amount(self, obj):
        """
        Returns the amount in Naira
        """
        return float(f"{obj.payment.amount / 100:.2f}")

    @extend_schema_field(OpenApiTypes.BOOL)
    def get_verified(self, obj):
        return obj.payment.status == PaymentStatus.VERIFIED

