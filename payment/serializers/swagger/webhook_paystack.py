from common.swagger import (
    get_success_response,
    get_error_response,
)

# SWAGGER SCHEMAS FOR PAYSTACK WEBHOOK
paystack_webhook_schema = {
    'summary': 'Paystack Webhook',
    'description': 'Webhook to catch successful payments events triggered by Paystack.',
    'tags': ['Paystack-Webhook'],
    'operation_id': 'paystack_webhook',
    'request': None,
    'responses': {
        200: get_success_response('Webhook processed successfully.'),
        400: get_error_response('Invalid signature.', 400),
    }
}