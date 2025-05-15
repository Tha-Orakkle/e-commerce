from rest_framework import serializers

from common.swagger import (
    get_success_response,
    get_error_response
)
from user.serializers.user import UserSerializer


# SWAGGER SCHEMAS FOR NON-ADMIN USERS LOGIN & LOGOUT
class UserDataRequest(serializers.Serializer):
    """
    Serializer for user registration requests.
    """
    email = serializers.EmailField()
    password = serializers.CharField()
    confirm_password = serializers.CharField()


class UserLoginDataRequest(serializers.Serializer):
    """
    Serializer for user login requests.
    """
    email = serializers.EmailField()
    password = serializers.CharField()
    remember_me = serializers.BooleanField(required=False)


# schemas
user_registration_schema = {
    'summary': 'User registration',
    'description': 'Register a new user by providing email and password.',
    'tags': ['Auth'],
    'operation_id': 'user_registration',
    'request': UserDataRequest,
    'responses': {
        201: get_success_response('User <email> created successfully.', 201),
        400: get_error_response('string', 400),
    }
}

user_login_schema = {
    'summary': 'User login',
    'description': 'Login a user by providing email and password. \
        Optionally, you can provide remember_me to keep the user logged in. \
        Returns access and refresh token as cookies.',
    'tags': ['Auth'],
    'operation_id': 'user_login',
    'request': UserLoginDataRequest,
    'responses': {
        200: get_success_response('User logged in successfully.', 200, UserSerializer()),
        400: get_error_response('Invalid login credentials.', 400),
    }
}
