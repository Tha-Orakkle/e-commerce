from rest_framework import serializers

from .item import OrderItemSerializer
from order.models import Order, OrderGroup
from shop.models import Shop


class ShopBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = ['id', 'name']


class OrderSerializerForGroup(serializers.ModelSerializer):
    shop = ShopBriefSerializer(read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        exclude = ['group']


class OrderGroupSerializer(serializers.ModelSerializer):
    """
    Consumer-facing order group serializer.
    """
    orders = OrderSerializerForGroup(many=True, read_only=True)

    class Meta:
        model = OrderGroup
        exclude = ['shipping_address', 'user']


class OrderGroupListSerializer(serializers.ModelSerializer):
    """
    Serializer that returns minimal data for a list of OrderGroups.
    """
    class Meta:
        model = OrderGroup
        exclude = ['user', 'shipping_address']
