from drf_spectacular.utils import OpenApiParameter, OpenApiTypes

from common.swagger import (
    get_success_response,
    get_error_response,
    get_error_response_with_examples
)
from address.api.v1.serializers import CitySerializer

# SWAGGER SCHEMAS FOR CITY
get_cities_schema = {
    'summary': 'Get all cities of a state',
    'description': 'Returns a list of all cities within the state associated with the id passed as query parameter',
    'tags': ['location'],
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
        200: get_success_response("Cities retrieved successfully.", 200, CitySerializer(many=True)),
        400: get_error_response("Invalid state id."),
        401: get_error_response_with_examples(code=401)
    }
}