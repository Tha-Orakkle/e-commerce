# module for admin user creation and sign in
from datetime import timedelta
from django.contrib.auth import authenticate
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken


from common.exceptions import ErrorException
from common.utils.check_valid_uuid import validate_id
from common.backends.permissions import IsSuperUser
from common.utils.api_responses import SuccessAPIResponse
from common.utils.pagination import Pagination
from user.models import User
from user.utils.password_validation import password_check
from user.serializers.user import UserSerializer
from user.serializers.swagger import (
    admin_user_login_schema,
    admin_user_registration_schema,
    delete_admin_user_schema,
    get_admin_user_schema,
    get_admin_users_schema,
    update_admin_user_schema
)


class AdminUserRegistrationView(APIView):
    permission_classes = [IsSuperUser, IsAuthenticated]

    @extend_schema(**admin_user_registration_schema)
    def post(self, request):
        """
        Create a new user with staff (Admin) access.
        The staff id should be in form of a username for the user.
        """
        staff_id = request.data.get('staff_id', None)
        pwd = request.data.get('password', None)
        if not staff_id or not pwd:
            raise ErrorException("Please, provide staff_id (username) and password for the staff.")
        if pwd and pwd != request.data.get('confirm_password'):
            raise ErrorException("Password and confirm_password fields do not match.")
        try:
            password_check(pwd)
            user = User.objects.create_staff(
                staff_id=staff_id, password=pwd)
        except ValueError as e:
            raise ErrorException(str(e))
        return Response(
            SuccessAPIResponse(
                code=201,
                message=f"Admin user {user.staff_id} created successfully."
            ).to_dict(), status=status.HTTP_201_CREATED
        )


class AdminUserLoginView(APIView):
    authentication_classes = []

    @extend_schema(**admin_user_login_schema)
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
            raise ErrorException("Please provide staff id and password.")
        user = authenticate(staff_id=staff_id, password=pwd)
        if not user:
            raise ErrorException("Invalid login credentials.")
        serializer = UserSerializer(user)
        response = Response(
            SuccessAPIResponse(
                message="Admin user logged in successfully.",
                data=serializer.data
            ).to_dict(), status=status.HTTP_200_OK
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

    @extend_schema(**get_admin_users_schema)
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
            ).to_dict(), status=status.HTTP_200_OK
        )


class AdminView(APIView):
    permission_classes = [IsAdminUser, IsAuthenticated]

    @extend_schema(**get_admin_user_schema)
    def get(self, request, user_id):
        """
        Get a specific admin user.
        """
        validate_id(user_id, "admin user")
        user = User.objects.exclude(is_staff=False).filter(id=user_id).first()
        if not user:
            raise ErrorException("Admin user not found.", code=status.HTTP_404_NOT_FOUND)
        if user != request.user and not request.user.is_superuser:
            raise PermissionDenied()
        serializer = UserSerializer(user)
        return Response(
            SuccessAPIResponse(
                message="Admin user retrieved successfully.",
                data=serializer.data
            ).to_dict(), status=status.HTTP_200_OK
        )
    
    @extend_schema(**update_admin_user_schema)
    def put(self, request, user_id):
        """
        Update an admin user.
        Admin users can change only their passwords and not their staff_id.
        Only a super user can change staff_id.
        """
        validate_id(user_id, "admin user")
        data = {
            'staff_id': request.data.get('staff_id', None),
            'password': request.data.get('password', None)
        }
        if data['staff_id'] and not request.user.is_superuser:
            raise PermissionDenied()
        if data['password'] and data['password'] != request.data['confirm_password']:
            raise ErrorException("Password and confirm_password fields do not match.")
        data.pop('password') if not data['password'] else None
        data.pop('staff_id') if not data['staff_id'] else None
        user = User.objects.exclude(is_staff=False).filter(id=user_id).first()
        if not user:
            raise ErrorException("Admin user not found.", code=status.HTTP_404_NOT_FOUND)
        if user != request.user and not request.user.is_superuser:
            raise PermissionDenied()
        if data['password']:
            if not user.check_password(request.data.get('old_password', None)):
                raise ErrorException("Old password is incorrect.")
        
        serializer = UserSerializer(data=data, instance=user, partial=True)
        if not serializer.is_valid():
            raise ErrorException(
                detail="Admin user update failed.",
                errors=serializer.errors)
        serializer.save()
        return Response(
            SuccessAPIResponse(
                message="Admin user updated successfully.",
                data=serializer.data
            ).to_dict(), status=status.HTTP_200_OK
        )
    

    @extend_schema(**delete_admin_user_schema)
    def delete(self, request, user_id):
        """
        Delete an admin user.
        Only a super user can delete an admin.
        """
        if not request.user.is_superuser:
            raise PermissionDenied()
        validate_id(user_id, "admin user")
        user = User.objects.exclude(is_staff=False).filter(id=user_id).first()
        if not user:
            raise ErrorException("Admin user not found.", code=status.HTTP_404_NOT_FOUND)
        if user == request.user:
            raise PermissionDenied()
        user.delete()
        return Response({}, status=status.HTTP_204_NO_CONTENT)
        