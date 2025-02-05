from datetime import timedelta
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.exceptions import AuthenticationFailed 
from rest_framework_simplejwt.tokens import RefreshToken


class SecureTokenObtainPairView(TokenObtainPairView):
    """
    Custom TokenObtainPairView to obtain access and refresh token.
    """

    def post(self, request, *args, **kwargs):
        """ 
        Makes refresh token only accessible via HttpOnly cookie.
        """
        response = super().post(request, *args, **kwargs)
        remember_me = request.data.get('remember_me', False)
        refresh_token = response.data.get('refresh', None)
        lifespan = 7 * 24* 60 * 60

        if remember_me and refresh_token:
            refresh = RefreshToken(refresh_token)
            refresh.set_exp(lifetime=timedelta(days=30))
            lifespan = 30 * 24* 60 * 60
            refresh_token = str(refresh)
            response.data['refresh'] = refresh_token

        if refresh_token:
            response.set_cookie(
                'refresh_token',
                refresh_token,
                httponly=True,
                secure=True,
                samesite='Lax',
                max_age=lifespan
            )
        return response
    

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

        request.data['refresh'] = refresh_token
        return super().post(request, *args, **kwargs)
    