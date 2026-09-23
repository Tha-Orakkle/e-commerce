from typing import Any

import requests
from django.conf import settings
from django.urls import reverse
from rest_framework import status

from payment.domain.exceptions import PaymentGatewayError


class PaystackGateway:
    INITIALIZE_URL = settings.PAYSTACK.get("INITIALIZE_URL")
    SECRET_KEY = settings.PAYSTACK.get("SECRET_KEY")
    TIMEOUT = 10

    def _build_headers(self) -> dict[str, str]:
        """
        Prepare headers for communication with paystack
        """

        return {
            "Authorization": f"Bearer {self.SECRET_KEY}",
            "Content/Type": "application/json"
        }

    def _get_callback_url(self) -> str:
        return f"{settings.BASE_URL}{reverse("temporary-callback")}"

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
                    "metadata": metadata,
                    "callback_url": self._get_callback_url()
                },
                timeout=self.TIMEOUT
            )
            response.raise_for_status()
            payload = response.json()

        except requests.HTTPError as exc:
            upstream = exc.response.status_code

            if 400 <= upstream < 500:
                raise PaymentGatewayError(
                    detail=(
                        "Unable to process your request due to an "
                        "error communicating with Paystack."
                    ),
                    code="paystack_request_rejected"
                )

            elif upstream >= 500:
                raise PaymentGatewayError(
                    detail="Payment service is temporarily unavailable.",
                    code="paystack_service_unavailable",
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE
                )

        except requests.JSONDecodeError:
            raise PaymentGatewayError(
                detail="Received an invalid response from the Paystack.",
                code="invalid_paystack_response",
                )

        except requests.Timeout:
            raise PaymentGatewayError(
                detail="Paystack timed out. Please try again.",
                code="paystack_timeout",
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            )

        except requests.ConnectionError:
            raise PaymentGatewayError(
                detail="Failed to connect to Paystack. Please try again.",
                code="paystack_connection_error",
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        except requests.RequestException:
            raise PaymentGatewayError(
                detail=(
                    "An unexpected error occurred while "
                    "communicating with Paystack."
                ),
                code="paystack_request_failed",
            )

        if not payload.get("status", False):
            raise PaymentGatewayError(
                detail=payload.get("message", "Paystack error."),
                status_code=status.HTTP_400_BAD_REQUEST
            )
        return payload
