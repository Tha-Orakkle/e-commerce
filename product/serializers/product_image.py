from rest_framework import serializers

from product.models import ProductImage


class ProductImageSerializer(serializers.ModelSerializer):
    """
    Serializer for ProductImage model.
    """
    url = serializers.ImageField(source='image')
    class Meta:
        model = ProductImage
        fields = ['id', 'url']
