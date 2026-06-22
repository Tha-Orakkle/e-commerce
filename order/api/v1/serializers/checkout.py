from rest_framework import serializers

from address.models import ShippingAddress


class CheckoutSerializer(serializers.Serializer):
    """
    Serializer to validate the shipping address, fulfillment
    and payment method passed in request body.
    """
    
    shipping_address = serializers.UUIDField()
    payment_method = serializers.CharField()
    fulfillment_method = serializers.CharField()
    
    def validate_shipping_address(self, value):
        user = self.context["request"].user
        
        address = ShippingAddress.objects.filter(
            user=user,
            id=value
        ).first()
        if not address:
            raise serializers.ValidationError(
                "No shipping address matching the given ID found."
            )
        return address
    
    def validate_payment_method(self, value):
        value = value.strip().upper()
        allowed = ["CASH", "DIGITAL"]
        
        if value not in allowed:
            raise serializers.ValidationError(
                "The payment method must be either 'CASH' or 'DIGITAL'."
            )
            
        return value
    
    def validate_fulfillment_method(self, value):
        value = value.strip().upper()
        
        allowed = ["PICKUP", "DELIVERY"]
        
        if value not in allowed:
            raise serializers.ValidationError(
                "The fulfillment method must be either 'PICKUP' or 'DELIVERY'."
            )
        return value