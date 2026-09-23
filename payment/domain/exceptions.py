from rest_framework import status

from common.exceptions import ApplicationError


class PaymentError(ApplicationError):
    """Base exception for payment-related errors."""


class PaymentGatewayError(PaymentError):
    """An external payment gateway operation failed."""

    code = "payment_provider_error"
    status_code = status.HTTP_502_BAD_GATEWAY


class DuplicatePaymentError(PaymentError):
    """
    Raised for duplicate payment transaction.
    """

    code = "duplicate_transaction"
    status_code = status.HTTP_409_CONFLICT

    def __init__(self):
        super().__init__("Payment has already been verified.")


class PaymentTransactionStatusError(PaymentError):
    """Raised for invalid payment transaction status."""

    code = "invalid_payment_transaction_status"
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR


class PaymentTransactionStateChangedError(PaymentError):
    """Raise for changed payment transaction state"""

    code = "payment_state_changed"
    status_code = status.HTTP_409_CONFLICT

    def __init__(self):
        super().__init__(
            "Payment transaction changed while initializing."
        )
