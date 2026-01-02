from common.swagger import (
    make_error_schema_response,
    make_success_schema_response
)


# VERIFY EMAIL ADDRESS SCHEMA

verify_email_errors = {
    'Missing token': 'Token not provided',
    'Invalid token': 'Invalid or expired token.'
}

verify_email_schema = {
    'summary': 'Verify Email',
    'description': 'Verifies the email address using a token.',
    'tags': ['Auth'],
    'request': None,
    'responses': {
        200: make_success_schema_response("Email verified successfully."),
        400: make_error_schema_response(
            errors=verify_email_errors,
            code='verification_error'
        )
    }
}
