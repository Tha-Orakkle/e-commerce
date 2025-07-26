# module for admin user creation and sign in
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from common.exceptions import ErrorException
from common.utils.check_valid_uuid import validate_id
from common.backends.permissions import IsSuperUser
from common.utils.api_responses import SuccessAPIResponse
from common.utils.pagination import Pagination
from user.models import User
from user.api.v1.serializers import UserSerializer
from user.serializers.swagger import (
    delete_admin_user_schema,
    get_admin_user_schema,
    get_admin_users_schema,
    update_admin_user_schema
)

 

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
        