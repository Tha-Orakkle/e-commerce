from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from common.utils.check_valid_uuid import validate_id
from common.utils.api_responses import SuccessAPIResponse
from common.exceptions import ErrorException
from product.models import Product
from product.serializers.product_image import ProductImageSerializer
from product.serializers.swagger import (
    create_product_image_schema,
    delete_product_image_schema,
    get_product_images_schema,
    get_product_image_schema
)


class ProductImagesView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(**get_product_images_schema)
    def get(self, request, product_id):
        validate_id(product_id, "product")
        product = Product.objects.filter(id=product_id).first()
        if not product:
            raise ErrorException("Product not found.", code=status.HTTP_404_NOT_FOUND)
        queryset = product.images.all()
        serializers = ProductImageSerializer(queryset, many=True, context={'request': request})
        return Response(
            SuccessAPIResponse(
                message=f"Product {product.name} images retrieved.",
                data=serializers.data
            ).to_dict(), status=status.HTTP_200_OK
        )
    
    @extend_schema(**create_product_image_schema)
    def post(self, request, product_id):
        """
        Adds an image to a product instance.
        """
        if not request.user.is_staff:
            raise PermissionDenied()
        validate_id(product_id, "product")
        product = Product.objects.filter(id=product_id).first()
        if not product:
            raise ErrorException("Product not found.", code=status.HTTP_404_NOT_FOUND)
        if product.images.count() == 8:
            raise ErrorException("Product images cannot exceed 8.")
        images = request.data.getlist('images', [])
        if images:
            product.add_images(images)
        return Response(
            SuccessAPIResponse(
                message="Product image added successfully."
            ).to_dict(), status=status.HTTP_201_CREATED
        )



class ProductImageView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(**get_product_image_schema)
    def get(self, request, product_id, image_id):
        validate_id(product_id, "product")
        validate_id(image_id, "product image")
        product = Product.objects.filter(id=product_id).first()
        if not product:
            raise ErrorException("Product not found.", code=status.HTTP_404_NOT_FOUND)
        product_image = product.images.filter(id=image_id).first()
        if not product_image:
            raise ErrorException("Product image not found.", code=status.HTTP_404_NOT_FOUND)
        serializer = ProductImageSerializer(product_image, context={'request': request})
        return Response(
            SuccessAPIResponse(
                message=f"Product {product.name} image retrieved.",
                data=serializer.data
            ).to_dict(), status=status.HTTP_200_OK
        )

    @extend_schema(**delete_product_image_schema)
    def delete(self, request, product_id, image_id):
        """
        Deletes an image from a product instance.
        """
        if not request.user.is_staff:
            raise PermissionDenied()
        validate_id(product_id, "product")
        validate_id(image_id, "product image")
        product = Product.objects.filter(id=product_id).first()
        if not product:
            raise ErrorException("Product not found.", code=status.HTTP_404_NOT_FOUND)
        image = product.images.filter(id=image_id).first()
        if not image:
            raise ErrorException("Product image not found.", code=status.HTTP_404_NOT_FOUND)
        image.delete()
        return Response({}, status=status.HTTP_204_NO_CONTENT)
