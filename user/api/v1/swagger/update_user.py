from common.swagger import (
    ForbiddenSerializer,
    make_success_schema_response,
    make_error_schema_response_with_errors_field,
    make_unauthorized_error_schema_response,
)
from user.api.v1.serializers import UserUpdateSerializer, UserSerializer



# SCHEMA FOR UPDATE USER (CUSTOMERS AND SHOP OWNERS)
patch_errors = {
    'validation_error': {
        'email': [
            'This field is required.',
            'User with email already exists.'
        ],
        'staff_handle': ['Staff member with staff handle already exists.'],
        'non_field_errors': ["Either 'email' or 'staff_handle' field is required."],  
    }
}

patch_user_schema = {
    'summary': 'Update a user',
    'description': 'Update a customer or shop owner. \
        The fields to be updated include email and/or shop owner \
        (where user is a shop owner). The target user is the authenticated user.',
    'tags': ['User'],
    'operation_id': 'update_user',
    'request': UserUpdateSerializer,
    'responses': {
        200: make_success_schema_response(
            "User updated successfully.",
            UserSerializer),
        400: make_error_schema_response_with_errors_field(
            errors=patch_errors,
            message="User update failed."),
        401: make_unauthorized_error_schema_response(),
        403: ForbiddenSerializer,
    }
}
