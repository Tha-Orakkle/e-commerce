from dataclasses import dataclass
from typing import Any

from django.db import transaction
from django.utils.timezone import now, timedelta

from order.models import OrderGroup
from payment.domain.exceptions import (
    DuplicatePaymentError,
    PaymentGatewayError,
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


@dataclass
class PaymentInitializationResult:
    authorization_url: str
    reference: str
    status: str


class InitializePaymentService:
    MAX_RETRIES = 1

    def __init__(self, gateway_registry):
        self.gateway_registry = gateway_registry

    def initialize(
        self,
        *,
        order_group: OrderGroup,
        provider: str
    ) -> PaymentInitializationResult:

        gateway = self.gateway_registry.get(provider)

        return self._initialize(
            order_group=order_group,
            provider=provider,
            gateway=gateway,
            retry_count=0
        )

    def _initialize(
        self,
        *,
        order_group: OrderGroup,
        provider: str,
        gateway: PaymentGateway,
        retry_count: int
    ) -> PaymentInitializationResult:

        with transaction.atomic():
            payment = (
                Payment.objects
                .select_for_update()
                .select_related("active_transaction")
                .get(order_group=order_group)
            )

            if payment.status == PaymentStatus.VERIFIED:
                raise DuplicatePaymentError()

            tx = payment.active_transaction

            if tx is None or tx.status in {
                PaymentTransactionStatus.EXPIRED,
                PaymentTransactionStatus.FAILED
            }:
                tx = self._create_new_transaction(
                    payment=payment,
                    provider=provider,
                    customer_email=order_group.user.email
                )

                action = "initialize"

            elif tx.status == PaymentTransactionStatus.SUCCESS:
                self._mark_payment_verified(
                    payment=payment,
                    tx=tx
                )
                return PaymentInitializationResult(
                    authorization_url=None,
                    reference=str(tx.reference),
                    status=PaymentTransactionStatus.SUCCESS
                )

            elif tx.status == PaymentTransactionStatus.PENDING:
                action = "verify"

            else:
                raise PaymentTransactionStatusError(
                    f"Unknown transaction status: {tx.status}"
                )

            transaction_id = tx.id

        metadata = {
            "order_group": str(order_group.id),
            "payment_id": str(payment.id)
        }

        if action == "initialize":
            provider_response = self._initialize_with_payment_provider(
                gateway=gateway,
                transaction=tx,
                metadata=metadata
            )
        elif action == "verify":
            provider_response = self._verify_payment_with_provider(
                gateway=gateway,
                transaction=tx,
                metadata=metadata
            )

        with transaction.atomic():
            payment = (
                Payment.objects
                .select_for_update()
                .select_related("active_transaction")
                .get(order_group=order_group)
            )

            if payment.status == PaymentStatus.VERIFIED:
                raise DuplicatePaymentError()

            if payment.active_transaction_id != transaction_id:

                return self._handle_transaction_changed(
                    payment=payment,
                    provider=provider,
                    gateway=gateway,
                    order_group=order_group,
                    retry_count=retry_count
                )

            tx = (
                PaymentTransaction.objects
                .select_for_update()
                .get(id=transaction_id)
            )

            if action == "initialize":
                return self._reconcile_initialization(
                    tx=tx,
                    provider_response=provider_response
                )
            elif action == "verify":
                return self._reconcile_verification(
                    payment=payment,
                    tx=tx,
                    provider_response=provider_response
                )

    def _create_new_transaction(
        self,
        *,
        payment: Payment,
        provider: str,
        customer_email: str
    ) -> PaymentTransaction:

        expires_at = now() + timedelta(minutes=30)

        tx = PaymentTransaction.objects.create(
            payment=payment,
            customer_email=customer_email,
            provider=provider,
            currency=payment.currency,
            amount=payment.amount,
            expires_at=expires_at
        )

        payment.active_transaction = tx
        payment.save(
            update_fields=[
                "active_transaction",
                "updated_at"
            ]
        )
        return tx

    def _handle_transaction_changed(
        self,
        *,
        payment: Payment,
        provider: str,
        gateway: PaymentGateway,
        order_group: OrderGroup,
        retry_count: int
    ):
        current_tx = payment.active_transaction

        if current_tx is None:
            if retry_count >= self.MAX_RETRIES:
                raise PaymentTransactionStateChangedError()

            return self._initialize(
                order_group=order_group,
                provider=provider,
                gateway=gateway,
                retry_count=retry_count + 1
            )

        elif current_tx.status == PaymentTransactionStatus.SUCCESS:
            self._mark_payment_verified(
                payment=payment,
                tx=current_tx
            )

            return PaymentInitializationResult(
                authorization_url=None,
                reference=str(current_tx.reference),
                status=PaymentTransactionStatus.SUCCESS
            )

        elif current_tx.status in {
            PaymentTransactionStatus.EXPIRED,
            PaymentTransactionStatus.FAILED
        }:
            if retry_count >= self.MAX_RETRIES:
                raise PaymentTransactionStateChangedError()

            return self._initialize(
                order_group=order_group,
                provider=provider,
                gateway=gateway,
                retry_count=retry_count + 1
            )

        elif current_tx.status == PaymentTransactionStatus.PENDING:

            if current_tx.authorization_url:
                raise PaymentTransactionStateChangedError()

            if retry_count >= self.MAX_RETRIES:
                raise PaymentTransactionStateChangedError()

            return self._initialize(
                order_group=order_group,
                provider=provider,
                gateway=gateway,
                retry_count=retry_count + 1
            )

        raise PaymentTransactionStatusError(
            f"Unexpected transaction status: {current_tx.status}"
        )

    def _mark_payment_verified(
        self,
        *,
        payment: Payment,
        tx: PaymentTransaction
    ):

        payment.status = PaymentStatus.VERIFIED
        payment.active_transaction = None
        payment.paid_at = tx.paid_at

        payment.save(
            update_fields=[
                "active_transaction",
                "paid_at",
                "status",
                "updated_at"
            ]
        )

    def _initialize_with_payment_provider(
        self,
        *,
        gateway: PaymentGateway,
        transaction: PaymentTransaction,
        metadata: dict[str, str]
    ) -> dict[str, Any]:

        try:
            response = gateway.initialize_payment(
                reference=str(transaction.reference),
                amount=transaction.amount,
                currency=transaction.currency,
                email=transaction.customer_email,
                metadata=metadata
            )
        except PaymentGatewayError as exc:
            # work in progress
            # log the exact error message
            raise PaymentGatewayError(
                "Payment gateway initialization failed.",
                status_code=exc.status_code
            )

        return response["data"]

    def _reconcile_initialization(
        self,
        *,
        tx: PaymentTransaction,
        provider_response: dict[str, Any]
    ):
        tx.authorization_url = provider_response.get("authorization_url")
        tx.save(
            update_fields=[
                "authorization_url",
                "updated_at"
            ]
        )
        return PaymentInitializationResult(
            authorization_url=tx.authorization_url,
            reference=str(tx.reference),
            status=PaymentTransactionStatus.PENDING
        )

    def _reconcile_verification(
        self,
        *,
        payment: Payment,
        tx: PaymentTransaction,
        provider_response: dict[str, Any]
    ):
        # check provider status
        # if transaction was a success/failed
        # update payment and transaction
        # set active transaction to None
        # updated the paid at date.
        # call update all orders to paid where necessary
        # return PaymentInitialization Result
        # Leave payment as pending if payment has not been made
        # return PaymentInitializationResult with current_tx authorization_url
        pass

    def _verify_payment_with_provider(
        self,
        *,
        gateway: PaymentGateway,
        transaction: PaymentTransaction,
        metadata: dict[str, str]
    ) -> dict[str, Any]:

        pass
