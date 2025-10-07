from django.db import transaction
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from common.exceptions import ErrorException
from common.permissions import IsStaff, IsShopOwner
from common.cores.validators import validate_id
from common.permissions import IsShopOwner
from common.utils.api_responses import SuccessAPIResponse
from common.utils.pagination import Pagination
from shop.models import Shop
from user.models import User
from user.api.v1.serializers import (
    UserSerializer,
    ShopStaffCreationSerializer,
    StaffUpdateSerializer,
)
from user.api.v1.swagger import (
    shop_staff_creation_schema,
    get_shop_staff_members_schema,
    get_shop_staff_member_schema,
    patch_shop_staff_member_schema,
    delete_shop_staff_member_schema
    
)


class ShopStaffListCreateView(APIView):
    permission_classes = [IsShopOwner]

    @extend_schema(**get_shop_staff_members_schema)
    def get(self, request, shop_id):
        """
        Gets all the staff members of a shop.
        Only accessible by shop owners and super users.
        """
        validate_id(shop_id, 'shop')
        shop = Shop.objects.filter(id=shop_id).first()
        if not shop:
            raise ErrorException(
                detail="No shop matching the given shop ID found.",
                code="not_found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        if not (shop == getattr(request.user, 'owned_shop', None)
                or request.user.is_superuser):
            raise PermissionDenied()
        paginator = Pagination()
        queryset = shop.get_all_staff_members()
        paginated_queryset = paginator.paginate_queryset(queryset, request)
        serializers = UserSerializer(paginated_queryset, many=True)
        data = paginator.get_paginated_response(serializers.data).data
        return Response(
            SuccessAPIResponse(
                message="Shop staff members retrieved successfully.",
                data=data
            ).to_dict(), status=status.HTTP_200_OK
        )

    @extend_schema(**shop_staff_creation_schema)
    def post(self, request, shop_id):
        """
        Create a new staff member for a shop.
        """
        validate_id(shop_id, 'shop')
        shop = Shop.objects.filter(id=shop_id).first()
        if not shop:
            raise ErrorException(
                detail="No shop matching the given ID found.",
                code="not_found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        if not (shop == request.user.owned_shop or request.user.is_superuser):
            raise PermissionDenied()
        serializer = ShopStaffCreationSerializer(
            data=request.data, context={'shop': shop})
        try:
            serializer.is_valid(raise_exception=True)
            with transaction.atomic():
                staff = serializer.save()
        except ValidationError as e:
            raise ErrorException(
                detail="Shop staff member creation failed.",
                code="validation_error",
                errors=e.detail
            )
        return Response(
            SuccessAPIResponse(
                message="Shop staff member creation successful.",
                data=UserSerializer(staff).data
            ).to_dict(),
            status=status.HTTP_201_CREATED
        )


class ShopStaffDetailView(APIView):
    permission_classes = [IsShopOwner]

    def get_permissions(self):
        # update the permission for a get request
        if self.request.method == 'GET':
            return [IsStaff()]
        return [perm() for perm in self.permission_classes]

    @extend_schema(**get_shop_staff_member_schema)
    def get(self, request, shop_id, staff_id):
        """
        Get a specific staff member of a specific shop.
        """
        validate_id(shop_id, 'shop')
        validate_id(staff_id, "staff")
        shop = Shop.objects.filter(id=shop_id).first()
        if not shop:
            raise ErrorException(
                detail="No shop matching the given ID found.",
                code="not_found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        staff = shop.get_staff_member(staff_id)
        if not staff:
            raise ErrorException(
                detail="No staff member matching the given ID found.",
                code="not_found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        if not (
            staff == request.user
            or request.user.is_superuser
            or (request.user.is_shopowner and request.user.owned_shop == shop)
        ):
            raise PermissionDenied()
        return Response(
            SuccessAPIResponse(
                message="Shop staff member retrieved successfully.",
                data=UserSerializer(staff).data
            ).to_dict(), status=status.HTTP_200_OK
        )

    @extend_schema(**patch_shop_staff_member_schema)
    def patch(self, request, shop_id, staff_id):
        """
        Update a staff member staff handle.
        Only accessible to the shop owner.
        """
        validate_id(shop_id, 'shop')
        validate_id(staff_id, "staff")
        shop = Shop.objects.filter(code=shop_id).first()
        if not shop:
            raise ErrorException(
                detail="No shop matching the given shop ID found.",
                code="not_found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        staff = shop.get_staff_member(staff_id)
        if not staff:
            raise ErrorException(
                detail="No staff member matching the given ID found.",
                code="not_found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        if not (request.user.owned_shop == shop):
            raise PermissionDenied()

        serializer = StaffUpdateSerializer(
            data=request.data,
            context={
                'shop': shop,
                'staff': staff
            }
        )
        try:
            serializer.is_valid(raise_exception=True)
            staff = serializer.save()
        except ValidationError as e:
            raise ErrorException(
                detail="Staff member update failed.",
                code="validation_error",
                errors=e.detail
            )
        return Response(
            SuccessAPIResponse(
                message="Staff member updated successfully.",
                data=UserSerializer(staff).data
            ).to_dict(),
            status=status.HTTP_200_OK
        )
        
        
    @extend_schema(**delete_shop_staff_member_schema)
    def delete(self, request, shop_id, staff_id):
        """
        Delete a staff member.
        Only a shop owner can delete a staff member.
        """
        validate_id(shop_id, 'shop')
        validate_id(staff_id, "staff")
        shop = Shop.objects.filter(code=shop_id).first()
        if not shop:
            raise ErrorException(
                detail="No shop found with the given shop code.",
                code="not_found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        staff = shop.get_staff_member(staff_id)
        if not staff:
            raise ErrorException(
                detail="No staff memnber found with the given ID.",
                code="not_found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        if request.user.owned_shop == shop:
            raise PermissionDenied()

        staff.delete()
        return Response({}, status=status.HTTP_204_NO_CONTENT)
