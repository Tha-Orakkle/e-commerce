from drf_spectacular.utils import OpenApiParameter, OpenApiTypes

from address.api.v1.serializers import StateSerializer
from common.swagger import (
    get_error_response_with_examples,
    get_success_response
)

# SWAGGER SCHEMAS FOR STATE
get_states_schema = {
    'summary': 'Get all states in a country',
    'description': 'Returns a list of all states in a country matching the iso 2 code passed as query parameter',
    'tags': ['location'],
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
        200: get_success_response("States retrieved successfully.", 200, StateSerializer(many=True)),
        401: get_error_response_with_examples(code=401)
    }

}