from rest_framework import status
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from common.utils.check_valid_uuid import validate_id
from common.utils.api_responses import SuccessAPIResponse
from common.exceptions import ErrorException
from product.models import Product, ProductImage
from product.serializers.product import ProductImageSerializer


class ProductImageView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, product_id, image_id=None):
        validate_id(product_id, "product")
        product = Product.objects.filter(id=product_id).first()
        if not product:
            raise ErrorException("Invalid product id.")
        if image_id:
            validate_id(image_id, "product image")
            product_image = product.images.filter(id=image_id).first()
            if not product_image:
                raise ErrorException("Invalid product image id.")
            serializer = ProductImageSerializer(product_image, context={'request': request})
            return Response(
                SuccessAPIResponse(
                    message=f"Product {product.name} image retrieved.",
                    data=serializer.data
                ).to_dict(), status=status.HTTP_200_OK
            )
        queryset = product.images.all()
        serializers = ProductImageSerializer(queryset, many=True, context={'request': request})
        return Response(
            SuccessAPIResponse(
                message=f"Product {product.name} image retrieved.",
                data=serializers.data
            ).to_dict(), status=status.HTTP_200_OK
        )

    def post(self, request, product_id):
        """
        Adds an image to a product instance.
        """
        if not request.user.is_staff:
            raise PermissionDenied()
        validate_id(product_id, "product")
        product = Product.objects.filter(id=product_id).first()
        if not product:
            raise ErrorException("Invalid product id.")
        images = request.data.getlist('images', [])
        if images:
            product.add_images(images)
        return Response(
            SuccessAPIResponse(
                message="Product image updated successfully."
            ).to_dict(), status=status.HTTP_200_OK
        )

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
            raise ErrorException("Invalid product id.")
        image = product.images.filter(id=image_id).first()
        if not image:
            raise ErrorException("Invalid product image id.")
        image.delete()
        return Response({}, status=status.HTTP_204_NO_CONTENT)
