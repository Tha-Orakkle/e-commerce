from drf_spectacular.utils import extend_schema
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated

from common.utils.api_responses import SuccessAPIResponse
from user.api.v1.swagger import logout_schema


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(**logout_schema)
    def post(self, request):
        """
        Logs out the user by deleting the session cookie.
        """
        response = Response(
            SuccessAPIResponse(
                message='Log out successful.'
            ).to_dict(), status=200
        )
        response.delete_cookie('refresh_token')
        response.delete_cookie('access_token')
        return response
