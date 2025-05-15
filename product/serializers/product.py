from rest_framework import serializers

from product.models import Product
from .product_image import ProductImageSerializer


class ProductSerializer(serializers.ModelSerializer):
    """
    Serializer for Product model.
    """
    images = ProductImageSerializer(read_only=True, many=True, required=False)

    class Meta:
        model = Product
        fields = '__all__'

    def create(self, validated_data):
        """
        Create a Product instance.
        """
        image_data = self.initial_data.getlist('images', [])
        product = Product.objects.create(**validated_data)
        if image_data:
            product.add_images(image_data)
        return product
    
    def update(self, instance, validated_data):
        """
        Update a Product instance.
        """
        image_data = self.initial_data.getlist('images', [])
        for k, v in validated_data.items():
            setattr(instance, k, v)
        if image_data:
            instance.update_images(image_data)
        instance.save()
        return instance