from drf_spectacular.utils import extend_schema
from rest_framework.views import APIView
from rest_framework.response import Response

from common.swagger import BadRequestSerializer, BaseSuccessSerializer
from common.utils.api_responses import SuccessAPIResponse
from common.exceptions import ErrorException
from user.utils.email_verification import verify_email_verification_token


class VerifyEmailView(APIView):
    @extend_schema(
            summary="Verify Email",
            description="Verifies the email address using a token.",
            tags=["Auth"],
            request=None,
            responses={
                200: BaseSuccessSerializer,
                400: BadRequestSerializer,
            }
    )
    def get(self, request):
        """
        Verifies the token from the request.
        """
        token = request.GET.get('token', None)
        if not token:
            raise ErrorException("Token not provided.")
        user = verify_email_verification_token(token)
        if not user:
            raise ErrorException("Invalid or expired token.")
        user.is_verified = True
        user.save()
        return Response(
            SuccessAPIResponse(
                message='Email verified successfully.'
            ).to_dict(), status=200
        )