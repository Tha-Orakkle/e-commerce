from django.db import transaction
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.cores.validators import validate_id
from common.exceptions import ErrorException
from common.permissions import IsStaff
from common.utils.api_responses import SuccessAPIResponse
from common.utils.pagination import Pagination
from product.models import Product
from product.api.v1.serializers import (
    ProductSerializer
) 
from product.api.v1.swagger import (
    create_product_schema,
    delete_product_schema,
    get_products_schema,
    get_product_schema,
    product_category_add_or_remove_schema,
    update_product_schema
)
from shop.models import Shop


class ShopProductListCreateView(APIView):
    
    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsStaff()]
        return [IsAuthenticated()]

    @extend_schema(**get_products_schema)
    def get(self, request, shop_id):
        """
        Gets all products.
        """
        validate_id(shop_id, 'shop')
        shop = Shop.objects.filter(id=shop_id).first()
        if not shop:
            raise ErrorException(
                detail="No shop found with the given shop ID.",
                code='not_found',
                status_code=status.HTTP_404_NOT_FOUND
            )
        paginator = Pagination()
        queryset = shop.products.all()
        paginated_queryset  = paginator.paginate_queryset(queryset, request)
        serializers = ProductSerializer(
            paginated_queryset,
            many=True,
            context={'request': request}
        )
        data = paginator.get_paginated_response(serializers.data).data
        return Response(SuccessAPIResponse(
            message="Shop products retrieved successfully.",
            data=data
        ).to_dict(), status=status.HTTP_200_OK)

    @extend_schema(**create_product_schema)
    def post(self, request, shop_id):
        """
        Create a new product.
        """
        validate_id(shop_id, 'shop')
        shop = Shop.objects.filter(id=shop_id).first()
        if not shop:
            raise ErrorException(
                detail="No shop found with the given shop ID.",
                code='not_found',
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        if not (
            request.user.is_superuser
            or shop.staff_id_exists(request.user.staff_id)
        ):
            raise PermissionDenied()    

        serializer = ProductSerializer(
            data=request.data,
            context={
                'request': request,
                'files': request.FILES,
                'shop': shop
            })
        if not serializer.is_valid():
            raise ErrorException(
                detail="Product creation failed.",
                code='validation_error',
                errors=serializer.errors
            )
        with transaction.atomic():
            serializer.save()
        return Response(SuccessAPIResponse(
            message="Product created successfully.",
            data=serializer.data
        ).to_dict(), status=status.HTTP_201_CREATED)
        

class ProductListView(APIView):
    permission_classes = [IsAuthenticated]
    
    @extend_schema(**get_products_schema)
    def get(self, request):
        """
        Gets all products.
        """
        # update to take filters
        # categories and names
        paginator = Pagination()
        queryset = Product.objects.all()
        paginated_queryset  = paginator.paginate_queryset(queryset, request)
        serializers = ProductSerializer(
            paginated_queryset,
            many=True,
            context={'request': request}
        )
        data = paginator.get_paginated_response(serializers.data).data
        return Response(SuccessAPIResponse(
            message="Products retrieved successfully.",
            data=data
        ).to_dict(), status=status.HTTP_200_OK)
 

class ProductDetailView(APIView):

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated()]
        return [IsStaff()] 

    @extend_schema(**get_product_schema)
    def get(self, request, product_id):
        """
        Get a specific product.
        """
        validate_id(product_id, "product")
        product = Product.objects.filter(id=product_id).first()
        if not product:
            raise ErrorException(
                detail="Product not found.",
                code='not_found',
                status_code=status.HTTP_404_NOT_FOUND
            )
        serializer = ProductSerializer(product, context={'request': request})
        return Response(
            SuccessAPIResponse(
                message="Product retrieved successfully.",
                data=serializer.data
            ).to_dict(), status=status.HTTP_200_OK
        )
        

    @extend_schema(**update_product_schema)
    def patch(self, request, product_id):
        """
        Update a specific product.
        """
        validate_id(product_id, "product")
        product = Product.objects.filter(id=product_id).first()
        if not product:
            raise ErrorException(
                detail="Product not found.",
                code='not_found',
                status_code=status.HTTP_404_NOT_FOUND)

        if not request.user.can_manage_product(product):
            raise PermissionDenied()

        serializer = ProductSerializer(
            instance=product,
            data=request.data,
            partial=True,
            context={
                'request': request,
                'files': request.FILES
            })
        if not serializer.is_valid():
            raise ErrorException(
                detail="Product update failed.",
                code='validation_errror',
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
        # if not request.user.is_staff:
        #     raise PermissionDenied()
        validate_id(product_id, "product")
        product = Product.objects.filter(id=product_id).first()
        if not product:
            raise ErrorException(
                detail="Product not found.",
                code='not_found',
                status_code=status.HTTP_404_NOT_FOUND)
            
        if not request.user.can_manage_product(product):
            raise PermissionDenied()
        
        product.delete()
        return Response({}, status=status.HTTP_204_NO_CONTENT)


class ProductCategoryUpdateView(APIView):
    permission_classes = [IsStaff]

    @extend_schema(**product_category_add_or_remove_schema)
    def post(self, request, product_id):
        """
        Add/Remove Category from a product.
        """
        validate_id(product_id, 'product')
        product = Product.objects.filter(id=product_id).first()
        if not product:
            raise ErrorException(
                detail="Product not found.",
                code='not_found',
                status_code=status.HTTP_404_NOT_FOUND)
        
        if not request.user.can_manage_product(product):
            raise PermissionDenied()

        action = request.data.get('action', '')
        if 'categories' not in request.data:
            raise ErrorException(
                detail="Please provide a list of categories in the 'categories' field.",
                code='missing_categories',
                status_code=status.HTTP_400_BAD_REQUEST
            )

        categories = request.data.getlist('categories', [])

        if action == 'add':
            product.add_categories(categories)
        elif action == 'remove':
            product.remove_categories(categories)
        else:
            raise ErrorException(
                detail="Enter a valid action: 'add' or 'remove'.",
                code='invalid_action',
                status_code=status.HTTP_400_BAD_REQUEST)        
        return Response(SuccessAPIResponse(
            message='Product categories updated successfully.',
        ).to_dict(), status=status.HTTP_200_OK)
    