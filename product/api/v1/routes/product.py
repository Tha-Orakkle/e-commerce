from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied

import uuid

from common.utils.api_responses import SuccessAPIResponse
from common.utils.check_valid_uuid import validate_id
from common.utils.pagination import Pagination as PNP
from common.exceptions import ErrorException
from product.models import Product
from product.serializers.product import ProductSerializer 


class ProductView(APIView):
    permission_classes = [IsAuthenticated]

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

    def get(self, request, id):
        """
        Get a specific product.
        """
        validate_id(id, "product")
        product = Product.objects.filter(id=id).first()
        if not product:
            raise ErrorException("Invalid product id.")
        serializer = ProductSerializer(product, context={'request': request})
        return Response(
            SuccessAPIResponse(
                message="Product retrieved successfully.",
                data=serializer.data
            ).to_dict(), status=status.HTTP_200_OK
        )
        

    
    def put(self, request, id):
        """
        Update a specific product.
        """
        if not request.user.is_staff:
            raise PermissionDenied()
        validate_id(id, "product")
        product = Product.objects.filter(id=id).first()
        if not product:
            raise ErrorException("Invalid product id.")
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
        

    def delete(self, request, id):
        """
        Delete a specific product.
        """
        if not request.user.is_staff:
            raise PermissionDenied()
        validate_id(id, "product")
        product = Product.objects.filter(id=id).first()
        if not product:
          raise ErrorException("Invalid product id.")
        product.delete()
        return Response({}, status=status.HTTP_204_NO_CONTENT)
