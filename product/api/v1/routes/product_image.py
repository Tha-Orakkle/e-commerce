from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from common.permissions import IsStaff
from common.cores.validators import validate_id
from common.utils.api_responses import SuccessAPIResponse
from common.exceptions import ErrorException
from product.models import Product
from product.api.v1.serializers import ProductImageSerializer
from product.api.v1.swagger import (
    create_product_image_schema,
    delete_product_image_schema,
    get_product_images_schema,
    get_product_image_schema
)


class ProductImageListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsStaff()]
        return [IsAuthenticated()]

    @extend_schema(**get_product_images_schema)
    def get(self, request, product_id):
        validate_id(product_id, "product")
        product = Product.objects.filter(id=product_id).first()
        if not product:
            raise ErrorException(
                detail="No product found matching the given product ID.",
                code='not_found',
                status_code=status.HTTP_404_NOT_FOUND)

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
        validate_id(product_id, "product")
        product = Product.objects.filter(id=product_id).first()
        if not product:
            raise ErrorException(
                detail="No product found matching the given product ID.",
                code='not_found',
                status_code=status.HTTP_404_NOT_FOUND
            )
        if not request.user.can_manage_product(product):
            raise PermissionDenied()
        if product.images.count() == 8:
            raise ErrorException(
                detail="Product images cannot exceed 8. Cannot add more images.",
                code='limit_exceeded'
            )
        images = request.FILES.getlist('images', [])
        if images:
            product.add_images(images)
        else:
            raise ErrorException(
                detail="No images were provided.",
                code='no_images'
            )
        return Response(
            SuccessAPIResponse(
                message="Product image added successfully."
            ).to_dict(), status=status.HTTP_201_CREATED
        )


class ProductImageDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.request.method == 'DELETE':
            return [IsStaff()]
        return [IsAuthenticated()]

    @extend_schema(**get_product_image_schema)
    def get(self, request, product_id, image_id):
        validate_id(product_id, "product")
        validate_id(image_id, "product image")
        product = Product.objects.filter(id=product_id).first()
        if not product:
            raise ErrorException(
                detail="No product found matching the given product ID.",
                code='not_found',
                status_code=status.HTTP_404_NOT_FOUND)
        product_image = product.images.filter(id=image_id).first()
        if not product_image:
            raise ErrorException(
                detail="No product image found matching the given image ID.",
                code='not_found',
                status_code=status.HTTP_404_NOT_FOUND)
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
        validate_id(product_id, "product")
        validate_id(image_id, "product image")
        product = Product.objects.filter(id=product_id).first()
        if not product:
            raise ErrorException(
                detail="No product found matching the given product ID.",
                code='not_found',
                status_code=status.HTTP_404_NOT_FOUND)
        if not request.user.can_manage_product(product):
            raise PermissionDenied()
        image = product.images.filter(id=image_id).first()
        if not image:
            raise ErrorException(
                detail="No product image found matching the given image ID.",
                code='not_found',
                status_code=status.HTTP_404_NOT_FOUND)
        image.delete()
        return Response({}, status=status.HTTP_204_NO_CONTENT)
