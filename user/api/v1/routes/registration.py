from django.db import transaction
from drf_spectacular.utils import extend_schema
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError


from common.exceptions import ErrorException
from common.utils.api_responses import SuccessAPIResponse
from user.api.v1.serializers import ShopOwnerRegistrationSerializer, CustomerRegistrationSerializer
from user.api.v1.swagger import user_registration_schema
from user.tasks import send_verification_mail_task
from shop.api.v1.serializers import ShopSerializer


class ShopOwnerRegistrationView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        """
        Create a new shop owner.
        A shop will be created for the shop owner upon registration.
        """
        serializer = ShopOwnerRegistrationSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            with transaction.atomic():
                shop = serializer.save()
                transaction.on_commit(
                    lambda: send_verification_mail_task.delay(str(shop.owner.id), shop.owner.email)
                )
        except ValidationError as e:
            raise ErrorException(
                detail="Shop owner registration failed.",
                code="validation_error",
                errors=e.detail
            )
        return Response(
            SuccessAPIResponse(
                message="Shop owner registration successful.",
                data=ShopSerializer(shop).data
            ).to_dict(),
            status=status.HTTP_201_CREATED
        )

class CustomerRegistrationView(APIView):
    authentication_classes = []

    @extend_schema(**user_registration_schema)
    def post(self, request):
        """
        Create a new customer.
        A cart will be created for the customer upon registration.
        """
        serializer = CustomerRegistrationSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            with transaction.atomic():
                user = serializer.save()
                transaction.on_commit(
                    lambda: send_verification_mail_task.delay(str(user.id), user.email)
                )
        except ValidationError as e:
            raise ErrorException(
                detail="Customer registration failed.",
                code="validation_error",
                errors=e.detail
            )
        return Response(
            SuccessAPIResponse(
                message="Customer registration successful.",
                data=serializer.data
            ).to_dict(),
            status=status.HTTP_201_CREATED
        )