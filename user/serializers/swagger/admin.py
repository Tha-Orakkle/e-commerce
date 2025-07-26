from drf_spectacular.utils import OpenApiParameter, OpenApiTypes
from rest_framework import serializers

from common.swagger import (
    get_success_response,
    get_error_response,
    get_error_response_with_examples,
    BasePaginatedResponse,
    ForbiddenSerializer
)
from user.api.v1.serializers import UserSerializer


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

admin_registration_error_examples = {
    'Incomplete credentials': 'Please provide staff_id (username) and password for the staff.',
    'Mismatching passwords': 'Password and confirm_password fields do not match.',
    'Existing admin user': 'Admin user with staff id already exists.',
    'Missing password': 'Password field is required.',
    'Short password': 'Password must be at least 8 characters long.',
    'Password without a digit': 'Password must contain at least one digit.',
    'Password without a letter': 'Password must contain at least one letter.',
    'Password without uppercase letter': 'Password must contain at least one uppercase letter.',
    'Password without lowercase letter': 'Password must contain at least one lowercase letter.',
    'Password without special character': 'Password must contain at least one special character.'

}

admin_user_registration_schema = {
    'summary': 'Admin user registration',
    'description': 'Create admin user with staff id and password. \
        Only an super user can create a new admin user.',
    'tags': ['Admin-Auth'],
    'operation_id': 'admin_user_registration',
    'request': AdminUserDataRequest,
    'responses' :{
        201: get_success_response('Admin user <staff_id> created successfully.', 201),
        400: get_error_response_with_examples(examples=admin_registration_error_examples),
        401: get_error_response_with_examples(code=401),
        403: ForbiddenSerializer
    }
}

admin_login_error_examples = {
    'Incomplete credentials': 'Please provide staff id and password.',
    'Invalid credentials': 'Invalid login credentials.'
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
        400: get_error_response_with_examples(examples=admin_login_error_examples)
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
        401: get_error_response_with_examples(code=401),
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
        401: get_error_response_with_examples(code=401), 
        403: ForbiddenSerializer,
        404: get_error_response('Admin user not found.', 404)
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
        401: get_error_response_with_examples(code=401), 
        403: ForbiddenSerializer,
        404: get_error_response('Admin user not found.', 404)
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
        401: get_error_response_with_examples(code=401), 
        403: ForbiddenSerializer,
        404: get_error_response('Admin user not found.', 404)
    }
}