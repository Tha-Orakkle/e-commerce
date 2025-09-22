from drf_spectacular.utils import extend_schema
from rest_framework.views import APIView
from rest_framework.response import Response

from common.utils.api_responses import SuccessAPIResponse
from common.exceptions import ErrorException
from user.utils.email_verification import verify_email_verification_token
from user.api.v1.swagger import verify_email_schema


class VerifyEmailView(APIView):
    @extend_schema(**verify_email_schema)
    def get(self, request):
        """
        Verifies the token from the request.
        """
        token = request.query_params.get('token', None)
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
