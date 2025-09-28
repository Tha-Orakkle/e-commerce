from rest_framework import serializers

from common.swagger import (
    get_success_response,
    get_error_response_with_examples
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


checkout_error_examples = {
    'Empty cart': 'Cart is empty.',
    'Invalid items': 'Cart contains invalid items.',
    'Insuffucient stock': 'Insufficient stock for <product_name>. Only <stock> left.',
    'Invalid fulfillment method': 'Invalid fulfillment method.',
    'Invalid payment method': 'Invalid payment method.',
}

checkout_schema = {
    'summary': 'Checkout Order',
    'description': 'Process the checkout of the current user\'s cart, \
        creating an order and handling payment. Fulfillment method in the \
        request body can be \'PICKUP\' or \'DELIVERY\'. Payment method can \
        be \'CASH\' or \'DIGITAL\'',
    'operation_id': 'checkout',
    'tags': ['Checkout'],
    'request': CheckoutRequestData,
    'responses': {
        200: get_success_response('Checkout successful. Order has been created.', 200, OrderGroupSerializer()),
        400: get_error_response_with_examples(examples=checkout_error_examples),
        401: get_error_response_with_examples(code=401),
    }
}