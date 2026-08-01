from django.conf import settings
from rest_framework import status

import requests

from .base import BasePaymentService
from payment.domain.exceptions import PaystackError


class PaystackService(BasePaymentService):
    """
    Paystack Service.
    """
    def __init__(self, user, group):
        self.payment = None
        self.headers = {
            "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
            "Content/Type": "application/json"
        }
        super().__init__(user, group)

    def _make_paystack_request(self, data):
        try:
            response = requests.post(
                settings.PAYSTACK_INITIALIZE_URL,
                json=data,
                # headers=self.headers,
                timeout=5
            )
            response.raise_for_status()
            payload = response.json()
        except requests.HTTPError as e:
            upstream = e.response.status_code

            if 400 <= upstream < 500:
                raise PaystackError(
                    detail="Unable to process your request due to an error communicating with Paystack.",
                    code="paystack_request_rejected"
                )
            elif upstream >= 500:
                raise PaystackError(
                    detail="Payment service is temporarily unavailable.",
                    code="paystack_service_unavailable",
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE
                )

        except requests.JSONDecodeError:
            raise PaystackError(
                detail="Received an invalid response from the Paystack.",
                code="invalid_paystack_response",
             )

        except requests.Timeout:
            raise PaystackError(
                detail="Paystack timed out. Please try again.",
                code="paystack_timeout",
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            )

        except requests.ConnectionError:
            raise PaystackError(
                detail="Unable to connect to Paystack.",
                code="payment_connection_error",
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        except requests.RequestException:
            raise PaystackError(
                detail="An unexpected error occurred while communicating with Paystack.",
                code="paystack_request_failed",
            )

        if not payload.get("status", False):
            raise PaystackError(
                detail=payload.get("message", "Paystack error."),
                status_code=status.HTTP_400_BAD_REQUEST
            )
        return payload

    def _get_authorization_url(self):
        """
        Gets the authorisation url from paystack.
        """
        data = self.payment.to_dict()
        response_data = self._make_paystack_request(data)
        return response_data["data"]["authorization_url"]

    def initialise_payment(self):
        """
        Initialise payment: verify payment and get authorization url
        from Paystack.
        """
        self.payment = self._verify_order_group_payment()
        return self._get_authorization_url()
