from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError

from common.cores.validators import validate_id
from common.utils.api_responses import SuccessAPIResponse
from common.exceptions import ErrorException
from order.models import OrderGroup, OrderGroupStatus, PaymentMethod
from payment.api.v1.serializers.payment import InitializePaymentSerializer
from payment.gateways.registry import PaymentGatewayRegistry
from payment.services import InitializePaymentService


class PaymentCreateView(APIView):

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

    def get_validated_provider(self):
        serializer = InitializePaymentSerializer(
            data=self.request.data
        )
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as exc:
            raise ErrorException(
                detail="Payment initialization failed.",
                code="validation_error",
                errors=exc.detail
            )

        return serializer.validated_data["provider"]

    def post(self, request, order_group_id):
        validate_id(order_group_id, "order group")

        order_group = self.get_order_group_object(order_group_id)
        self.validate_order_group(order_group)

        provider = self.get_validated_provider()
        
        gateway_factory = PaymentGatewayRegistry()

        service = InitializePaymentService(
            gateway_fatory=gateway_factory
        )

        try:
            payment, gateway_response = service.initialize_payment(
                order_group=order_group,
                provider=provider,
            )
        except:
            pass

        return Response(SuccessAPIResponse(
            message="Payment initialized successfully.",
            data={
                "reference": payment.reference,
                "provider": payment.provider,
                "authorization_url": (
                    gateway_response["authorization_url"]
                )
            }
        ), status=status.HTTP_201_CREATED)
