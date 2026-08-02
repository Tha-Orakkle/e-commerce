from rest_framework import serializers

from payment.services import SERVICE_MAP


class InitializePaymentSerializer(serializers.Serializer):
    """
    Serializer to handle the payment service provider.
    """
    service = serializers.CharField()

    def validate_service(self, value):
        value = value.strip().lower()

        if value not in SERVICE_MAP:
            raise serializers.ValidationError(
                f"{value} is not a supported service type."
            )
        return SERVICE_MAP[value]
