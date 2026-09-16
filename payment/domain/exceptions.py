from rest_framework import status


class PaymentProviderError(Exception):
    """
    Raise error errors from requests to payment services
    APIs.
    """
    code = "payment_provider_error"
    status_code = status.HTTP_502_BAD_GATEWAY

    def __init__(self, detail, code=None, status_code=None):
        super().__init__(detail)
        self.detail = detail
        self.code = self.code if code is None else code
        self.status_code = (
            self.status_code
            if status_code is None
            else status_code)


class PaystackError(PaymentProviderError):
    """
    Raised for errors from requests to Paystack APIs.
    """
    code = "paystack_error"


class DuplicatePaymentError(Exception):
    """
    Raised when a duplicate payment transaction is carried.
    """
    def __init__(self):
        self.detail = "Payment has already been verified."
        self.code = "duplicate_transaction"
        self.status_code = status.HTTP_400_BAD_REQUEST
