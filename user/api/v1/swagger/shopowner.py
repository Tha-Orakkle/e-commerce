from common.swagger import (
    build_invalid_id_error,
    ForbiddenSerializer,
    make_error_schema_response,
    make_success_schema_response,
    make_not_found_error_schema_response,
    make_unauthorized_error_schema_response
)
from user.api.v1.serializers import UserSerializer



get_shopowners_schema = {
    'summary': 'Get paginated list of all shop owners',
    'description': 'Returns a paginated list of shop owners. \
        Only accessible to super users.',
    'tags': ['Shop-Owner'],
    'operation_id': 'get_shopowners',
    'request': None,
    'responses': {
        200: make_success_schema_response(
            "Shop owners retrieved successfully.", 
            UserSerializer, 
            many=True,
            paginated=True
        ),
        401: make_unauthorized_error_schema_response(),
        403: ForbiddenSerializer
    }
}

get_shopowner_schema = {
    'summary': 'Get a shop owner',
    'description': 'Get a shop owner by the ID passed in the URL \
        Shop owners can only access their data. Only super users can \
        can access all shop owners data.',
    'tags': ['Shop-Owner'],
    'operation_id': 'get_shopowner',
    'request': None,
    'responses': {
        200: make_success_schema_response(
            "Shop owner retrieved successfully.",
            UserSerializer),
        400: make_error_schema_response(errors=build_invalid_id_error('shop owner')),
        401: make_unauthorized_error_schema_response(),
        403: ForbiddenSerializer,
        404: make_not_found_error_schema_response(['shop owner']),
    }
}
