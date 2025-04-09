from drf_spectacular.utils import extend_schema
from rest_framework.views import APIView
from rest_framework.response import Response

from common.swagger import BadRequestSerializer, BaseSuccessSerializer
from common.utils.api_responses import SuccessAPIResponse, ErrorAPIResponse
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
            return Response(
                ErrorAPIResponse(
                    message='Token not provided.'
                ).to_dict(), status=400
            )
        user = verify_email_verification_token(token)
        if not user:
            return Response(
                ErrorAPIResponse(
                    message='Invalid or expired token.'
                ).to_dict(), status=400
            )
        user.is_verified = True
        user.save()
        return Response(
            SuccessAPIResponse(
                message='Email verified successfully.'
            ).to_dict(), status=200
        )