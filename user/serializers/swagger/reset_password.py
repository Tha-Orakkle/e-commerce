from drf_spectacular.utils import OpenApiParameter
from rest_framework import serializers

from common.swagger import (
    get_success_response,
    get_error_response   
)


# SWAGGER SCHEMAS FOR RESET PASSWORD
class ForgotPasswordDataRequest(serializers.Serializer):
    email = serializers.CharField()

class ResetPasswordDataRequest(serializers.Serializer):
    new_password = serializers.CharField()
    confirm_password = serializers.CharField()

class ResetPasswordDataError(serializers.Serializer):
    password = serializers.ListField(child=serializers.CharField(
        default="Password and confirm password fields do not match."
    ), required=False)
    link = serializers.ListField(child=serializers.CharField(
        default="Invalid or expired password reset link."
    ), required=False)

# schemas
forgot_password_schema = {
    'summary': 'Password reset link generation',
    'description': 'Generates a password reset link and sends it to the user\'s email address.',
    'tags': ['User'],
    'operation_id': 'forgot_password',
    'request': ForgotPasswordDataRequest,
    'responses': {
        202: get_success_response('Password reset link sent.', 202),
        400: get_error_response('Email address required.', 400),
    }
}

reset_password_confirm_schema = {
    'summary': 'Reset password confirm',
    'description': 'Confirms the password reset link and resets the password.',
    'tags': ['User'],
    'operation_id': 'reset_password_confirm',
    'parameters' :[
        OpenApiParameter(
            name='uid',
            type=str,
            description="Base64 encoded unique email",
            required=True
        ),
        OpenApiParameter(
            name='token',
            type=str,
            description="Password reset token",
            required=True
        )
    ],
    'request':ResetPasswordDataRequest,
    'responses': {
        200: get_success_response('Password reset successfully.', 200),
        400: get_error_response('Password reset failed.', 400, ResetPasswordDataError()),
    }
}
