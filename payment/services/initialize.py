from decimal import Decimal

import uuid

from order.models import OrderGroup


class InitializePaymentService:

    def __init__(self, gateway_fatory):
        self.gateway_fatory = gateway_fatory

    def _get_authoritative_amount(order_group: OrderGroup) -> Decimal:
        """
        Get total amount of the order group
        and convert to smallest unit.
        """
        return order_group.total_amount

    def _generate_reference(self):
        """
        Generate the reference to be used by payment providers.
        """
        return uuid.uuid4()

    def _get_or_create_payment(self, order_group):
        pass

    def initialize_payment(
        self,
        *,
        order_group: OrderGroup,
        provider: str
    ):
        amount = self._get_authoritative_amount(order_group)
        payment = self._get_or_create_payment(order_group)
