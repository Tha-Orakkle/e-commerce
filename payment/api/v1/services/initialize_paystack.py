from drf_spectacular.utils import extend_schema
from django.conf import settings
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
from payment.serializers.swagger import initialize_payment_schema


class InitializePaymentView(APIView):
    """
    Initialize Payment (Paystack).
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(**initialize_payment_schema)
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
        try:
            response = requests.post(
                settings.PAYSTACK_INITIALIZE_URL,
                json=data,
                headers=headers,
                timeout=5
            )
            response.raise_for_status()
            res_json = response.json()
        except requests.RequestException as e:
            raise ErrorException(f"Paystack request failed: {str(e)}.")
        except ValueError:
            raise ErrorException("Invalid response from Paystack.")

        if response.status_code != 200 or not res_json.get('status', False):
            raise ErrorException(res_json.get('message', 'Paystack error.'))
        
        return Response(SuccessAPIResponse(
            message="Payment initialized successfully.",
            data={'authorization_url': res_json['data']['authorization_url']}
        ).to_dict(), status=status.HTTP_200_OK)