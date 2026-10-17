from typing import ClassVar

from payment.domain.exceptions import UnsupportedPaymentProviderError
from payment.models import PaymentProvider

from .paystack import PaystackGateway
from .ports import PaymentGateway


class PaymentGatewayRegistry:
    _gateways: ClassVar[dict[PaymentProvider, PaystackGateway]]  = {
        PaymentProvider.PAYSTACK: PaystackGateway()
    }

    @classmethod
    def check_provider(cls, provider: str) -> PaymentProvider:
        normalized = str(provider).strip().lower()

        try:
            return PaymentProvider(normalized)
        except ValueError:
            raise UnsupportedPaymentProviderError(
                f"Unsupported payment provider: {provider}"
            )

    @classmethod
    def get(
        cls,
        provider: str | PaymentProvider
    ) -> PaymentGateway:

        if isinstance(provider, str):
            provider = cls.check_provider(provider)

        try:
            return cls._gateways[provider]
        except KeyError:
            raise UnsupportedPaymentProviderError(
                f"No gateway configured for provider: {provider}"
            )
