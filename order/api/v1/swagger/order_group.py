from common.swagger import (
    build_invalid_id_error,
    ForbiddenSerializer,
    make_error_schema_response,
    make_success_schema_response,
    make_unauthorized_error_schema_response,
    make_not_found_error_schema_response
)

from order.api.v1.serializers import OrderGroupSerializer, OrderGroupListSerializer



# CUSTOMER ORDER GROUPS SCHEMA
get_order_groups_schema = {
    'summary': "Get paginated list of user's order groups",
    'description': "Returns a paginated list of all user's order groups.",
    'tags': ['Order'],
    'operation_id': 'get_order_groups',
    'request': None,
    'responses': {
        200: make_success_schema_response(
            "User order groups retrieved successfully.",
            OrderGroupListSerializer,
            many=True,
            paginated=True
        ),
        401: make_unauthorized_error_schema_response(),
        403: ForbiddenSerializer
    }
}

get_order_group_schema = {
    'summary': "Get a user's specific order group",
    'description': "Takes an order group id as part of the url and returns the matching order.",
    'tags': ['Order'],
    'operation_id': 'get_order_group',
    'request': None,
    'responses': {
        200: make_success_schema_response(
            "Order group retrieved successfully.",
            OrderGroupSerializer
        ),
        400: make_error_schema_response(errors=build_invalid_id_error('order group')),
        401: make_unauthorized_error_schema_response(),
        404: make_not_found_error_schema_response(['order group'])
    }
}
