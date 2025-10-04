from rest_framework import serializers

from common.swagger import (
    ForbiddenSerializer,
    make_success_schema_response,
    make_error_schema_response,
    make_not_found_error_schema_response,
    make_unauthorized_error_schema_response,
    build_invalid_id_error
)
from payment.api.v1.serializers import PaymentSerializer



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
    **build_invalid_id_error('order group'),
    'not_allowed': 'Cash payment method does not require Paystack initialization.',
    'invalid_status': 'Only pending order groups can be paid for.',
    'duplicate_transaction': 'Payment has already been verified',
    'paystack_error': 'Payment request failed; Paystack error.',
}

initialize_payment_schema = {
    'summary': 'Initialize a payment',
    'description': 'Initializes a payment for an order group. \
        The order group ID will be passed as part of the url path. \
        The order must be one with a pending status and a \'digital\' payment method.',
    'tags': ['Payment'],
    'operation_id': 'initialize_payment',
    'request': None,
    'responses': {
        200: make_success_schema_response(
            'Payment initialized successfully.',
            InitializePaymentResponseData),
        400: make_error_schema_response(initailze_error_examples),
        401: make_unauthorized_error_schema_response(),
        403: ForbiddenSerializer,
        404: make_not_found_error_schema_response(['order group'])
    }
}


vf_errors = {
    'not_found': 'No payment matching the given reference found.'
}

verify_payment_schema = {
    'summary': 'Verify a payment',
    'description': 'Verifies a payment using the payment reference. \
        The payment reference will be passed as part of the url path.',
    'tags': ['Payment'],
    'operation_id': 'verify_payment',
    'request': None,
    'responses': {
        200: make_success_schema_response(
            'Payment is (not) verified.', 
            PaymentSerializer),
        401: make_unauthorized_error_schema_response(),
        403: ForbiddenSerializer,
        404: make_error_schema_response(vf_errors)
    }
}
