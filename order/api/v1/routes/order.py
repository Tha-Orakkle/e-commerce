from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from django.utils.timezone import now
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from common.cores.validators import validate_id
from common.exceptions import ErrorException
from common.permissions import IsStaff
from common.utils.api_responses import SuccessAPIResponse
from common.utils.bools import parse_bool
from common.utils.pagination import Pagination
from order.api.v1.swagger import (
    admin_update_order_status_schema,
    get_orders_schema
)
from order.api.v1.serializers import OrderSerializerForShop
from order.api.v1.state_machine import OrderStateMachine
from order.models import Order
from order.tasks import restock_inventory_with_cancelled_order
from order.utils.ordering_filter import SmartOrdering, OrderFilter
from order.utils.validators import validate_order, validate_delivery_date


class ShopOrderView(APIView):
    """
    Gets all orders sorted by the ordering parameters and
    filtered by the status parameter. All passed as query strings.
    """
    permission_classes = [IsStaff]

    filter_backends = [DjangoFilterBackend, SmartOrdering]
    ordering_fields = ['created_at', 'status']
    filterset_class = OrderFilter

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Order.objects.all()
        if user.is_shopowner:
            shop = user.owned_shop
        else:
            shop = user.shop

        return shop.orders.all()            


    @extend_schema(**get_orders_schema)
    def get(self, request):
        queryset = self.get_queryset()

        # apply filters
        for backend in self.filter_backends:
            queryset = backend().filter_queryset(request, queryset, self)

        # paginate
        paginator = Pagination()
        paginated_queryset = paginator.paginate_queryset(queryset, request, view=self)

        serializers = OrderSerializerForShop(paginated_queryset, many=True)

        return Response(SuccessAPIResponse(
            message="All orders retrieved successfully.",
            data=paginator.get_paginated_response(serializers.data).data
        ).to_dict(), status=status.HTTP_200_OK)


class ShopOrderDetailView(APIView):
    permission_classes = [IsStaff]
    
    def get_object(self):
        user =  self.request.user
        o_id = self.kwargs.get('order_id')
        if user.is_superuser:
            return Order.objects.filter(id=o_id).first()
        if user.is_shopowner:
            shop = user.owned_shop
        else:
            shop = user.shop
    
        return shop.orders.filter(id=o_id).first()
    
    def get(self, request, order_id):
        """
        Get a specific order from a shop matching the given order ID.
        """
        validate_id(order_id, 'order')
        order = self.get_object()
        if not order:
            raise ErrorException(
                detail="No order matching the given ID found.",
                code='not_found',
                status_code=status.HTTP_404_NOT_FOUND
            )
        return Response(SuccessAPIResponse(
            message="Order retrieved successfully.",
            data=OrderSerializerForShop(order).data
        ).to_dict(), status=status.HTTP_200_OK)



class ShopOrderStatusUpdateView(APIView):
    """
    Admin endpoint to update order status.
    """
    permission_classes = [IsStaff]

    @extend_schema(**admin_update_order_status_schema)
    def post(self, request, order_id):
        """
        Update the status of an order.
        """
        validate_id(order_id, 'order')
        order = Order.objects.select_related('group__payment').filter(id=order_id).first()
        if not order:
            raise ErrorException(
                detail="No order matching the given ID found.",
                code='not_found',
                status_code=status.HTTP_404_NOT_FOUND
            )
            
        o_group = order.group
        payment_status = parse_bool(request.data.get('payment_status', False)) # needed for cash transactions
        new_status = request.data.get('status', '').strip().upper()
        delivery_date = request.data.get('delivery_date', None)
        
        order_state_machine = OrderStateMachine(
            order=order,
            group=o_group,
            payment_status=payment_status,
            delivery_date=delivery_date
        )
        order = order_state_machine.transition_to(new_status)

        return Response(SuccessAPIResponse(
            message=f"Order status updated to {new_status}.",
            data=OrderSerializerForShop(order).data
        ).to_dict(), status=status.HTTP_200_OK)
