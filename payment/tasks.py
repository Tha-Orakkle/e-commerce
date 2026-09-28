import logging
from uuid import UUID

from celery import shared_task

from payment.domain.exceptions import (
    PaymentGatewayConnectionError,
    PaymentGatewayTimeoutError,
)
from payment.models import PaymentTransaction
from payment.services.verification import get_payment_verification_service

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    autoretry_for=(
        PaymentGatewayTimeoutError,
        PaymentGatewayConnectionError
    ),
    retry_backoff=True,
    max_retries=3
)
def verify_payment_task(self, reference: str | UUID):
    """
    Background task to verify Paystack payment.
    """

    if not reference:
        logger.error("Missing reference in provider webhook payload.")
        return

    tx = (
        PaymentTransaction.objects
        .filter(reference=reference)
        .first()
    )
    if tx is None:
        logger.error(
            "No payment transaction associated with provider reference: %s",
            reference
        )
        return

    verification_service = get_payment_verification_service()

    verification_service.verify(
        transaction_id=tx.id
    )
