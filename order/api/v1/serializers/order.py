from rest_framework import serializers

from .item import OrderItemSerializer
from order.models import Order


class ShippingSummarySerializer(serializers.Serializer):
    full_name = serializers.CharField(source='shipping_full_name', allow_null=True, default=None)
    telephone = serializers.CharField(source='shipping_telephone', allow_null=True, default=None)
    street_address = serializers.CharField(source='shipping_street_address', allow_null=True, default=None)
    city = serializers.CharField(source='shipping_city', allow_null=True, default=None)
    state = serializers.CharField(source='shipping_state', allow_null=True, default=None)
    country = serializers.CharField(source='shipping_country', allow_null=True, default=None)
    postal_code = serializers.CharField(source='shipping_postal_code', allow_null=True, default=None)


class OrderSerializerForShop(serializers.ModelSerializer):
    shipping = ShippingSummarySerializer(source='group', read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        exclude = ['shop', 'group']