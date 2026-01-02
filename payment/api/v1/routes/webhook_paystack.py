from drf_spectacular.utils import extend_schema
from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

import hmac, hashlib, json

from common.exceptions import ErrorException
from common.utils.api_responses import SuccessAPIResponse
from payment.models import Payment
from payment.api.v1.swagger import paystack_webhook_schema
from payment.tasks import verify_paystack_payment


@method_decorator(csrf_exempt, name='dispatch')
class PaystackWebhookView(APIView):
    """
    Webhook to catch successful payments events triggered by Paystack.
    """
    permission_classes = [AllowAny]

    @extend_schema(**paystack_webhook_schema)
    def post(self, request):
        # Check if the request is a valid Paystack webhook
        signature = request.headers.get('x-paystack-signature')
        computed = hmac.new(
            settings.PAYSTACK_SECRET_KEY.encode(),
            request.body,
            hashlib.sha512
        ).hexdigest()
        if computed != signature:
            raise ErrorException(detail="Invalid signature.", code='invalid_signature')

        event = json.loads(request.body)
        if event.get('event') == 'charge.success':
            data = event.get('data')
            # perform verification of the payment in the background
            verify_paystack_payment.delay(data=data)

        return Response(SuccessAPIResponse(
            message="Webhook processed successfully."
        ).to_dict(), status=status.HTTP_200_OK)