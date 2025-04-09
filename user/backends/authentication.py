from drf_spectacular.extensions import OpenApiAuthenticationExtension
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed


class CookieJWTAuthentication(JWTAuthentication):
    """ Custom Authentication for API requests """
    
    def authenticate(self, request):
        """
        Gets access token from Authorization header or from cookie
        if header not available. Authenticates user afterwards.
        """
        header = self.get_header(request)
        if header:
            raw_token = self.get_raw_token(header)
        else:
            raw_token = request.COOKIES.get('access_token')

        if not raw_token:
            return None
        
        try:
            validated_token = self.get_validated_token(raw_token)
        except AuthenticationFailed:
            return None
        return self.get_user(validated_token), validated_token


class CookieJWTAuthenticationScheme(OpenApiAuthenticationExtension):
    target_class = "user.backends.authentication.CookieJWTAuthentication"
    name = "CookieJWTAuthentication"

    def get_security_definition(self, auto_schema):
        """
        defines the security details for the API docs
        """
        view = auto_schema.view
        return {
            'type': 'apiKey',
            'in': 'cookie',
            'name': 'access_token',
            'description': 'JWT access token stored in http-only cookie'
        }