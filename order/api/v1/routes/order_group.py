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

    @extend_schema(**get_order_groups_schema)
    def get(self, request):
        """
        Get a list of user's order groups 
        """
        paginator = Pagination()
        queryset = request.user.order_groups.all()
        paginated_queryset = paginator.paginate_queryset(queryset, request)
        serializers = OrderGroupListSerializer(paginated_queryset, many=True)
        return Response(SuccessAPIResponse(
            message="User order groups retrieved successfully.",
            data=paginator.get_paginated_response(serializers.data).data
        ).to_dict(), status=status.HTTP_200_OK)


class CustomerOrderGroupView(APIView):
    permission_classes = [IsCustomer]

    @extend_schema(**get_order_group_schema)
    def get(self, request, order_group_id):
        """
        Get a specific order group.
        """
        validate_id(order_group_id, 'order group')
        o_grp = OrderGroup.objects.filter(id=order_group_id).first()
        if not o_grp or (o_grp and o_grp.user != request.user and not request.user.is_superuser):
            raise ErrorException(
                detail="No order group matching the given ID found.",
                code='not_found',
                status_code=status.HTTP_404_NOT_FOUND
            )
        serializer = OrderGroupSerializer(o_grp)
        return Response(SuccessAPIResponse(
            message="Order group retrieved successfully.",
            data=serializer.data
        ).to_dict(), status=status.HTTP_200_OK)
