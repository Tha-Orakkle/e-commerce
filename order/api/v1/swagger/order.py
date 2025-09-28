from rest_framework import serializers
from drf_spectacular.utils import OpenApiParameter, OpenApiTypes


from common.swagger import (
    BasePaginatedResponse,
    get_success_response,
    get_error_response,
    get_error_response_with_examples,
    ForbiddenSerializer
)
from order.api.v1.serializers import OrderGroupSerializer, OrderGroupListSerializer

# SWAGGER SCHEMAS FOR ORDER

class OrderListResponse(BasePaginatedResponse):
    """
    Serializer for the paginated response of orders.
    """
    results = OrderGroupListSerializer(many=True)


# schemas
get_orders_schema = {
    'summary': 'Get all orders by admin',
    'description': 'Orders retrieved will be sorted by the ordering \
        parameters passed and filtered by the status passed.',
    'tags': ['Order'],
    'operation_id': 'get_orders',
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
        200: get_success_response('All orders retrieved successfully.', 200, OrderListResponse()),
        401: get_error_response_with_examples(code=401),
        403: ForbiddenSerializer
    },
}

get_user_orders_schema = {
    'summary': "Get a user's list of orders",
    'description': "Returns a paginated list of the user's orders.",
    'tags': ['Order'],
    'operation_id': 'get_user_orders',
    'request': None,
    'responses': {
        200: get_success_response("User orders retrieved successfully.", 200, OrderListResponse()),
        401: get_error_response_with_examples(code=401)
    }
}

get_user_order_schema = {
    'summary': "Get a user's specific order by order id",
    'description': "Takes an order id as part of the url and returns the matching order.",
    'tags': ['Order'],
    'operation_id': 'get_user_order',
    'request': None,
    'responses': {
        200: get_success_response("Order retrieved successfully.", 200, OrderGroupSerializer()),
        400: get_error_response('Invalid order id.', 400),
        401: get_error_response_with_examples(code=401),
        404: get_error_response('Order not found.', 404)
    }
}