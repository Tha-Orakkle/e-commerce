from drf_spectacular.utils import extend_schema
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied

from common.cores.validators import validate_id
from common.exceptions import ErrorException
from common.permissions import IsSuperUser, IsShopOwner
from common.utils.api_responses import SuccessAPIResponse
from common.utils.pagination import Pagination
from user.api.v1.serializers import UserSerializer
from user.api.v1.swagger import (
    get_shopowner_schema,
    get_shopowners_schema
)

User = get_user_model()


class ShopOwnerListView(APIView):
    permission_classes = [IsSuperUser]

    @extend_schema(**get_shopowners_schema)
    def get(self, request):
        """
        Gets a paginated list of all shopowners.
        Only accessibly by super users.
        """
        paginator = Pagination()
        queryset = User.objects.get_shopowners()
        paginated_queryset = paginator.paginate_queryset(queryset, request)
        serializers = UserSerializer(paginated_queryset, many=True)
        data = paginator.get_paginated_response(serializers.data).data
        return Response(
            SuccessAPIResponse(
                message="Shop owners retrieved successfully.",
                data=data
            ).to_dict(),
            status=status.HTTP_200_OK
        )


class ShopOwnerDetailView(APIView):
    permission_classes = [IsShopOwner]

    @extend_schema(**get_shopowner_schema)
    def get(self, request, shopowner_id):
        """
        Get a shop owner.
        """
        validate_id(shopowner_id, 'shop owner')
        shop_owner = User.objects.filter(
            id=shopowner_id, is_shopowner=True).first()
        if not shop_owner:
            raise ErrorException(
                detail="No shop owner found with the given ID.",
                code="not_found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        if not (shop_owner == request.user or request.user.is_superuser):
            raise PermissionDenied()
        return Response(
            SuccessAPIResponse(
                message="Shop owner retrived successfully.",
                data=UserSerializer(shop_owner).data
            ).to_dict(),
            status=status.HTTP_200_OK
        )
