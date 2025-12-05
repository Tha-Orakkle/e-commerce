from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from drf_spectacular.utils import extend_schema
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from common.utils.api_responses import SuccessAPIResponse
from common.exceptions import ErrorException
from common.permissions import IsShopOwner
from common.cores.validators import validate_id
from shop.models import Shop
from user.api.v1.serializers import (
    ForgotPasswordSerializer,
    PasswordUpdateSerializer,
    ResetPasswordConfirmSerializer
)
from user.api.v1.swagger import (
    forgot_password_schema,
    reset_password_confirm_schema,
    update_password_schema,
    update_staff_password_by_shopowner_schema
)
from user.tasks import send_password_reset_mail_task

User = get_user_model()


class ForgotPasswordView(APIView):
    """
    Generates password reset link and sends as mai.
    """
    authentication_classes = []

    @extend_schema(**forgot_password_schema)
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            email = serializer.validated_data['email']
        except ValidationError as e:
            raise ErrorException(
                detail="Could not generate password reset link.",
                code='validation_error',
                errors=e.detail
            )
        
        user = User.objects.filter(email=email).first()
        if user:
            token_generator = PasswordResetTokenGenerator()
            token = token_generator.make_token(user)
            encoded_email = urlsafe_base64_encode(force_bytes(email))
            link = f"http://127.0.0.1:8000/api/v1/reset-password-confirm/?uid={encoded_email}&token={token}"
            # send email with link in the background
            send_password_reset_mail_task.delay(email, link)
        return Response(
            SuccessAPIResponse(
                message="Password reset link sent.",
            ).to_dict(), status=status.HTTP_202_ACCEPTED
        )


class ResetPasswordConfirmView(APIView):
    authentication_classes = []
    
    @extend_schema(**reset_password_confirm_schema)
    def post(self, request):
        serializer = ResetPasswordConfirmSerializer(
            data=request.data,
            context = {'request': request}
        )
        try:
            serializer.is_valid(raise_exception=True)
            serializer.save()
        except ValidationError as e:
            raise ErrorException(
                detail="Password reset failed.",
                code='validation_error',
                errors=e.detail
            )
        except ErrorException as ee:
            raise ee
        
        return Response(SuccessAPIResponse(
            message="Password has been reset successfully."
        ).to_dict(), status=status.HTTP_200_OK)


class UpdatePasswordView(APIView):
    permission_classes = [IsAuthenticated]
    
    @extend_schema(**update_password_schema)
    def patch(self, request):
        serializer = PasswordUpdateSerializer(
            data=request.data,
            context={'request': request}
        )
        try:
            serializer.is_valid(raise_exception=True)
            serializer.save()
        except ValidationError as e:
            raise ErrorException(
                detail="Password change failed",
                code='validation_error',
                errors=e.detail
            )
        return Response(SuccessAPIResponse(
            message="Password changed successfully."
        ).to_dict(), status=status.HTTP_200_OK)
        
    
class UpdateStaffPasswordByShopOwnerView(APIView):
    permission_classes = [IsShopOwner]
    
    @extend_schema(**update_staff_password_by_shopowner_schema)
    def patch(self, request, shop_id, staff_id):
        validate_id(shop_id, 'shop')
        validate_id(staff_id, 'staff')
        shop = Shop.objects.filter(id=shop_id).first()
        user = request.user
        if not shop:
            raise ErrorException(
                detail="No shop matching the given ID found.",
                code="not_found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        staff = shop.get_staff_member(staff_id)
        if not staff:
            raise ErrorException(
                detail="No staff member matching given ID found.",
                code="not_found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        if not (
            user.is_superuser
            or (user.is_shopowner and user.owned_shop == shop)
        ):
            raise PermissionDenied()
        serializer = PasswordUpdateSerializer(
            data=request.data,
            context={
                'request': request,
                'user': staff
            }
        )
        try:
            serializer.is_valid(raise_exception=True)
            serializer.save()
        except ValidationError as e:
            raise ErrorException(
                detail="Staff password change failed",
                code='validation_error',
                errors=e.detail
            )

        return Response(SuccessAPIResponse(
            message="Staff password changed successfully."
        ).to_dict(), status=status.HTTP_200_OK)
