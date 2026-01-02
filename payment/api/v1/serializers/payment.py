from drf_spectacular.utils import extend_schema_field, OpenApiTypes
from rest_framework import serializers

from payment.models import Payment

class PaymentSerializer(serializers.ModelSerializer):
    amount = serializers.SerializerMethodField()
    
    class Meta:
        model = Payment
        fields = ['reference', 'verified', 'amount', 'paid_at']
        
    @extend_schema_field(OpenApiTypes.FLOAT)
    def get_amount(self, obj):
        """
        Returns the amount in Naira
        """
        return float(f"{obj.amount/100:.2f}")