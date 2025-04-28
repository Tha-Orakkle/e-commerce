from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from common.utils.api_responses import (
    ErrorAPIResponse,
    SuccessAPIResponse
)
from user.models import User
from user.tasks import send_password_reset_mail_task

class ForgotPasswordView(APIView):
    """
    Generates password reset link and sends as mai.
    """
    authentication_classes = []

    def post(self, request):
        # Logic for handling password reset
        email = request.data.get('email')
        if not email:
            return Response(
                ErrorAPIResponse(
                    message="Please provide an email address."
                ).to_dict(), status=status.HTTP_400_BAD_REQUEST
            )
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                ErrorAPIResponse(
                    message="User with this email does not exist."
                ).to_dict(), status=status.HTTP_400_BAD_REQUEST
            )
        token_generator = PasswordResetTokenGenerator()
        token = token_generator.make_token(user)
        encoded_email = urlsafe_base64_encode(force_bytes(email))
        link = f"http://127.0.0.1:8000/api/v1/reset-password-confirm/?uid={encoded_email}&token={token}"
        # send email with link in the background
        send_password_reset_mail_task.delay(email, link)
        return Response(
            SuccessAPIResponse(
                message="Password reset link will be sent to your email address.",
                code=202,
                data={"link": link}
            ).to_dict(), status=status.HTTP_202_ACCEPTED
        )
    

class ResetPasswordConfirmView(APIView):
    """
    Confirms the password reset link and resets the password.
    """
    authentication_classes = []
    def post(self, request):
        uid = request.GET.get('uid')
        token = request.GET.get('token')
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')
        if not uid or not token:
            return Response(
                ErrorAPIResponse(
                    message="Invalid password reset link."
                ).to_dict(), status=status.HTTP_400_BAD_REQUEST
            )
        if not new_password or not confirm_password:
            return Response(
                ErrorAPIResponse(
                    message="Please provide a new password and confirm password."
                ).to_dict(), status=status.HTTP_400_BAD_REQUEST
            )
        if new_password != confirm_password:
            return Response(
                ErrorAPIResponse(
                    message="Passwords do not match."
                ).to_dict(), status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            email = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(email=email)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response(
                ErrorAPIResponse(
                    message="Invalid password reset link."
                ).to_dict(), status=status.HTTP_400_BAD_REQUEST
            )
        token_generator = PasswordResetTokenGenerator()
        if not token_generator.check_token(user, token):
            return Response(
                ErrorAPIResponse(
                    message="Invalid or expired password reset token."
                ).to_dict(), status=status.HTTP_400_BAD_REQUEST
            )
        user.set_password(new_password)
        user.save()
        
        return Response(
            SuccessAPIResponse(
                message="Password reset successfully."
            ).to_dict(), status=status.HTTP_200_OK
        )