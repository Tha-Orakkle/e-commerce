from decimal import Decimal
from typing import Protocol, Any


class PaymentGateway(Protocol):
    def verify_transaction(self, reference: str):
        """Verify payment with provider."""
        ...
        
    def initialize_payment(
        self,
        *,
        reference: str,
        amount: Decimal,
        currency: str,
        customer_email: str,
        metadata: dict[str, Any]
    ):
        """
        Initialize payment and get authorization url
        from provider.
        """
        ...
