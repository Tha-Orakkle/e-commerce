from datetime import timedelta
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from drf_spectacular.utils import extend_schema
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from common.swagger import BadRequestSerializer
from common.utils.api_responses import (
    SuccessAPIResponse,
    ErrorAPIResponse,
)
from user.models import User
from user.serializers.user import UserSerializer
from user.serializers.swagger import (
    UserRegistrationRequestSerializer,
    UserLoginRequestSerializer,
    RegistrationSuccessSerializer,
    UserResponseSerializer
)
from user.tasks import send_verification_mail_task
from user.utils.password_validation import password_check


class RegisterView(APIView):
    permission_classes = []

    @extend_schema(
        summary='Register a new user',
        description='Register a new user by providing email and password.',
        request=UserRegistrationRequestSerializer,
        tags=['Auth'],
        responses={
            201: RegistrationSuccessSerializer,
            400: BadRequestSerializer,
        }
    )
    def post(self, request):
        """
        Handle the user registration process.
        Expects 'email' and 'password' in the request data.
        """
        data = request.data
        if not data or not data.get('email') or not data.get('password'):
            return Response(
                ErrorAPIResponse(
                    message='Please provide email and password.',
                ).to_dict(), status=400
            )
        if data.get('password') != data.get('confirm_password', None):
            return Response(
                ErrorAPIResponse(
                    message='Password and confirm_password fields do not match.',
                ).to_dict(), status=400
            )
        try:
            password_check(data.get('password'))
            user = User.objects.create_user(
                email=data.get('email'), password=data.get('password'))
        except (ValidationError, ValueError) as e:
            return Response(
                ErrorAPIResponse(
                    message=str(e),
                ).to_dict(), status=400
            )
        send_verification_mail_task.delay(str(user.id), user.email)
        return Response(
            SuccessAPIResponse(
                code=201,
                message=f'User {user.email} created successfully.',
            ).to_dict(), status=201)
    

class LoginView(APIView):
    permission_classes = []

    @extend_schema(
        summary='Login a user',
        description='Login a user by providing email and password.',
        tags=['Auth'],
        request=UserLoginRequestSerializer,
        responses={
            200: UserResponseSerializer,
            400: BadRequestSerializer,
        },
        
    )
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
            return Response(
                ErrorAPIResponse(
                    message='Please provide email and password.',
                ).to_dict(), status=400
            )
        user = authenticate(email=email, password=pwd)
        if not user:
            return Response(
                ErrorAPIResponse(
                    message='Invalid login credentials.',
                ).to_dict(), status=400
            )
        serializer = UserSerializer(user)
        response = Response(
            SuccessAPIResponse(
                message='User login successful.',
                data=serializer.data,
            ).to_dict(), status=200)
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
