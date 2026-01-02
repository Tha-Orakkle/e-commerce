from common.swagger import (
    build_invalid_id_error,
    ForbiddenSerializer,
    make_success_schema_response,
    make_error_schema_response,
    make_not_found_error_schema_response,
    make_unauthorized_error_schema_response
)


# SWAGGER SCHEMAS FOR CANCEL ORDER

cancel_order_group_errors = {
    **build_invalid_id_error('order group'),
    'order_already_processed': 'Only pending order groups can be cancelled.',
    'cancellation_time_expired': 'Order cannot be cancelled after 4 hours of creation.',
    
}

cancel_customer_order_group_schema = {
    'summary': 'Cancel an order group',
    'description': 'Allows a user to cancel an order group where none of the \
        orders in the group has been processed and group is still within 4 hours of creation.',
    'tags': ['Order'],
    'operation_id': 'cancel_order_group',
    'request': None,
    'responses': {
        200: make_success_schema_response(
           "Order cancelled. A refund will be processed shortly if payment was already made."),
        400: make_error_schema_response(errors=cancel_order_group_errors),
        401: make_unauthorized_error_schema_response(),
        403: ForbiddenSerializer,
        404: make_not_found_error_schema_response(['order group'])
    }
}
