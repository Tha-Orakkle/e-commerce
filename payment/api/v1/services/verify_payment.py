from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response


from common.exceptions import ErrorException
from common.utils.api_responses import SuccessAPIResponse
from order.models import Order
from payment.models import Payment


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
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """"
        Verify payment from paystack.
        """
        reference = request.query_params.get('reference')

        payment = Payment.objects.filter(reference=reference).first()
        if not payment:
            raise ErrorException("Payment not found", code=status.HTTP_404_NOT_FOUND)
        
        if payment.verified:
            return Response(SuccessAPIResponse(
                message="Payment verified."
            ).to_dict(), status=status.HTTP_200_OK)
        
        return Response(SuccessAPIResponse(
            message="Payment not verified yet."
        ).to_dict(), status=status.HTTP_200_OK)