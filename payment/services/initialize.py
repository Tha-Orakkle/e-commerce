import logging
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from django.db import transaction
from django.utils.timezone import now, timedelta

from order.models import OrderGroup
from payment.domain.exceptions import (
    PaymentAlreadyVerifiedError,
    PaymentTransactionStateChangedError,
    PaymentTransactionStatusError,
)
from payment.gateways.ports import PaymentGateway
from payment.models import (
    Payment,
    PaymentStatus,
    PaymentTransaction,
    PaymentTransactionStatus,
)
from payment.services.verification import (
    PaymentVerificationResult,
    get_payment_verification_service,
)

logger = logging.getLogger(__name__)


class InitializationOperation(StrEnum):
    INITIALIZE = "initialize"
    VERIFY = "verify"


class InitializationAction(StrEnum):
    RETURN = "return"
    NEW_ATTEMPT = "new_attempt"


@dataclass(frozen=True)
class PaymentInitializationResult:
    authorization_url: str | None
    reference: str
    status: str

    @staticmethod
    def from_transaction(tx: PaymentTransaction):
        return PaymentInitializationResult(
            authorization_url=tx.authorization_url,
            reference=str(tx.reference),
            status=tx.status
        )


@dataclass(frozen=True)
class InitializationDecision:
    action: InitializationAction
    result: PaymentInitializationResult | None = None


