from common.swagger import (
    get_error_response_with_examples,
    get_success_response
)


# SWAGGER SCHEMAS FOR VERIFY EMAIL ADDRESS

# schema
verify_email_error_examples = {
    'Missing token': 'Token not provided',
    'Invalid token': 'Invalid or expired token.'
}
verify_email_schema = {
    'summary': 'Verify Email',
    'description': 'Verifies the email address using a token.',
    'tags': ['Auth'],
    'request': None,
    'responses': {
        200: get_success_response('Email verified successfully.', 200),
        400: get_error_response_with_examples(examples=verify_email_error_examples)
    }
}