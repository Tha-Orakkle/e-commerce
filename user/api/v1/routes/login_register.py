from datetime import timedelta
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from common.utils.api_responses import SuccessAPIResponse
from common.exceptions import ErrorException
from user.models import User
from user.serializers.user import UserSerializer
from user.serializers.swagger import (
    user_login_schema,
    user_registration_schema
)
from user.tasks import send_verification_mail_task
from user.utils.password_validation import password_check


class RegisterView(APIView):
    authentication_classes = []

    @extend_schema(**user_registration_schema)
    def post(self, request):
        """
        Handle the user registration process.
        Expects 'email' and 'password' in the request data.
        """
        data = request.data
        if not data or not data.get('email') or not data.get('password'):
            raise ErrorException("Please provide email and password.")
        if data.get('password') != data.get('confirm_password', None):
            raise ErrorException("Password and confirm_password fields do not match.")
        try:
            password_check(data.get('password'))
            user = User.objects.create_user(
                email=data.get('email'), password=data.get('password'))
        except (ValidationError, ValueError) as e:
            raise ErrorException(str(e))
        send_verification_mail_task.delay(str(user.id), user.email)
        return Response(
            SuccessAPIResponse(
                code=201,
                message=f'User {user.email} created successfully.',
            ).to_dict(), status=status.HTTP_201_CREATED)
    

class LoginView(APIView):
    authentication_classes = []

    @extend_schema(**user_login_schema)
    def post(self, request):
        """
        Takes user email and password for authentication. 
        Returns access_token and refresh_token cookies.
        """
        email = request.data.get('email', None)
        pwd = request.data.get('password', None)
        remember_me = request.data.get('remember_me', False)
        lifespan = timedelta(days=7) if remember_me else timedelta(days=1)

        if not email or not pwd:
            raise ErrorException("Please provide email and password.")
        user = authenticate(email=email, password=pwd)
        if not user:
            raise ErrorException("Invalid login credentials.")

        serializer = UserSerializer(user)
        response = Response(
            SuccessAPIResponse(
                message=f'User logged in successfully.',
                data=serializer.data,
            ).to_dict(), status=status.HTTP_200_OK)
        refresh = RefreshToken.for_user(user)
        refresh.set_exp(lifetime=lifespan)
        response.set_cookie(
            'refresh_token', str(refresh),
            httponly=True, secure=False,
            samesite='Lax', max_age=(604800 if remember_me else 86400)
        )
        response.set_cookie(
            'access_token', str(refresh.access_token),
            httponly=True, secure=False,
            samesite='Lax'
        )
        return response
