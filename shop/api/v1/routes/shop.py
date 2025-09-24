from django.db import transaction
from rest_framework import status
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.cores.validators import validate_id
from common.exceptions import ErrorException
from common.permissions import IsShopOwner
from common.utils.api_responses import SuccessAPIResponse
from common.utils.pagination import Pagination
from shop.models import Shop
from shop.api.v1.serializers import ShopSerializer


class ShopListView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get (self, request):
        """
        Get a paginated list of all shops.
        """
        queryset = Shop.objects.all()
        
        paginator = Pagination()
        paginated_queryset = paginator.paginate_queryset(queryset, request)
        serializers = ShopSerializer(
            paginated_queryset,
            many=True,
            context={'request': request}
        )
        data = paginator.get_paginated_response(serializers.data).data
        
        return Response(SuccessAPIResponse(
            message="Shops retrived successfully.",
            data=data
        ).to_dict(), status=status.HTTP_200_OK)
        
        
class ShopDetailView(APIView):
    permission_classes = [IsShopOwner]
    
    def get_permissions(self):
        """
        Check GET request permission to IsAuthenticated.
        """
        if self.request.method == 'GET':
            return [IsAuthenticated()]
        return [perm() for perm in self.permission_classes]
    
    def get(self, request, shop_id):
        """
        Get a specific shop.
        """
        validate_id(shop_id, 'shop')
        shop = Shop.objects.filter(id=shop_id).first()
        if not shop:
            raise ErrorException(
                detail="No shop found matching the given shop ID.",
                code='not_found',
                status_code=status.HTTP_404_NOT_FOUND
            )
        return Response(SuccessAPIResponse(
            message="Shop retrieved successfully.",
            data=ShopSerializer(shop, context={'request': request}).data
        ).to_dict(), status=status.HTTP_200_OK)
        
        
    def patch(self, request, shop_id):
        """
        Update a specific shop.
        """
        validate_id(shop_id, 'shop')
        shop = Shop.objects.filter(id=shop_id).first()
        if not shop:
            raise ErrorException(
                detail="No shop found matching the given shop ID.",
                code='not_found',
                status_code=status.HTTP_404_NOT_FOUND
            )
        serializer = ShopSerializer(
            instance=shop,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        try:
            serializer.is_valid(raise_exception=True)
            serializer.save()
        except ValidationError as e:
            raise ErrorException(
                detail="Shop update failed.",
                code='validation_error',
                errors=e.detail
            )
        return Response(SuccessAPIResponse(
            message="Shop updated successfully.",
            data=serializer.data
        ).to_dict(), status=status.HTTP_200_OK)
        
    def delete(self, request, shop_id):
        """
        Deletes a shop and the associated
        user if user is not a customer also.
        """
        validate_id(shop_id, 'shop')
        shop = Shop.objects.filter(id=shop_id).first()
        if not shop:
            raise ErrorException(
                detail="No shop found matching the given shop ID.",
                code='not_found',
                status_code=status.HTTP_404_NOT_FOUND
            )
        if not (request.user.is_superuser or shop.owner == request.user):
            raise PermissionDenied()
        
        user = shop.owner
        with transaction.atomic():
            shop.delete()
            if not user.is_customer:
                user.delete()
            else:
                user.is_shopowner = False
                user.is_staff = False
                user.staff_id = None
                user.save()
            
        return Response({}, status=status.HTTP_204_NO_CONTENT)