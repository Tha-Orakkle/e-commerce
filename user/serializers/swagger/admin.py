from rest_framework import serializers

from common.swagger import (
    get_success_response,
    get_error_response,
    BasePaginatedResponse,
    UnauthorizedSerializer,
    ForbiddenSerializer
)
from user.serializers.user import UserSerializer


# SWAGGER SCHEMAS FOR ADMIN USERS
class AdminListResponse(BasePaginatedResponse):
    """
    Serializer for paginated admin user list response.
    """
    results = UserSerializer(many=True)


class AdminUserDataRequest(serializers.Serializer):
    """
    Serializer for admin user registration requests.
    """
    staff_id = serializers.CharField()
    password = serializers.CharField()
    confirm_password = serializers.CharField()

class AdminUserLoginDataRequest(serializers.Serializer):
    """
    Serializer for admin user login requests.
    """
    staff_id = serializers.CharField()
    password = serializers.CharField()
    remember_me = serializers.BooleanField(required=False)


class AdminUserDataError(serializers.Serializer):
    """
    Serializer for the error response when creating or updating an admin user.
    """
    staff_id = serializers.ListField(child=serializers.CharField(), required=False)
    password = serializers.ListField(child=serializers.CharField(), required=False)


admin_user_registration_schema = {
    'summary': 'Admin user registration',
    'description': 'Create admin user with staff id and password. \
        Only an super user can create a new admin user.',
    'tags': ['Admin-Auth'],
    'operation_id': 'admin_user_registration',
    'request': AdminUserDataRequest,
    'responses' :{
        201: get_success_response('Admin user <staff_id> created successfully.', 201),
        400: get_error_response('string', 400),
        401: UnauthorizedSerializer,
        403: ForbiddenSerializer
    }
}

admin_user_login_schema = {
    'summary': 'Admin user login',
    'description': 'Login an admin user with staff id and password. \
        Returns access and refresh token as cookies. \
        Only an admin user can login.',
    'tags': ['Admin-Auth'],
    'operation_id': 'admin_user_login',
    'request': AdminUserLoginDataRequest,
    'responses': {
        200: get_success_response('Admin user logged in successfully.', 200, UserSerializer()),
        400: get_error_response('Invalid login credentials.', 400)
    }
}

get_admin_users_schema = {
    'summary': 'Get all the admin users',
    'description': 'Returns a paginated list of admin users. \
        Only super users can access this endpoint.',
    'operation_id': 'get_admin_users',
    'tags': ['Admin'],
    'request': None,
    'responses': {
        200: get_success_response('Admin users retrieved successfully.', 200, AdminListResponse()),
        401: UnauthorizedSerializer, 
        403: ForbiddenSerializer
    }
}

get_admin_user_schema = {
    'summary': 'Get a specific admin user',
    'description': 'Takes an admin user id as part of the url \
        and returns matching admin user. \
        Only admin users can access this endpoint. \
        Admin users can only access their own data.',
    'operation_id': 'get_admin_user',
    'tags': ['Admin'],
    'request': None,
    'responses': {
        200: get_success_response('Admin user retrieved successfully.', 200, UserSerializer()),
        400: get_error_response('Invalid admin user id.', 400),
        401: UnauthorizedSerializer, 
        403: ForbiddenSerializer
    }
}

update_admin_user_schema = {
    'summary': 'Update a specific admin user',
    'description': 'Takes an admin user id as part of the url. \
        Admin users can change only their passwords and not their staff_id. \
        Only a super user can change staff_id.',
    'tags': ['Admin'],
    'operation_id': 'update_admin_user',
    'request': AdminUserDataRequest,
    'responses': {
        200: get_success_response('Admin user updated successfully.', 200, UserSerializer()),
        400: get_error_response('Admin user update failed.', 400, AdminUserDataError()),
        401: UnauthorizedSerializer, 
        403: ForbiddenSerializer
    }
}

delete_admin_user_schema = {
    'summary': 'Delete an admin user',
    'description': 'Takes an admin user id as part of the url. \
        Only a super user can delete an admin. \
        A super user can only delete another super user and not himself. \
        This makes sure at least a super user always exists.',
    'tags': ['Admin'],
    'operation_id': 'delete_admin_user',
    'request': None,
    'responses': {
        204: {},
        400: get_error_response('Invalid admin user id.', 400),
        401: UnauthorizedSerializer, 
        403: ForbiddenSerializer
    }
}