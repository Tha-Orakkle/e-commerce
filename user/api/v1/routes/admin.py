# module for admin user creation and sign in
from datetime import timedelta
from django.contrib.auth import authenticate
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from common.backends.permissions import IsSuperUser
from common.swagger import BadRequestSerializer
from common.utils.api_responses import ErrorAPIResponse, SuccessAPIResponse
from user.models import User
from user.utils.password_validation import password_check
from user.serializers.user import UserSerializer
from user.serializers.swagger import (
    AdminUserLoginRequestSerializer,
    AdminUserRegistrationRequestSerializer,
    RegistrationSuccessSerializer,
    UserResponseSerializer
)


class AdminUserRegistrationView(APIView):
    permission_classes = [IsSuperUser, IsAuthenticated]

    @extend_schema(
        summary="Create an Admin user",
        description="create admin user with staff id and password",
        tags=['Admin-Auth'],
        request=AdminUserRegistrationRequestSerializer,
        responses={
            201: RegistrationSuccessSerializer,
            400: BadRequestSerializer
        }
    )
    def post(self, request):
        """
        Create a new user with staff (Admin) access.
        The staff id should be in form of a username for the user.
        """
        staff_id = request.data.get('staff_id', None)
        pwd = request.data.get('password', None)
        if not staff_id or not pwd:
            return Response(
                ErrorAPIResponse(
                    message="Please, provide staff_id (username) and password for the staff."
                ).to_dict(), status=400
            )
        if pwd and pwd != request.data.get('confirm_password'):
            return Response(
                ErrorAPIResponse(
                    message="Password and confirm_password fields do not match."
                ).to_dict(), status=400
            )
        try:
            password_check(pwd)
            user = User.objects.create_staff(
                staff_id=staff_id, password=pwd)
        except ValueError as e:
            return Response(
                ErrorAPIResponse(
                    message=str(e)
                ).to_dict(), status=400
            )
        print(user)
        print("PASSED STAFF_ID", staff_id)
        return Response(
            SuccessAPIResponse(
                code=201,
                message=f"Admin user {user.staff_id} created successfully."
            ).to_dict(), status=201
        )


class AdminUserLoginView(APIView):
    # permission_classes = [IsAdminUser]

    @extend_schema(
        summary="Login an admin user",
        description="Login an admin user with staff id and password",
        tags=['Admin-Auth'],
        request=AdminUserLoginRequestSerializer,
        responses={
            200: UserResponseSerializer,
            400: BadRequestSerializer,
        }
    )
    def post(self, request):
        """
        Sign in the admin user with staff id and password
        Return access and refresh token as cookies.
        """
        staff_id = request.data.get('staff_id', None)
        pwd = request.data.get('password', None)
        remember_me = request.data.get('remember_me', False)
        lifespan = timedelta(days=7) if remember_me else timedelta(days=1)

        if not staff_id or not pwd:
            return Response(
                ErrorAPIResponse(
                    message="Please provide staff id and password."
                ).to_dict(), status=400
            )
        user = authenticate(staff_id=staff_id, password=pwd)
        if not user:
            return Response(
                ErrorAPIResponse(
                    message="Invalid login credentials"
                ).to_dict(), status=400
            )
        serializer = UserSerializer(user)
        response = Response(
            SuccessAPIResponse(
                message="Staff user login successful.",
                data=serializer.data
            ).to_dict(), status=200
        )
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