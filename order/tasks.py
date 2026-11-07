import logging
from datetime import timedelta

from celery import shared_task
from django.db import transaction
from django.utils.timezone import now

from order.models import (
    Order,
    OrderGroup,
    OrderGroupStatus,
    OrderOutboxEvent,
    OrderOutboxEventStatus,
    OrderOutboxEventType,
    OrderStatus,
    PaymentMethod,
)
from payment.models import Payment, PaymentStatus
from product.models import Inventory

RESTOCK_HANDLE = 'sys_cancelled_order'
UNPAID_ORDER_MAX_AGE = timedelta(hours=4)

# Outbox
OUTBOX_BATCH_SIZE = 100
OUTBOX_RETRY_BASE_SECONDS = 30
OUTBOX_RETRY_MAX_SECONDS = 60 * 60

logger = logging.getLogger(__name__)


def _restock_order(order_id):
    """
    Return a cancelled order's items to stock, at most once.

    The order row is locked and `restocked_at` is set in the same
    transaction as the stock update, so repeated or concurrent calls
    (task retries, group-level plus order-level dispatch) cannot add
    the stock twice.

    Returns the number of items restocked, or None if the order was
    skipped (missing, not cancelled, or already restocked).
    """
    with transaction.atomic():
        order = Order.objects.select_for_update().filter(id=order_id).first()
        if order is None or order.restocked_at is not None:
            return None
        if order.status != OrderStatus.CANCELLED:
            return None

        # Items whose product was deleted have no stock to return to.
        restorable_items = [
            i for i in order.items.all() if i.product_id is not None
        ]

        product_ids = {item.product_id for item in restorable_items}

        inventories = {
            inv.product_id: inv
            for inv in (
                Inventory.objects
                .select_for_update()
                .filter(product_id__in=product_ids)
                .order_by("id")
            )
        }

        missing_inventories = product_ids - inventories.keys()

        if missing_inventories:
            raise Inventory.DoesNotExist(
                "Cannot restock order because inventory is missing for "
                f"product IDs: {sorted(map(str, missing_inventories))}"
            )

        for item in restorable_items:
            inventories[item.product_id].add(
                item.quantity,
                RESTOCK_HANDLE
            )

        order.restocked_at = now()
        order.save(update_fields=["restocked_at", "updated_at"])

        return len(restorable_items)


@shared_task
def restock_inventory_with_cancelled_order(id, order_group=False):
    """
    Restock a cancelled order, or every order of a cancelled order group
    when `order_group` is True (then `id` is an OrderGroup ID).
    """
    if order_group:
        order_ids = list(
            Order.objects.filter(group_id=id).values_list("id", flat=True)
        )
        if not order_ids:
            return
        restocked = [
            order_id for order_id in order_ids
            if _restock_order(order_id) is not None
        ]

        return (
            f"Inventory restocked from order group {id}: "
            f"{len(restocked)} of {len(order_ids)} orders."
        )

    item_count = _restock_order(id)
    if item_count is None:
        return (
            f"Order {id} was not restocked "
            "(missing, not cancelled, or already restocked)."
        )
    return f"Inventory restocked from order {id} with {item_count} items."


def _cancel_group_if_still_unpaid(group_id, cutoff_time):
    """
    Cancel one order group and its orders if it is still pending, old
    enough and unpaid.

    The state is re-checked under row locks, so a payment that is
    verified between selecting the group and cancelling it is respected.
    Locks are taken in the same order as payment verification and the
    customer cancel view: payment, then group, then orders.

    Returns (order_count, item_count) if cancelled, otherwise None.
    """
    with transaction.atomic():
        payment = (
            Payment.objects
            .select_for_update()
            .filter(order_group_id=group_id)
            .first()
        )
        group = (
            OrderGroup.objects
            .select_for_update()
            .filter(id=group_id)
            .first()
        )
        if (
            group is None
            or group.status != OrderGroupStatus.PENDING
            or group.created_at >= cutoff_time
        ):
            return None
        if payment is not None and payment.status == PaymentStatus.VERIFIED:
            return None

        orders = list(group.orders.select_for_update())
        if any(order.is_paid for order in orders):
            return None

        cancelled_at = now()
        group.status = OrderGroupStatus.CANCELLED
        group.cancelled_at = cancelled_at
        group.save(update_fields=['status', 'cancelled_at', 'updated_at'])

        item_count = 0
        for order in orders:
            order.status = OrderStatus.CANCELLED
            order.cancelled_at = cancelled_at
            order.updated_at = cancelled_at
            item_count += order.items.count()

            OrderOutboxEvent.objects.get_or_create(
                order=order,
                event_type=OrderOutboxEventType.RESTOCK_CANCELLED_ORDER,
                defaults={"payload": str(order.id)},
            )

        Order.objects.bulk_update(
            orders, ['status', 'cancelled_at', 'updated_at']
        )
        return len(orders), item_count


