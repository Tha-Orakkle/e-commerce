from common.swagger import (
    get_success_response,
    UnauthorizedSerializer
)

logout_schema = {
    'summary': 'Logout user',
    'description': 'Logs out the user by deleting the session cookie.',
    'tags': ["Auth"],
    'operation_id': 'user_logout',
    'request': None,
    'responses': {
        200: get_success_response('User logged out successfully.', 200),
        401: UnauthorizedSerializer
    }
}