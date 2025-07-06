from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from common.exceptions import ErrorException
from common.utils.api_responses import SuccessAPIResponse
from common.utils.check_valid_uuid import validate_id
from common.utils.pagination import Pagination
from order.models import Order
from order.serializers.order import OrderSerializer
from order.serializers.swagger import (
    get_orders_schema,
    get_user_orders_schema,
    get_user_order_schema
)
from order.utils.ordering_filter import SmartOrderingFilter


class OrdersView(APIView):
    """
    Gets all orders sorted by the ordering parameters passed and
    filtered by the stat
    """
    permission_classes = [IsAdminUser]

    filter_backends = [DjangoFilterBackend, SmartOrderingFilter]
    ordering_fields = ['created_at', 'status'] # will add amount later
    filterset_fields = ['status']

    def get_queryset(self):
        return Order.objects.all()

    @extend_schema(**get_orders_schema)
    def get(self, request):
        queryset = self.get_queryset()

        # apply filters
        for backend in self.filter_backends:
            queryset = backend().filter_queryset(request, queryset, self)

        # paginate
        paginator = Pagination()
        paginated_queryset = paginator.paginate_queryset(queryset, request, view=self)

        serializers = OrderSerializer(paginated_queryset, many=True)

        return Response(SuccessAPIResponse(
            message="All orders retrieved successfully.",
            code=status.HTTP_200_OK,
            data=paginator.get_paginated_response(serializers.data).data
        ).to_dict(), status=status.HTTP_200_OK)


class UserOrdersView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(**get_user_orders_schema)
    def get(self, request):
        """
        Get a list of user's order 
        """
        paginator = Pagination()
        queryset = request.user.orders.all()
        paginated_queryset = paginator.paginate_queryset(queryset, request)
        serializers = OrderSerializer(paginated_queryset, many=True)
        return Response(SuccessAPIResponse(
            message="User orders retrieved successfully.",
            code=status.HTTP_200_OK,
            data=paginator.get_paginated_response(serializers.data).data
        ).to_dict(), status=status.HTTP_200_OK)


class UserOrderView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(**get_user_order_schema)
    def get(self, request, order_id):
        """
        Get a specific order.
        """
        validate_id(order_id, 'order')
        order = Order.objects.filter(id=order_id).first()
        if not order or (order and order.user != request.user and not request.user.is_superuser):
            raise ErrorException('Order not found', code=status.HTTP_404_NOT_FOUND)
        serializer = OrderSerializer(order)
        return Response(SuccessAPIResponse(
            message="Order retrieved successfully.",
            data=serializer.data
        ).to_dict(), status=status.HTTP_200_OK)
