from dataclasses import dataclass
from decimal import Decimal
from django.db import transaction
from django.utils.timezone import now, timedelta
from typing import Any

import uuid

from order.models import OrderGroup
from payment.domain.exceptions import DuplicatePaymentError, PaymentProviderError
from payment.gateways.ports import PaymentGateway
from payment.models import (
    NewPayment,
    PaymentTransaction,
    PaymentStatus,
    PaymentTransactionStatus
)


class InitializePaymentService:

    def __init__(self, gateway_registry):
        self.gateway_registry = gateway_registry

    def _get_authoritative_amount(order_group: OrderGroup) -> Decimal:
        """
        Get total amount of the order group
        and convert to smallest unit.
        """
        return order_group.total_amount * 100

    def _generate_reference(self):
        """
        Generate the reference to be used by payment providers.
        """
        return uuid.uuid4()

    def _create_new_transaction(
        self,
        *,
        payment: NewPayment,
        provider: str,
        customer_email: str
    ):
        expires_at = now() + timedelta(minutes=30)
        return PaymentTransaction.objects.create(
            payment=payment,
            reference=self._generate_reference(),
            customer_email=customer_email,
            provider=provider,
            currency=payment.currency,
            amount=payment.amount,
            expires_at=expires_at
        )

    def _update_completed_payment(
        self,
        payment: NewPayment,
        tx: PaymentTransaction
    ):
        payment.status == PaymentStatus.VERIFIED
        payment.active_transaction = None
        payment.paid_at = tx.paid_at,
        payment.save(update_fields=[
            "status", "active_transaction", "paid_at", "updated_at"
        ])
        # raise DuplicatePaymentError()
        # use something else to indicate successful payment

    def _initialize_with_payment_provider(
        self,
        *,
        gateway: PaymentGateway,
        transaction: PaymentTransaction,
        metadata: dict[str, str]
    ):
        response = gateway.initialize_payment(
            reference=transaction.reference,
            amount=transaction.amount,
            currency=transaction.currency,
            email=transaction.customer_email,
            metadata=metadata
        )
        return response

    def initialize(
        self,
        *,
        order_group: OrderGroup,
        provider: str
    ):
        with transaction.atomic():
            payment = (
                NewPayment.objects
                .select_for_update()
                .select_related("active_transaction")
                .get(order_group=order_group)
            )

            if payment.status == PaymentStatus.VERIFIED:
                raise DuplicatePaymentError()

            tx = payment.active_transaction

            if tx is None or (tx and tx.status in {
                PaymentTransactionStatus.FAILED,
                PaymentTransactionStatus.EXPIRED
            }):
                tx = self._create_new_transaction(
                    payment=payment,
                    provider=provider,
                    customer_email=order_group.user.email
                )
                action = "initialize"

            elif tx.status == PaymentTransactionStatus.SUCCESS:
                self._update_completed_payment()
                return
                # return successful payment

            elif tx.status == PaymentTransactionStatus.PENDING:
                action = "verify"

            transaction_id = tx.id
            reference = str(tx.reference)

        gateway = self.gateway_registry.get(provider)
        metadata = {
            "order_group_id": str(order_group.id),
            "payment_id": str(payment.id)
        }

        if action == "initialize":
            payload = self._initialize_with_payment_provider(
                gateway=gateway,
                transaction=tx,
                metadata=metadata
            )
            with transaction.atomic():
                payment = (
                    NewPayment.objects
                    .select_for_update()
                    .select_related("active_transaction")
                    .get(order_group=order_group)
                )
                if payment.status == PaymentStatus.VERIFIED:
                    raise DuplicatePaymentError()
                if payment.active_transaction.id != transaction_id:
                    return 
                
        elif action == "verify":
            # Verify payment from gateway
            self._verify_from_payment_provider(
                gateway=gateway,
                transaction=tx,
                metadata=metadata
            )


@dataclass
class PaymentInitializationResult:
    authorization_url: str
    payment_id: str
    transacton_id: str
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
                NewPayment.objects
                .select_for_update()
                .select_related("active_transaction")
                .get(order_group=order_group)
            )

            if payment.status == PaymentStatus.VERIFIED:
                raise DuplicatePaymentError()

            tx = payment.active_transaction
            
            if tx is None:
                tx = self._create_new_transaction(
                    payment=payment,
                    provider=provider,
                    customer_email=order_group.user.email
                )

                action = "initialize"

            elif tx.status in {
                PaymentTransactionStatus.FAILED,
                PaymentTransactionStatus.EXPIRED
            }:
                tx = self._create_new_transaction(
                    payment=payment,
                    provider=provider,
                    customer_email=order_group.user.email
                )
            
                action = "initialize"

            elif tx.status == PaymentTransactionStatus.SUCCESS:
                self._mark_payment_verified(
                    payment,
                    tx=tx
                )
                return PaymentInitializationResult(
                    authorization_url=None,
                    payment_id=payment.id,
                    transacton_id=tx.id,
                    status=PaymentTransactionStatus.SUCCESS
                )
            elif tx.status == PaymentTransactionStatus.PENDING:
                
                if tx.authorization_url:
                    return PaymentInitializationResult(
                        authorization_url=tx.authroization_url,
                        payment_id=payment.id,
                        transacton_id=tx.id,
                        status=PaymentTransactionStatus.PENDING
                    )
                
                # check again
                action = "verify"
            
            else:
                # write another error for this
                raise PaymentProviderError(
                    f"Unknown transaction status: {tx.status}"
                )

            transaction_id = tx.id
            reference = tx.reference

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

        else:
            raise AssertionError(f"Unknow action: {action}")

        with transaction.atomic():
            payment = (
                NewPayment.objects
                .select_for_update()
                .select_related("active_transaction")
                .get(order_group=order_group)
            )
            
            

    def _create_new_transaction(
        self,
        *,
        payment: NewPayment,
        provider: str,
        customer_email: str
    ) -> PaymentTransaction:

        expires_at = now() + timedelta(minutes=30)

        tx = PaymentTransaction.objects.create(
            payment=payment,
            reference=self._generate_reference(),
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

    def _mark_payment_verified(
        payment: NewPayment,
        tx: PaymentTransaction
    ):
        # tx.status = PaymentTransactionStatus.SUCCESS
        # tx.save(
        #     update_fields=[
        #         "status",
        #         "updated_at"
        #     ]
        # )

        payment.status = PaymentStatus.VERIFIED
        payment.active_transaction = None

        payment.save(
            update_fields=[
                "status",
                "active_transaction",
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
        
        pass

    def _verify_payment_with_provider(
        self,
        *,
        gateway: PaymentGateway,
        transaction: PaymentTransaction,
        metadata: dict[str, str]
    ) -> dict[str, Any]:

        pass