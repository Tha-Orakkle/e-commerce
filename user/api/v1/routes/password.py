from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

from common.utils.api_responses import SuccessAPIResponse
from common.exceptions import ErrorException
from common.permissions import IsShopOwner
from common.cores.validators import validate_id
from shop.models import Shop
from user.models import User
from user.api.v1.serializers import PasswordUpdateSerializer
from user.api.v1.swagger import forgot_password_schema, reset_password_confirm_schema
from user.tasks import send_password_reset_mail_task

class ForgotPasswordView(APIView):
    """
    Generates password reset link and sends as mai.
    """
    authentication_classes = []

    @extend_schema(**forgot_password_schema)
    def post(self, request):
        # Logic for handling password reset
        email = request.data.get('email')
        if not email:
            raise ErrorException("Email address required.")
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
    """
    Confirms the password reset link and resets the password.
    """
    authentication_classes = []

    @extend_schema(**reset_password_confirm_schema)
    def post(self, request):
        uid = request.query_params.get('uid')
        token = request.query_params.get('token')
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')
        exc = ErrorException(
            detail='Password reset failed.',
            errors = {'link': ['Invalid or expired password reset link.']}
        )
        if not uid or not token:
            raise exc
        if not new_password or not confirm_password:
            exc.errors = {'password': ['Password and confirm password fields are required.']}
            raise exc
        if new_password != confirm_password:
            exc.errors =  {'password': ['Password and confirm password fields do not match.']}
            raise exc
        try:
            email = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(email=email)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise exc
        token_generator = PasswordResetTokenGenerator()
        if not token_generator.check_token(user, token):
            raise exc
        user.set_password(new_password)
        user.save()
        return Response(
            SuccessAPIResponse(
                message="Password reset successfully."
            ).to_dict(), status=status.HTTP_200_OK
        )
      
        
class UpdatePasswordView(APIView):
    permission_classes = [IsAuthenticated]
    
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
    
    def patch(self, request, shop_code, staff_id):
        validate_id(staff_id, 'staff')
        shop = Shop.objects.filter(code=shop_code).first()
        user = request.user
        if not shop:
            raise ErrorException(
                detail="No shop found with the given shop code.",
                code="not_found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        staff = shop.get_staff_member(staff_id)
        if not staff:
            raise ErrorException(
                detail="No staff member found with the given ID.",
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
