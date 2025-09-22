from rest_framework import serializers

from common.swagger import (
    get_success_response,
    get_error_response_with_examples,
    get_error_response_for_post_requests,
    ForbiddenSerializer
)

from user.api.v1.serializers import (
    BaseUserCreationSerializer,
    CustomerRegistrationSerializer,
    ShopOwnerRegistrationSerializer,
    ShopStaffCreationSerializer
)
from shop.api.v1.serializers import ShopSerializer
from user.api.v1.serializers import UserSerializer

# SWAGGER SCHEMAS FOR SHOP OWNERS REGISTRATION

class CreateStaffRequestData(BaseUserCreationSerializer):
    staff_id = serializers.CharField(min_length=2, max_length=20)


# error fields
invalid_credentials = {'non_field_errors': ['Invalid credentials matching any customer.']}
email = [
    'This field is required',
    'This field may not be blank.',
    'Enter a valid email address.',
    'User with email already exists.',
]
staff_id = [
    'This field is required',
    'This field may not be blank.',
    'Ensure this field has at least 3 characters.',
    'Ensure this field has no more than 20 characters.',
]
name = [
    'This field is required.',
    'This field may not be blank.',
    'Ensure this field has at least 2 characters.',
    'Ensure this field has no more than 30 characters.',
]
telephone = [
    'Enter a valid phone number.'
]

password = [
    'This field is required.',
    'This field may not be blank.',
    'Password must be at least 8 characters long.',
    'Password must contain at least one digit.',
    'Password must contain at least one letter.',
    'Password must contain at least one uppercase letter.',
    'Password must contain at least one lowercase letter.',
    'Password must contain at least one special character.'
]

confirm_password = [
    'This field is required.',
    'This field may not be blank.',
    'Passwords do not match.'
]

shopowner_registration_errors = {
    'invalid_credentials': {
        'non_field_errors': [
            'Invalid credentials matching any customer.'
        ]
    },
    'validation_error': {
        'email': [
            *email,
            'Shop owner with email already exists.'
        ],
        'staff_id': staff_id,
        'first_name': name,
        'last_name': name,
        'telephone': telephone,
        'password': password,
        'confirm_password': confirm_password,
        'shop_name': [
            'This field may not be blank.',
            'This field is required.',
            'Shop with name already exists.',
            'Ensure this field has at least 3 characters.',
            'Ensure this field has no more than 40 characters.',
        ],
        'shop_description': [
            'Ensure this field has at least 10 characters.',
            'Ensure this field has no more than 2000 characters.',
        ],
    }
}


customer_registration_errors = {
    'invalid_credentials': {
        'non_field_errors': [
            'Invalid credentials matching any shop owner.'
        ]
    },
    'validation_error': {
        'email': [
            *email,
            'Customer with email already exists.'
        ],
        'first_name': name,
        'last_name': name,
        'telephone': telephone,
        'password': password,
        'confirm_password': confirm_password,
    }
}

staff_creation_errors = {
    'validation_error': {
        'staff_id': [
            *staff_id,
            'Staff member with staff ID already exists.'
        ],
        'first_name': name,
        'last_name': name,
        'telephone': telephone,
        'password': password,
        'confirm_password': confirm_password,
    }
}




# schemas

shopowner_registration_schema = {
    'summary': 'Register as a shop owner.',
    'description': 'Create an account for a seller.',
    'operation_id': 'shopowner_registration',
    'tags': ['Auth'],
    'request': ShopOwnerRegistrationSerializer,
    'responses': {
        200: get_success_response(
            message="Shop owner registration successful.",
            data_serializer=ShopSerializer()
        ),
        400: get_error_response_for_post_requests(
            message="Shop owner registration failed.",
            errors=shopowner_registration_errors
        )
        
    }
}

customer_registration_schema = {
    'summary': 'Register as a customer.',
    'description': 'Create an account for a customer.',
    'operation_id': 'customer_registration',
    'tags': ['Auth'],
    'request': CustomerRegistrationSerializer,
    'responses': {
        200: get_success_response(
            message="Customer registration successful.",
            data_serializer=UserSerializer()
        ),
        400: get_error_response_for_post_requests(
            message="Customer registration failed.",
            errors=customer_registration_errors
        )
        
    }
}

shop_staff_creation_schema = {
    'summary': 'Create a staff for a shop.',
    'description': 'Create a new staff for a shop by the shop owner.',
    'operation_id': 'staff_creation',
    'tags': ['Shop-Staff'],
    'request': CreateStaffRequestData,
    'responses': {
        200: get_success_response(
            message="Shop staff member creation successful.",
            data_serializer=UserSerializer()
        ),
        400: get_error_response_for_post_requests(
            message="Shop staff member creation failed.",
            errors=staff_creation_errors
        ),
        401: get_error_response_with_examples(),
        403: ForbiddenSerializer
    }
}

