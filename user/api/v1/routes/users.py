from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

import uuid
import os

from common.swagger import (
    BadRequestSerializer,
    UnauthorizedSerializer,
    ForbiddenSerializer,
)
from common.utils.api_responses import (
    DeleteAPIResponse,
    ErrorAPIResponse,
    SuccessAPIResponse,
    InvalidIdAPIResponse
)
from common.utils.pagination import Pagination
from user.serializers.user import UserSerializer
from user.serializers.swagger import (
    UserResponseSerializer,
    UserListResponseSerializer,
    UserRegistrationRequestSerializer
)
from user.models import User
from user.tasks import send_verification_mail_task


class UsersView(APIView):
    permission_classes = [IsAuthenticated]
    @extend_schema(
        operation_id='users_list',
        tags=['Users'],
        summary='Get all users',
        request= None,
        responses={
            200: UserListResponseSerializer,
            400: BadRequestSerializer,
            401: UnauthorizedSerializer,
            403: ForbiddenSerializer,
        }
        
    )
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
    
    @extend_schema(
        summary='Get a specific user',
        description='Get a specific user by id to be contained in the URL',
        tags=['Users'],
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
        Gets a specific user.
        """
        try:
            uuid.UUID(id)
        except Exception:
            return Response(InvalidIdAPIResponse("user").to_dict(), status=400)
        user = User.objects.exclude(is_staff=True).filter(id=id).first() # admin endpoint should be used to get admin data
        if not user:
            return Response(InvalidIdAPIResponse("user").to_dict(), status=400)
        serializer = UserSerializer(user)
        return Response(
            SuccessAPIResponse(
                code=200,
                message='User retrieved successfully.',
                data=serializer.data
            ).to_dict()
        )
    

    @extend_schema(
        summary='Update a specific user',
        description='Update a specific user by id to be contained in the URL',
        tags=['Users'],
        request=UserRegistrationRequestSerializer,
        responses={
            200: UserResponseSerializer,
            400: BadRequestSerializer,
            401: UnauthorizedSerializer,
            403: ForbiddenSerializer
        }
    )
    def put(self, request, id):
        """
        Updates a specific user where id is not None.
        """
        send_mail = False
        try:
            uuid.UUID(id)
        except Exception:
            return Response(InvalidIdAPIResponse("user").to_dict(), status=400)
        data = {
            'email': request.data.get('email', None),
            'password': request.data.get('password', None)
        }
        if data['password'] and (data['password'] != request.data.get('confirm_password')):
            return Response(
                ErrorAPIResponse(
                    message='Password and confirm_password fields do not match.'
                ).to_dict(), status=400
            )
        user = User.objects.exclude(is_staff=True).filter(id=id).first()
        if not user:
            return Response(InvalidIdAPIResponse("user").to_dict(), status=400)
        if user != request.user:
            raise PermissionDenied()
        if data['email'] and data['email'] != user.email:
            data['is_verified'] = False
            send_mail = True
        data.pop('email') if not data['email'] else None
        data.pop('password') if not data['password'] else None
        
        serializer = UserSerializer(data=data, instance=user, partial=True)
        if not serializer.is_valid():
            return Response(
                ErrorAPIResponse(
                    message="User update failed.",
                    errors=serializer.errors
                ).to_dict(), status=400
            )
        serializer.save()
        if send_mail: send_verification_mail_task.delay(str(user.id), user.email)
        return Response(
            SuccessAPIResponse(
                message='User updated successfully.',
                data=serializer.data
            ).to_dict(), status=200)
    

    def delete(self, request, id):
        try:
            uuid.UUID(id)
        except Exception:
            return Response(InvalidIdAPIResponse("user").to_dict(), status=400)

        user = User.objects.exclude(is_staff=True).filter(id=id).first()
        if not user:
            return Response(InvalidIdAPIResponse("user").to_dict(), status=400)

        if user != request.user:
            raise PermissionDenied()
        user.delete()
        return Response(DeleteAPIResponse("User").to_dict(), status=200)