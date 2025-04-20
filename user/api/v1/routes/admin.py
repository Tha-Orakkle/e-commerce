# module for admin user creation and sign in
from datetime import timedelta
from django.contrib.auth import authenticate
from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

import uuid

from common.backends.permissions import IsSuperUser
from common.swagger import (
    BadRequestSerializer,
    UnauthorizedSerializer,
    ForbiddenSerializer
)
from common.utils.api_responses import (
    DeleteAPIResponse, ErrorAPIResponse,
    InvalidIdAPIResponse, SuccessAPIResponse
)
from common.utils.pagination import Pagination
from user.models import User
from user.utils.password_validation import password_check
from user.serializers.user import UserSerializer
from user.serializers.swagger import (
    AdminUserLoginRequestSerializer,
    AdminUserRegistrationRequestSerializer,
    BaseSuccessSerializer,
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
        return Response(
            SuccessAPIResponse(
                code=201,
                message=f"Admin user {user.staff_id} created successfully."
            ).to_dict(), status=201
        )


class AdminUserLoginView(APIView):
    authentication_classes = []

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
                    message="Invalid login credentials."
                ).to_dict(), status=400
            )
        serializer = UserSerializer(user)
        response = Response(
            SuccessAPIResponse(
                message="Admin user login successful.",
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
    

class AdminsView(APIView):
    permission_classes = [IsSuperUser, IsAuthenticated]

    @extend_schema(
        description="Get all the admin users",
        tags=['Admin'],
        request=None,
        responses={
            200: UserResponseSerializer,
            400: BadRequestSerializer,
            401: UnauthorizedSerializer, 
            403: ForbiddenSerializer
        }
    )
    def get(self, request):
        """
        Gets all admin users.
        """
        paginator = Pagination()
        queryset = User.objects.exclude(is_staff=False)
        paginated_queryset = paginator.paginate_queryset(queryset, request)
        serializers =  UserSerializer(paginated_queryset, many=True)
        data = paginator.get_paginated_response(serializers.data).data
        return Response(
            SuccessAPIResponse(
                message="Admin users retrieved successfully.",
                data=data
            ).to_dict(), status=200
        )


class AdminView(APIView):
    permission_classes = [IsAdminUser, IsAuthenticated]

    @extend_schema(
        description="Get a specific admin user",
        tags=['Admin'],
        request=None,
        responses={
            200: UserResponseSerializer,
            400: BadRequestSerializer,
            401: UnauthorizedSerializer, 
            403: ForbiddenSerializer
        }
    )
    def get(self, request, id):
        """
        Get a specific admin user.
        """
        try:
            uuid.UUID(id)
        except ValueError:
            return Response(InvalidIdAPIResponse("admin user").to_dict(), status=400)
        user = User.objects.exclude(is_staff=False).filter(id=id).first()
        if not user:
            return Response(InvalidIdAPIResponse("user").to_dict(), status=400)
        if user != request.user and not request.user.is_superuser:
            raise PermissionDenied()
        serializer = UserSerializer(user)
        return Response(
            SuccessAPIResponse(
                message="Admin user retrieved successfully.",
                data=serializer.data
            ).to_dict(), status=200
        )
    
    @extend_schema(
        description="Update a specific admin user",
        tags=['Admin'],
        request=AdminUserRegistrationRequestSerializer,
        responses={
            200: UserResponseSerializer,
            400: BadRequestSerializer,
            401: UnauthorizedSerializer, 
            403: ForbiddenSerializer
        }
    )

    def put(self, request, id):
        """
        Update an admin user.
        Admin users can change only their passwords and not their staff_id.
        Only a super user can change staff_id.
        """
        try:
            uuid.UUID(id)
        except Exception:
            return Response(InvalidIdAPIResponse("admin user").to_dict(), status=400)
        data = {
            'staff_id': request.data.get('staff_id', None),
            'password': request.data.get('password', None)
        }
        if data['staff_id'] and not request.user.is_superuser:
            raise PermissionDenied()
        if data['password'] and data['password'] != request.data['confirm_password']:
            return Response(
                ErrorAPIResponse(
                    message="Password and confirm_password fields do not match."
                ).to_dict(), status=400
            )
        data.pop('password') if not data['password'] else None
        data.pop('staff_id') if not data['staff_id'] else None
        user = User.objects.exclude(is_staff=False).filter(id=id).first()
        if not user:
            return Response(InvalidIdAPIResponse("user").to_dict(), status=400)

        if user != request.user and not request.user.is_superuser:
            raise PermissionDenied()
        
        serializer = UserSerializer(data=data, instance=user, partial=True)
        if not serializer.is_valid():
            return Response(
                ErrorAPIResponse(
                    message="Admin user update failed.",
                    errors=serializer.errors
                ).to_dict(), status=400
            )
        serializer.save()
        return Response(
            SuccessAPIResponse(
                message="Admin user updated successfully.",
                data=serializer.data
            ).to_dict(), status=200
        )
    

    @extend_schema(
        summary="Delete an admin user",
        description="Only a super user can delete an admin.",
        request=None,
        responses={
            200: BaseSuccessSerializer,
            400: BadRequestSerializer,
            401: UnauthorizedSerializer, 
            403: ForbiddenSerializer

        }
    )

    def delete(self, request, id):
        """
        Delete an admin user.
        Only a super user can delete an admin.
        """
        if not request.user.is_superuser:
            raise PermissionDenied()
        try:
            uuid.UUID(id)
        except Exception:
            return Response(InvalidIdAPIResponse("admin user").to_dict(), status=400)
        user = User.objects.exclude(is_staff=False).filter(id=id).first()
        if not user:
            return Response(InvalidIdAPIResponse("user").to_dict(), status=400)
        if user == request.user:
            return Response(
                ErrorAPIResponse(
                    message="A super user cannot delete itself."
                ).to_dict(), status=400
            )
        user.delete()
        return Response(DeleteAPIResponse("Admin user").to_dict(), status=200)
        