from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from django.db import transaction
from django.utils.timezone import now

from order.models import Order
from payment.domain.exceptions import (
    PaymentAmountMismatchError,
    PaymentCurrencyMismatchError,
    PaymentCustomerMismatchError,
    PaymentGatewayError,
    PaymentMetadataMismatchError,
    PaymentProviderStatusError,
    PaymentReferenceNotFoundError,
    PaymentTransactionStateChangedError,
    PaymentVerificationError,
)
from payment.gateways.registry import PaymentGatewayRegistry
from payment.models import (
    Payment,
    PaymentStatus,
    PaymentTransaction,
    PaymentTransactionStatus,
)


class VerificationStatus(StrEnum):
    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"
    REFERENCE_NOT_FOUND = "reference_not_found"
    INCONSISTENT = "Inconsistent"
    REVERSED = "Reversed"


@dataclass(frozen=True)
class PaymentVerificationResult:
    status: VerificationStatus
    tx: PaymentTransaction

    @property
    def is_success(self) -> bool:
        return self.status == VerificationStatus.SUCCESS

    @property
    def is_failed(self) -> bool:
        return self.status == VerificationStatus.FAILED

    @property
    def is_pending(self) -> bool:
        return self.status == VerificationStatus.PENDING

    @property
    def is_reference_not_found(self) -> bool:
        return self.status == VerificationStatus.REFERENCE_NOT_FOUND

    @property
    def is_reversed(self) -> bool:
        return self.status == VerificationStatus.REVERSED

    @property
    def is_inconsistent(self) -> bool:
        return self.status == VerificationStatus.INCONSISTENT

    @staticmethod
    def success(tx: PaymentTransaction):
        return PaymentVerificationResult(
            status=VerificationStatus.SUCCESS,
            tx=tx
        )

    @staticmethod
    def pending(tx: PaymentTransaction):
        return PaymentVerificationResult(
            status=VerificationStatus.PENDING,
            tx=tx
        )

    @staticmethod
    def failed(tx: PaymentTransaction):
        return PaymentVerificationResult(
            status=VerificationStatus.FAILED,
            tx=tx
        )

    @staticmethod
    def reversed(tx: PaymentTransaction):
        return PaymentVerificationResult(
            status=VerificationStatus.REVERSED,
            tx=tx
        )

    @staticmethod
    def reference_not_found(tx: PaymentTransaction):
        return PaymentVerificationResult(
            status=VerificationStatus.REFERENCE_NOT_FOUND,
            tx=tx
        )

    @staticmethod
    def inconsistent(tx: PaymentTransaction):
        return PaymentVerificationResult(
            status=VerificationStatus.INCONSISTENT,
            tx=tx
        )


