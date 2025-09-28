from celery import shared_task
from django.db import transaction
from django.utils.timezone import now
from datetime import timedelta

from order.models import Order, OrderGroup
from product.models import Inventory

@shared_task
def restock_inventory_with_cancelled_order(id, order_group=False):
    
    # If order_group is True, id is treated as an OrderGroup ID
    if order_group:
        o_group = OrderGroup.objects.prefetch_related('orders__items__product__inventory').filter(id=id).first()
        if not o_group:
            return
        for order in o_group.orders.all():
            for item in order.items.all():
                with transaction.atomic():
                    inventory = Inventory.objects.select_for_update().filter(product=item.product).first()
                    if inventory:
                        inventory.add(item.quantity, 'sys_cancelled_order')
        return f"Inventory restocked from order group {o_group.id} with {o_group.orders.count()} orders."
    
    
    order = Order.objects.prefetch_related('items__product__inventory').filter(id=id).first()
    if not order:
        return
    for item in order.items.all():
        with transaction.atomic():
            inventory = Inventory.objects.select_for_update().filter(product=item.product).first()
            if inventory:
                inventory.add(item.quantity, 'sys_cancelled_order')
    return f"Inventory restocked from order {order.id} with {order.items.count()} items."



@shared_task
def cancel_unpaid_orders_older_than_4_hours():
    """
    Cancel unpaid DIGITAL order groups older than 4 hours,
    and trigger inventory restock asynchronously.
    """
    cutoff_time = now() - timedelta(hours=4)
    
    order_groups = OrderGroup.objects.filter(
        status='PENDING',
        payment_method='DIGITAL',
        is_paid=False,
        created_at__lt=cutoff_time
    )
    cancelled_orders = 0
    total_group_count = 0
    total_item_count = 0

    for group in order_groups:
        with transaction.atomic():
            total_group_count += 1
            group.status = 'CANCELLED'
            group.cancelled_at = now()
            group.save(update_fields=['status', 'cancelled_at'])
            orders = group.orders.all()
            for order in orders:
                total_item_count += order.items.count()
                order.status = 'CANCELLED'
                order.save(update_fields=['status'])
                cancelled_orders += 1
                transaction.on_commit(
                    lambda order_id=order.id: restock_inventory_with_cancelled_order.delay(order_id))

    return f"TOTAL ORDER GROUPS: {total_group_count}.\n \
        Cancelled {cancelled_orders} unpaid orders (with {total_item_count} items) older than 4 hours."