@shared_task
def cancel_unpaid_orders_older_than_4_hours():
    """
    Cancel unpaid DIGITAL order groups older than 4 hours,
    and trigger inventory restock in the background.
    """
    cutoff_time = now() - UNPAID_ORDER_MAX_AGE

    candidate_ids = list(
        OrderGroup.objects
        .filter(
            status=OrderGroupStatus.PENDING,
            payment_method=PaymentMethod.DIGITAL,
            created_at__lt=cutoff_time
        )
        .exclude(orders__is_paid=True)
        .values_list('id', flat=True)
    )

    total_group_count = 0
    cancelled_orders = 0
    total_item_count = 0

    for group_id in candidate_ids:
        result = _cancel_group_if_still_unpaid(group_id, cutoff_time)
        if result is None:
            continue
        order_count, item_count = result
        total_group_count += 1
        cancelled_orders += order_count
        total_item_count += item_count

    return (
        f"TOTAL ORDER GROUPS: {total_group_count}.\n"
        f"Cancelled {cancelled_orders} unpaid orders "
        f"(with {total_item_count} items) older than 4 hours."
    )


@shared_task
def update_group_status_for_orders(order_ids):
    """
    Update the group status for orders.
    """
    group_ids = (
        Order.objects.filter(id__in=order_ids)
        .values_list('group_id', flat=True)
        .distinct()
    )
    if not group_ids:
        return True

    updated_grps = []
    s_conditions = [OrderStatus.CANCELLED, OrderStatus.COMPLETED]

    with transaction.atomic():
        groups = (
            OrderGroup.objects.select_for_update()
            .filter(id__in=group_ids)
        )

        for g in groups:
            orders = g.orders.select_for_update().all()
            total_count = orders.count()
            cancelled = g.orders.filter(status=OrderStatus.CANCELLED).count()
            done = g.orders.filter(status__in=s_conditions).count()

            if cancelled == total_count:
                g.status = OrderStatus.CANCELLED
            elif done == total_count:
                g.status = OrderStatus.COMPLETED
            else:
                continue
            updated_grps.append(g)
        if updated_grps:
            OrderGroup.objects.bulk_update(updated_grps, ['status'])

        return True


def _outbox_retry_delay(attempts):
    """
    Exponential backoff:
    30s, 60s, 120s, 240s ... capped at 1 hour.
    """
    delay = OUTBOX_RETRY_BASE_SECONDS * (2 ** (attempts - 1))
    return min(delay, OUTBOX_RETRY_MAX_SECONDS)


def _dispatch_order_outbox_event(event_id):
    """
    Publish one outbox event.

    The event row remains locked while publishing and updating its state.
    This prevents two dispatchers from publishing the same event
    concurrently under normal operation.

    Duplicate publication is still possible after a crash between broker
    acceptance and database commit. Consumers must remain idempotent.
    """
    with transaction.atomic():
        event = (
            OrderOutboxEvent.objects
            .select_for_update()
            .filter(
                id=event_id,
                status=OrderOutboxEventStatus.PENDING,
                next_attempt_at__lte=now()
            )
            .first()
        )

        if event is None:
            return "skipped"

        try:
            if event.event_type == OrderOutboxEventType.RESTOCK_CANCELLED_ORDER:
                restock_inventory_with_cancelled_order.apply_async(
                    args=[str(event.order_id)],
                    task_id=f"restock-{event.id}",
                )
            else:
                raise ValueError(
                    f"Unsupported outbox event type: {event.event_type}"
                )
        except Exception as exc:
            event.attempts += 1
            event.last_error = str(exc)[:4000]
            event.next_attempt_at = (
                now() + timedelta(
                    seconds=_outbox_retry_delay(event.attempts)
                )
            )
            event.save(
                update_fields=[
                    "attempts",
                    "last_error",
                    "next_attempt_at"
                ]
            )
            logger.exception(
                "Failed to dispatch outbox event %s (attempt %s)",
                event.id,
                event.attempts,
            )
            return "failed"

        event.mark_published()
        return "published"


@shared_task
def dispatch_order_outbox_events():
    """
    Dispatch due pending outbox events.

    Safe to run periodically and concurrently from multiple workers.
    """

    event_ids = (
        OrderOutboxEvent.objects
        .filter(
            status=OrderOutboxEventStatus.PENDING,
            next_attempt_at__lte=now()
        )
        .order_by("created_at")
        .values_list("id", flat=True)[:OUTBOX_BATCH_SIZE]
    )

    published = 0
    skipped = 0
    failed = 0

    for event_id in event_ids:
        result = _dispatch_order_outbox_event(event_id)

        if result == "published":
            published += 1
        elif result == "failed":
            failed += 1
        else:
            skipped += 1

    logger.info(
        "Outbox dispatch complete: published=%s failed=%s skipped=%s",
        published,
        failed,
        skipped,
    )

    return {
        "published": published,
        "failed": failed,
        "skipped": skipped
    }
