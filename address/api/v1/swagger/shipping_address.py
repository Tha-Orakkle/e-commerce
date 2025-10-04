from drf_spectacular.utils import  OpenApiResponse
from rest_framework import serializers

from address.models import ShippingAddress
from common.swagger import (
    make_success_schema_response,
    make_unauthorized_error_schema_response,
    make_not_found_error_schema_response,
    make_error_schema_response,
    make_error_schema_response_with_errors_field,
    build_invalid_id_error,
    ForbiddenSerializer,
    polymorphic_response,
    build_error_schema_examples,
    build_error_schema_examples_with_errors_field
)
from address.api.v1.serializers import ShippingAddressSerializer

# SWAGGER SCHEMAS FOR SHIPPING ADDRESS

class ShippingAddressDataRequest(ShippingAddressSerializer):
    """
    Serializer for the request data to create or update a shipping address.
    """
    country = serializers.CharField(
        default='NG',
        help_text="ISO 2 code of the country."
    )
    state = serializers.UUIDField(
        required=True,
        help_text="ID of the state or province."
    )
    city = serializers.UUIDField(
        required=True,
        help_text="ID of the city or town."
    )

    class Meta:
        model = ShippingAddress
        exclude = ['id', 'created_at', 'updated_at', 'user']
        read_only_fields = ['id', 'created_at', 'updated_at', 'user']

# ERROR RESPONSES FOR SWAGGER UI
errors = {
    **build_invalid_id_error('shipping address')
}
shipping_address_errors = {
    'validation_error': {
        'full_name': [
            'This field is required.',
            'This field may not be blank.',
            'Ensure this field has at least 3 characters.',
            'Ensure this field has no more than 32 characters.'
        ],
        'telephone': [
            'This field is required.',
            'This field may not be blank.',
            'Enter a valid phone number.'
        ],
        'street_address': [
            'This field is required.',
            'This field may not be blank.',
            'Ensure this field has no more than 256 characters.'
        ],
        'city': [
            'This field is required.',
            'Invalid UUID format.',
            'City with given ID not found or supported.',
            'City does not belong to state.'
            ],
        'state': [
            'This field is required.',
            'Invalid UUID format.',
            'State with given ID not found or supported.',
            'State does not belong to country with code.'
        ],
        'country': ['Country with code not found or supported.'],
        'postal_code': [
            'Ensure this field has no more than 20 characters.',
            'Cannot validate postal code for the given country code.',
            'Invalid postal code format for the given country.'
        ]
    }
}


# schemas 
get_shipping_addresses_schema = {
    'summary': 'Get Shipping Addresses of a customer',
    'description': 'Retrieve all shipping addresses associated with a customer. \
        Superusers can access all shipping addresses.',
    'tags': ['Shipping Address'],
    'operation_id': 'get_shipping_addresses',
    'request': None,
    'responses': {
        200: make_success_schema_response(
            "Shipping addresses retrieved successfully.",
            ShippingAddressSerializer, many=True),
        401: make_unauthorized_error_schema_response()
    }
}

get_shipping_address_schema = {
    'summary': 'Get a Shipping Address by ID',
    'description': 'Retrieve a specific shipping address by its ID. \
        User can only access their own shipping addresses unless they are a superuser.',
    'tags': ['Shipping Address'],
    'operation_id': 'get_shipping_address',
    'request': None,
    'responses': {
        200: make_success_schema_response(
            "Shipping address retrieved successfully.",
            ShippingAddressSerializer),
        400: make_error_schema_response(errors),
        401: make_unauthorized_error_schema_response(),
        404: make_not_found_error_schema_response(['Shipping address'])
    },
}

post_shipping_address_schema = {
    'summary': 'Create a Shipping Address',
    'description': 'Create a new shipping address for the authenticated user.',
    'tags': ['Shipping Address'],
    'operation_id': 'create_shipping_address',
    'request': ShippingAddressDataRequest,
    'responses': {
        201: make_success_schema_response(
            "Shipping address created successfully.",
            ShippingAddressSerializer),
        400: make_error_schema_response_with_errors_field(
            message="Shipping address creation failed.",
            errors=shipping_address_errors),
        401: make_unauthorized_error_schema_response(),
        403: ForbiddenSerializer
    },
}

patch_shipping_address_schema = {
    'summary': 'Update a Shipping Address',
    'description': 'Update an existing shipping address by its ID.',
    'tags': ['Shipping Address'],
    'operation_id': 'update_shipping_address',
    'request': ShippingAddressDataRequest,
    'responses': {
        201: make_success_schema_response(
            "Shipping address updated successfully.",
            ShippingAddressSerializer),
        400: OpenApiResponse(
            response=polymorphic_response,
            examples=[
                *build_error_schema_examples(errors),
                *build_error_schema_examples_with_errors_field(
                    message="Shipping address update failed.",
                    errors=shipping_address_errors
                )        
            ]
            ),
        401: make_unauthorized_error_schema_response(),
        403: ForbiddenSerializer,
        404: make_not_found_error_schema_response(['Shipping address']),
    },
}

delete_shipping_address_schema = {
    'summary': 'Delete a Shipping Address',
    'description': 'Delete a specific shipping address by its ID. Customers can only \
        update their own shipping addresses unless they are a superuser.',
    'tags': ['Shipping Address'],
    'operation_id': 'delete_shipping_address',
    'request': None,
    'responses': {
        204: {},
        400: make_error_schema_response(errors),
        401: make_unauthorized_error_schema_response(),
        404: make_not_found_error_schema_response(['Shipping address']),
    },
}
