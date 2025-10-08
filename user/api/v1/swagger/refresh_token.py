from common.swagger import (
    make_success_schema_response,
    make_error_schema_response
)


# TOKEN REFRESH SCHEMA
token_refresh_errors = {
    'Missing refresh token': 'Refresh token was not provided.',
    'Invalid refresh token': 'Token is invalid or expired.',
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
        200: make_success_schema_response("Token refreshed successfully"),
        400: make_error_schema_response(
            errors=token_refresh_errors,
            code='authentication_error'
        )
    }
}
