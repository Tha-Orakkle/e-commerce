from payment.domain.exceptions import UnsupportedPaymentProviderError
from payment.models import PaymentProvider

from .paystack import PaystackGateway
from .ports import PaymentGateway


class PaymentGatewayRegistry:
    def __init__(self):
        self._gateways = {
            PaymentProvider.PAYSTACK: PaystackGateway(),
        }

    def get(self, provider: str) -> PaymentGateway:
        try:
            return self._gateways[provider]
        except KeyError:
            raise UnsupportedPaymentProviderError(
                f"Unsupported payment provider: {provider}"
            )
