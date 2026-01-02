from drf_spectacular.utils import OpenApiParameter, OpenApiTypes

from address.api.v1.serializers import StateSerializer
from common.swagger import (
    make_success_schema_response,
    make_unauthorized_error_schema_response,
    make_error_schema_response
)

# SWAGGER SCHEMAS FOR STATE

errors = {
    'missing_country': 'Country code (ISO2) is required to retrieve associated states.'
}
get_states_schema = {
    'summary': 'Get all states in a country',
    'description': 'Returns a list of all states in a country matching the iso 2 code passed as query parameter',
    'tags': ['Location'],
    'operation_id': 'get_states',
    'parameters': [OpenApiParameter(
        name='country',
        type=OpenApiTypes.STR,
        description='country code',
        location=OpenApiParameter.QUERY,
        required=True
    )],
    'request': None,
    'responses': {
        200: make_success_schema_response(
            "States retrieved successfully.",
            StateSerializer, many=True),
        400: make_error_schema_response(errors),
        401: make_unauthorized_error_schema_response()
    }
}
