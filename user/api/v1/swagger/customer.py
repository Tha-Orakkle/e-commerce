from common.swagger import (
    build_invalid_id_error,
    ForbiddenSerializer,
    make_error_schema_response,
    make_success_schema_response,
    make_not_found_error_schema_response,
    make_unauthorized_error_schema_response
)
from user.api.v1.serializers import UserSerializer



get_customers_schema = {
    'summary': 'Get paginated list of all customers',
    'description': 'Returns a paginated list of customers. \
        Only accessible to super users.',
    'tags': ['Customer'],
    'operation_id': 'get_customers',
    'request': None,
    'responses': {
        200: make_success_schema_response(
            "Customers retrieved successfully.", 
            UserSerializer, 
            many=True,
            paginated=True
        ),
        401: make_unauthorized_error_schema_response(),
        403: ForbiddenSerializer
    }
}

get_customer_schema = {
    'summary': 'Get a customer',
    'description': 'Get a customer by the ID passed in the URL \
        Customers can only access their data. Only super users can \
        can access all customers data.',
    'tags': ['Customer'],
    'operation_id': 'get_customer',
    'request': None,
    'responses': {
        200: make_success_schema_response(
            "Customer retrieved successfully.",
            UserSerializer),
        400: make_error_schema_response(errors=build_invalid_id_error('customer')),
        401: make_unauthorized_error_schema_response(),
        403: ForbiddenSerializer,
        404: make_not_found_error_schema_response(['customer']),
    }
}


delete_customer_schema = {
    'summary': 'Delete a customer',
    'description': 'Delete a customer matching the ID passed in url. \
        Where the customer is also a shopowner, only the customer access is revoked. \
        Customer can only delete their data. Super users can delete any customers account.',
    'tags': ['Customer'],
    'operation_id': 'delete_customer',
    'request': None,
    'responses': {
        204: {},
        400: make_error_schema_response(errors=build_invalid_id_error('customer')),
        401: make_unauthorized_error_schema_response(),
        403: ForbiddenSerializer,
        404: make_not_found_error_schema_response(['customer'])
    }
}
