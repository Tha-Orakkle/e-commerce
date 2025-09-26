from drf_spectacular.utils import extend_schema
from django.db import transaction
from django.utils.timezone import now
from rest_framework import status
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from common.exceptions import ErrorException
from common.utils.api_responses import SuccessAPIResponse
from common.utils.bools import parse_bool
from common.utils.check_valid_uuid import validate_id
from order.serializers.swagger import admin_update_order_status_schema
from order.utils.delivery import validate_delivery_date
from order.utils.validators import validate_order
from order.models import Order


class AdminUpdateOrderStatus(APIView):
    """
    Admin endpoint to update order status.
    """
    permission_classes = [IsAdminUser]

    @extend_schema(**admin_update_order_status_schema)
    def post(self, request, order_id):
        """
        Update the status of an order.
        """
        validate_id(order_id, 'order')
        order = Order.objects.filter(id=order_id).first()
        if not order:
            raise ErrorException("Order not found.", code=status.HTTP_404_NOT_FOUND)
        payment = order.payment if hasattr(order, 'payment') else None
        
        new_status = request.data.get('status', '').strip().upper()
        payment_status = parse_bool(request.data.get('payment_status', None))
        validate_order(new_status, order, payment_status)
        update_fields = ['status']
    
        update_datetime = now()

        if new_status == 'PROCESSING':
            order.status = new_status
            if not order.processing_at:
                order.processing_at = update_datetime
                update_fields.append('processing_at')
        elif new_status == 'SHIPPED':
            order.status = new_status
            if not order.shipped_at:
                order.shipped_at = update_datetime
                update_fields.append('shipped_at')
            delivery_date = request.data.get('delivery_date')
            validated_date = validate_delivery_date(delivery_date)
            order.delivery_date = validated_date
            update_fields.append('delivery_date')
        elif new_status == 'COMPLETED': 
            order.status = new_status
            if order.payment_method == 'CASH' and not order.is_paid:
                order.is_paid = payment_status # value is already validated for this
                update_fields.append('is_paid')
            if order.fulfillment_method == 'PICKUP':
                order.is_picked_up = True
                update_fields.append('is_picked_up')
            elif order.fulfillment_method == 'DELIVERY':
                order.is_delivered = True
                update_fields.append('is_delivered')

            if not order.completed_at:
                order.completed_at = update_datetime
                update_fields.append('completed_at')
        elif new_status == 'CANCELLED':
            order.status = new_status
            if not order.cancelled_at:
                order.cancelled_at = update_datetime
                update_fields.append('cancelled_at')
                # add logic to restock inventory from order items
                # this will only apply once. since the order.cancelled_at field will be set only once
                if order.payment_method == 'DIGITAL' and payment and payment.verified:
                    order.payment.refund_requested = True
        else:
            raise ErrorException("Invalid status provided.")
        
        with transaction.atomic():
            order.save(update_fields=update_fields)
            if payment and payment.verified:
                payment.save(update_fields=['refund_requested'])
        return Response(SuccessAPIResponse(
            message=f"Order status updated to {new_status}."
        ).to_dict(), status=status.HTTP_200_OK)