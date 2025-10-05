from drf_spectacular.utils import OpenApiParameter, OpenApiTypes
from rest_framework import serializers

from common.swagger import (
    get_error_response,
    get_error_response_with_examples,
    get_success_response,
    ForbiddenSerializer,
    build_invalid_id_error,
    make_success_schema_response,
    make_unauthorized_error_schema_response,
    make_not_found_error_schema_response,
    make_error_schema_response
)
from order.api.v1.serializers import OrderSerializerForShop
 

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

get_shop_orders_schema = {
    'summary': 'Get all orders for a shop',
    'description': 'Get orders for a shop. Orders retrieved will be sorted by the ordering \
        parameters passed and filtered by the status passed.',
    'tags': ['Order'],
    'operation_id': 'get_shop_orders',
    'parameters': [
        OpenApiParameter(
            name='status',
            type=OpenApiTypes.STR,
            description="Filter orders by status. \
                e.g. 'pending', 'processing', 'completed', 'cancelled', 'failed'.",
            location=OpenApiParameter.QUERY,
            required=False
        ),
        OpenApiParameter(
            name='ordering',
            type=OpenApiTypes.STR,
            description="Ordering parameters to sort the orders by. \
                e.g. 'created_at', '-status'. \
                Prefix with '-' to sort in descending order.",
            location=OpenApiParameter.QUERY,
            required=False
        )
    ],
    'request': None,
    'responses': {
        200: make_success_schema_response(
            'All orders retrieved successfully.',
            OrderSerializerForShop,
            many=True,
            paginated=True
            ),
        401: make_unauthorized_error_schema_response(),
        403: ForbiddenSerializer
    },
}



id_error = build_invalid_id_error('order')

get_shop_order_schema = {
    'summary': 'Get a specific order for a shop',
    'description': 'Get a specific order for a shop by the ID passed in the url',
    'tags': ['Order'],
    'operation_id': 'get_shop_order',
    'request': None,
    'responses': {
        200: make_success_schema_response(
            'Order retrieved successfully.',
            OrderSerializerForShop
        ),
        400: make_error_schema_response(errors=id_error),
        401: make_unauthorized_error_schema_response(),
        403: ForbiddenSerializer,
        404: make_not_found_error_schema_response(['order'])
    }
    
}


shop_update_status_errors = {
    **id_error,
    'invalid_status': 'Invalid status provided.',
    'invalid_status_transition': [
        'Invalid transition from <old_status> to <new_status>.',
        'PICKUP orders can not  be shipped.'
    ],
    'invalid_payment_status': [
        'Digital orders must be paid before transition.',
        'Cash orders must be marked paid before completing.'
    ],
    'missing_field': 'Delivery date is required for DELIVERY orders ready to be shipped.',
    'invalid_date_format': 'Invalid date format. Use ISO format (YYYY-MM-DD).',
    'invalid_delivery_date': 'Delivery date cannot be in the past.'
}

update_shop_order_status_schema = {
    'summary': 'Update order status by staff',
    'description': 'Allows staff to update the status of an order. \
        e.g from "PENDING" -> "PROCESSING" -> "SHIPPED" -> "COMPLETED" for orders to be delivered, \
        or from "PENDING" -> "PROCESSING" -> "COMPLETED" for self pickup orders. \
        or "PENDING" -> "CANCELLED" for orders that are cancelled.',
    'tags': ['Order'],
    'operation_id': 'update_shop_order_status',
    'request': AdminUpdateOrderStatusRequest,
    'responses': {
        200: make_success_schema_response(
            "Order status updated to <new_status>.",
            OrderSerializerForShop
        ),
        400: make_error_schema_response(errors=shop_update_status_errors),
        401: make_unauthorized_error_schema_response(),
        403: ForbiddenSerializer,
        404: make_not_found_error_schema_response(['order'])
    }
}