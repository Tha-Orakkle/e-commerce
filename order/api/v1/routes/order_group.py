from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from common.cores.validators import validate_id
from common.exceptions import ErrorException
from common.permissions import IsCustomer
from common.utils.api_responses import SuccessAPIResponse
from common.utils.pagination import Pagination
from order.models import OrderGroup
from order.api.v1.serializers import (
    OrderGroupSerializer,
    OrderGroupListSerializer
)
from order.api.v1.swagger import (
    get_order_groups_schema,
    get_order_group_schema
)


class CustomerOrderGroupListView(APIView):
    permission_classes = [IsCustomer]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return OrderGroup.objects.all()
        return user.order_groups.all()

    @extend_schema(**get_order_groups_schema)
    def get(self, request):
        """
        Get a list of user's order groups 
        """
        paginator = Pagination()
        queryset = self.get_queryset()
        paginated_queryset = paginator.paginate_queryset(queryset, request)
        serializers = OrderGroupListSerializer(paginated_queryset, many=True)
        return Response(SuccessAPIResponse(
            message="User order groups retrieved successfully.",
            data=paginator.get_paginated_response(serializers.data).data
        ).to_dict(), status=status.HTTP_200_OK)


class CustomerOrderGroupView(APIView):
    permission_classes = [IsCustomer]
    
    def get_object(self, order_group_id):
        user = self.request.user
        if user.is_superuser:
            return OrderGroup.objects.filter(id=order_group_id).first()
        
        return user.order_groups.filter(id=order_group_id).first()

    @extend_schema(**get_order_group_schema)
    def get(self, request, order_group_id):
        """
        Get a specific order group.
        """
        validate_id(order_group_id, 'order group')

        order_group = self.get_object(order_group_id)
        if not order_group:
            raise ErrorException(
                detail="No order group matching the given ID found.",
                code='not_found',
                status_code=status.HTTP_404_NOT_FOUND
            )
        serializer = OrderGroupSerializer(order_group)
        return Response(SuccessAPIResponse(
            message="Order group retrieved successfully.",
            data=serializer.data
        ).to_dict(), status=status.HTTP_200_OK)
