from rest_framework import serializers

from product.models import Inventory


class InventorySerializer(serializers.ModelSerializer):
    product = serializers.CharField(source='product.name', read_only=True)
    class Meta:
        model = Inventory
        fields = ['product', 'quantity']
          
