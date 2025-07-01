from django.conf import settings
from django.urls import reverse
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

import requests
import uuid

from common.exceptions import ErrorException
from common.utils.api_responses import SuccessAPIResponse
from common.utils.check_valid_uuid import validate_id
from payment.models import Payment


class InitializePaymentView(APIView):
    """
    Initiate Payment (Paystack).
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        order_id = request.data.get('order')
        validate_id(order_id, "order")
        order = request.user.orders.filter(id=order_id).first()
        if not order:
            raise ErrorException("Order not found.", code=status.HTTP_404_NOT_FOUND)
        
        # payment can only be created for delivery payment method 
        if order.payment_method == 'CASH':
            raise ErrorException("Cash payment method does not require Paystack initialization.", code=status.HTTP_400_BAD_REQUEST)
    
        # create payment
        payment = Payment.objects.filter(order=order).first()
        if not payment:
            payment = Payment.objects.create(
                email=request.user.email,
                amount=order.total_amount * 100, # convert to kobo
                order=order
            )
        elif payment and payment.verified:
            raise ErrorException("Payment has already been verified.", code=status.HTTP_400_BAD_REQUEST)
        else:
            payment.reference = uuid.uuid4()
            payment.save(update_fields=['reference'])        

        data = payment.to_dict()
        headers = {
            "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json"
        }
        response = requests.post(
            settings.PAYSTACK_INITIALIZE_URL,
            json=data,
            headers=headers,
            timeout=5
        )
        res_json = response.json()

        if response.status_code != 200 or res_json['status'] == False:
            raise ErrorException(res_json['message'])
        
        return Response(SuccessAPIResponse(
            message="Payment initiated successfully.",
            data={'authorization_url': res_json['data']['authorization_url']}
        ).to_dict(), status=status.HTTP_200_OK)