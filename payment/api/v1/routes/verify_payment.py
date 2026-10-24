from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from common.cores.validators import validate_id
from common.exceptions import ErrorException
from common.permissions import IsCustomer
from common.utils.api_responses import SuccessAPIResponse
from payment.api.v1.serializers import PaymentStatusSerializer
from payment.api.v1.swagger import verify_payment_schema
from payment.models import PaymentStatus, PaymentTransaction


class TempCallback(APIView):
    """
    Temporary callback view to test the payment verification.
    In production, callback will be a frontend URL that Paystack will call
    after a successful payment.
    This view is only for testing purposes and should be removed later.
    """
    permission_classes = [AllowAny]  # noqa: RUF012

    def get(self, request):
        """
        Temporary callback to test the payment verification.
        """
        return Response(SuccessAPIResponse(
            message="Temporary callback for testing payment verification."
        ).to_dict(), status=status.HTTP_200_OK)


class VerifyPaymentView(APIView):
    """
   Report the status of a payment transaction.

    The reference is the one returned when the payment was initialized.
    This endpoint is read-only: it reports what is stored and never
    contacts the payment provider. Verification happens through the
    provider webhook.
    """
    permission_classes = [IsCustomer]  # noqa: RUF012

    def get_object(self, reference):
        """
        Get the payment transaction by reference.
        Customers only see their own; superusers see any.
        """
        user = self.request.user
        queryset = PaymentTransaction.objects.select_related(
            "payment__order_group"
        )
        if not user.is_superuser:
            queryset = queryset.filter(payment__order_group__user=user)
        return queryset.filter(reference=reference).first()

    @extend_schema(**verify_payment_schema)
    def get(self, request, reference):
        """
        Get the status of a payment transaction.
        """
        validate_id(reference, "payment transaction reference")
        tx = self.get_object(reference)
        if not tx:
            raise ErrorException(
                detail=(
                    "No payment transaction matching the given "
                    "reference found."
                ),
                code='not_found',
                status_code=status.HTTP_404_NOT_FOUND)

        serializer = PaymentStatusSerializer(tx)
        if tx.payment.status == PaymentStatus.VERIFIED:
            return Response(SuccessAPIResponse(
                message="Payment is verified.",
                data=serializer.data
            ).to_dict(), status=status.HTTP_200_OK)

        return Response(SuccessAPIResponse(
            message="Payment not verified yet.",
            data=serializer.data
        ).to_dict(), status=status.HTTP_200_OK)
