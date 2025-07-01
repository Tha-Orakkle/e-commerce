from rest_framework import serializers

from payment.models import Payment

class PaymentSeriallizer(serializers.ModelSerializer):
    """
    Payment model serializer.
    """
    class Meta:
        model = Payment
        fields = '__all__'
