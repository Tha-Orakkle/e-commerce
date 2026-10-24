from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils.timezone import now

from order.models import (
    Order,
    OrderGroup,
    OrderGroupStatus,
    OrderStatus,
    PaymentMethod,
)
from order.tasks import (
    _cancel_group_if_still_unpaid,
    cancel_unpaid_orders_older_than_4_hours,
    restock_inventory_with_cancelled_order,
)
from payment.models import PaymentStatus

DELAY_PATH = "order.tasks.restock_inventory_with_cancelled_order.delay"


# ==========================================================
# HELPERS
# ==========================================================
@pytest.fixture
def cancelled_order_with_items(shopowner, order_group_factory, order_factory,
                               order_item_factory, product_factory):
    """
    Build a cancelled order with one item of quantity 3 for a product
    holding 10 units. Returns (order, product).
    """
    def build(status=OrderStatus.CANCELLED):
        shop = shopowner.owned_shop
        product = product_factory(shop=shop)
        product.inventory.add(qty=10, handle="test")
        group = order_group_factory()
        order = order_factory(group=group, shop=shop, status=status)
        order_item_factory(order=order, product=product, quantity=3)
        return order, product

    return build


def stock_of(product):
    product.inventory.refresh_from_db()
    return product.inventory.stock


def age(group, hours):
    """
    Backdate an order group (created_at is auto_now_add).
    """
    OrderGroup.objects.filter(id=group.id).update(
        created_at=now() - timedelta(hours=hours)
    )


# ==========================================================
# RESTOCK IDEMPOTENCY
# ==========================================================
def test_restock_returns_stock_and_marks_order(cancelled_order_with_items):
    """
    Test that restocking a cancelled order returns its items to stock
    and records that it happened.
    """
    order, product = cancelled_order_with_items()

    restock_inventory_with_cancelled_order(str(order.id))

    order.refresh_from_db()
    assert stock_of(product) == 13
    assert order.restocked_at is not None


def test_restock_twice_only_adds_stock_once(cancelled_order_with_items):
    """
    Test that re-running the restock for the same order (a task retry or
    duplicate delivery) does not add the stock a second time.
    """
    order, product = cancelled_order_with_items()

    restock_inventory_with_cancelled_order(str(order.id))
    result = restock_inventory_with_cancelled_order(str(order.id))

    assert stock_of(product) == 13
    assert "already restocked" in result


def test_restock_skips_orders_that_are_not_cancelled(
    cancelled_order_with_items
):
    """
    Test that an order which is not cancelled is never restocked.
    """
    order, product = cancelled_order_with_items(status=OrderStatus.PENDING)

    restock_inventory_with_cancelled_order(str(order.id))

    order.refresh_from_db()
    assert stock_of(product) == 10
    assert order.restocked_at is None


def test_restock_for_unknown_order_does_nothing(db):
    """
    Test that an unknown order id is skipped without error.
    """
    result = restock_inventory_with_cancelled_order(
        "00000000-0000-0000-0000-000000000000"
    )

    assert "not restocked" in result


def test_group_restock_then_order_restock_does_not_double_count(
    shopowner, order_group_factory, order_factory, order_item_factory,
    product_factory
):
    """
    Test that group-level and order-level dispatch for the same orders
    cannot both add stock.
    """
    shop = shopowner.owned_shop
    group = order_group_factory()
    products = []
    orders = []
    for _ in range(2):
        product = product_factory(shop=shop)
        product.inventory.add(qty=10, handle="test")
        order = order_factory(
            group=group, shop=shop, status=OrderStatus.CANCELLED
        )
        order_item_factory(order=order, product=product, quantity=2)
        products.append(product)
        orders.append(order)

    restock_inventory_with_cancelled_order(str(group.id), order_group=True)
    restock_inventory_with_cancelled_order(str(orders[0].id))
    restock_inventory_with_cancelled_order(str(group.id), order_group=True)

    assert [stock_of(p) for p in products] == [12, 12]


