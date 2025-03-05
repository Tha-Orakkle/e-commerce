from datetime import timedelta
from rest_framework.response import Response
from dj_rest_auth.registration.views import SocialLoginView
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client

import os

class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    callback_url =os.getenv('AUTH_GOOGLE_REDIRECT_URL')
    client_class = OAuth2Client

    def get_response(self):

        response = super().get_response()
        if isinstance(response, Response) and response.data:
            access_token = response.data.pop('access', None)
            refresh_token = response.data.pop('refresh', None)

            response.set_cookie(
                'refresh_token', refresh_token,
                httponly=True, secure=False,
                samesite='Lax', max_age=timedelta(days=7),
            )
            response.set_cookie(
                'access_token', access_token,
                httponly=True, secure=False,
                samesite='Lax', max_age=timedelta(minutes=15),
            )
        return response