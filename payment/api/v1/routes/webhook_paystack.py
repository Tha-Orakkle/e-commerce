import hashlib
import hmac
import json

from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from common.exceptions import ErrorException
from common.utils.api_responses import SuccessAPIResponse
from payment.api.v1.swagger import paystack_webhook_schema
from payment.tasks import verify_payment_task


@method_decorator(csrf_exempt, name='dispatch')
class PaystackWebhookView(APIView):
    """
    Webhook to catch successful payments events triggered by Paystack.
    """
    permission_classes = [AllowAny]  # noqa: RUF012

    def _extract_reference(self, event):
        data = event.get("data")
        return data.get("reference")        

    @extend_schema(**paystack_webhook_schema)
    def post(self, request):
        # Check if the request is a valid Paystack webhook
        signature = request.headers.get('x-paystack-signature')
        computed = hmac.new(
            settings.PAYSTACK.get("SECRET_KEY").encode(),
            request.body,
            hashlib.sha512
        ).hexdigest()
        if computed != signature:
            raise ErrorException(
                detail="Rejected.",
                code='invalid_signature'
            )

        event = json.loads(request.body)
        if event.get('event') == 'charge.success':
            reference = self._extract_reference(event)
            # perform verification of the payment in the background
            verify_payment_task.delay(reference=reference)

        return Response(SuccessAPIResponse(
            message="Accepted."
        ).to_dict(), status=status.HTTP_200_OK)