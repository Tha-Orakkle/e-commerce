from common.swagger import (
    get_success_response,
    get_error_response_with_examples
)
from order.serializers.order import OrderSerializer

# SWAGGER SCHEMAS FOR CHECKOUT
checkout_error_examples = {
    'Empty cart': 'Cart is empty.',
    'Invalid items': 'Cart contains invalid items.',
    'Insuffucient stock': 'Insufficient stock for <product_name>. Only <stock> left.',
}

checkout_schema = {
    'summary': 'Checkout Order',
    'description': 'Process the checkout of the current user\'s cart, creating an order and handling payment.',
    'operation_id': 'checkout',
    'tags': ['Checkout'],
    'request': None, # wil be updated later to take the shipping/billing address
    'responses': {
        200: get_success_response('Checkout successful. Order has been created.', 200, OrderSerializer()),
        400: get_error_response_with_examples(examples=checkout_error_examples),
        401: get_error_response_with_examples(code=401),
    }
}