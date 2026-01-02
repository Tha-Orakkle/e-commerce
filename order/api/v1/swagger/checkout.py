from drf_spectacular.utils import OpenApiResponse
from rest_framework import serializers

from common.swagger import (
    build_error_schema_examples,
    build_error_schema_examples_with_errors_field,
    ForbiddenSerializer,
    make_error_schema_response,
    make_success_schema_response,
    make_unauthorized_error_schema_response,
    polymorphic_response
)


from order.api.v1.serializers import OrderGroupSerializer

# SWAGGER SCHEMAS FOR CHECKOUT
class CheckoutRequestData(serializers.Serializer):
    """
    Serializer for the request data to checkou.
    """
    shipping_address = serializers.UUIDField(required=True)
    fulfillment_method = serializers.CharField(default="PICKUP")
    payment_method = serializers.CharField(default="CASH") 


non_error_field_errors = {
    'empty_cart': 'Cart is empty.',
    'invalid_items': 'Cart contains invalid items.',
    'insufficient_stock': 'Insufficient stock for <product_name>. Only <count> left.'
}

error_field_errors = {
    'missing_or_invalid_fields': {    
        'shipping_address': [
            "This field is required.",
            "Invalid shipping address id.",
            "No shipping address matching the given ID found."
        ],
        'fulfillment_method': [
            "The fulfillment method must be either 'PICKUP' or 'DELIVERY'."
        ],
        'payment_method': [
            "The payment method must be either 'CASH' or 'DIGITAL'."
        ]
    }
}

checkout_schema = {
    'summary': 'Checkout Order Group',
    'description': 'Process the checkout of the current user\'s cart, \
        creating an order group containing all orders for different shops and handling payment. \
        Fulfillment method in the request body can be \'PICKUP\' or \'DELIVERY\'. Payment method can \
        be \'CASH\' or \'DIGITAL\'',
    'operation_id': 'checkout',
    'tags': ['Checkout'],
    'request': CheckoutRequestData,
    'responses': {
        200: make_success_schema_response(
            "Checkout successful. Order has been created.",
            OrderGroupSerializer),
        400: OpenApiResponse(
            response=polymorphic_response,
            examples=[
                *build_error_schema_examples(errors=non_error_field_errors),
                *build_error_schema_examples_with_errors_field(
                    message="Invalid request data.",
                    errors=error_field_errors)
            ]
        ),
        401: make_unauthorized_error_schema_response(),
        403: ForbiddenSerializer,
        404: make_error_schema_response({'not_found': 'No Cart found for the user.'})
    }
}