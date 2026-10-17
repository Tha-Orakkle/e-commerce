import logging
from typing import Any

import requests
from django.conf import settings
from django.urls import reverse
from rest_framework import status

from payment.domain.exceptions import (
    PaymentGatewayConnectionError,
    PaymentGatewayError,
    PaymentGatewayTimeoutError,
)

logger = logging.getLogger(__name__)


class PaystackGateway:
    INITIALIZE_URL = settings.PAYSTACK.get("INITIALIZE_URL")
    VERIFY_URL = settings.PAYSTACK.get("VERIFY_URL")
    SECRET_KEY = settings.PAYSTACK.get("SECRET_KEY")
    TIMEOUT = 10

    def _build_headers(self) -> dict[str, str]:
        """
        Prepare headers for communication with paystack
        """

        return {
            "Authorization": f"Bearer {self.SECRET_KEY}",
            "Content-Type": "application/json"
        }

    def _get_callback_url(self) -> str:
        return f"{settings.BASE_URL}{reverse("temporary-callback")}"

    def _raise_http_error(self, exc: Exception, reference: str):
        upstream = exc.response.status_code

        logger.warning(
            "Paystack returned an HTTP error",
            extra={
                "status_code": upstream,
                "reference": reference
            },
        )

        if 400 <= upstream < 500:

            raise PaymentGatewayError(
                detail=(
                    "Unable to process your request due to an "
                    "error communicating with Paystack."
                ),
                code="paystack_request_rejected"
            )

        elif upstream >= 500:

            logger.error(
                "Paystack service returned a server error",
                extra={
                    "status_code": upstream,
                    "reference": reference
                },
            )

            raise PaymentGatewayError(
                detail="Payment service is temporarily unavailable.",
                code="paystack_service_unavailable",
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE
            )

    def _raise_json_decode_error(self, exc: Exception, reference: str):
        logger.error(
            "Paystack returned an invalid JSON response",
            extra={
                "reference": reference
            }
        )

        raise PaymentGatewayError(
            detail="Received an invalid response from Paystack.",
            code="invalid_paystack_response",
        )

    def _raise_timeout_error(self, reference: str):
        logger.warning(
            "Paystack request timed out",
            extra={
                "reference": reference
            }

        )
        raise PaymentGatewayTimeoutError()

    def _raise_connection_error(self, reference: str):
        logger.error(
            "Unable to connect to Paystack",
            extra={
                "reference": reference
            }
        )
        raise PaymentGatewayConnectionError()

    def _raise_request_exception(self, exc: Exception, reference: str):
        logger.exception(
            "Unexpected error communicating with Paystack",
            extra={
                "reference": reference
            }
        )
        raise PaymentGatewayError(
            detail=(
                "An unexpected error occurred while "
                "communicating with Paystack."
            ),
            code="paystack_request_failed",
        )

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

            logger.info(
                "Initializing payment with Paystack",
                extra={"reference": reference}
            )

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

            logger.info(
                "Paystack payment initialization response received",
                extra={"reference": reference}
            )

        except requests.HTTPError as exc:
            self._raise_http_error(exc=exc, reference=reference)

        except requests.JSONDecodeError as exc:
            self._raise_json_decode_error(exc=exc, reference=reference)

        except requests.Timeout as exc:
            self._raise_timeout_error(exc=exc, reference=reference)

        except requests.ConnectionError as exc:
            self._raise_connection_error(exc=exc, reference=reference)

        except requests.RequestException as exc:
            self._raise_request_exception(exc=exc, reference=reference)

        if not payload.get("status", False):
            provider_messsage = payload.get("message")
            logger.warning(
                "Paystack rejected the payment initialization",
                extra={
                    "reference": reference,
                    "provider_message": provider_messsage,
                },
            )
            raise PaymentGatewayError(
                detail=provider_messsage or "Paystack error.",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        logger.info(
            "Paystack payment initialized successfully",
            extra={"reference": reference},
        )
        return payload["data"]

    def verify_payment(
        self,
        *,
        reference: str
    ) -> dict[str, Any]:

        try:
            logger.info(
               "Verifying payment with Paystack",
               extra={"reference": reference},
            )
            response = requests.get(
                f"{self.VERIFY_URL}{reference}",
                headers=self._build_headers(),
                timeout=self.TIMEOUT
            )

            response.raise_for_status()
            payload = response.json()
            logger.info(
                "Paystack payment verification response received",
                extra={"reference": reference},
            )
        except requests.HTTPError as exc:
            self._raise_http_error(exc=exc, reference=reference)

        except requests.JSONDecodeError as exc:
            self._raise_json_decode_error(exc=exc, reference=reference)

        except requests.Timeout as exc:
            # implement a reliability policy
            # retries timeouts
            self._raise_timeout_error(exc=exc, reference=reference)

        except requests.ConnectionError as exc:
            self._raise_connection_error(exc=exc, reference=reference)

        except requests.RequestException as exc:
            self._raise_request_exception(exc=exc, reference=reference)

        if not payload.get("status", False):
            provider_message = payload.get("message")
            logger.warning(
                "Paystack rejected the payment initialization",
                extra={
                    "reference": reference,
                    "provider_message": provider_message,
                },
            )
            raise PaymentGatewayError(
                detail=provider_message or "Paystack error.",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        logger.info(
            "Paystack payment verification completed successfully",
            extra={"reference": reference},
        )
        return payload["data"]