class InitializePaymentService:
    MAX_STATE_RECONCILIATION_RETRIES = 1
    NEW_TRANSACTION_STATUSES = {  # noqa: RUF012
        PaymentTransactionStatus.EXPIRED,
        PaymentTransactionStatus.FAILED,
        PaymentTransactionStatus.INCONSISTENT,
        PaymentTransactionStatus.REVERSED,
        PaymentTransactionStatus.INITIALIZATION_FAILED
    }

    def __init__(self, gateway_registry):
        self.gateway_registry = gateway_registry

    def initialize(
        self,
        *,
        order_group: OrderGroup,
        provider: str
    ) -> PaymentInitializationResult:

        gateway = self.gateway_registry.get(provider)

        for _ in range(self.MAX_STATE_RECONCILIATION_RETRIES + 1):
            decision = self._initialize_attempt(
                order_group=order_group,
                provider=provider,
                gateway=gateway
            )

            if decision.action == InitializationAction.NEW_ATTEMPT:
                logger.INFO(
                    "Retrying the initialization attempt"
                )
                continue

            if decision.action == InitializationAction.RETURN:
                return decision.result

        raise PaymentTransactionStateChangedError()

    def _initialize_attempt(
        self,
        *,
        order_group: OrderGroup,
        provider: str,
        gateway: PaymentGateway,
    ) -> InitializationDecision:

        with transaction.atomic():
            payment = (
                Payment.objects
                .select_for_update()
                .select_related("active_transaction")
                .get(order_group=order_group)
            )

            if payment.status == PaymentStatus.VERIFIED:
                raise PaymentAlreadyVerifiedError()

            metadata = {
                "order_group_id": str(order_group.id),
                "payment_id": str(payment.id)
            }

            tx = payment.active_transaction

            if tx is None or tx.status in self.NEW_TRANSACTION_STATUSES:
                tx = self._create_new_transaction(
                    payment=payment,
                    provider=provider,
                    customer_email=order_group.user.email,
                    metadata=metadata
                )

                operation = InitializationOperation.INITIALIZE

            elif tx.status == PaymentTransactionStatus.PENDING:
                operation = InitializationOperation.VERIFY

            else:
                raise PaymentTransactionStatusError(
                    f"Unknown transaction status: {tx.status}"
                )

            transaction_id = tx.id

        if operation == InitializationOperation.INITIALIZE:
            provider_data = self._initialize_with_payment_provider(
                gateway=gateway,
                transaction=tx,
                metadata=metadata
            )
        elif operation == InitializationOperation.VERIFY:
            verification_service = get_payment_verification_service()

            service_result = verification_service.verify(
                transaction_id=tx.id
            )

        with transaction.atomic():
            payment = (
                Payment.objects
                .select_for_update()
                .select_related("active_transaction")
                .get(order_group=order_group)
            )

            if payment.status == PaymentStatus.VERIFIED:
                raise PaymentAlreadyVerifiedError()

            tx = (
                PaymentTransaction.objects
                .select_for_update()
                .get(id=transaction_id)
            )

            if payment.active_transaction_id != transaction_id:

                return self._handle_transaction_changed(
                    payment=payment,
                    operaion=operation,
                    previous_tx=tx
                )

            if operation == InitializationOperation.INITIALIZE:
                return self._reconcile_initialization(
                    tx=tx,
                    provider_data=provider_data
                )

            return self._handle_verification_result(
                tx=tx,
                result=service_result,
            )

    def _create_new_transaction(
        self,
        *,
        payment: Payment,
        provider: str,
        customer_email: str,
        metadata: dict[str, str]
    ) -> PaymentTransaction:

        expires_at = now() + timedelta(minutes=30)

        tx = PaymentTransaction.objects.create(
            payment=payment,
            customer_email=customer_email,
            provider=provider,
            currency=payment.currency,
            amount=payment.amount,
            expires_at=expires_at,
            metadata=metadata
        )

        payment.active_transaction = tx
        payment.save(
            update_fields=[
                "active_transaction",
                "updated_at"
            ]
        )
        return tx

    def _mark_previous_transaction_expired(
        self,
        *,
        tx: PaymentTransaction
    ):
        tx.status = PaymentTransactionStatus.EXPIRED
        tx.verification_failure_reason = (
            "Transaction was initialized after another "
            "transaction became active."
        )
        tx.save(
            update_fields=[
                "status",
                "verification_failure_reason",
                "updated_at"
            ]
        )

    def _handle_transaction_changed(
        self,
        *,
        payment: Payment,
        operation: InitializationOperation,
        previous_tx: PaymentTransaction
    ) -> InitializationDecision:

        if operation == InitializationOperation.INITIALIZE:
            self._mark_previous_transaction_expired(tx=previous_tx)

        current_tx = payment.active_transaction

        if (
            current_tx is None
            or current_tx.status in self.NEW_TRANSACTION_STATUSES
        ):
            return InitializationDecision(
                action=InitializationAction.NEW_ATTEMPT
            )

        elif current_tx.status == PaymentTransactionStatus.PENDING:

            if current_tx.authorization_url:
                return InitializationDecision(
                    action=InitializationAction.RETURN,
                    result=PaymentInitializationResult.from_transaction(
                        current_tx
                    )
                )

            return InitializationDecision(
                action=InitializationAction.NEW_ATTEMPT
            )

        raise PaymentTransactionStatusError(
            f"Unexpected transaction status: {current_tx.status}"
        )

    def _initialize_with_payment_provider(
        self,
        *,
        gateway: PaymentGateway,
        transaction: PaymentTransaction,
        metadata: dict[str, str]
    ) -> dict[str, Any]:

        response = gateway.initialize_payment(
            reference=str(transaction.reference),
            amount=transaction.amount,
            currency=transaction.currency,
            email=transaction.customer_email,
            metadata=metadata
        )

        return response

    def _reconcile_initialization(
        self,
        *,
        tx: PaymentTransaction,
        provider_data: dict[str, Any]
    ) -> InitializationDecision:
        tx.authorization_url = provider_data.get("authorization_url")
        tx.save(
            update_fields=[
                "authorization_url",
                "updated_at"
            ]
        )
        return InitializationDecision(
            action=InitializationAction.RETURN,
            result=PaymentInitializationResult.from_transaction(tx)
        )

    def _handle_verification_result(
        self,
        *,
        tx: PaymentTransaction,
        result: PaymentVerificationResult,
    ) -> InitializationDecision:

        if result.is_success:
            raise PaymentAlreadyVerifiedError()

        if result.is_pending:
            return InitializationDecision(
                action=InitializationAction.RETURN,
                result=PaymentInitializationResult.from_transaction(tx)
            )

        if (
            result.is_reference_not_found
            or result.is_failed
            or result.is_reversed
            or result.is_inconsistent
        ):
            return InitializationDecision(
                action=InitializationAction.NEW_ATTEMPT,
            )
