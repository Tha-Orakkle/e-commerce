from celery import shared_task
from django.db import transaction
from django.utils.timezone import now
from datetime import timedelta

from order.models import Order
from product.models import Inventory

@shared_task
def restock_inventory_with_cancelled_order(order_id):
    order = Order.objects.prefetch_related('items__product__inventory').filter(id=order_id).first()
    if not order:
        return
    for item in order.items.all():
        with transaction.atomic():
            inventory = Inventory.objects.select_for_update().filter(product=item.product).first()
            if inventory:
                inventory.add(item.quantity, 'system')
    return f"Inventory restocked for order {order.id} with {len(order.items.all())} items."



@shared_task
def cancel_unpaid_orders_older_than_4_hours():
    """
    Cancel unpaid DIGITAL orders older than 4 hours,
    and trigger inventory restock asynchronously.
    """
    cutoff_time = now() - timedelta(hours=4)
    orders = Order.objects.filter(
        status='PENDING',
        payment_method='DIGITAL',
        is_paid=False,
        created_at__lt=cutoff_time
    )
    cancelled_orders = 0
    _temp_items = 0

    for order in orders:
        with transaction.atomic():
            _temp_items += order.items.first().quantity
            order.status = 'CANCELLED'
            order.save(update_fields=['status'])
            cancelled_orders += 1
            transaction.on_commit(
                lambda: restock_inventory_with_cancelled_order.delay(order.id))
    return f"TOTAL ITEMS: {_temp_items}. Cancelled {cancelled_orders} unpaid orders older than 4 hours."



