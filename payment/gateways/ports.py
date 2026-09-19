from typing import Protocol


class PaymentGateway(Protocol):
    def verify_transaction(self, reference: str):
        """Verify payment with provider."""
        ...
        
    def initialize_payment(
        self,
        *,
        reference: str,
        amount: int,
        currency: str,
        email: str,
        metadata: dict[str, str]
    ):
        """
        Initialize payment and get authorization url
        from provider.
        """
        ...
