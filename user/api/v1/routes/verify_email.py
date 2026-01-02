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
            raise ErrorException(
                detail="Token not provided.",
                code='verification_error'
            )
        user = verify_email_verification_token(token)
        if not user:
            raise ErrorException(
                detail="Invalid or expired token.",
                code='verification_error'
            )
        if not user.is_verified:
            user.is_verified = True
            user.save(update_fields=['is_verified'])
            message = "Email verified successfully."
        else:
            message="Email already verified."
            
        return Response(
            SuccessAPIResponse(
                message=message
            ).to_dict(), status=200
        )
