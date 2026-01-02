from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.exceptions import AuthenticationFailed 
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken

from user.api.v1.swagger import token_refresh_schema
from common.utils.api_responses import SuccessAPIResponse
from common.exceptions import ErrorException


class SecureTokenRefreshView(TokenRefreshView):
    """
    Custom TokenRefreshView for refreshing access token.
    """
    authentication_classes = []

    @extend_schema(**token_refresh_schema)
    def post(self, request, *args, **kwargs):
        """ 
        Gets refresh token from cookies before generating new acccess token.
        """
        exc = ErrorException(code='authentication_error')

        refresh_token = request.COOKIES.get('refresh_token', None)
        if not refresh_token:
            exc.detail="Refresh token was not provided."
            raise exc
        try:
            refresh = RefreshToken(refresh_token)
        except Exception as e:
            exc.detail = str(e)
            raise exc
        if not refresh:
            exc.detail = "Token is invalid or expired."
            raise exc
        response = Response(
            SuccessAPIResponse(
                message='Token refreshed successfully',
            ).to_dict(), status=200
        )
        response.set_cookie(
            'access_token', str(refresh.access_token),
            httponly=True, secure=False,
            samesite='Lax'
        )
        return response
