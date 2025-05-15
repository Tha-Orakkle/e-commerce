from common.swagger import (
    get_success_response,
    get_error_response
)


# SWAGGER SCHEMA FOR TOKEN REFRESH
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
        400: get_error_response('Refresh token was not provided. \nOR\n Invalid refresh token.')
    }
}
