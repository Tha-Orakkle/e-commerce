from rest_framework.response import Response
from rest_framework.exceptions import AuthenticationFailed 
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken


class SecureTokenRefreshView(TokenRefreshView):
    """
    Custom TokenRefreshView for refreshing access token.
    """

    def post(self, request, *args, **kwargs):
        """ 
        Gets refresh token from cookies before generating new acccess token.
        """
        refresh_token = request.COOKIES.get('refresh_token', None)
        if not refresh_token:
            raise AuthenticationFailed('refresh token was not provided.')

        refresh = RefreshToken(refresh_token)
        response = Response({'success': 'token refreshed successsfully'})
        response.set_cookie(
            'access_token', str(refresh.access_token),
            httponly=True, secure=False,
            samesite='Lax'
        )

        return response
    