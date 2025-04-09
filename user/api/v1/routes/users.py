from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

import uuid

from common.swagger import (
    BadRequestSerializer,
    UnauthorizedSerializer,
    ForbiddenSerializer,
)
from common.utils.api_responses import (
    SuccessAPIResponse,
    ErrorAPIResponse
)
from user.serializers.user import UserSerializer
from user.serializers.swagger import (
    UserResponseSerializer,
    UserListResponseSerializer,
    UserRegistrationRequestSerializer
)
from user.models import User
from user.tasks import send_verification_mail_task


class UsersView(APIView):
    permission_classes = [IsAdminUser, IsAuthenticated]
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
        Gets all users.
        """
        users = User.objects.all()
        serializers = UserSerializer(users, many=True)
        return Response(
            SuccessAPIResponse(
                message="Users retrieved successfully.",
                data= serializers.data
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
    def get(self, request, id=None):
        """
        Gets a specific user where id is not None.
        """
        if not id:
            return Response(
                ErrorAPIResponse(
                    message='Please provide a user id.'
                ).to_dict(), status=400
            )
        try:
            uuid.UUID(id)
        except ValueError:
            return Response(
                ErrorAPIResponse(
                    message='Invalid user id.'
                ).to_dict(), status=400
            )
        user = User.objects.filter(id=id).first()
        if not user:
            return Response(
                ErrorAPIResponse(
                    message='Invalid user id.'
                ).to_dict(), status=400
            )
        if user != request.user and not request.user.is_staff:
            raise PermissionDenied()
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
        if not id:
            return Response(
                ErrorAPIResponse(
                    message='Please provide a user id.'
                ).to_dict(), status=400
            )
        try:
            uuid.UUID(id)
        except ValueError:
            return Response(
                ErrorAPIResponse(
                    message='Invalid user id.'
                ).to_dict(), status=400
            )
        if not request.data:
            return Response(
                ErrorAPIResponse(
                    code=400,
                    message='Please provide data to update.'
                ).to_dict(), status=400
            )
        user = User.objects.filter(id=id).first()
        if not user:
            return Response(
                ErrorAPIResponse(
                    message='Invalid user id.'
                ), status=400
            )
        if user != request.user:
            return Response(
                ErrorAPIResponse(
                    code=403,
                    message='You do not have permission to perform this action.'
                ).to_dict(), status=403
            )
        data = request.data.copy()
        if data.get('password', None) and (data.get('password') != data.get('confirm_password', None)):
            return Response(
                ErrorAPIResponse(
                    message='password and confirm_password fields do not match.'
                ).to_dict(), status=400
            )
        if data.get('email') and data.get('email') != user.email:
            data['is_verified'] = False
        serializer = UserSerializer(data=data, instance=user, partial=True)
        if serializer.is_valid():
            serializer.save()
            if data.get('email') and data.get('email') != user.email:
                send_verification_mail_task.delay(str(user.id), user.email)
        else:
            return Response(
                ErrorAPIResponse(
                    message=serializer.errors
                ).to_dict(), status=400
            )
        return Response(
            SuccessAPIResponse(
                message='User updated successfully.',
                data=serializer.data
            ).to_dict(), status=200)
    
