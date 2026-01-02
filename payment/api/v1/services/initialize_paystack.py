from drf_spectacular.utils import extend_schema
from django.conf import settings
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

import requests
import uuid

from common.cores.validators import validate_id
from common.exceptions import ErrorException
from common.permissions import IsCustomer
from common.utils.api_responses import SuccessAPIResponse
from payment.models import Payment
from payment.api.v1.swagger import initialize_payment_schema


class InitializePaystackView(APIView):
    """
    Initialize Payment (Paystack).
    """
    permission_classes = [IsCustomer]
    
    @extend_schema(**initialize_payment_schema)
    def post(self, request, order_group_id):
        validate_id(order_group_id, "order group")
        
        o_grp = request.user.order_groups.filter(id=order_group_id).first()
        if not o_grp:
            raise ErrorException(
                detail="No order group matching the given ID found.",
                code='not_found',
                status_code=status.HTTP_404_NOT_FOUND
            )

        # payment can only be created for delivery payment method 
        if o_grp.payment_method == 'CASH':
            raise ErrorException(
                detail="Cash payment method does not require Paystack initialization.",
                code='not_allowed',
            )

        if o_grp.status != 'PENDING':
            raise ErrorException(
                detail="Only pending order groups can be paid for.",
                code='invalid_status',
            )
        
        # create payment
        payment = Payment.objects.filter(order_group=o_grp).first()
        if not payment:
            payment = Payment.objects.create(
                email=request.user.email,
                amount=o_grp.total_amount * 100, # convert to kobo
                order_group=o_grp
            )
        elif payment and payment.verified:
            raise ErrorException(
                detail="Payment has already been verified.",
                code='duplicate_transaction'
            )
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
            raise ErrorException(detail=f"Paystack request failed: {str(e)}.", code='paystack_error')
        except ValueError:
            raise ErrorException(detail="Invalid response from Paystack.", code='paystack_error')
        
        if response.status_code != 200 or not res_json.get('status', False):
            raise ErrorException(
                detail=res_json.get('message', 'Paystack error.'),
                code='paystack_error'
            )
        
        return Response(SuccessAPIResponse(
            message="Payment initialized successfully.",
            data={'authorization_url': res_json['data']['authorization_url']}
        ).to_dict(), status=status.HTTP_200_OK)