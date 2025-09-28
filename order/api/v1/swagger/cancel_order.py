from common.swagger import (
    get_error_response,
    get_error_response_with_examples,
    get_success_response
)


# SWAGGER SCHEMAS FOR CANCEL ORDER

cancel_order_error_exmaples = {
    'Timeout': 'Order cannot be cancelled after 4 hours of creation.',
    'Order Processed': 'Processed orders cannot be cancelled.',
}

cancel_order_schema = {
    'summary': 'Cancel an order',
    'description': 'Allows a user to cancel an order that has not been processed and is within 4 hours of creation.',
    'tags': ['Order'],
    'operation_id': 'cancel_order',
    'request': None,
    'responses': {
        200: get_success_response(
            "Order cancelled successfully. A refund will be processed shortly if payment was already made."),
        400: get_error_response_with_examples(examples=cancel_order_error_exmaples, code=400),
        401: get_error_response_with_examples(code=401),
        404: get_error_response("Order not found.", 404)
    }
}