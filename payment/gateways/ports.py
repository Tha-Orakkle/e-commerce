from typing import Any, Protocol


class PaymentGateway(Protocol):

    def initialize_payment(
        self,
        *,
        reference: str,
        amount: int,
        currency: str,
        email: str,
        metadata: dict[str, str]
    ) -> dict[str, Any]:
        """
        Initialize payment and get authorization url
        from provider.
        """
        ...

    def verify_payment(
        self,
        *,
        reference: str
    ) -> dict[str, Any]:
        """Verify payment with provider."""
        ...
