from django.utils.text import slugify
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from common.exceptions import ErrorException
from common.utils.api_responses import SuccessAPIResponse
from common.utils.check_valid_uuid import validate_id
from common.utils.pagination import Pagination as PNP
from product.models import Product, Category
from product.serializers.product import ProductSerializer 
from product.serializers.swagger import (
    create_product_schema,
    delete_product_schema,
    get_products_schema,
    get_product_schema,
    product_category_add_or_remove_schema,
    update_product_schema
)


class ProductView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(**get_products_schema)
    def get(self, request):
        """
        Gets all products.
        """
        paginator = PNP()
        queryset = Product.objects.all()
        paginated_queryset  = paginator.paginate_queryset(queryset, request)
        serializers = ProductSerializer(paginated_queryset, many=True, context={'request': request})
        data = paginator.get_paginated_response(serializers.data).data
        return Response(
            SuccessAPIResponse(
                message="Products retrieved successfully.",
                data=data
            ).to_dict(), status=status.HTTP_200_OK
        )

    @extend_schema(**create_product_schema)
    def post(self, request):
        """
        Create a new product.
        """
        if not request.user.is_staff:
            raise PermissionDenied()
        serializer = ProductSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(
                SuccessAPIResponse(
                    message="Product created successfully.",
                    code=201,
                    data=serializer.data
                ).to_dict(), status=status.HTTP_201_CREATED
            )
        raise ErrorException(
            detail="Product creation failed.",
            errors=serializer.errors
        )
    

class ProductDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(**get_product_schema)
    def get(self, request, product_id):
        """
        Get a specific product.
        """
        validate_id(product_id, "product")
        product = Product.objects.filter(id=product_id).first()
        if not product:
            raise ErrorException("Product not found.")
        serializer = ProductSerializer(product, context={'request': request})
        return Response(
            SuccessAPIResponse(
                message="Product retrieved successfully.",
                data=serializer.data
            ).to_dict(), status=status.HTTP_200_OK
        )
        

    @extend_schema(**update_product_schema)
    def put(self, request, product_id):
        """
        Update a specific product.
        """
        if not request.user.is_staff:
            raise PermissionDenied()
        validate_id(product_id, "product")
        product = Product.objects.filter(id=product_id).first()
        if not product:
            raise ErrorException("Product not found.", code=status.HTTP_404_NOT_FOUND)
        serializer = ProductSerializer(
            instance=product,
            data=request.data,
            partial=True,
            context={'request': request}    
        )
        if not serializer.is_valid():
            raise ErrorException(
                detail="Product update failed.",
                errors=serializer.errors)
        serializer.save()
        return Response(
            SuccessAPIResponse(
                message="Product updated successfully.",
                data=serializer.data
            ).to_dict(), status=status.HTTP_200_OK
        )
        

    @extend_schema(**delete_product_schema)
    def delete(self, request, product_id):
        """
        Delete a specific product.
        """
        if not request.user.is_staff:
            raise PermissionDenied()
        validate_id(product_id, "product")
        product = Product.objects.filter(id=product_id).first()
        if not product:
          raise ErrorException("Product not found.", code=status.HTTP_404_NOT_FOUND)
        product.delete()
        return Response({}, status=status.HTTP_204_NO_CONTENT)


class ProductCategoryView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    @extend_schema(**product_category_add_or_remove_schema)
    def post(self, request, product_id):
        """
        Add/Remove Category from a product.
        """
        validate_id(product_id, 'product')
        action = request.query_params.get('action')
        product = Product.objects.filter(id=product_id).first()
        if not product:
            raise ErrorException(detail="Product not found.", code=status.HTTP_404_NOT_FOUND)

        categories = request.data.getlist('categories', [])

        if action == 'add':
            product.add_categories(categories)
        elif action == 'remove':
            product.remove_categories(categories)
        else:
            raise ErrorException(detail="Invalid action.", code=status.HTTP_400_BAD_REQUEST)        
        return Response(SuccessAPIResponse(
            message='Product categories updated successfully.',
        ).to_dict(), status=status.HTTP_200_OK)
    