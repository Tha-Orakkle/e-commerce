from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from common.utils.api_responses import SuccessAPIResponse
from common.exceptions import ErrorException
from common.permissions import IsCustomer
from common.cores.validators import validate_id
from order.models import OrderGroup, OrderGroupStatus, PaymentMethod
from payment.api.v1.serializers import InitializePaymentSerializer
from payment.api.v1.swagger import initialize_payment_schema
from payment.domain.exceptions import DuplicatePaymentError, PaymentProviderError


class InitializePaymentView(APIView):
    """
    Initialize Payment.
    """
    permission_classes = [IsCustomer]

    def get_order_group_object(self, id):
        """
        Get order group associated to the authenticated customer.
        Super user can get any order group.
        """
        user = self.request.user
        if user.is_superuser:
            return OrderGroup.objects.filter(id=id).first()

        return user.order_groups.filter(id=id).first()

    def validate_order_group_exists(self, order_group):
        """
        Validate order group exists.
        """
        if not order_group:
            raise ErrorException(
                detail="No order group matching the given ID found.",
                code="not_found",
                status_code=status.HTTP_404_NOT_FOUND
            )

    def validate_order_group_payment_method(self, order_group):
        """
        Vaidate that the payment method is DIGITAL.
        """
        if order_group.payment_method != PaymentMethod.DIGITAL:
            raise ErrorException(
                detail="Payment can only be initialized for order groups with DIGITAL payment method.",
                code="invalid_payment_method"
            )

    def validate_order_group_status(self, order_group):
        """
        Validate that the order group status is PENDING.
        """
        if order_group.status != OrderGroupStatus.PENDING:
            raise ErrorException(
                detail="Only pending order groups can be paid for.",
                code="invalid_order_group_status"
            )

    def validate_order_group(self, order_group):
        """
        Validate order group.
        """
        self.validate_order_group_exists(order_group)
        self.validate_order_group_payment_method(order_group)
        self.validate_order_group_status(order_group)

    def get_payment_service(self):
        """
        Get the class for the payment service type passed.
        If no service_type is found, raise Error.
        """
        serializer = InitializePaymentSerializer(
            data=self.request.data
        )
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as e:
            raise ErrorException(
                detail="Payment initialization failed.",
                code="validation_error",
                errors=e.detail
            )
        return serializer.validated_data["service"]


    @extend_schema(**initialize_payment_schema)
    def post(self, request, order_group_id):
        validate_id(order_group_id, "order group")

        service = self.get_payment_service()

        order_group = self.get_order_group_object(order_group_id)
        self.validate_order_group(order_group)

        service = service(user=order_group.user, group=order_group)

        try:
            authorization_url = service.initialize_payment()
        except (DuplicatePaymentError, PaymentProviderError) as e:
            raise ErrorException(
                detail=e.detail,
                code=e.code,
                status_code=e.status_code
            )

        return Response(SuccessAPIResponse(
            message="Payment initialized successfully.",
            data={"authorization_url": authorization_url}
        ).to_dict(), status=status.HTTP_200_OK)
