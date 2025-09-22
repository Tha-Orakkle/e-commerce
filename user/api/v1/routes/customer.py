from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from common.utils.api_responses import SuccessAPIResponse
from common.exceptions import ErrorException
from common.permissions import IsCustomer, IsSuperUser
from common.utils.check_valid_uuid import validate_id
from common.utils.pagination import Pagination
from user.api.v1.serializers import UserSerializer
from user.api.v1.swagger import (
    delete_user_schema,
    get_user_schema,
    get_users_schema,
)
from user.models import User


class CustomerListView(APIView):
    permission_classes = [IsSuperUser]

    @extend_schema(**get_users_schema)
    def get(self, request):
        """
        Gets all customers.
        Only accessible by super users.
        """
        paginator = Pagination()
        queryset = User.objects.get_customers()
        paginated_queryset = paginator.paginate_queryset(queryset, request)
        serializers = UserSerializer(paginated_queryset, many=True)
        data = paginator.get_paginated_response(serializers.data).data
        return Response(
            SuccessAPIResponse(
                message="Customers retrieved successfully.",
                data=data
            ).to_dict(), status=200
        )


class CustomerDetailView(APIView):
    permission_classes = [IsCustomer]

    @extend_schema(**get_user_schema)
    def get(self, request, customer_id):
        """
        Gets a specific user.
        """
        validate_id(customer_id, "customer")
        user = User.objects.filter(id=customer_id, is_customer=True).first()
        if not user:
            raise ErrorException(
                detail="No customer found with the given ID.",
                code="not_found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        if not (user == request.user or request.user.is_superuser):
            raise PermissionDenied()

        return Response(
            SuccessAPIResponse(
                message='Customer retrieved successfully.',
                data=UserSerializer(user).data
            ).to_dict()
        )

    @extend_schema(**delete_user_schema)
    def delete(self, request, customer_id):
        """
        Delete a customer.
        """
        validate_id(customer_id, "customer")
        user = User.objects.filter(id=customer_id, is_customer=True).first()
        if not user:
            raise ErrorException(
                detail="No customer found with the given ID.",
                code="not_found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        if not (user == request.user or request.user.is_superuser):
            raise PermissionDenied()
        user.delete()
        return Response({}, status=status.HTTP_204_NO_CONTENT)
