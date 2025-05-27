from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import PermissionDenied
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from common.exceptions import ErrorException
from common.utils.check_valid_uuid import validate_id
from common.utils.pagination import Pagination
from common.utils.api_responses import SuccessAPIResponse
from product.models import Category
from product.serializers.category import CategorySerializer
from product.serializers.swagger import (
    create_category_schema,
    delete_category_schema,
    get_categories_schema,
    get_category_schema,
    update_category_schema
)


class CategoriesView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(**get_categories_schema)
    def get(self, request):
        """
        Gets all categories.
        """
        paginator = Pagination()
        queryset = Category.objects.all()
        paginated_queryset = paginator.paginate_queryset(queryset, request)
        serializers = CategorySerializer(paginated_queryset, many=True)
        data = paginator.get_paginated_response(serializers.data).data
        return Response(
            SuccessAPIResponse(
                message="Categories retrieved successfully.",
                data=data
            ).to_dict(), status=status.HTTP_200_OK
        )

    @extend_schema(**create_category_schema)
    def post(self, request):
        """
        Create a new category.
        """
        if not request.user.is_staff:
            raise PermissionDenied()
        serializer = CategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                SuccessAPIResponse(
                    message="Category created successfully.",
                    data=serializer.data
                ).to_dict(), status=status.HTTP_201_CREATED
            )
        raise ErrorException(
            detail="Category creation failed.",
            errors=serializer.errors
        )
    

class CategoryView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(**get_category_schema)
    def get(self, request, category_id):
        """
        Retrieve a category by its id.
        """
        validate_id(category_id, "category")
        category = Category.objects.filter(id=category_id).first()
        if not category:
            raise ErrorException(detail="Category not found.", code=status.HTTP_404_NOT_FOUND)
        serializer = CategorySerializer(category)
        return Response(
            SuccessAPIResponse(
                message="Category retrieved successfully.",
                data=serializer.data
            ).to_dict(), status=status.HTTP_200_OK
        )
    
    @extend_schema(**update_category_schema)
    def put(self, request, category_id):
        """
        Update a category by its id.
        """
        if not request.user.is_staff:
            raise PermissionDenied()
        validate_id(category_id, "category")
        category = Category.objects.filter(id=category_id).first()
        if not category:
            raise ErrorException(detail="Category not found.", code=status.HTTP_404_NOT_FOUND)
        
        serializer = CategorySerializer(category, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(
                SuccessAPIResponse(
                    message="Category updated successfully.",
                    data=serializer.data
                ).to_dict(), status=status.HTTP_200_OK
            )
        raise ErrorException(
            detail="Category update failed.",
            errors=serializer.errors
        )
    
    @extend_schema(**delete_category_schema)
    def delete(self, request, category_id):
        """
        Delete a category by its id.
        """
        if not request.user.is_staff:
            raise PermissionDenied()
        validate_id(category_id, "category")
        category = Category.objects.filter(id=category_id).first()
        if not category:
            raise ErrorException(detail="Category not found.", code=status.HTTP_404_NOT_FOUND)
        
        category.delete()
        return Response(SuccessAPIResponse({}, status=status.HTTP_204_NO_CONTENT))