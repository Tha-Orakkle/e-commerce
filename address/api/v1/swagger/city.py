from drf_spectacular.utils import OpenApiParameter, OpenApiTypes

from address.api.v1.serializers import CitySerializer
from common.swagger import (
    make_success_schema_response,
    make_error_schema_response,
    make_unauthorized_error_schema_response
)

# SWAGGER SCHEMAS FOR CITY

errors = {
    'invalid_uuid': 'Invalid state id.',
    'missing_state': 'State ID is required to retrievd asociated cities.'
}
get_cities_schema = {
    'summary': 'Get all cities of a state',
    'description': 'Returns a list of all cities within the state associated with the id passed as query parameter',
    'tags': ['Location'],
    'operation_id': 'get_cities',
    'parameters': [OpenApiParameter(
        name='state',
        type=OpenApiTypes.UUID,
        description='The id of a state',
        location=OpenApiParameter.QUERY,
        required=True
    )],
    'request': None,
    'responses': {
        200: make_success_schema_response(
            "Cities retrieved successfully.", 
            CitySerializer, many=True),
        400: make_error_schema_response(errors),
        401: make_unauthorized_error_schema_response()
    }
}