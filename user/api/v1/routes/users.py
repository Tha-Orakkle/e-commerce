from drf_spectacular.utils import extend_schema
from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from common.utils.api_responses import SuccessAPIResponse
from common.exceptions import ErrorException
from common.utils.check_valid_uuid import validate_id
from common.utils.pagination import Pagination
from user.serializers.user import UserSerializer
from user.serializers.swagger import (
    delete_user_schema,
    get_user_schema,
    get_users_schema,
    update_user_schema
)
from user.models import User
from user.tasks import send_verification_mail_task


class UsersView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(**get_users_schema)
    def get(self, request):
        """
        Gets all non admin users.
        """
        paginator = Pagination()
        queryset = User.objects.exclude(is_staff=True)
        paginated_queryset = paginator.paginate_queryset(queryset, request)
        serializers = UserSerializer(paginated_queryset, many=True)
        data = paginator.get_paginated_response(serializers.data).data
        return Response(
            SuccessAPIResponse(
                message="Users retrieved successfully.",
                data=data
            ).to_dict(), status=200
        )


class UserView(APIView):
    permission_classes = [IsAuthenticated]
    
    @extend_schema(**get_user_schema)
    def get(self, request, user_id):
        """
        Gets a specific user.
        """
        validate_id(user_id, "user")
        user = User.objects.exclude(is_staff=True).filter(id=user_id).first() # admin endpoint should be used to get admin data
        if not user:
            raise ErrorException("User not found.", code=status.HTTP_404_NOT_FOUND)
        serializer = UserSerializer(user)
        return Response(
            SuccessAPIResponse(
                message='User retrieved successfully.',
                data=serializer.data
            ).to_dict()
        )
    

    @extend_schema(**update_user_schema)
    def put(self, request, user_id):
        """
        Updates a specific user where user_ is user_not None.
        """
        send_mail = False
        validate_id(user_id, "user")
        data = {
            'email': request.data.get('email', None),
            'password': request.data.get('password', None)
        }
        if data['password'] and (data['password'] != request.data.get('confirm_password')):
            raise ErrorException("Password and confirm_password fields do not match.")
        user = User.objects.exclude(is_staff=True).filter(id=user_id).first()
        if not user:
            raise ErrorException("User not found.", code=status.HTTP_404_NOT_FOUND)
        if user != request.user:
            raise PermissionDenied()
        if data['email'] and data['email'] != user.email:
            data['is_verified'] = False
            send_mail = True
        data.pop('email') if not data['email'] else None
        data.pop('password') if not data['password'] else None
        if data.get('password'):
            if not user.check_password(request.data.get('old_password', None)):
                raise ErrorException("Old password is incorrect.")
        serializer = UserSerializer(data=data, instance=user, partial=True)
        if not serializer.is_valid():
            raise ErrorException(
                detail="User update failed.",
                errors=serializer.errors
            )

        serializer.save()
        if send_mail: send_verification_mail_task.delay(str(user.id), user.email)
        return Response(
            SuccessAPIResponse(
                message='User updated successfully.',
                data=serializer.data
            ).to_dict(), status=200)
    
    @extend_schema(**delete_user_schema)
    def delete(self, request, user_id):
        """
        Delete a specific non-admin user.
        """
        validate_id(user_id, "user")
        user = User.objects.exclude(is_staff=True).filter(id=user_id).first()
        if not user:
            raise ErrorException("User not found.", code=status.HTTP_404_NOT_FOUND)
        if user != request.user:
            raise PermissionDenied()
        user.delete()
        return Response({}, status=status.HTTP_204_NO_CONTENT)