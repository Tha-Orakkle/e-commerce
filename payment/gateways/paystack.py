from django.conf import settings
from rest_framework import status

import requests

from payment.domain.exceptions import PaymentProviderError

class PaystackGateway:
    INITIALIZE_URL = settings.PAYSTACK.get("INITIALIZE_URL") 
    SECRET_KEY = settings.PAYSTACK.get("SECRET_KEY")
    TIMEOUT = 10
    
    def _build_headers(self):
        return {
            "Authorization": f"Bearer {self.SECRET_KEY}",
            "Content/Type": "application/json"
        }


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
        Initialize payment and get authorization url.
        """
        try:
            response = requests.post(
                self.INITIALIZE_URL,
                headers=self._build_headers(),
                json={
                    "reference": reference,
                    "amount": amount,
                    "currency": currency,
                    "email": email,
                    "metadata": metadata
                },
                timeout=self.TIMEOUT
            )
            response.raise_for_status()
            payload = response.json
        except requests.HTTPError as exc:
            upstream = exc.response.status_code

            if 400 <= upstream < 500:
                raise PaymentProviderError(
                    detail=(
                        "Unable to process your request due to an "
                        "error communicating with Paystack."
                    ),
                    code="paystack_request_rejected"
                )
            elif upstream >= 500:
                raise PaymentProviderError(
                    detail="Payment service is temporarily unavailable.",
                    code="paystack_service_unavailable",
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE
                )
        except requests.JSONDecodeError:
            raise PaymentProviderError(
                detail="Received an invalid response from the Paystack.",
                code="invalid_paystack_response",
                )

        except requests.Timeout:
            raise PaymentProviderError(
                detail="Paystack timed out. Please try again.",
                code="paystack_timeout",
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            )

        except requests.ConnectionError:
            raise PaymentProviderError(
                detail="Failed to connect to Paystack. Please try again.",
                code="paystack_connection_error",
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        except requests.RequestException:
            raise PaymentProviderError(
                detail="An unexpected error occurred while communicating with Paystack.",
                code="paystack_request_failed",
            )

        if not payload.get("status", False):
            raise PaymentProviderError(
                detail=payload.get("message", "Paystack error."),
                status_code=status.HTTP_400_BAD_REQUEST
            )
        return payload
        
        
        