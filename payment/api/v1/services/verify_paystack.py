from django.conf import settings
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

import requests

from common.exceptions import ErrorException
from common.utils.api_responses import SuccessAPIResponse
from order.models import Order
from payment.models import Payment


class VerifyPaymentView(APIView):
    """
    Verify payment (Paystack).
    """
    permission_classes = [AllowAny]

    def get(self, request):
        """"
        Verify payment from paystack.
        """
        reference = request.query_params.get('reference')

        payment = Payment.objects.filter(reference=reference).first()
        if not payment:
            raise ErrorException("Payment not found", code=status.HTTP_404_NOT_FOUND)
        
        verify_url = f"{settings.PAYSTACK_VERIFY_URL}{reference}"

        headers = {'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}'}
        response = requests.get(verify_url, headers=headers)
        res_json = response.json()
        if response.status_code != 200 or res_json['data']['status'] != 'success':
            raise ErrorException(res_json['message'])
        
        
        payment.verified = True
        payment.save()
        payment.order.payment_status = 'COMPLETED'
        payment.order.is_paid = True
        payment.order.save()
        return Response(SuccessAPIResponse(
            message="Payment successfully.",
        ).to_dict(), status=status.HTTP_200_OK)