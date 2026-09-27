from rest_framework import status

from common.exceptions import ApplicationError


class PaymentError(ApplicationError):
    """Base exception for payment-related errors."""


class PaymentTransactionStatusError(PaymentError):
    """Raised for invalid payment transaction status."""

    code = "invalid_payment_transaction_status"
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR


class PaymentTransactionStateChangedError(PaymentError):
    """Raise for changed payment transaction state"""

    code = "payment_state_changed"
    status_code = status.HTTP_409_CONFLICT

    def __init__(self, action="initializing"):
        super().__init__(
            f"Payment transaction changed while {action}."
        )


# =========================================================
# PAYMENT GATEWAY ERRORS
# =========================================================
class PaymentGatewayError(PaymentError):
    """Base exception for gateway communication errors."""

    code = "payment_provider_error"
    status_code = status.HTTP_502_BAD_GATEWAY


class UnsupportedPaymentProviderError(PaymentGatewayError):
    code = "unsupported_payment_provider"
    status_code = status.HTTP_400_BAD_REQUEST


class PaymentReferenceNotFoundError(PaymentGatewayError):
    code = "payment_reference_not_found"
    status_code = status.HTTP_404_NOT_FOUND


class PaymentGatewayTimeoutError(PaymentGatewayError):
    code = "payment_gateway_timeout"
    status_code = status.HTTP_504_GATEWAY_TIMEOUT

    def __init__(self):
        super().__init__(
            "Payment provider timed out. Please try again"
        )


class PaymentGatewayConnectionError(PaymentGatewayError):
    code = "payment_gateway_connection_error"
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    def __init__(self):
        super().__init__(
            "Failed to connect to payment provider. Please try again."
        )


class PaymentGatewayResponseError(PaymentGatewayError):
    code = "payment_gateway_response_error"
    status_code = status.HTTP_502_BAD_GATEWAY


# =========================================================
# PAYMENT VERIFICATION ERRORS
# =========================================================
class PaymentVerificationError(PaymentError):
    """Base exception for verification failures."""


class PaymentReferenceMismatchError(PaymentVerificationError):
    code = "payment_reference_mismatch"
    status_code = status.HTTP_400_BAD_REQUEST

    def __init__(self):
        super().__init__(
            "Payment verification reference does not match."
        )


class PaymentAmountMismatchError(PaymentVerificationError):
    code = "payment_amount_mismatch"
    status_code = status.HTTP_400_BAD_REQUEST

    def __init__(self):
        super().__init__(
            "Payment amount does not match the expected amount."
        )


class PaymentCurrencyMismatchError(PaymentVerificationError):
    code = "payment_currency_mismatch"
    status_code = status.HTTP_400_BAD_REQUEST

    def __init__(self):
        super().__init__(
            "Payment currency does not match the expected currency."
        )


class PaymentCustomerMismatchError(PaymentVerificationError):
    code = "payment_customer_mismatch"
    status_code = status.HTTP_400_BAD_REQUEST

    def __init__(self):
        super().__init__(
            "Payment customer does not match the expected customer."
        )


class PaymentMetadataMismatchError(PaymentVerificationError):
    code = "payment_metadata_mismatch"
    status_code = status.HTTP_400_BAD_REQUEST

    def __init__(self):
        super().__init__(
            "Payment metadata does not match."
        )


class PaymentProviderStatusError(PaymentVerificationError):
    code = "invalid_payment_provider_status"
    status_code = status.HTTP_400_BAD_REQUEST

    def __init__(self):
        super().__init__(
            "Payment provider returned a invalid transaction status."
        )


class PaymentAlreadyVerifiedError(PaymentVerificationError):
    """
    Raised for duplicate payment transaction.
    """

    code = "duplicate_transaction"
    status_code = status.HTTP_409_CONFLICT

    def __init__(self):
        super().__init__("Payment has already been verified.")
