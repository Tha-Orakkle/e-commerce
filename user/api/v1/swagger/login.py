from rest_framework import serializers

from common.swagger import (
    make_error_schema_response_with_errors_field,
    make_success_schema_response,
)
from user.api.v1.serializers import UserSerializer


class StaffLogInRequestData(serializers.Serializer):
    """
    Serializer for admin user login request.
    """
    shop_code = serializers.CharField(default='SH12345')
    staff_handle = serializers.CharField()
    password = serializers.CharField()
    remember_me = serializers.BooleanField()


class CustomerLoginRequestData(serializers.Serializer):
    """
    Serializer for admin user login request.
    """
    email = serializers.EmailField()
    password = serializers.CharField()
    remember_me = serializers.BooleanField()


invalid_credentials = {'non_field_errors': ['Invalid credentials matching any customer.']}
email = ['This field is required',]
staff_handle = ['This field is required']
shop_code = ['This field is required']
password = ['This field is required']


# STAFF LOGIN SCHEMA

staff_login_errors = {
    'invalid_credentials': invalid_credentials,
    'validation_error': {
        'shop_code': shop_code,
        'staff_handle': staff_handle,
        'password': password
    }
}

staff_login_schema = {
    'summary': 'Log a shop owner or staff in',
    'description': 'Takes the shop_code, staff_handle \
        and password. Returns access and refresh token as cookies.',
    'tags': ['Auth'],
    'operation_id': 'staff_login',
    'request': StaffLogInRequestData,
    'responses': {
        200: make_success_schema_response(
            "Log in successful.",
            UserSerializer
        ),
        400: make_error_schema_response_with_errors_field(
            message="Log in failed.",
            errors=staff_login_errors
        )
    }
}


# CUSTOMER LOGIN SCHEMA

customer_login_errors = {
    'invalid_credentials': invalid_credentials,
    'validation_error': {
        'email': email,
        'password': password
    }
}

customer_login_schema = {
    'summary': 'Log a customer in',
    'description': 'Takes the email and password. \
        Returns access and refresh token as cookies.',
    'tags': ['Auth'],
    'operation_id': 'customer_login',
    'request': CustomerLoginRequestData,
    'responses': {
        200: make_success_schema_response(
            "Log in successful.",
            UserSerializer
        ),
        400: make_error_schema_response_with_errors_field(
            message="Log in failed.",
            errors=customer_login_errors
        )
    }
}
