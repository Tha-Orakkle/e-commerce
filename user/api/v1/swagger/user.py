from rest_framework import serializers

from common.swagger import (
    get_success_response,
    get_error_response,
    get_error_response_with_examples,
    BasePaginatedResponse,
    ForbiddenSerializer
)
from .login_register import UserDataRequest
from user.api.v1.serializers import UserSerializer


# SWAGGER SCHEMAS FOR NON-ADMIN USERS
class UserListResponse(BasePaginatedResponse):
    """
    Serializer for paginated user list response.
    """
    results = UserSerializer(many=True)


class UserDataError(serializers.Serializer):
    """
    Serializer for the error response when creating or updating a user.
    """
    email = serializers.ListField(child=serializers.CharField(), required=False)
    password = serializers.ListField(child=serializers.CharField(), required=False)


# schemas
get_users_schema = {
    'summary': 'Get all users (non-admin)',
    'description': 'Returns a paginated list of non-admin users.',
    'tags': ['User'],
    'operation_id': 'get_users',
    'request': None,
    'responses': {
        200: get_success_response('Users retrieved successfully.', 200, UserListResponse()),
        401: get_error_response_with_examples(code=401),
    }
}

get_user_schema = {
    'summary': 'Get a specific user (non-admin)',
    'description': 'Takes a user id as part of the url \
        and returns the matching  user',
    'tags': ['User'],
    'operation_id': 'get_user',
    'request': None,
    'responses': {
        200: get_success_response('User retrieved successfully.', 200, UserListResponse()),
        400: get_error_response('Invalid user id.', 400),
        401: get_error_response_with_examples(code=401),
        404: get_error_response('User not found.', 404),
    }
}

update_user_schema = {
    'summary': 'Update a specific user',
    'description': 'Update a specific user by id to be contained in the URL. \
        Users cannot update another user.',
    'tags': ['User'],
    'operation_id': 'update_user',
    'request': UserDataRequest,
    'responses': {
        200: get_success_response('User updated successfully.', 200, UserSerializer()),
        400: get_error_response('User update failed.', 400, UserDataError()),
        401: get_error_response_with_examples(code=401),
        403: ForbiddenSerializer,
        404: get_error_response('User not found.', 404)
    }
}

delete_user_schema = {
    'summary': 'Delete a user',
    'description': 'Takes a user id as part of the url. \
        Only a user can delete his account.',
    'tags': ['User'],
    'operation_id': 'delete_user',
    'request': None,
    'responses': {
        204: {},
        400: get_error_response('Invalid user id.', 400),
        401: get_error_response_with_examples(code=401),
        403: ForbiddenSerializer,
        404: get_error_response('User not found.', 404)
    }
}
