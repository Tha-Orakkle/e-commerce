from rest_framework import serializers

from common.swagger import (
    get_error_response_for_post_requests,
    get_success_response
)
from user.api.v1.serializers import UserSerializer


# SWAGGER SCHEMAS FOR ADMIN USERS

class AdminLoginRequestData(serializers.Serializer):
    """
    Serializer for admin user login request.
    """
    shop_code = serializers.CharField()
    staff_id = serializers.CharField()
    password = serializers.CharField()
    remember_me = serializers.BooleanField()



class CustomerLoginRequestData(serializers.Serializer):
    """
    Serializer for admin user login request.
    """
    email = serializers.EmailField()
    password = serializers.CharField()
    remember_me = serializers.BooleanField()



# error_fields

invalid_credentials = {'non_field_errors': ['Invalid credentials matching any customer.']}
email = ['This field is required',]
staff_id = ['This field is required']
shop_code = ['This field is required']
password = ['This field is required']

admin_login_errors = {
    'invalid_credentials': invalid_credentials,
    'validation_error': {
        'shop_code': shop_code,
        'staff_id': staff_id,
        'password': password
    }
}

customer_login_errors = {
    'invalid_credentials': invalid_credentials,
    'validation_error': {
        'email': email,
        'password': password
    }
}

# schemas
admin_login_schema = {
    'summary': 'Admin user login',
    'description': 'Login an admin with the shop_code, staff id \
        and password. Returns access and refresh token as cookies. \
        Only an admin user can login.',
    'tags': ['Auth'],
    'operation_id': 'admin_login',
    'request': AdminLoginRequestData,
    'responses': {
        200: get_success_response(
            message='Admin user logged in successfully.',
            data_serializer=UserSerializer()
        ),
        400: get_error_response_for_post_requests(
            message="Admin login failed.",
            errors=admin_login_errors
        )
    }
}

customer_login_schema = {
    'summary': 'Customer login',
    'description': 'Login a customer with the email  \
        and password. Returns access and refresh token as cookies. \
        Only a customer can login.',
    'tags': ['Auth'],
    'operation_id': 'customer_login',
    'request': CustomerLoginRequestData,
    'responses': {
        200: get_success_response(
            message='Customer login successful.',
            data_serializer=UserSerializer()
        ),
        400: get_error_response_for_post_requests(
            message="Customer login failed.",
            errors=customer_login_errors
        )
    }
}

