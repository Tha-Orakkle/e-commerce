from common.swagger import (
    make_success_schema_response,
    make_unauthorized_error_schema_response,
)
from address.api.v1.serializers import CountrySerializer


# SWAGGER SCHEMAS FOR COUNTRY
get_countries_schema = {
    'summary': 'Get all supported countries.',
    'description': 'Returns a list of all supported countries.',
    'tags': ['Location'],
    'operation_id': 'get_countries',
    'request': None,
    'responses': {
        200: make_success_schema_response(
            "Countries retrieved successfully.",
            CountrySerializer, many=True),
        401: make_unauthorized_error_schema_response(),
    }
}
