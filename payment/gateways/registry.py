from .ports import PaymentGateway
from payment.models import PaymentProvider
from .paystack import PaystackGateway


class PaymentGatewayRegistry:
    def __init__(self):
        self._gateways = {
            PaymentProvider.PAYSTACK: PaystackGateway(),
        }

    def get(self, provider: str) -> PaymentGateway:
        try:
            return self._gateways[provider]
        except KeyError:
            raise ValueError(
                f"Unsupported payment provider: {provider}"
            )
