from drf_spectacular.utils import OpenApiTypes, extend_schema_field
from rest_framework import serializers

from payment.models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    amount = serializers.SerializerMethodField()

    class Meta:
        model = Payment
        fields = [  # noqa: RUF012
            "amount",
            "currency",
            "paid_at",
            "status"
        ]

    @extend_schema_field(OpenApiTypes.FLOAT)
    def get_amount(self, obj):
        """
        Returns the amount in Naira
        """
        return float(f"{obj.amount/100:.2f}")
