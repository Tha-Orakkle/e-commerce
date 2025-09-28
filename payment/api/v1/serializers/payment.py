from rest_framework import serializers

from payment.models import Payment

class PaymentSerializer(serializers.ModelSerializer):
    amount = serializers.SerializerMethodField()
    
    class Meta:
        model = Payment
        fields = ['reference', 'verified', 'amount', 'paid_at']
        
    def get_amount(self, obj):
        """
        Returns the amount in Naira
        """
        return float(f"{obj.amount/100:.2f}")