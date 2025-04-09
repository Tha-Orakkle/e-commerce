from drf_spectacular.utils import extend_schema
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from common.utils.api_responses import SuccessAPIResponse
from common.swagger import (
    BadRequestSerializer,
    BaseSuccessSerializer
)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Logout User",
        description="Logs out the user by deleting the session cookie.",
        tags=["Auth"],
        request=None,
        responses={
            200: BaseSuccessSerializer,
            400: BadRequestSerializer,
        }
    )
    def post(self, request):
        """
        Logs out the user by deleting the session cookie.
        """
        response = Response(
            SuccessAPIResponse(
                message='User logged out successfully.'
            ).to_dict(), status=200
        )
        response.delete_cookie('refresh_token')
        response.delete_cookie('access_token')
        return response