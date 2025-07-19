from datetime import timedelta
from drf_spectacular.utils import extend_schema
from django.utils.timezone import now
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.exceptions import ErrorException
from common.utils.api_responses import SuccessAPIResponse
from common.utils.check_valid_uuid import validate_id
from order.serializers.swagger import cancel_order_schema
from order.tasks import restock_inventory_with_cancelled_order


class CancelOrderView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(**cancel_order_schema)
    def post(self, request, order_id):
        """
        Cancel an order by a user as long as it has not been
        processed and not more than 4 hours.
        """
        validate_id(order_id, 'order')
        order = request.user.orders.filter(id=order_id).first()
        if not order:
            raise ErrorException("Order not found.", code=status.HTTP_404_NOT_FOUND)
        if order.status != 'PENDING':
            raise ErrorException("Processed orders cannot be cancelled.", code=status.HTTP_400_BAD_REQUEST)
        if order.created_at < now() - timedelta(hours=4):
            raise ErrorException(
                "Order cannot be cancelled after 4 hours of creation.",
                code=status.HTTP_400_BAD_REQUEST
            )
        order.status = 'CANCELLED'
        order.cancelled_at = now()
        order.save()
    
        if order.payment_method == 'DIGITAL' and hasattr(order, 'payment') and order.payment.verified:
            order.payment.refund_requested = True
            order.payment.save()

        restock_inventory_with_cancelled_order.delay(order.id)
        return Response(SuccessAPIResponse(
            message="Order cancelled. A refund will be processed shortly if payment was already made."
        ).to_dict(), status=status.HTTP_200_OK)