from common.swagger import (
    get_success_response,
    get_error_response_with_examples
)


# SWAGGER SCHEMA FOR TOKEN REFRESH
token_refresh_error_examples = {
    'Missing refresh token': 'Refresh token was not provided.',
    'Invalid refresh token': 'Invalid refresh token.'

}

token_refresh_schema = {
    'summary': 'Refresh access token',
    'description':'Refresh access token using refresh token. \
        The refresh token will be passed as a cookie and a new access \
        token will be returned as cookie.',
    'tags': ['Auth'],
    'operation_id': 'token_refresh',
    'request': None,
    'responses': {
        200: get_success_response('Token refreshed successfully', 200),
        400: get_error_response_with_examples(examples=token_refresh_error_examples)
    }
}
