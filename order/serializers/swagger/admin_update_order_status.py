from rest_framework import serializers

from common.swagger import (
    get_error_response,
    get_error_response_with_examples,
    get_success_response,
    ForbiddenSerializer
)

# SWAGGER SCHEMAS FOR ADMIN UPDATE ORDER STATUS

class AdminUpdateOrderStatusRequest(serializers.Serializer):
    status = serializers.CharField(
        required=True,
        help_text="New status for the order. Must be one of: 'PROCESSING', 'SHIPPED', 'COMPLETED', 'CANCELLED'."
    )
    payment_status = serializers.BooleanField(
        required=False,
        help_text="Indicates if the payment has been made. Required for 'COMPLETED' status if payment method is 'CASH'."
    )
    delivery_date = serializers.DateField(
        required=False,
        help_text="Expected delivery date for the order. Required if status is 'SHIPPED'."
    )


# schemas

admin_update_order_status_error_examples = {
    'Invalid status': 'Invalid status provided.',
    'Non-payment for digital orders before PROCESSING status request': 'Non-cash orders must be paid before processing order.',
    'Non-payment for digital orders before SHIPPED status request': 'Non-cash orders must be paid before shipping order.',
    'Non-payment for digital orders before COMPLETED status request': 'Non-cash orders must be paid before completing order.',
    'Non-payment for cash orders before COMPLETED status request': 'Cash orders must be paid before completing order. Please provide payment status.',
    
    
    
    'Unprocessed pickup order before COMPLETED status request': 'Order must be a processing order. Current status is PENDING.',
    'Unprocessed delivery order before SHIPPED status request': 'Order must be a processing order. Current status is PENDING.',
    'Unprocessed delivery order before COMPLETED status request': 'Order must be a shipped order. Current status is PENDING.',

    'Unshipped delivery order before COMPLETED status request': 'Order must be a shipped order. Current status is PROCESSING.',
    
    'Pickup order cannot be shipped': 'Pickup orders cannot be shipped.',
    'Invalid order status for cancellation': 'Order must be a pending or processing order. Current status is COMPLETED.',
    
}

admin_update_order_status_schema = {
    'summary': 'Update order status by admin',
    'description': 'Allows an admin to update the status of an order. \
        e.g from "PENDING" -> "PROCESSING" -> "SHIPPED" -> "COMPLETED" for orders to be delivered, \
        or from "PENDING" -> "PROCESSING" -> "COMPLETED" for self pickup orders. \
        or "PENDING" -> "CANCELLED" for orders that are cancelled.',
    'tags': ['Order'],
    'operation_id': 'admin_update_order_status',
    'request': AdminUpdateOrderStatusRequest,
    'responses': {
        200: get_success_response("Order status updated to PROCESSING."),
        400: get_error_response_with_examples(examples=admin_update_order_status_error_examples, code=400),
        401: get_error_response_with_examples(code=401),
        403: ForbiddenSerializer,
        404: get_error_response("Order not found.", 404)
    }
}