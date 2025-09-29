from django.db import transaction
from datetime import timedelta
from drf_spectacular.utils import extend_schema
from django.utils.timezone import now
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from common.cores.validators import validate_id
from common.permissions import IsCustomer
from common.exceptions import ErrorException
from common.utils.api_responses import SuccessAPIResponse
from order.models import Order
from order.api.v1.swagger import cancel_order_schema
from order.tasks import restock_inventory_with_cancelled_order


class CancelCustomerOrderGroupView(APIView):
    permission_classes = [IsCustomer]

    @extend_schema(**cancel_order_schema)
    def post(self, request, order_group_id):
        """
    Cancel an order by a user as long as it has not been
        processed and not more than 4 hours.
        """
        validate_id(order_group_id, 'order group')
        o_group = request.user.order_groups.filter(id=order_group_id).first()
        if not o_group:
            raise ErrorException(
                detail="No order group matching the given ID found.",
                code='not_found',
                status_code=status.HTTP_404_NOT_FOUND)
        if o_group.status != 'PENDING':
            raise ErrorException(
                detail="Only pending order groups can be cancelled.",
                code='order_already_processed',
            )
        if o_group.created_at < now() - timedelta(hours=4):
            raise ErrorException(
                detail="Order cannot be cancelled after 4 hours of creation.",
                code='cancellation_time_expired',
            )
        with transaction.atomic():
            n = now()
            o_group.status = 'CANCELLED'
            o_group.cancelled_at = n
            o_group.save()
            
            orders = list(o_group.orders.all())
            for order in orders:
                order.status = 'CANCELLED'
                order.cancelled_at = n
            Order.objects.bulk_update(orders, ['status', 'cancelled_at'])
    
            if o_group.payment_method == 'DIGITAL' and hasattr(o_group, 'payment') and o_group.payment.verified:
                o_group.payment.refund_requested = True
                o_group.payment.save()
            transaction.on_commit(
                lambda: restock_inventory_with_cancelled_order.delay(str(o_group.id), order_group=True)
            )

        # restock_inventory_with_cancelled_order.delay(order.id)
        return Response(SuccessAPIResponse(
            message="Order cancelled. A refund will be processed shortly if payment was already made."
        ).to_dict(), status=status.HTTP_200_OK)