# ==========================================================
# CANCEL UNPAID ORDERS
# ==========================================================
def test_cancel_task_cancels_old_unpaid_digital_group(
    mocker, django_capture_on_commit_callbacks, customer,
    order_group_factory, order_factory, payment_factory
):
    """
    Test that an old, unpaid DIGITAL group and its orders are cancelled
    and each order is queued for restock.
    """
    mock_delay = mocker.patch(DELAY_PATH)
    group = order_group_factory(
        user=customer,
        payment_method=PaymentMethod.DIGITAL,
        total_amount=Decimal("1000.00")
    )
    payment_factory(group)
    orders = [order_factory(group=group) for _ in range(2)]
    age(group, hours=5)

    with django_capture_on_commit_callbacks(execute=True):
        result = cancel_unpaid_orders_older_than_4_hours()

    group.refresh_from_db()
    assert group.status == OrderGroupStatus.CANCELLED
    assert group.cancelled_at is not None
    for order in Order.objects.filter(group=group):
        assert order.status == OrderStatus.CANCELLED
        assert order.cancelled_at is not None
    queued = sorted(call.args[0] for call in mock_delay.call_args_list)
    assert queued == sorted(str(order.id) for order in orders)
    assert "TOTAL ORDER GROUPS: 1" in result
    assert "Cancelled 2 unpaid orders" in result


def test_cancel_task_skips_recent_groups(
    mocker, customer, order_group_factory, order_factory
):
    """
    Test that a group younger than 4 hours is left alone.
    """
    mocker.patch(DELAY_PATH)
    group = order_group_factory(
        user=customer, payment_method=PaymentMethod.DIGITAL
    )
    order_factory(group=group)
    age(group, hours=1)

    cancel_unpaid_orders_older_than_4_hours()

    group.refresh_from_db()
    assert group.status == OrderGroupStatus.PENDING


def test_cancel_task_skips_cash_groups(
    mocker, customer, order_group_factory, order_factory
):
    """
    Test that cash orders are never auto-cancelled.
    """
    mocker.patch(DELAY_PATH)
    group = order_group_factory(
        user=customer, payment_method=PaymentMethod.CASH
    )
    order_factory(group=group)
    age(group, hours=5)

    cancel_unpaid_orders_older_than_4_hours()

    group.refresh_from_db()
    assert group.status == OrderGroupStatus.PENDING


def test_cancel_task_skips_group_with_a_paid_order(
    mocker, customer, order_group_factory, order_factory
):
    """
    Test that a group with any paid order is not cancelled.
    """
    mocker.patch(DELAY_PATH)
    group = order_group_factory(
        user=customer, payment_method=PaymentMethod.DIGITAL
    )
    order_factory(group=group, is_paid=True)
    order_factory(group=group)
    age(group, hours=5)

    cancel_unpaid_orders_older_than_4_hours()

    group.refresh_from_db()
    assert group.status == OrderGroupStatus.PENDING


def test_cancel_task_skips_group_whose_payment_was_verified(
    mocker, customer, order_group_factory, order_factory, payment_factory
):
    """
    Test the race this guards against: the group still looks unpaid
    (its orders are not yet flagged) but the payment has been verified,
    so the lock-and-recheck must leave it alone.
    """
    mock_delay = mocker.patch(DELAY_PATH)
    group = order_group_factory(
        user=customer, payment_method=PaymentMethod.DIGITAL
    )
    order_factory(group=group)
    payment_factory(group, status=PaymentStatus.VERIFIED)
    age(group, hours=5)

    cancel_unpaid_orders_older_than_4_hours()

    group.refresh_from_db()
    assert group.status == OrderGroupStatus.PENDING
    assert not Order.objects.filter(
        group=group, status=OrderStatus.CANCELLED
    ).exists()
    mock_delay.assert_not_called()


def test_cancel_group_recheck_ignores_group_no_longer_pending(
    mocker, customer, order_group_factory, order_factory
):
    """
    Test that the locked re-check skips a group that changed state after
    it was selected (e.g. already cancelled by the customer).
    """
    mock_delay = mocker.patch(DELAY_PATH)
    group = order_group_factory(
        user=customer,
        payment_method=PaymentMethod.DIGITAL,
        status=OrderGroupStatus.CANCELLED
    )
    order_factory(group=group)
    age(group, hours=5)

    result = _cancel_group_if_still_unpaid(group.id, now())

    assert result is None
    mock_delay.assert_not_called()
