from django.db import transaction
from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from common.backends.permissions import IsShopOwner
from common.exceptions import ErrorException
from common.utils.api_responses import SuccessAPIResponse
from user.api.v1.serializers import (
    UserSerializer,
    ShopStaffCreationSerializer
)
from user.api.v1.swagger import staff_creation_schema

User = get_user_model()

class ShopStaffCreationView(APIView):
    permission_classes = [IsShopOwner]

    @extend_schema(**staff_creation_schema)
    def post(self, request):
        """
        Create a new staff member for a shop.
        """
        shop = request.user.owned_shop
        serializer = ShopStaffCreationSerializer(
            data=request.data, context={'shop': shop})
        try:
            serializer.is_valid(raise_exception=True)
            with transaction.atomic():
                staff = serializer.save()
        except ValidationError as e:
            raise ErrorException(
                detail="Staff member creation failed.",
                code="validation_error",
                errors=e.detail
            )
        return Response(
            SuccessAPIResponse(
                message="Staff member creation successful.",
                data=UserSerializer(staff).data
            ).to_dict(),
            status=status.HTTP_201_CREATED
        )