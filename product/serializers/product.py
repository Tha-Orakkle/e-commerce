from django.utils.text import slugify
from rest_framework import serializers

from product.models import Product, Category
from .product_image import ProductImageSerializer
from .category import CategorySerializer


class ProductSerializer(serializers.ModelSerializer):
    """
    Serializer for Product model.
    """
    images = ProductImageSerializer(read_only=True, many=True, required=False)
    categories = CategorySerializer(read_only=True, many=True, required=False)
    stock = serializers.IntegerField(source='inventory.stock', read_only=True)

    class Meta:
        model = Product
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        exclude = kwargs.pop('exclude', None)
        super().__init__(*args, **kwargs)

        if exclude is not None:
            for field_name in exclude:
                self.fields.pop(field_name, None)



    def create(self, validated_data):
        """
        Create a Product instance.
        """
        image_data = self.initial_data.getlist('images', [])
        category_list = self.initial_data.getlist('categories', [])

        product = Product.objects.create(**validated_data)

        if category_list:
            product.add_categories(category_list)
        if image_data:
            product.add_images(image_data)
        return product
    
    def update(self, instance, validated_data):
        """
        Update a Product instance.
        """
        image_data = self.initial_data.getlist('images', [])
        category_list = self.initial_data.getlist('categories', [])

        for k, v in validated_data.items():
            setattr(instance, k, v)
        if category_list:
            instance.add_categories(category_list)
        if image_data:
            instance.update_images(image_data)
        instance.save()
        return instance