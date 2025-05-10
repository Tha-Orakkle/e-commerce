from rest_framework import serializers

from product.models import Product, ProductImage


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['image']

    def to_representation(self, instance):
        request = self.context.get('request')
        if request is not None and instance.image:
            return request.build_absolute_uri(instance.image.url)
        return instance.image.url if instance.image else None


class ProductSerializer(serializers.ModelSerializer):
    image_urls = ProductImageSerializer(many=True, required=False)

    class Meta:
        model = Product
        fields = '__all__'

    def create(self, validated_data):
        """
        Create a Product instance.
        """
        image_data = self.initial_data.getlist('images', [])
        product = Product.objects.create(**validated_data)
        for image in image_data:
            ProductImage.objects.create(product=product, image=image)
        return product
    
    def update(self, instance, validated_data):
        """
        Update a Product instance.
        """
        image_data = validated_data.pop('images', [])
        for k, v in validated_data.items():
            setattr(instance, k, v)
        instance.save()
        if image_data is not None:
            for image in instance.images.all():
                image.delete() # deletes related image file 
            for image in image_data:
                Product.objects.create(product=instance, **image)
        return instance