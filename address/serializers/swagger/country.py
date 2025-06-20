from common.swagger import (
    get_error_response_with_examples,
    get_success_response,
)
from address.serializers.country import CountrySerializer

# SWAGGER SCHEMAS FOR COUNTRY
get_countries_schema = {
    'summary': 'Get all supported countries.',
    'description': 'Returns a list of all supported countries.',
    'tags': ['location'],
    'operation_id': 'get_countries',
    'request': None,
    'responses': {
        200: get_success_response("Countries retrieved successfully.", 200, CountrySerializer(many=True)),
        401: get_error_response_with_examples(code=401)
    }

}