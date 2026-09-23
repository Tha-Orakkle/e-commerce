from rest_framework import serializers

from payment.models import PaymentProvider


class InitializePaymentSerializer(serializers.Serializer):
    provider = serializers.CharField()

    def validate_provider(self, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in PaymentProvider.values:
            raise serializers.ValidationError(
                f"'{value}' is not a supported provider."
            )
        return normalized
