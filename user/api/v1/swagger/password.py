from drf_spectacular.utils import OpenApiParameter, OpenApiTypes, OpenApiResponse
from rest_framework import serializers

from common.swagger import (
    ForbiddenSerializer,
    build_invalid_id_error,
    build_error_schema_examples,
    build_error_schema_examples_with_errors_field,
    make_success_schema_response,
    make_error_schema_response,
    make_error_schema_response_with_errors_field,
    make_unauthorized_error_schema_response,
    make_not_found_error_schema_response,
    polymorphic_response
)

from user.api.v1.serializers import PasswordUpdateSerializer

class ForgotPasswordDataRequest(serializers.Serializer):
    email = serializers.CharField()


class PasswordDataRequest(serializers.Serializer):
    new_password = serializers.CharField()
    confirm_password = serializers.CharField()


# FORGOT PASSWORD SCHEMA

forgot_password_error = {
    'validation_error': {
        'email': ['This field is required']
    }
}
forgot_password_schema = {
    'summary': 'Password reset link generation',
    'description': 'Generates a password reset link and sends it to the user\'s email address.',
    'tags': ['Password'],
    'operation_id': 'forgot_password',
    'request': ForgotPasswordDataRequest,
    'responses': {
        202: make_success_schema_response("Password reset link sent."),
        400: make_error_schema_response_with_errors_field(
            message="Could not generate password reset link.",
            errors=forgot_password_error
        )
    }
}


# RESET PASSWORD SCHEMA
password_errors = {
    'validation_error': {
        'new_password': [
            'This field is required.',
            'This field may not be blank.',
            'Password must be at least 8 characters long.',
            'Password must contain at least one digit.',
            'Password must contain at least one letter.',
            'Password must contain at least one uppercase letter.',
            'Password must contain at least one lowercase letter.',
            'Password must contain at least one special character.'
        ],
        'confirm_password': [
            'This field is required.',
            'This field may not be blank.',
            'Passwords do not match.'
        ]
    }
}


reset_password_errors = {
    'reset_failed': 'Invalid or expired password reset link.'
}

reset_password_confirm_schema = {
    'summary': 'Reset password confirm',
    'description': 'Confirms the password reset link and resets the password.',
    'tags': ['Password'],
    'operation_id': 'reset_password_confirm',
    'parameters' :[
        OpenApiParameter(
            name='uid',
            type=OpenApiTypes.STR,
            description="Base64 encoded unique email",
            location=OpenApiParameter.QUERY,
            required=True
        ),
        OpenApiParameter(
            name='token',
            type=OpenApiTypes.STR,
            description="Password reset token",
            location=OpenApiParameter.QUERY,
            required=True
        )
    ],
    'request':PasswordDataRequest,
    'responses': {
        200: make_success_schema_response("Password reset successfully."),
        400: OpenApiResponse(
            response=polymorphic_response,
            examples=[
                *build_error_schema_examples(errors=reset_password_errors),
                *build_error_schema_examples_with_errors_field(
                    message="Passeord reset failed.",
                    errors=password_errors)
            ]
        ),
    }
}

# UPDATE PASSWORD SCHEMA

update_password_errors = password_errors.copy()
update_password_errors.get('validation_error')['old_password'] = [
    'This field is required.',
    'Old password is incorrect.'
]

update_password_schema = {
    'summary': 'Change password',
    'description': 'Update a user password. The target user is the authenticated user.',
    'tags': ['Password'],
    'operation_id': 'update_password',
    'request': PasswordUpdateSerializer,
    'responses': {
        200: make_success_schema_response("Password changed successfully."),
        400: make_error_schema_response_with_errors_field(
            message="Password change failed.",
            errors=update_password_errors
        ),
        401: make_unauthorized_error_schema_response(),
    }
}

# UPDATE STAFF PASSWORD

invalid_id_errors = {
    **build_invalid_id_error('shop'),
    **build_invalid_id_error('staff')
}

update_staff_password_by_shopowner_schema = {
    'summary': 'Change password of a staff member',
    'description': 'Update a staff member password by shop owner. \
        Shop and staff member ID would be passed to the URL.',
    'tags': ['Password'],
    'operation_id': 'update_staff_password',
    'request': PasswordDataRequest,
    'responses': {
        200: make_success_schema_response("Password changed successfully."),
        400: OpenApiResponse(
            response=polymorphic_response,
            examples=[
                *build_error_schema_examples(errors=invalid_id_errors),
                *build_error_schema_examples_with_errors_field(
                    message="Staff password change failed.",
                    errors=password_errors
                )
            ]
        ),    
        401: make_unauthorized_error_schema_response(),
        403: ForbiddenSerializer,
        404: make_not_found_error_schema_response(['shop', 'staff member'])
    }
}
