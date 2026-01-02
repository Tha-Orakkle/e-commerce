from django.db import transaction
from django.utils.timezone import now 

from common.exceptions import ErrorException
from order.models import Order, OrderGroup, OrderGroupStatus, OrderStatus
from order.tasks import restock_inventory_with_cancelled_order, update_group_status_for_orders
from order.utils.validators import validate_delivery_date

class OrderStateMachine:
    ALLOWED_TRANSACTIONS = {
        'PROCESSING': {
            'from': ['PENDING'],
            'requires_payment': True,
            'update_field': 'processing_at'
            
        },
        'SHIPPED': {
            'from': ['PROCESSING'], 
            'requires_payment': True,
            'disallowed_fulfillment': ['PICKUP'],
            'update_field': 'shipped_at'
        },
        'COMPLETED': {
            'from_pickup': ['PROCESSING'],
            'from_delivery': ['SHIPPED'],
            'requires_payment': True,
            'cash_requires_status': True,
            'update_field': 'completed_at'
        },
        'CANCELLED': {
            'from': ['PENDING', 'PROCESSING'],
            'update_field': 'cancelled_at'
        }
    }
    
    # To be implemented for notifications and logging
    # HOOKS = {
    #     ('PENDING', 'PROCESSING'): ['mark_as_paid', 'send_payment_confirmation'],
    #     ('PROCESSING', 'SHIPPED'): ['ship_order', 'notify_customer_shipping'],
    #     ('SHIPPED', 'COMPLETED'): ['finalize_order'],
    #     ('PENDING', 'CANCELLED'): ['release_inventory', 'notify_customer_cancellation'],
    #     ('PROCESSING', 'CANCELLED'): ['release_inventory', 'refund_payment'],
    # }
    
    def __init__(self, order, group, payment_status=False, delivery_date=None):
        """
        Initialize the OrderStateMachine.
        """
        self.order = order
        self.group = group
        self.payment_status = payment_status
        self.delivery_date = delivery_date

    def _get_rules(self, new_status):
        """
        Get the rules for the new status to be transitioned to.
        """
        rules = self.ALLOWED_TRANSACTIONS.get(new_status)
        if not rules:
            raise ErrorException(detail="Invalid status provided.", code='invalid_status')
        return rules

    def _raise(self, msg, code='invalid_status_transition'):
        """
        Raise Error Exceptions.
        """
        raise ErrorException(detail=msg, code=code)

    def _is_self_transition(self, new_status):
        """
        Check if transition is being made to the same status.
        """
        return new_status == self.order.status
    
    def _structural_check(self, new_status, rules):
        """
        Check if transition from one status to another is allowed.
        """
        old = self.order.status
        if new_status == 'COMPLETED':
            allowed = rules.get('from_delivery', []) if self.group.fulfillment_method == 'DELIVERY' else rules.get('from_pickup', [])
        else: 
            allowed = rules.get('from', [])
        if old not in allowed:
            self._raise(msg=f"Invalid transition from {old} to {new_status}.")
            
    def _payment_check(self, new_status, rules):
        if not rules.get('requires_payment'):
            return
         
        if self.group.payment_method == 'DIGITAL' and not self.order.is_paid:
            self._raise(
                msg="Digital orders must be paid before transition.", 
                code='invalid_payment_status'
            )
        if (self.group.payment_method == 'CASH' and not self.order.is_paid
            and rules.get('cash_requires_status') and not self.payment_status
        ):
            self._raise(
                msg="Cash orders must be marked paid before completing.",
                code='invalid_payment_status'
            )

    def _fulfillment_check(self, new_status, rules):
        disallowed = rules.get('disallowed_fulfillment',[])
        if disallowed and self.group.fulfillment_method in disallowed:
            self._raise(f"{self.group.fulfillment_method} orders can not be {new_status.lower()}.")

    def _extra_check(self, new_status):
        if new_status == 'SHIPPED' and self.group.fulfillment_method == 'DELIVERY':
            validate_delivery_date(self.delivery_date) 

    def _update_timestamp(self, rules):
        update_field = rules.get('update_field')
        if update_field:
            setattr(self.order, update_field, now())
    
    def _update_is_delivered_or_picked(self, new_status):
        if new_status == 'COMPLETED':
            if self.group.fulfillment_method == 'DELIVERY':
                self.order.is_delivered = True
                field = 'is_delivered'
            elif self.group.fulfillment_method == 'PICKUP':
                self.order.is_picked_up = True
                field = 'is_picked_up'
            return field
        return None

    def _update_group_status(self, new_status):
        qs = self.group.orders.all()
        total = qs.count()
        completed = qs.filter(status='COMPLETED').count()

        if total == 0:
            return False

        if total == completed:
            if self.group.status != 'FULFILLED':
                self.group.status = 'FULFILLED'
                # implement on commit operation to anonymise user data if user is deleted
                return True
            return False

        if completed > 0 and self.group.status != 'PARTIALLY_FULFILLED':
            self.group.status = 'PARTIALLY_FULFILLED'
            return True 
        return False   

    def _update_is_paid_for_completed_cash_order(self, new_status):
        if new_status == 'COMPLETED' and self.group.payment_method == 'CASH' and self.payment_status:
            self.order.is_paid = True
            self.order.paid_at = now()
            return True
        return False
        
    # def _run_hooks_after_commit(self, old_status, new_status):
    #     hooks = getattr(self, 'HOOKS', {}).get(old_status, new_status)
    #     if not hooks:
    #         return
    #     def call_hooks():
    #         # hook_name will be the function to be defined
    #         for hook_name in hooks:
    #             hook = getattr(self, hook_name, None)
    #             if hook:
    #                 try:
    #                     hook()
    #                 except:
    #                     pass
    #     transaction.on_commit(call_hooks)
                

    def validate_transition(self, new_status):
        """
        Run pre-transition checks for transition feasibility.
        """
        rules = self._get_rules(new_status)
        
        if self._is_self_transition(new_status):
            self._raise(msg=f"Order {str(self.order.id)} is already in {new_status} state.")
        
        self._structural_check(new_status, rules)
        self._payment_check(new_status, rules)
        self._fulfillment_check(new_status, rules)
        self._extra_check(new_status)
        return True
    
    def transition_to(self, new_status):
        """
        Transition order from one state to another.
        """
        
        rules = self._get_rules(new_status)
        self.validate_transition(new_status)
        
        
        with transaction.atomic():
            locked_order = Order.objects.select_for_update().select_related('group').get(id=self.order.id)
            locked_group = OrderGroup.objects.select_for_update().get(id=self.group.id)
            self.order = locked_order
            self.group = locked_group
            
            self._structural_check(new_status, rules)
            self._payment_check(new_status, rules)
            self._fulfillment_check(new_status, rules)
        
            # old_status = self.order.status
            self.order.status = new_status
            update_fields = ['status']
            
            
            if new_status == 'SHIPPED' and self.group.fulfillment_method == 'DELIVERY':
                self.order.delivery_date = self.delivery_date
                update_fields.append('delivery_date')
                
            self._update_timestamp(rules)
            f = self._update_is_delivered_or_picked(new_status)
            uf = rules.get('update_field')
            pf = self._update_is_paid_for_completed_cash_order(new_status)
            
            if f:
                update_fields.append(f)
            if uf:
                update_fields.append(uf)
            if pf:
                update_fields.extend(['is_paid', 'paid_at'])

            update_fields = list(dict.fromkeys(update_fields))  # dedupe duplicate fields
            self.order.save(update_fields=update_fields)
            
            if self._update_group_status(new_status):
                self.group.save(update_fields=['status'])
            
            if new_status == 'CANCELLED':
                transaction.on_commit(
                    lambda: restock_inventory_with_cancelled_order.delay(self.order.id))
            
            # self._run_hooks_after_commit(old_status, new_status)
            
        return self.order


    @staticmethod
    def cancel_customer_pending_orders(customer):
        """
        Cancel all pending orders belonging to a customer.
        """
        with transaction.atomic():
            all_order_grps = (
                OrderGroup.objects.select_for_update()
                    .filter(
                        user=customer,
                        status__in = [
                            OrderGroupStatus.PENDING,
                            OrderGroupStatus.PARTIALLY_FULFILLED
                        ]
                    )
            )
            updated_orders = []
            updated_grps = []
            for g in all_order_grps:
                pending_orders = g.orders.select_for_update().filter(status=OrderStatus.PENDING)
                for o in pending_orders:
                    o.status = OrderStatus.CANCELLED
                updated_orders.extend(pending_orders)
                if g.status == OrderGroupStatus.PENDING:
                    g.status = OrderGroupStatus.CANCELLED
                    updated_grps.append(g)
            if updated_grps:
                OrderGroup.objects.bulk_update(updated_grps, ['status'])
            if updated_orders:
                Order.objects.bulk_update(updated_orders, ['status'])
        return True
    

    @staticmethod
    def cancel_shop_pending_orders(shop):
        """
        Cancel all pending orders belonging to a shop.
        """
        with transaction.atomic():
            pending_orders = list(
                Order.objects.select_for_update()
                    .filter(
                        shop=shop,
                        status=OrderStatus.PENDING
                    )
            )
            for o in pending_orders:
                o.status = OrderStatus.CANCELLED
                
            if pending_orders:
                Order.objects.bulk_update(pending_orders, ['status'])

            pending_orders_id = [o.id for o in pending_orders]
            
            transaction.on_commit(
                lambda: update_group_status_for_orders.delay(pending_orders_id)
            )
            return True
