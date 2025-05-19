from common.swagger import (
    get_error_response,
    get_success_response
)


# SWAGGER SCHEMAS FOR VERIFY EMAIL ADDRESS

# schema
verify_email_schema = {
    'summary': 'Verify Email',
    'description': 'Verifies the email address using a token.',
    'tags': ['Auth'],
    'request': None,
    'responses': {
        200: get_success_response('Email verified successfully.', 200),
        400: get_error_response('Invalid or expired token.', 400),
    }
}