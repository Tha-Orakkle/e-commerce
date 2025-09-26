from rest_framework import serializers

from order.models import OrderItem
from product.models import Product


class ProductBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name']


class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductBriefSerializer(read_only=True)
    
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'quantity', 'price']
