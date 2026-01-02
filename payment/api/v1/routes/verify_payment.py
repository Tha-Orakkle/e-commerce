from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from common.cores.validators import validate_id
from common.exceptions import ErrorException
from common.permissions import IsCustomer
from common.utils.api_responses import SuccessAPIResponse
from payment.models import Payment
from payment.api.v1.swagger import verify_payment_schema
from payment.api.v1.serializers import PaymentSerializer


class TempCallback(APIView):
    """
    Temporary callback view to test the payment verification.
    In production, callback will be a frontend URL that Paystack will call
    after a successful payment.
    This view is only for testing purposes and should be removed later.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        """
        Temporary callback to test the payment verification.
        """
        return Response(SuccessAPIResponse(
            message="Temporary callback for testing payment verification."
        ).to_dict(), status=status.HTTP_200_OK)


class VerifyPaymentView(APIView):
    """
    Verify payment.
    """
    permission_classes = [IsCustomer]

    @extend_schema(**verify_payment_schema)
    def get(self, request, reference):
        """"
        Verify payment from paystack.
        """
        validate_id(reference, "payment reference")
        payment = Payment.objects.filter(reference=reference).first()
        if not payment:
            raise ErrorException(
                detail="No payment matching the given reference found.",
                code='not_found',
                status_code=status.HTTP_404_NOT_FOUND)
        
        serializer = PaymentSerializer(payment)
        if payment.verified:
            return Response(SuccessAPIResponse(
                message="Payment is verified.",
                data=serializer.data
            ).to_dict(), status=status.HTTP_200_OK)
        
        return Response(SuccessAPIResponse(
            message="Payment not verified yet.",
            data=serializer.data
        ).to_dict(), status=status.HTTP_200_OK)