class PaymentVerificationService:

    def __init__(
        self,
        *,
        gateway_registry: PaymentGatewayRegistry
    ):
        self.gateway_registry = gateway_registry

    def _get_transaction(self, *, id: str | UUID) -> PaymentTransaction:
        return PaymentTransaction.objects.get(id=id)

    def _get_locked_transaction(
        self,
        *,
        id: str | UUID
    ) -> PaymentTransaction:

        return (
            PaymentTransaction.objects
            .select_for_update()
            .get(id=id)
        )

    def _parse_paid_at(
        self,
        *,
        provider_data: dict[str, Any]
    ) -> datetime:
        return provider_data.get("paid_at")

    def _handle_reference_not_found(
        self,
        *,
        tx: PaymentTransaction
    ) -> PaymentVerificationResult:

        with transaction.atomic():
            locked_tx = self._get_locked_transaction(id=tx.id)

            if locked_tx.status == PaymentTransactionStatus.SUCCESS:
                return PaymentVerificationResult(
                    status=VerificationStatus.SUCCESS,
                    transaction_id=str(locked_tx.id),
                )

            locked_tx.status = PaymentTransactionStatus.INITIALIZATION_FAILED
            locked_tx.verification_failure_reason(
                "The payment provider could not locate "
                "the transaction reference"
            )

            locked_tx.save(
                update_fields=[
                    "status",
                    "verification_failure_reason",
                    "updated_at"
                ]
            )

        return PaymentVerificationResult.reference_not_found(tx)

    def _handle_pending(
        self,
        *,
        transaction_id: str,
        provider_data: dict[str, Any]
    ) -> PaymentVerificationResult:

        with transaction.atomic():
            locked_tx = self._get_locked_transaction(
                id=transaction_id
            )

            if locked_tx.status == PaymentTransactionStatus.SUCCESS:
                return PaymentVerificationResult.success(locked_tx)

            locked_tx.provider_status = provider_data.get("status")
            locked_tx.provider_response = provider_data

            locked_tx.save(
                update_fields=[
                    "provider_status",
                    "provider_response",
                    "updated_at"
                ]
            )

            return PaymentVerificationResult.pending(locked_tx)

    def _handle_failed(
        self,
        *,
        transaction_id: str,
        provider_data: dict[str, Any]
    ) -> PaymentVerificationResult:

        with transaction.atomic():
            locked_tx = self._get_locked_transaction(
                id=transaction_id
            )

            if locked_tx.status == PaymentTransactionStatus.SUCCESS:
                return PaymentVerificationResult.success(locked_tx)

            locked_tx.status = PaymentTransactionStatus.FAILED
            locked_tx.provider_status = provider_data.get("status")
            locked_tx.verification_failure_reason = (
                provider_data.get("gateway_response")
                or "Payment was declined by the privider"
            )
            locked_tx.provider_response = provider_data

            locked_tx.save(
                update_fields=[
                    "status",
                    "provider_status",
                    "verification_failure_reason",
                    "provider_response",
                    "updated_at"
                ]
            )

            return PaymentVerificationResult.failed(locked_tx)

    def _handle_reversed(
        self,
        *,
        transaction_id: str,
        provider_data: dict[str, Any]
    ) -> PaymentVerificationResult:

        with transaction.atomic():
            locked_tx = self._get_locked_transaction(
                id=transaction_id
            )

            if locked_tx.status == PaymentTransactionStatus.SUCCESS:
                PaymentVerificationResult.success(locked_tx)

            locked_tx.status = PaymentTransactionStatus.REVERSED
            locked_tx.provider_status = provider_data.get("status")
            locked_tx.provider_response = provider_data

            locked_tx.save(
                update_fields=[
                    "status",
                    "provider_status",
                    "provider_response",
                    "updated_at"
                ]
            )

            return PaymentVerificationResult.reversed(locked_tx)

    def _mark_orders_paid(
        self,
        *,
        payment: Payment,
        paid_at: datetime
    ):
        orders = list(
            payment.order_group.orders.all()
            .select_for_update()
        )
        for order in orders:
            order.is_paid = True
            order.paid_at = paid_at

        Order.objects.bulk_update(orders, [
            "is_paid",
            "paid_at",
            "updated_at"
        ])

    def _commit_success(
        self,
        *,
        transaction_id: str,
        provider_data: dict[str, Any]
    ) -> PaymentVerificationResult:

        with transaction.atomic():
            locked_tx = self._get_locked_transaction(
                id=transaction_id
            )
            payment = (
                Payment.objects
                .select_for_update()
                .get(id=locked_tx.payment_id)
            )

            if locked_tx.status == PaymentTransactionStatus.SUCCESS:
                return PaymentVerificationResult.success(locked_tx)

            if payment.active_transaction_id != locked_tx.id:
                raise PaymentTransactionStateChangedError(
                    action="verifying"
                )

            paid_at = self._parse_paid_at(provider_data=provider_data)

            locked_tx.status = PaymentTransactionStatus.SUCCESS
            locked_tx.provider_status = provider_data.get("status")
            locked_tx.channel = provider_data.get("channel")
            locked_tx.paid_at = paid_at
            locked_tx.verified_at = now()
            locked_tx.provider_response = provider_data

            locked_tx.save(
                update_fields=[
                    "status",
                    "provider_status",
                    "channel",
                    "paid_at",
                    "verified_at",
                    "provider_response",
                    "updated_at"
                ]
            )

            payment.status = PaymentStatus.VERIFIED
            payment.paid_at = paid_at
            payment.active_transaction = None

            payment.save(
                update_fields=[
                    "status",
                    "paid_at",
                    "active_transaction",
                    "updated_at"
                ]
            )

            self._mark_orders_paid(
                payment=payment,
                paid_at=paid_at
            )

            return PaymentVerificationResult.success(locked_tx)

    def _validate_provider_reference(
        self,
        *,
        tx: PaymentTransaction,
        provider_data: dict[str, Any]
    ) -> PaymentVerificationResult | None:

        if provider_data.get("reference") != str(tx.reference):
            return self._handle_inconsistency_error(
                tx=tx,
                provider_data=provider_data,
                error="Payment verification reference does not match."
            )

    def _validate_provider_data(
        self,
        *,
        tx: PaymentTransaction,
        provider_data: dict[str, Any]
    ) -> None:

        if provider_data.get("amount") != tx.amount:
            raise PaymentAmountMismatchError()

        if provider_data.get("currency") != tx.currency:
            raise PaymentCurrencyMismatchError()

        customer = provider_data.get("customer") or {}

        if customer.get("email") != tx.customer_email:
            raise PaymentCustomerMismatchError()

        metadata = provider_data.get("metadata") or {}

        if (
            metadata.get("payment_id") != str(tx.payment_id)
            or metadata.get("order_group_id") != str(tx.payment.order_group_id)
        ):
            raise PaymentMetadataMismatchError()

    def _handle_inconsistency_error(
        self,
        *,
        tx: PaymentTransaction,
        provider_data: dict[str, Any],
        error: PaymentVerificationError
    ) -> PaymentVerificationResult:

        with transaction.atomic():
            locked_tx = (
                PaymentTransaction.objects
                .select_for_update()
                .get(id=tx.id)
            )

            locked_tx.status = PaymentTransactionStatus.INCONSISTENT
            locked_tx.channel = provider_data.get("channel")
            locked_tx.provider_status = provider_data.get("status")
            locked_tx.verification_failure_reason = str(error)
            locked_tx.provider_response = provider_data

            locked_tx.save(
                update_fields=[
                    "status",
                    "channel",
                    "provider_status",
                    "verification_failure_reason",
                    "provider_response",
                    "updated_at"
                ]
            )

            return PaymentVerificationResult.inconsistent(locked_tx)

    def _process_provider_data(
        self,
        *,
        tx: PaymentTransaction,
        provider_data: dict[str, Any]
    ) -> PaymentVerificationResult:

        provider_status = provider_data.get("status")

        if provider_status in {
            "pending",
            "processing",
            "ongoing",
            "queued",
        }:
            return self._handle_pending(
                transaction_id=str(tx.id),
                provider_data=provider_data
            )

        try:
            self._validate_provider_data(
                tx=tx,
                provider_data=provider_data
            )

        except PaymentVerificationError as exc:
            return self._handle_inconsistency_error(
                tx=tx,
                provider_data=provider_data,
                error=exc
            )

        if provider_status in {
            "failed",
            "abandoned",
        }:
            return self._handle_failed(
                transaction_id=str(tx.id),
                provider_data=provider_data
            )

        if provider_status == "reversed":
            return self._handle_reversed(
                transaction_id=str(tx.id),
                provider_data=provider_data
            )

        if provider_status == "success":
            return self._commit_success(
                transaction_id=str(tx.id),
                provider_data=provider_data
            )

        raise PaymentProviderStatusError()

    def verify(
        self,
        *,
        transaction_id: str | UUID
    ) -> PaymentVerificationResult:
        tx = self._get_transaction(id=transaction_id)

        if tx.status == PaymentTransactionStatus.SUCCESS:
            return PaymentVerificationResult.success(tx)

        gateway = self.gateway_registry.get(tx.provider)

        try:
            provider_data = gateway.verify_payment(
                reference=str(tx.reference)
            )

        except PaymentReferenceNotFoundError:
            return self._handle_reference_not_found(
                tx=tx
            )

        except PaymentGatewayError:
            raise

        self._validate_provider_reference(
            tx=tx,
            provider_data=provider_data
        )

        return self._process_provider_data(
            tx=tx,
            provider_data=provider_data
        )


def get_payment_verification_service() -> PaymentVerificationService:
    gateway_registry = PaymentGatewayRegistry()
    return PaymentVerificationService(gateway_registry=gateway_registry)
