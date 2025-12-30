from rest_framework import serializers

from .category import CategorySerializer
from .product_image import ProductImageSerializer
from common.exceptions import ErrorException
from product.models import Product
from shop.api.v1.serializers import ShopSerializer


class ProductSerializer(serializers.ModelSerializer):
    """
    Serializer for Product model.
    """
    images = ProductImageSerializer(read_only=True, many=True, required=False)
    categories = CategorySerializer(read_only=True, many=True, required=False)
    stock = serializers.IntegerField(source='inventory.stock', read_only=True)
    shop = ShopSerializer(read_only=True)

    class Meta:
        model = Product
        exclude = ['is_active']

    def __init__(self, *args, **kwargs):
        exclude = kwargs.pop('exclude', None)
        super().__init__(*args, **kwargs)
        
        self._shop = self.context.get('shop', None)
        
        if exclude is not None:
            for field_name in exclude:
                self.fields.pop(field_name, None)
                
    def validate_name(self, value):
        """
        Validate that the product name is unique.
        """
        value = value.strip()

        if self.instance and self.instance.name == value:
            return value
        if self.instance:
            shop = self.instance.shop
        else:
            shop = self._shop
        if not shop:
            raise AssertionError(
                "ProductSerializer requires shop in the context when creating new product."
            )
        if shop.products.filter(name__iexact=value).exists():
            raise serializers.ValidationError(
                "A product with this name already exists in the shop."
            )
        return value

    def validate(self, attrs):
        """
        Check that the self._shop exists before a product is created.
        """
        if not self._shop and not self.instance:
            raise AssertionError(
                "ProductSerializer requires shop in the context when creating new product."
            )
        return attrs

    def create(self, validated_data):
        """
        Create a Product instance.
        """
        files = self.context.get('files')
        images = files.getlist('images') if files else []
        categories = self.initial_data.getlist('categories') if 'categories' in self.initial_data else []

        product = Product.objects.create(
            **validated_data, shop=self._shop)

        if categories:
            try:
                product.add_categories(categories)
            except ErrorException:
                pass
        if images:
            product.add_images(images)
        return product
    
    def update(self, instance, validated_data):
        """
        Update a Product instance.
        """
        files = self.context.get('files')
        images = files.getlist('images', []) if files else []
        categories = self.initial_data.getlist('categories') if 'categories' in self.initial_data else []
        
        if not validated_data and not files and not categories:
            return instance

        for k, v in validated_data.items():
            setattr(instance, k, v)
        if categories:
            instance.add_categories(categories)
        if images:
            instance.update_images(images)
        instance.save()
        return instance
