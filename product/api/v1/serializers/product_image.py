from rest_framework import serializers

from product.models import ProductImage
from common.exceptions import ErrorException

class ProductImageSerializer(serializers.ModelSerializer):
    """
    Serializer for ProductImage model.
    """
    url = serializers.ImageField(source='image')
    class Meta:
        model = ProductImage
        fields = ['id', 'url']


class UploadProductImageSeriallizer(serializers.Serializer):
    """
    Serializer to add images to a product.
    """
    images = serializers.ListField(
        child=serializers.ImageField(),
        allow_empty=False
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._product = self.context.get('product')
        assert self._product is not None, "Product must be provided in the serializer context"
        self._count = self._product.images.count()

    def _raise(self, msg, code):
        raise ErrorException(
            detail=msg,
            code=code
        )    
    
    def validate_images(self, images):
        if self._count == 8:
            self._raise(
                "Product images cannot exceed 8. Cannot add more images.",
                "image_limit_reached")
        d = 8 - self._count
        if len(images) > d:
            self._raise(f"Too many images. You can only add {d} more porduct image(s).", "too_many_images")
        if any(img.size > (2 * 1024 * 1024) for img in images):
            self._raise("Ensure that all images are less than 2MB", "image_too_large")
        return images
    
    def create(self, validated_data):
        """
        Add images to the associated product.
        """
        images = validated_data.pop('images')
        img_objs = [ProductImage(
            product=self._product,
            image=img
        ) for img in images]
        ProductImage.objects.bulk_create(img_objs)
        return self._product.images.all()