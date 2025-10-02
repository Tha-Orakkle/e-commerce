from drf_spectacular.utils import OpenApiParameter
from rest_framework import serializers

from address.models import ShippingAddress
from common.swagger import (
    get_error_response,
    get_error_response_with_examples,
    get_success_response
)
from address.api.v1.serializers import ShippingAddressSerializer, ShippingAddressCreateUpdateSerializer

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


class ShippingAddressDataError(serializers.Serializer):
    """
    Serializer for the error response when creating or updating a shipping address.
    """
    full_name = serializers.ListField(child=serializers.CharField(
        default="Full name must be at least 2 characters long."
    ), required=False)
    telephone = serializers.ListField(child=serializers.CharField(
        default="Invalid telephone number."
    ), required=False)
    city = serializers.ListField(child=serializers.CharField(
        default="Invalid or unsupported city name."
    ), required=False)
    state = serializers.ListField(child=serializers.CharField(
        default="Invalid or unsupported state name."
    ), required=False)
    country = serializers.ListField(child=serializers.CharField(
        default="Invalid or unsupported country code."
    ), required=False)
    postal_code = serializers.ListField(child=serializers.CharField(
        default="Invalid postal code."
    ), required=False)


# schemas 
get_shipping_addresses_schema = {
    'summary': 'Get Shipping Addresses of a user',
    'description': 'Retrieve all shipping addresses associated with the authenticated user.',
    'tags': ['Shipping Address'],
    'operation_id': 'get_shipping_addresses',
    'request': None,
    'responses': {
        200: get_success_response("Shipping addresses retrieved successfully.", 200, ShippingAddressSerializer(many=True)),
        401: get_error_response_with_examples(code=401)
    }
}

get_shipping_address_schema = {
    'summary': 'Get a Shipping Address by ID',
    'description': 'Retrieve a specific shipping address by its ID.',
    'tags': ['Shipping Address'],
    'operation_id': 'get_shipping_address',
    'request': None,
    'responses': {
        200: get_success_response("Shipping address retrieved successfully.", 200, ShippingAddressSerializer()),
        400: get_error_response("Invalid address id."),
        401: get_error_response_with_examples(code=401),
        404: get_error_response("Shipping address not found.", 404)
    },
}

create_shipping_address_schema = {
    'summary': 'Create a Shipping Address',
    'description': 'Create a new shipping address for the authenticated user.',
    'tags': ['Shipping Address'],
    'operation_id': 'create_shipping_address',
    'request': ShippingAddressDataRequest,
    'responses': {
        201: get_success_response("Shipping address created successfully.", 201, ShippingAddressSerializer()),
        400: get_error_response("Shipping address creation failed.", 400, ShippingAddressDataError()),
        401: get_error_response_with_examples(code=401)
    },
}

update_shipping_address_schema = {
    'summary': 'Update a Shipping Address',
    'description': 'Update an existing shipping address by its ID.',
    'tags': ['Shipping Address'],
    'operation_id': 'update_shipping_address',
    'request': ShippingAddressDataRequest,
    'responses': {
        201: get_success_response("Shipping address updated successfully.", 201, ShippingAddressSerializer()),
        400: get_error_response("Shipping address update failed.", 400, ShippingAddressDataError()),
        401: get_error_response_with_examples(code=401),
        404: get_error_response("Shipping address not found.", 404)
    },
}

delete_shipping_address_schema = {
    'summary': 'Delete a Shipping Address',
    'description': 'Delete a specific shipping address by its ID.',
    'tags': ['Shipping Address'],
    'operation_id': 'delete_shipping_address',
    'request': None,
    'responses': {
        204: {},
        400: get_error_response("Invalid shipping address ID.", 400),
        401: get_error_response_with_examples(code=401),
        404: get_error_response("Shipping address not found.", 404)
    },
}