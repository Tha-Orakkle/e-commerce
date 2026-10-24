from datetime import timedelta

from django.db import transaction
from django.utils.timezone import now
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from common.cores.validators import validate_id
from common.exceptions import ErrorException
from common.permissions import IsCustomer
from common.utils.api_responses import SuccessAPIResponse
from order.api.v1.swagger import cancel_customer_order_group_schema
from order.models import Order, OrderGroup, OrderGroupStatus, OrderStatus
from order.tasks import restock_inventory_with_cancelled_order
from payment.models import Payment, PaymentStatus


class CancelCustomerOrderGroupView(APIView):
    permission_classes = [IsCustomer]  # noqa: RUF012

    def get_object(self, group_id):
        user = self.request.user
        if user.is_superuser:
            return OrderGroup.objects.filter(id=group_id).first()
        return user.order_groups.filter(id=group_id).first()

    @extend_schema(**cancel_customer_order_group_schema)
    def post(self, request, order_group_id):
        """
        Cancel an order group by a user as long as it has not been
        processed and not more than 4 hours.
        """
        validate_id(order_group_id, 'order group')
        o_group = self.get_object(order_group_id)
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
                code='cancellation_time_expired'
            )
        with transaction.atomic():
            payment = (
                Payment.objects
                .select_for_update()
                .filter(order_group=o_group)
                .first()
            )
            o_group = (
                OrderGroup.objects.select_for_update().get(id=order_group_id)
            )

            timestamp = now()
            o_group.status = OrderGroupStatus.CANCELLED
            o_group.cancelled_at = timestamp
            o_group.save()

            orders = list(o_group.orders.all())
            for order in orders:
                order.status = OrderStatus.CANCELLED
                order.cancelled_at = timestamp
            Order.objects.bulk_update(
                orders,
                ["status", "cancelled_at", "updated_at"]
            )

            if (
                payment is not None
                and payment.status == PaymentStatus.VERIFIED
            ):
                payment.refund_requested = True
                payment.save(update_fields=["refund_requested", "updated_at"])
            transaction.on_commit(
                lambda: restock_inventory_with_cancelled_order.delay(
                    str(o_group.id), order_group=True
                )
            )

        # restock_inventory_with_cancelled_order.delay(order.id)
        return Response(SuccessAPIResponse(
            message=(
                "Order cancelled. A refund will be processed shortly "
                "if payment was already made."
            )
        ).to_dict(), status=status.HTTP_200_OK)
