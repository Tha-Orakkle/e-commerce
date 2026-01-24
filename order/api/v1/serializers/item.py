from rest_framework import serializers

from order.models import OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = OrderItem
        fields = ['id', 'product_name', 'product_description', 'quantity', 'price']
