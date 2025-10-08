from common.swagger import (
    make_success_schema_response,
    make_unauthorized_error_schema_response
)

# LOG OUT SCHEMA

logout_schema = {
    'summary': 'Log user out',
    'description': 'Logs user out by deleting the authentication cookies.',
    'tags': ["Auth"],
    'operation_id': 'logout',
    'request': None,
    'responses': {
        200: make_success_schema_response('Log out successful.'),
        401: make_unauthorized_error_schema_response(),
    }
}