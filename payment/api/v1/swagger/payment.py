from drf_spectacular.utils import OpenApiParameter, OpenApiTypes
from rest_framework import serializers

from common.swagger import (
    get_success_response,
    get_error_response,
    get_error_response_with_examples
)

# SWAGGER SCHEMAS FOR PAYMENT
class InitializePaymentRequestData(serializers.Serializer):
    """
    Serializer for the request data to initialize a payment.
    """
    order = serializers.UUIDField(
        help_text="The ID of the order to initialize payment for.",
        required=True
    )

class InitializePaymentResponseData(serializers.Serializer):
    """
    Serializer for the response data after initializing a payment.
    """
    authorization_url = serializers.URLField(
        help_text="The URL to redirect the user to for payment authorization.",
        required=True
    )


# schemas
initailze_error_examples = {
    'Invalid order id': 'Invalid order id.',
    'Payment method not digital': 'Cash payment method does not require Paystack initialization.',
    'payment already verified': 'Payment has already been verified.'
}

initialize_payment_schema = {
    'summary': 'Initialize a payment',
    'description': 'Initializes a payment for an order. \
        The order ID will be passed as a request data. \
        The order must be one with a pending status and a \'digital\' payment method.',
    'tags': ['Payment'],
    'operation_id': 'initialize_payment',
    'request': InitializePaymentRequestData,
    'responses': {
        200: get_success_response(
            'Payment initialized successfully.',
            200,
            InitializePaymentResponseData()
        ),
        400: get_error_response_with_examples(examples=initailze_error_examples),
        401: get_error_response_with_examples(code=401),
        404: get_error_response('Order not found.', 404)
    }
}


verify_payment_schema = {
    'summary': 'Verify a payment',
    'description': 'Verifies a payment using the payment reference. \
        The payment reference will be passed as a query string parameter.',
    'tags': ['Payment'],
    'operation_id': 'verify_payment',
    'parameters': [
        OpenApiParameter(
            name='reference',
            type=OpenApiTypes.STR,
            description="The payment reference to verify.",
            location=OpenApiParameter.QUERY,
            required=True
        )
    ],
    'request': None,
    'responses': {
        200: get_success_response('Payment verified.'),
        401: get_error_response_with_examples(code=401),
        404: get_error_response('Payment not found.', 404)
    }
}
